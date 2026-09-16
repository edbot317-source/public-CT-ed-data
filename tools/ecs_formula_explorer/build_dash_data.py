"""Build ecs_dash_data.json for the ECS Formula Explorer from the clean ECS panels.

Inputs (repo clean-data/ and data/): town_year_ecs_inputs.csv, town_year_ecs_entitlement.csv,
cpi-u-annual-avg-fred.csv, data/ecs/acs/acs5_subject_ct_towns_{vintage}.csv (mean HH income).
Output: ecs_dash_data.json next to this script (and the scratch copy path if given as argv[1]).
"""
import json, os, re, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
# Two layouts: the working repo (clean-data/, data/) or the public release (public-CT-ed-data/tools/ecs_formula_explorer,
# datasets under data/<key>/<key>.csv, ACS mean-income files under tools/ecs_formula_explorer/inputs).
PUBLIC = os.path.exists(os.path.join(HERE, "..", "..", "datapackage.json"))
BASE = os.path.abspath(os.path.join(HERE, "..", "..")) if PUBLIC else os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def clean(key):
    return os.path.join(BASE, "data", key, f"{key}.csv") if PUBLIC else os.path.join(BASE, "clean-data", f"{key}.csv")


ACS_DIR = os.path.join(HERE, "inputs") if PUBLIC else os.path.join(BASE, "data", "ecs", "acs")
CPI_PATH = os.path.join(BASE, "data", "cpi_u_deflator", "raw", "cpi-u-annual-avg-fred.csv") if PUBLIC else os.path.join(BASE, "data", "cpi-u-annual-avg-fred.csv")
p = pd.read_csv(clean("town_year_ecs_inputs"))
e = pd.read_csv(clean("town_year_ecs_entitlement"))
cpi = pd.read_csv(CPI_PATH)
cpi["year"] = pd.to_datetime(cpi.observation_date).dt.year
cpi = cpi.dropna(subset=["CPIAUCSL"])
# Employment Cost Index, state and local government total compensation (BLS CIU3010000000000I via FRED),
# calendar-year averages (74_download_eci.py); an alternative to CPI-U for indexing the foundation
ECI_PATH = os.path.join(HERE, "inputs", "eci-state-local-govt-fred.csv") if PUBLIC else os.path.join(BASE, "data", "eci-state-local-govt-fred.csv")
eci = pd.read_csv(ECI_PATH) if os.path.exists(ECI_PATH) else None
eci_complete = eci[eci.quarters == 4] if eci is not None else None

# mean household income by town and ACS vintage (S1901_C01_013E)
ahi = {}
for f in sorted(os.listdir(ACS_DIR)):
    m = re.match(r"acs5_subject_ct_towns_(\d{4})\.csv", f)
    if not m:
        continue
    v = int(m.group(1))
    a = pd.read_csv(os.path.join(ACS_DIR, f), dtype=str)
    a = a[a["NAME"].str.contains(" town,| city,", regex=True)].copy()
    a["town"] = a["NAME"].str.replace(r"\s+(town|city),.*$", "", regex=True)
    a["mean"] = pd.to_numeric(a["S1901_C01_013E"], errors="coerce")
    a.loc[a["mean"] < 0, "mean"] = np.nan
    ahi[v] = a.set_index("town")["mean"].to_dict()

# NCEP (net current expenditures per pupil) by town district and fiscal year, same-year alignment
ncep = pd.read_csv(clean("district_year_ncep"))
ncep = ncep[ncep.district_code <= 169]
NCEP = {(int(r.district_code), int(r.fiscal_year)): (float(r.nce), float(r.adm), float(r.ncep)) for r in ncep.itertuples()}

# SEDA 2025.2 achievement (GCS grade levels vs the national average), all students, by town and spring test year
seda = pd.read_csv(clean("district_year_seda_gcs"))
seda = seda[(seda.subgroup == "all") & seda.town_code.notna()]
SEDA = {(int(r.town_code), int(r.fiscal_year)): (r.grade_levels_vs_national, r.grade_levels_vs_national_mth, r.grade_levels_vs_national_rla,
                                                 r.gcs_mn_avg_eb_se, r.tot_asmts, r.town_match, r.district) for r in seda.itertuples()}
SEDAH = {}   # town -> {spring year: [overall, math, reading, tests]} over every SEDA year (2009-2025)
for (tc, fy), v in SEDA.items():
    SEDAH.setdefault(tc, {})[fy] = [round(float(v[0]), 3), (round(float(v[1]), 3) if pd.notna(v[1]) else None),
                                    (round(float(v[2]), 3) if pd.notna(v[2]) else None), int(v[4])]

# simulation inputs: k (grade levels per SD) by grade x subject, and per-town baseline test weights
kpath = clean("seda_k_grade_subject")
bpath = clean("town_grade_subject_seda_baseline")
KTAB, BASEW = None, {}
if os.path.exists(kpath) and os.path.exists(bpath):
    kt = pd.read_csv(kpath)
    KTAB = {f"{int(r.grade)}_{r.subject}": round(float(r.k), 4) for r in kt.itertuples()}
    bw = pd.read_csv(bpath)
    for r in bw.itertuples():
        BASEW.setdefault(int(r.town_code), {})[f"{int(r.grade)}_{r.subject}"] = [round(float(r.n_tests), 1), round(float(r.vs_national_baseline), 3)]

towns = sorted(p.town_code.unique())
names = p.drop_duplicates("town_code").set_index("town_code").town.to_dict()
# every year with a full calculation worksheet: FY2019 (first PA 17-2 formula year) through FY2027.
# FY2018 grants were legislated with holdbacks, not computed, so the dashboard starts at FY2019.
START_YEAR = 2019
years = [int(fy) for fy in sorted(p.fiscal_year.unique()) if fy >= START_YEAR]
prm = pd.read_csv(clean("ecs_parameters" if not PUBLIC else "ecs_formula_parameters"))
prm = prm[prm.is_primary].set_index("fiscal_year")
NOTES = {2020: "CSDE's final used revised Public Investment Community rankings for a few Alliance towns",
         2021: "same PIC revision carried in the prior-year grant",
         2022: "worksheet is the School and State Finance Project's copy (no official FY2022 shell in hand)",
         2027: "awaits CSDE's final calculation"}

policy = {}
for fy in years:
    d = p[p.fiscal_year == fy]
    mhi_year = int(d.mhi_year.iloc[0])
    ahi_vals = [ahi.get(mhi_year, {}).get(names[tc]) for tc in towns]
    ahi_vals = [v for v in ahi_vals if v is not None and not np.isnan(v)]
    q = prm.loc[fy]
    policy[fy] = {"w_frpl": float(q.need_weight_frpl), "cp_thr": float(q.conc_pov_threshold),
                  "w_cp": float(q.need_weight_conc_pov), "w_ell": float(q.need_weight_ell),
                  "thr_factor": float(q.wealth_threshold_factor), "w_engl": float(q.engl_weight), "w_mhi": float(q.mhi_weight),
                  "min_bar": float(q.min_bar_nonalliance), "min_bar_hh": float(q.min_bar_alliance),
                  "foundation": float(q.foundation), "pct_under": float(q.pct_under_applied), "pct_over": float(q.pct_over_applied),
                  "gap_base": str(q.phase_in_gap_base), "start_base": str(q.phase_in_start_base), "hh_fy17": bool(q.hh_floor_fy2017),
                  "source_type": str(q.source_type), "note": NOTES.get(fy, ""), "statute": str(q.phase_in_statute),
                  "engl_median": float(d.engl_median.iloc[0]) if pd.notna(d.engl_median.iloc[0]) else float(d.engl_per_capita.median()),
                  "mhi_median": float(d.mhi_median.iloc[0]) if pd.notna(d.mhi_median.iloc[0]) else float(d.mhi.median()),
                  "ahi_median": float(np.median(ahi_vals)) if ahi_vals else None, "ahi_n": len(ahi_vals),
                  "mhi_year": mhi_year, "count_date": str(d.count_date.iloc[0]), "source_sheet": str(d.source_sheet.iloc[0])}


def f(v):
    if v is None or (isinstance(v, float) and np.isnan(v)) or pd.isna(v):
        return None
    v = float(v)
    return int(v) if v.is_integer() else v


E = e.pivot(index="town_code", columns="fiscal_year", values="entitlement")
out = {"towns": [], "years": years, "start_year": START_YEAR, "policy": {str(k): v for k, v in policy.items()},
       "cpi": {int(r.year): float(r.CPIAUCSL) for r in cpi.itertuples()},
       "eci": ({int(r.year): float(r.eci_avg) for r in eci_complete.itertuples()} if eci_complete is not None else None),
       "ent_years": sorted(int(x) for x in e.fiscal_year.unique())}
FIELDS = [("res", "resident_students"), ("frpl", "frpl_count"), ("ell", "ell_count"), ("engl", "engl_avg"),
          ("pop", "population"), ("eepc", "engl_per_capita"), ("mhi", "mhi"), ("pic", "pic_bar_adjustment"),
          ("rsd", "rsd_bonus"), ("end", "endowed_bonus"), ("fy17", "fy2017_actual"), ("prior", "prior_year_entitlement"),
          ("ff", "fully_funded_grant"), ("shell_ent", "entitlement"), ("need", "need_students"), ("bar", "final_base_aid_ratio")]
for tc in towns:
    d = p[p.town_code == tc].set_index("fiscal_year")
    t = {"code": int(tc), "name": names[tc], "ent": {int(fy): f(E.loc[tc, fy]) for fy in E.columns}, "yr": {}}
    for fy in years:
        r = d.loc[fy]
        row = {k: f(r[c]) for k, c in FIELDS}
        row["hh"] = int((r.alliance_flag == 1) or (r.psd_flag == 1))
        row["alliance"] = int(r.alliance_flag == 1)
        row["psd"] = int(r.psd_flag == 1)
        row["drg"] = r.drg if isinstance(r.drg, str) else None
        row["ahi"] = f(ahi.get(policy[fy]["mhi_year"], {}).get(names[tc]))
        nc = NCEP.get((int(tc), fy))
        row["nce"], row["adm"], row["ncep"] = (f(nc[0]), f(nc[1]), f(nc[2])) if nc else (None, None, None)
        sd = SEDA.get((int(tc), fy))
        if sd:
            row["seda"] = {"gl": round(float(sd[0]), 3), "mth": (round(float(sd[1]), 3) if pd.notna(sd[1]) else None),
                           "rla": (round(float(sd[2]), 3) if pd.notna(sd[2]) else None), "se": round(float(sd[3]), 3),
                           "n": int(sd[4]), "via": sd[5], "district": sd[6]}
        else:
            row["seda"] = None
        t["yr"][fy] = row
    t["simw"] = BASEW.get(int(tc))          # {grade_subject: [n_tests, baseline grade levels vs national]}
    t["sedah"] = SEDAH.get(int(tc), {})     # {spring year: [overall, math, reading, tests]}
    out["towns"].append(t)
# Massachusetts Chapter 70 style rule: per-town inputs, the FY2025 DESE rate schedule and parameters (79_build_ma_inputs.py)
MA_PATH = clean("town_year_ma_inputs"); RATES_PATH = clean("ma_fy2025_foundation_rates"); MAP_PATH = clean("ma_chapter70_parameters")
if os.path.exists(MA_PATH) and os.path.exists(RATES_PATH):
    ma = pd.read_csv(MA_PATH); rates = pd.read_csv(RATES_PATH)
    for t in out["towns"]:
        d = ma[ma.town_code == t["code"]].set_index("fiscal_year")
        t["ma"] = {int(fy): {"sh": [round(float(d.loc[fy, c]), 5) for c in ("share_pk", "share_k", "share_el", "share_ms", "share_hs")],
                             "waf": round(float(d.loc[fy, "wage_adjustment_factor"]), 5), "eqv": f(d.loc[fy, "equalized_valuation"]),
                             "inc": f(d.loc[fy, "aggregate_household_income"]), "county": str(d.loc[fy, "county"])}
                   for fy in years if fy in d.index}
    out["ma"] = {"rates": {r.column: [round(float(r.total), 2), round(float(r.waf_applicable), 2)] for r in rates.itertuples()},
                 "li_upper": [5.99, 11.99, 17.99, 23.99, 29.99, 35.99, 41.99, 47.99, 53.99, 69.99, 79.99, 100],
                 "sped_in": 0.0393, "sped_out": 0.01, "pk_weight": 0.5, "lam": 0.59, "cap": 0.825, "min_aid": 104,
                 "inflation_cap": 1.045, "rates_year": 2025,
                 "source": "DESE FY2025 Chapter 70 formula workbook (chapter-2025.xlsm, Rates and parameters sheets); MGL c.70 s.2"}
out["sim"] = {"k": KTAB, "beta": 0.0343, "beta_se": 0.00681, "beta_tau": 0.0211, "beta_li": 0.0312, "beta_nli": 0.0161,
              "beta_col3": 0.0359, "dose_years": 4, "base_year": 2018, "baseline_years": [2023, 2024, 2025],
              "source": "Jackson & Mackevicius (2024) AEJ: Applied 16(1) Table 3; SEDA 2025.2"}

dest = [os.path.join(HERE, "ecs_dash_data.json")] + sys.argv[1:]
for path in dest:
    with open(path, "w") as fh:
        json.dump(out, fh, separators=(",", ":"))
print("towns", len(out["towns"]), "| ahi coverage by FY:", {fy: policy[fy]["ahi_n"] for fy in years},
      "| KB", os.path.getsize(dest[0]) // 1024)
