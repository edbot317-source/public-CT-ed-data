
from __future__ import annotations
from pathlib import Path
from io import StringIO
import csv, re, shutil, tempfile, runpy
import pandas as pd
import numpy as np

HERE = Path(__file__).resolve().parent
RAW = HERE / 'raw'
KEY = HERE.name
DATA = HERE.parent

def fiscal_year(label: str) -> int:
    a,b = str(label).split('-')
    return int(a[:2] + b)

def clean_num(x):
    s = str(x).replace('$','').replace(',','').replace('%','').replace('"','').strip()
    if s in ['', '*', 'N/A', 'nan', 'None']:
        return pd.NA
    return s

def money_series(s):
    return pd.to_numeric(s.map(clean_num) if hasattr(s,'map') else s, errors='coerce')

def read_from_header(path: Path, needle: str) -> pd.DataFrame:
    lines = path.read_text(encoding='utf-8-sig', errors='replace').splitlines()
    for i,line in enumerate(lines):
        if needle in line:
            return pd.read_csv(StringIO('\n'.join(lines[i:])), dtype=str)
    raise RuntimeError(f'No header {needle!r} in {path}')

def copytree(src: Path, dst: Path):
    if src.exists():
        shutil.copytree(src, dst, dirs_exist_ok=True)

def copy_files(src: Path, dst: Path, pattern='*'):
    dst.mkdir(parents=True, exist_ok=True)
    for p in src.glob(pattern):
        if p.is_file() and p.name not in {'_cookies.txt'} and p.suffix.lower() != '.png':
            shutil.copy2(p, dst/p.name)

def cpi_source(tmp: Path):
    cp = DATA/'cpi_u_deflator'/'cpi_u_deflator.csv'
    raw = RAW/'cpi-u-annual-avg-fred.csv'
    out = tmp/'data'/'cpi-u-annual-avg-fred.csv'
    out.parent.mkdir(parents=True, exist_ok=True)
    if raw.exists():
        shutil.copy2(raw, out)
    elif cp.exists():
        df = pd.read_csv(cp)[['observation_date','cpi_u']].rename(columns={'cpi_u':'CPIAUCSL'})
        df.to_csv(out, index=False)

def replay_clean(script_name: str, output: str, setup, nullable_ints: bool=False):
    # nullable_ints=True keeps integer columns that contain blanks as Int64 on the
    # read-back (otherwise pandas upcasts them to float and writes "7.0").
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        tmp=Path(td); (tmp/'code').mkdir(); (tmp/'clean-data').mkdir(); (tmp/'data').mkdir()
        setup(tmp)
        shutil.copy2(RAW/'original_scripts'/script_name, tmp/'code'/script_name)
        runpy.run_path(str(tmp/'code'/script_name), run_name='__main__')
        kw = {'dtype_backend': 'numpy_nullable'} if nullable_ints else {}
        return pd.read_csv(tmp/'clean-data'/output, **kw)

def build_district_year_enrollment():
    def setup(t): copytree(RAW, t/'data'/'enrollment')
    return replay_clean('07_clean_enrollment.py', 'district_year_enrollment.csv', setup)

def build_district_year_spending():
    def setup(t): copy_files(RAW, t/'data'/'per-pupil-expenditures-by-function', 'spending-*.csv'); cpi_source(t)
    return replay_clean('01_clean_district.py', 'district_year_spending.csv', setup)

def build_district_year_ppe_archived():
    def setup(t):
        copy_files(RAW, t/'data'/'per-pupil-expenditures-archived', 'ppe-archived-*.csv')
        copy_files(RAW/'_dependencies', t/'clean-data', '*.csv')
        cpi_source(t)
    return replay_clean('10_clean_archived_ppe.py', 'district_year_ppe_archived.csv', setup)

def build_district_year_ppe_extended():
    def setup(t):
        copy_files(RAW/'archived', t/'data'/'per-pupil-expenditures-archived', 'ppe-archived-*.csv')
        copy_files(RAW/'current', t/'data'/'per-pupil-expenditures-by-function', 'spending-*.csv')
        copy_files(RAW/'_dependencies', t/'clean-data', '*.csv')
        cpi_source(t)
        shutil.copy2(RAW/'original_scripts'/'01_clean_district.py', t/'code'/'01_clean_district.py')
        runpy.run_path(str(t/'code'/'01_clean_district.py'), run_name='__main__')
    return replay_clean('10_clean_archived_ppe.py', 'district_year_ppe_extended.csv', setup)

def build_district_year_revenue():
    def setup(t): copy_files(RAW, t/'data'/'revenue-sources', 'revenue-*.csv'); copy_files(RAW/'_dependencies', t/'clean-data', '*.csv')
    return replay_clean('04_clean_revenue.py', 'district_year_revenue.csv', setup)

def build_district_year_accountability():
    def setup(t): copy_files(RAW, t/'data'/'accountability', '*')
    return replay_clean('35_clean_accountability.py', 'district_year_accountability.csv', setup)

def build_cpi_u_deflator():
    df=pd.read_csv(RAW/'cpi-u-annual-avg-fred.csv')
    df['year']=pd.to_datetime(df['observation_date']).dt.year
    df=df.rename(columns={'CPIAUCSL':'cpi_u'})
    cpi_2025=df.loc[df['year']==2025,'cpi_u'].iloc[0]
    df['deflator']=cpi_2025/df['cpi_u']
    return df[['year','observation_date','cpi_u','deflator']]

def add_cpi(df):
    cpi=pd.read_csv(DATA/'cpi_u_deflator'/'cpi_u_deflator.csv') if (DATA/'cpi_u_deflator'/'cpi_u_deflator.csv').exists() else build_cpi_u_deflator()
    return df.merge(cpi[['year','cpi_u','deflator']], left_on='fiscal_year', right_on='year', how='left').drop(columns=['year'])

def build_per_pupil_expenditures_by_object():
    frames=[]
    for f in sorted(RAW.glob('object-*.csv')):
        fy=int(re.search(r'(\d{4})-(\d{4})', f.name).group(2)); df=read_from_header(f,'"District","District Code"')
        df.columns=df.columns.str.strip().str.strip('"')
        df['District']=df['District'].str.strip('"').str.strip(); df['District Code']=df['District Code'].str.replace(r'[="]','',regex=True).str.strip(); df['Object']=df['Object'].str.strip('"').str.strip()
        for c in ['Expenditures','Pupils','Pupil Basis','PPE']: df[c]=money_series(df[c])
        df['fiscal_year']=fy; frames.append(df[['District','District Code','fiscal_year','Object','Expenditures','Pupils','Pupil Basis','PPE']])
    out=pd.concat(frames,ignore_index=True).rename(columns={'District':'district','District Code':'district_code','Object':'object','Expenditures':'expenditures','Pupils':'pupils','Pupil Basis':'pupil_basis','PPE':'ppe'})
    out=add_cpi(out); out['expenditures_real']=out['expenditures']*out['deflator']; out['ppe_real']=out['ppe']*out['deflator']; return out

def build_total_annual_expenditures_archived():
    return pd.concat([pd.read_csv(f) for f in sorted(RAW.glob('total-exp-archived-*.csv'))], ignore_index=True)

def district_xwalk():
    p=DATA/'district_year_enrollment'/'district_year_enrollment.csv'
    if p.exists():
        d=pd.read_csv(p,dtype={'District Code':str}); return dict(d.sort_values('fiscal_year').drop_duplicates('District',keep='last')[['District','District Code']].dropna().values)
    return {}

def parse_sped_arch(f):
    fy=fiscal_year(re.search(r'(\d{4}-\d{2})', f.name).group(1)); df=pd.read_csv(f,skiprows=4,dtype=str); df.columns=df.columns.str.strip().str.strip('"'); df=df.rename(columns={df.columns[0]:'District'}); df['District']=df['District'].str.lstrip('=').str.strip('"').str.strip(); df=df[df['District'].str.len()>0].copy(); rows=[]
    for c in [x for x in df.columns if x!='District']:
        t=df[['District',c]].copy().rename(columns={c:'amount'}); t['expenditure_category']=c; rows.append(t)
    out=pd.concat(rows,ignore_index=True); out['fiscal_year']=fy; out['district_code']=out['District'].map(district_xwalk()); out['amount']=money_series(out['amount']); out['source_format']='archived_wide'; return out.rename(columns={'District':'district'})[['district','district_code','fiscal_year','expenditure_category','amount','source_format']]

def parse_sped_new(f):
    fy=fiscal_year(re.search(r'(\d{4}-\d{2})', f.name).group(1)); df=pd.read_csv(f,skiprows=2,dtype=str); df.columns=df.columns.str.strip().str.strip('"'); df['District']=df['District'].str.strip('"').str.strip().replace('',pd.NA).ffill(); df['District Code']=df['District Code'].str.replace(r'[="]','',regex=True).str.strip().replace('',pd.NA).ffill(); df['Description']=df['Description'].str.strip('"').str.strip(); df['amount']=money_series(df['Amount']); df['fiscal_year']=fy; df['source_format']='current_long'; return df.rename(columns={'District':'district','District Code':'district_code','Description':'expenditure_category'})[['district','district_code','fiscal_year','expenditure_category','amount','source_format']]

def build_special_education_expenditures():
    frames=[parse_sped_arch(f) for f in sorted(RAW.glob('sped-exp-archived-*.csv'))]+[parse_sped_new(f) for f in sorted(RAW.glob('sped-exp-new-*.csv'))]
    out=pd.concat(frames,ignore_index=True).dropna(subset=['amount']); out=add_cpi(out); out['amount_real']=out['amount']*out['deflator']; return out

def parse_sbac(f, high=False):
    fy=fiscal_year(re.search(r'(\d{4}-\d{2})', f.name).group(1)); df=read_from_header(f,'"District","District Code","Subject"'); df.columns=df.columns.str.strip().str.strip('"'); df['District']=df['District'].str.strip('"').str.strip().replace('',pd.NA).ffill(); df['District Code']=df['District Code'].str.replace(r'[="]','',regex=True).str.strip().replace('',pd.NA).ffill(); df['Subject']=df['Subject'].str.strip('"').str.strip().ffill()
    if high:
        hn=[c for c in df.columns if 'High Needs' in c][0]; df=df[df[hn].isin(['Y','N'])].copy(); needs=df[hn].map({'Y':'High Needs','N':'Non-High Needs'})
    else: needs='All Students'
    out=pd.DataFrame({'district':df['District'],'district_code':df['District Code'],'fiscal_year':fy,'subject':df['Subject'],'needs_group':needs,'total_students':money_series(df['Total Number of Students']),'total_tested':money_series(df['Total Number Tested']),'participation_rate':money_series(df['Smarter Balanced Participation Rate']),'n_scored':money_series(df['Total Number with Scored Tests'])})
    counts=[c for c in df.columns if c.startswith('Count')]; pcts=[c for c in df.columns if c.startswith('%')]; names=['level1','level2','level3','level4','level3_4']
    for i,n in enumerate(names): out[f'{n}_count']=money_series(df[counts[i]]); out[f'{n}_pct']=money_series(df[pcts[i]])
    return out.rename(columns={'level3_4_pct':'pct_prof'}).drop_duplicates().reset_index(drop=True)

def build_sbac():
    return pd.concat([parse_sbac(f,False) for f in sorted((RAW/'all_students').glob('sbac-*.csv'))]+[parse_sbac(f,True) for f in sorted((RAW/'high_needs').glob('sbac-high-needs-*.csv'))], ignore_index=True)

def build_sat():
    frames=[]
    for f in sorted((RAW/'all_students').glob('sat-*.csv')):
        d=pd.read_csv(f); d.insert(3,'needs_group','All Students'); frames.append(d)
    frames += [pd.read_csv(f) for f in sorted((RAW/'high_needs').glob('sat-high-needs-*.csv'))]
    return pd.concat(frames,ignore_index=True).rename(columns={'District':'district'}).drop_duplicates().reset_index(drop=True)

def build_graduation_4yr():
    frames=[]
    for f in sorted((RAW/'all_students').glob('grad-*.csv')):
        d=pd.read_csv(f); d.insert(2,'needs_group','All Students'); frames.append(d)
    frames += [pd.read_csv(f) for f in sorted((RAW/'high_needs').glob('grad-high-needs-*.csv'))]
    return pd.concat(frames,ignore_index=True).rename(columns={'District':'district'}).drop_duplicates().reset_index(drop=True)

def build_graduation_5yr():
    frames=[]
    for f in sorted((RAW/'all_students').glob('grad5-*.csv')):
        d=pd.read_csv(f); d.insert(2,'needs_group','All Students'); frames.append(d)
    frames += [pd.read_csv(f) for f in sorted((RAW/'high_needs').glob('grad5-high-needs-*.csv'))]
    return pd.concat(frames,ignore_index=True).rename(columns={'District':'district'}).drop_duplicates().reset_index(drop=True)

def build_swd_outplacement():
    df=pd.read_csv(RAW/'swd_district_all_years.csv'); df['fiscal_year']=df['School Year'].map(fiscal_year); return df.rename(columns={'School Year':'school_year','Type':'placement_type','DistrictName':'district','Count*':'count','Percent*':'percent'})[['district','fiscal_year','school_year','placement_type','count','percent']]

def _ecs_csde_setup(t):
    copy_files(RAW, t/'data'/'ecs'/'csde', '*.xlsx')

def _ecs_ssfp_setup(t):
    # 65_parse_ecs_shells.py: official OFA shells (raw/ofa, primary) + SSFP copies (raw, alternates and FY2018/FY2022),
    # and CSDE's entitlement panel for town names and the FY2017 base
    copy_files(RAW, t/'data'/'ecs'/'ssfp', '*.xls*')
    copy_files(RAW/'ofa', t/'data'/'ecs'/'ofa', '*.xls*')
    ent = DATA/'town_year_ecs_entitlement'/'town_year_ecs_entitlement.csv'
    if ent.exists():
        shutil.copy2(ent, t/'clean-data'/'town_year_ecs_entitlement.csv')

def build_town_year_ecs_entitlement():
    return replay_clean('64_clean_ecs_csde.py', 'town_year_ecs_entitlement.csv', _ecs_csde_setup, nullable_ints=True)

def build_town_year_ecs_payment():
    return replay_clean('64_clean_ecs_csde.py', 'town_year_ecs_payment.csv', _ecs_csde_setup, nullable_ints=True)

def build_town_year_ecs_inputs():
    return replay_clean('65_parse_ecs_shells.py', 'town_year_ecs_inputs.csv', _ecs_ssfp_setup, nullable_ints=True)

def build_ecs_formula_parameters():
    return replay_clean('65_parse_ecs_shells.py', 'ecs_parameters.csv', _ecs_ssfp_setup, nullable_ints=True)

def build_district_year_ncep():
    def setup(t): copy_files(RAW, t/'data'/'ncep', '*.pdf'); copy_files(RAW, t/'data'/'ncep', '*.xls')
    return replay_clean('69_clean_ncep.py', 'district_year_ncep.csv', setup, nullable_ints=True)

def build_district_year_seda_gcs():
    def setup(t):
        copy_files(RAW, t/'data'/'seda', '*_CT.csv')
        copy_files(RAW/'_dependencies', t/'clean-data', '*.csv')   # town names/codes for the town mapping
    return replay_clean('71_clean_seda_ct.py', 'district_year_seda_gcs.csv', setup, nullable_ints=True)

def _seda73_setup(t):
    # 73_seda_k_and_baselines.py: k from SEDA's published NAEP parameters (Table 9) + CT grade-level baselines.
    # The national long files it uses for the regression cross-check are ~119 MB each and are not redistributed;
    # the script falls back to the logged per-year slopes (k_gcs_on_cs_by_year.csv) when they are absent.
    kraw = DATA/'seda_k_grade_subject'/'raw'; braw = DATA/'town_grade_subject_seda_baseline'/'raw'
    copy_files(braw, t/'data'/'seda', '*_CT.csv')
    copy_files(kraw, t/'data'/'seda', 'seda_table9_naep_params.csv')
    (t/'output'/'ecs'/'sim').mkdir(parents=True, exist_ok=True)
    shutil.copy2(kraw/'k_gcs_on_cs_by_year.csv', t/'output'/'ecs'/'sim'/'k_by_year.csv')
    copy_files(braw/'_dependencies', t/'clean-data', '*.csv')
    (t/'output'/'ecs'/'dashboard'/'sim').mkdir(parents=True, exist_ok=True)
    shutil.copy2(kraw/'original_scripts'/'seda_spending_sim.py', t/'output'/'ecs'/'dashboard'/'sim'/'seda_spending_sim.py')

def build_seda_k_grade_subject():
    return replay_clean('73_seda_k_and_baselines.py', 'seda_k_grade_subject.csv', _seda73_setup)

def build_town_grade_subject_seda_baseline():
    return replay_clean('73_seda_k_and_baselines.py', 'town_grade_subject_seda_baseline.csv', _seda73_setup)

def _ma_setup(t):
    # 79_build_ma_inputs.py: CCD grade enrollment, QCEW wages, ACS aggregate income and OPM grand list under raw/,
    # DESE's FY2025 workbook under raw/dese, and the clean ECS / SEDA panels it joins to
    copy_files(RAW/'ccd', t/'data'/'ma', '*.csv'); copy_files(RAW/'qcew', t/'data'/'ma', '*.csv')
    copy_files(RAW/'dese', t/'data'/'ma'/'dese', '*.xlsm')
    copy_files(RAW/'acs', t/'data'/'ecs'/'acs', '*.csv'); copy_files(RAW/'ctdata', t/'data'/'ecs'/'ctdata', '*.csv')
    for k in ('town_year_ecs_inputs', 'town_year_ecs_entitlement', 'district_year_seda_gcs'):
        src = DATA/k/f'{k}.csv'
        if src.exists():
            shutil.copy2(src, t/'clean-data'/f'{k}.csv')

def build_town_year_ma_inputs():
    return replay_clean('79_build_ma_inputs.py', 'town_year_ma_inputs.csv', _ma_setup, nullable_ints=True)

def build_ma_fy2025_foundation_rates():
    return replay_clean('79_build_ma_inputs.py', 'ma_fy2025_foundation_rates.csv', _ma_setup)

def build_ma_chapter70_parameters():
    return replay_clean('79_build_ma_inputs.py', 'ma_chapter70_parameters.csv', _ma_setup)

BUILDERS={name:obj for name,obj in globals().items() if name.startswith('build_')}
if __name__ == '__main__':
    out=BUILDERS['build_'+KEY](); out.to_csv(HERE/f'{KEY}.csv', index=False); print(f'Wrote {KEY}.csv: {len(out)} rows x {len(out.columns)} cols')
