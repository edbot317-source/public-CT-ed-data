"""
79_build_ma_inputs.py

Builds the town x fiscal-year inputs a Massachusetts Chapter 70 foundation budget and
required local contribution need for Connecticut towns, FY2019-FY2027, and copies the
FY2025 Chapter 70 rate schedule out of DESE's formula workbook.

Per town-year (clean-data/town_year_ma_inputs.csv):
  grade-band shares of resident students (pre-K, kindergarten, grades 1-5, 6-8, 9-12),
  built from NCES CCD enrollment by grade for the town's local district plus its share
  of each regional district it belongs to (share = the town's students sent to the
  region, from the ECS worksheet, over all member towns' students sent);
  county and the county/state average-wage ratio (BLS QCEW), from which the wage
  adjustment factor is 1 + (ratio - 1)/3, floored at 1 (MGL c.70 s.2);
  equalized valuation = OPM equalized net grand list for the latest grand-list year in
  the ECS window (fiscal year t uses grand list t-4);
  aggregate household income = ACS 5-year table B19025, vintage t-4 (the ECS median-income
  convention; Chapter 70 uses state income-tax returns from two years prior).

Rates (clean-data/ma_fy2025_foundation_rates.csv): the FY2025 per-pupil foundation
allotments by category for each enrollment column (7 grade bands, special education
in-district and tuitioned-out, English learners by band, low-income groups 1-12), from
the 'Rates' sheet of data/ma/dese/chapter-2025.xlsm, plus the parameters the formula
needs (low-income group thresholds, assumed special-education shares, contribution
target 59%, cap 82.5%, effort thresholds and increments, minimum aid per pupil).

Inputs: data/ma/ccd_grade_enrollment_ct.csv, ccd_directory_ct.csv, qcew_ct_county_wages.csv,
        data/ma/dese/chapter-2025.xlsm, data/ecs/ctdata/engl_by_town.csv,
        data/ecs/acs/acs5_agg_income_ct_towns_{v}.csv, acs5_ct_towns_2021.csv (county names),
        clean-data/town_year_ecs_inputs.csv, district_year_seda_gcs.csv (LEA -> town map)
"""
import os
import re

import numpy as np
import openpyxl
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MA = os.path.join(BASE, "data", "ma")
ACS = os.path.join(BASE, "data", "ecs", "acs")
CLEAN = os.path.join(BASE, "clean-data")
YEARS = list(range(2019, 2028))

# Secondary-only regional school districts and their member towns (stable membership; the
# K-12 regions come from the SEDA town mapping year by year). Region 6 (K-12, Goshen /
# Morris / Warren) and Region 20 (K-12 from FY2025, adding Litchfield) are in that mapping.
SECONDARY_REGIONS = {
    "Regional School District 01": ["Canaan", "Cornwall", "Kent", "North Canaan", "Salisbury", "Sharon"],
    "Regional School District 04": ["Chester", "Deep River", "Essex"],
    "Regional School District 05": ["Bethany", "Orange", "Woodbridge"],
    "Regional School District 07": ["Barkhamsted", "Colebrook", "New Hartford", "Norfolk"],
    "Regional School District 08": ["Andover", "Hebron", "Marlborough"],
    "Regional School District 09": ["Easton", "Redding"],
    "Regional School District 11": ["Chaplin", "Hampton", "Scotland"],
    "Regional School District 19": ["Ashford", "Mansfield", "Willington"],
}
PARAMS = [
        {"parameter": "li_group_upper_pct", "value": "5.99,11.99,17.99,23.99,29.99,35.99,41.99,47.99,53.99,69.99,79.99,100", "source": "DESE FY2025 formula workbook, Foundation Budget sheet"},
        {"parameter": "sped_in_district_share", "value": 0.0393, "source": "3.93% of K-12 non-vocational enrollment (FY2025 workbook)"},
        {"parameter": "sped_tuitioned_out_share", "value": 0.01, "source": "1% of K-12 non-vocational enrollment"},
        {"parameter": "pk_and_half_k_weight", "value": 0.5, "source": "pre-K and half-day K count 0.5 in foundation enrollment"},
        {"parameter": "target_local_share", "value": 0.59, "source": "parameters sheet: statewide target for local contribution"},
        {"parameter": "max_local_share", "value": 0.825, "source": "parameters sheet: maximum local contribution pct of foundation"},
        {"parameter": "cey_threshold_for_max", "value": 1.75, "source": "combined effort yield > 175% of foundation -> contribution set at 82.5%"},
        {"parameter": "effort_thresholds_pct", "value": "2.5,7.5", "source": "below-target shortfall thresholds for the 1% and 2% increments"},
        {"parameter": "effort_increments", "value": "0.01,0.02", "source": "increments toward target as share of foundation budget"},
        {"parameter": "effort_reduction", "value": 1.0, "source": "FY2025: 100% of excess above target removed"},
        {"parameter": "min_aid_per_pupil", "value": 104, "source": "FY2025 general appropriations act ($30 statutory floor)"},
        {"parameter": "inflation_cap", "value": 1.045, "source": "MGL c.70 s.2 foundation inflation index cap"},
        {"parameter": "waf_rule", "value": "1 + (area_wage/state_wage - 1)/3, not less than 1; county stands in for the labor market area", "source": "MGL c.70 s.2; DESE workbook"},
        {"parameter": "rates_fiscal_year", "value": 2025, "source": "DESE chapter-2025.xlsm Rates sheet"},
    ]

RATES = CATS = None
BANDS = {"pk": ["pk"], "k": ["k"], "el": ["1", "2", "3", "4", "5"], "ms": ["6", "7", "8"], "hs": ["9", "10", "11", "12"]}


def rates_from_workbook():
    wb = openpyxl.load_workbook(os.path.join(MA, "dese", "chapter-2025.xlsm"), read_only=True, data_only=True)
    ws = wb["Rates"]
    rows = list(ws.iter_rows(min_row=8, max_row=32, values_only=True))
    cats = [str(c).replace("\n", " ").strip() for c in rows[0][2:13]]   # 11 categories; column 14 is the row total
    keys = {"Pre-school": "pk", "Kindergarten half-day": "k_half", "Kindergarten full-day": "k_full", "Elementary": "el",
            "Junior/Middle": "ms", "High School": "hs", "Vocational": "voc", "Special Education in-district": "sped_in",
            "Special Education tuitioned-out": "sped_out", "English learners PK-5": "el_pk5", "English learners 6-8": "el_68",
            "English learners high school": "el_hs"}
    out = []
    for r in rows[1:]:
        if r[1] is None:
            continue
        label = str(r[1]).strip()
        key = None
        for k, v in keys.items():
            if label.lower().startswith(k.lower()):
                key = v
        m = re.match(r"Low-income group (\d+)", label)
        if m:
            key = f"li_{int(m.group(1))}"
        if key is None:
            continue
        rec = {"column": key, "label": label}
        for c, v in zip(cats, r[2:13]):
            rec[c] = float(v or 0)
        out.append(rec)
    df = pd.DataFrame(out)
    # the wage adjustment factor applies to every category except instructional materials,
    # employee benefits and special-education tuition (DESE FY2025 formula workbook, Foundation Budget sheet)
    waf_cats = [c for c in cats if not (c.startswith("Instructional Materi") or c.startswith("Employee Benefits") or c.startswith("Special Education Tu"))]
    df["total"] = df[cats].sum(axis=1)
    df["waf_applicable"] = df[waf_cats].sum(axis=1)
    return df, cats


def town_names():
    e = pd.read_csv(os.path.join(CLEAN, "town_year_ecs_entitlement.csv"))
    return e.drop_duplicates("town_code").set_index("town_code")["town"].str.strip().str.title()


def write_rates_and_params():
    rates, cats = rates_from_workbook()
    rates.to_csv(os.path.join(CLEAN, "ma_fy2025_foundation_rates.csv"), index=False)
    params = pd.DataFrame(PARAMS)
    params.to_csv(os.path.join(CLEAN, "ma_chapter70_parameters.csv"), index=False)
    return rates, cats, params


def main():
    os.makedirs(CLEAN, exist_ok=True)
    global RATES, CATS
    RATES, CATS, _ = write_rates_and_params()
    if not os.path.exists(os.path.join(MA, "ccd_grade_enrollment_ct.csv")):
        print(f"[write] ma_fy2025_foundation_rates.csv ({len(RATES)} columns x {len(CATS)} categories), ma_chapter70_parameters.csv ({len(PARAMS)}); no CCD file, town panel skipped")
        return
    names = town_names()
    code_of = {v.upper(): k for k, v in names.items()}
    ecs = pd.read_csv(os.path.join(CLEAN, "town_year_ecs_inputs.csv"))
    seda = pd.read_csv(os.path.join(CLEAN, "district_year_seda_gcs.csv"))
    seda["leaid"] = seda.sedaadmin.astype(str).str.zfill(7)
    grade = pd.read_csv(os.path.join(MA, "ccd_grade_enrollment_ct.csv")); grade["leaid"] = grade.leaid.astype(str).str.zfill(7)
    direc = pd.read_csv(os.path.join(MA, "ccd_directory_ct.csv")); direc["leaid"] = direc.leaid.astype(str).str.zfill(7)
    lea_name = direc.sort_values("year").drop_duplicates("leaid", keep="last").set_index("leaid")["lea_name"]
    name_lea = {str(v).strip().lower(): k for k, v in lea_name.items()}
    # local district LEA for each town (SEDA mapping, any year)
    local_lea = seda[seda.town_match == "local district"].drop_duplicates("town_code").set_index("town_code")["leaid"]
    # K-12 regional membership by fiscal year (SEDA mapping is by spring test year = fiscal year)
    k12 = seda[seda.town_match == "regional district"][["fiscal_year", "town_code", "district", "leaid"]].drop_duplicates()
    # free-lunch share of FRPL by district (EdSight enrollment): free eligibility is 130% of poverty or direct
    # certification, the narrower identification closest to Massachusetts' administrative matches
    enr = pd.read_csv(os.path.join(CLEAN, "district_year_enrollment.csv"))
    codes = enr["District Code"].astype(str).str.zfill(7)
    enr["dc"] = pd.to_numeric(codes.str[:3], errors="coerce")
    enr = enr[enr.dc.notna() & codes.str.endswith(("0011", "0012"))].copy(); enr["dc"] = enr.dc.astype(int)
    FREE = {(int(r.dc), int(r.fiscal_year)): (float(r.n_free_lunch) if pd.notna(r.n_free_lunch) else np.nan, float(r.n_frpl) if pd.notna(r.n_frpl) else np.nan) for r in enr.itertuples()}
    REG_CODE = {f"Regional School District {n:02d}": 200 + n for n in range(1, 21)}
    def free_share(tc, fy, regions):
        """free / (free + reduced) for the town's own district plus its regional districts, latest year <= fy with data."""
        for y in range(min(fy, 2026), 2017, -1):
            f = n = 0.0; ok = False
            for code in [tc] + [REG_CODE[d] for d in regions if d in REG_CODE]:
                v = FREE.get((code, y))
                if v and pd.notna(v[0]) and pd.notna(v[1]) and v[1] > 0:
                    f += v[0]; n += v[1]; ok = True
            if ok:
                return f / n, y
        return np.nan, np.nan
    # direct-certification share (CEP identified student percentage) by LEA and fiscal year (78_parse_cep_isp.py)
    cep_path = os.path.join(MA, "cep_isp_by_lea.csv")
    cep = pd.read_csv(cep_path, dtype={"lea_id": str}) if os.path.exists(cep_path) else pd.DataFrame(columns=["fiscal_year", "lea_id", "isp"])
    ISP = {(int(r.lea_id[:3]), int(r.fiscal_year)): float(r.isp) for r in cep.itertuples()}
    isp_years = sorted({y for _, y in ISP}) or [2025]

    def dc_share(tc, fy, regions, w_local, w_region):
        """Town ISP = the local district's ISP and each regional district's ISP weighted by where the town's
        resident students sit (grade-mix weights); nearest CEP year (2024-2026) for other years."""
        y = min(isp_years, key=lambda v: (abs(v - fy), -v))
        parts = []
        v = ISP.get((tc, y))
        if v is not None and w_local > 0:
            parts.append((v, w_local))
        for d in regions:
            code = REG_CODE.get(d); v = ISP.get((code, y)) if code else None
            if v is not None and w_region.get(d, 0) > 0:
                parts.append((v, w_region[d]))
        if not parts:
            return np.nan, y
        w = sum(x[1] for x in parts)
        return sum(x[0] * x[1] for x in parts) / w, y
    # wages
    q = pd.read_csv(os.path.join(MA, "qcew_ct_county_wages.csv"))
    state_pay = q[q.area_fips == 9000].set_index("year").avg_annual_pay
    q = q[q.area_fips != 9000].copy(); q["ratio"] = q.avg_annual_pay / q.year.map(state_pay)
    ratio = {(r.area, r.year): r.ratio for r in q.itertuples()}
    a21 = pd.read_csv(os.path.join(ACS, "acs5_ct_towns_2021.csv"), dtype=str)
    a21 = a21[a21.NAME.str.contains(" town,| city,", regex=True)].copy()
    a21["town"] = a21.NAME.str.replace(r"\s+(town|city),.*$", "", regex=True)
    a21["county"] = a21.NAME.str.extract(r", (.*? County),")[0]
    county = {code_of[t.upper()]: c for t, c in zip(a21.town, a21.county) if t.upper() in code_of}
    # equalized valuation
    engl = pd.read_csv(os.path.join(BASE, "data", "ecs", "ctdata", "engl_by_town.csv"))
    engl["town_code"] = pd.to_numeric(engl.town_code, errors="coerce"); engl = engl[engl.town_code.between(1, 169)]
    E = engl.pivot_table(index="town_code", columns="grand_list_year", values="total_equalized")
    # aggregate income by vintage
    inc = {}
    for v in range(2015, 2024):
        f = os.path.join(ACS, f"acs5_agg_income_ct_towns_{v}.csv")
        if not os.path.exists(f):
            continue
        a = pd.read_csv(f, dtype=str); a = a[a.NAME.str.contains(" town,| city,", regex=True)].copy()
        a["town"] = a.NAME.str.replace(r"\s+(town|city),.*$", "", regex=True)
        a["inc"] = pd.to_numeric(a.B19025_001E, errors="coerce")
        inc[v] = {code_of[t.upper()]: x for t, x in zip(a.town, a.inc) if t.upper() in code_of and pd.notna(x) and x > 0}

    rows = []
    for fy in YEARS:
        ccd_year = min(max(fy - 2, 2018), 2023)
        g = grade[grade.year == ccd_year].pivot_table(index="leaid", columns="grade", values="enrollment", aggfunc="sum").fillna(0)
        p = ecs[ecs.fiscal_year == fy].set_index("town_code")
        # regional membership this year: K-12 from SEDA (nearest year with a mapping) + secondary regions
        avail = sorted(k12.fiscal_year.unique()); ky_year = min(avail, key=lambda y: (abs(y - fy), -y))
        ky = k12[k12.fiscal_year == ky_year]
        members = {}
        for r in ky.itertuples():
            members.setdefault(r.district, []).append(int(r.town_code))
        for d, towns in SECONDARY_REGIONS.items():
            members[d] = [code_of[t.upper()] for t in towns]
        region_of_town = {}
        for d, tcs in members.items():
            for tc in tcs:
                region_of_town.setdefault(tc, []).append(d)
        for tc in sorted(p.index):
            counts = {b: 0.0 for b in BANDS}
            src = []; w_local = 0.0; w_region = {}
            lea = local_lea.get(tc)
            if lea is None:      # town not in the SEDA map (e.g. Litchfield): match the CCD name "<Town> School District"
                lea = name_lea.get(f"{names[tc].lower()} school district")
            if lea is not None and lea in g.index:
                for b, grades in BANDS.items():
                    counts[b] += float(sum(g.loc[lea].get(x, 0) for x in grades))
                w_local = sum(counts.values()); src.append("local")
            for d in region_of_town.get(tc, []):
                rlea = name_lea.get(str(d).strip().lower())
                if rlea is None or rlea not in g.index:
                    continue
                sent = {m: float(p.rsd_students.get(m, 0) or 0) for m in members[d]}
                tot = sum(sent.values())
                share = (sent.get(tc, 0) / tot) if tot > 0 else 1.0 / len(members[d])
                before = sum(counts.values())
                for b, grades in BANDS.items():
                    counts[b] += share * float(sum(g.loc[rlea].get(x, 0) for x in grades))
                w_region[d] = sum(counts.values()) - before; src.append("region")
            total = sum(counts.values())
            if total <= 0:
                # no district data (a town tuitioning all pupils out): statewide shares
                st = {b: float(sum(g[x].sum() for x in grades if x in g)) for b, grades in BANDS.items()}
                counts = st; total = sum(st.values()); src.append("statewide")
            shares = {f"share_{b}": counts[b] / total for b in BANDS}
            cty = county.get(tc)
            wy = min(max(fy - 2, 2016), 2023)
            wr = ratio.get((cty, wy), np.nan)
            gl_years = [int(y) for y in re.findall(r"20\d\d", str(p.engl_grand_list_years.get(tc, "")))]
            gl = max(gl_years) if gl_years else fy - 4
            eqv = float(E.loc[tc, gl]) if (tc in E.index and gl in E.columns) else np.nan
            vint = int(p.mhi_year.get(tc)) if pd.notna(p.mhi_year.get(tc)) else fy - 4
            fs, fs_year = free_share(tc, fy, region_of_town.get(tc, []))
            ds, ds_year = dc_share(tc, fy, region_of_town.get(tc, []), w_local if (w_local > 0 or w_region) else 1.0, w_region)
            rows.append({"town_code": tc, "town": names[tc], "fiscal_year": fy, "ccd_year": ccd_year, "grade_source": "+".join(src),
                         "free_share_of_frpl": fs, "free_share_year": fs_year,
                         "free_lunch_count": (float(p.frpl_count.get(tc)) * fs) if pd.notna(fs) else np.nan,
                         "direct_cert_share": ds, "direct_cert_year": ds_year,
                         "direct_cert_count": (float(p.resident_students.get(tc)) * ds) if pd.notna(ds) else np.nan,
                         **shares, "county": cty, "wage_year": wy, "county_wage_ratio": wr,
                         "wage_adjustment_factor": max(1.0, 1 + (wr - 1) / 3) if pd.notna(wr) else 1.0,
                         "eqv_grand_list_year": gl, "equalized_valuation": eqv,
                         "income_vintage": vint, "aggregate_household_income": inc.get(vint, {}).get(tc, np.nan),
                         "resident_students": p.resident_students.get(tc), "frpl_count": p.frpl_count.get(tc), "ell_count": p.ell_count.get(tc),
                         "alliance_or_psd": int((p.alliance_flag.get(tc, 0) == 1) or (p.psd_flag.get(tc, 0) == 1))})
    out = pd.DataFrame(rows)
    for c in ("free_share_year", "direct_cert_year", "eqv_grand_list_year", "income_vintage", "wage_year", "ccd_year"):
        out[c] = pd.to_numeric(out[c], errors="coerce").round().astype("Int64")
    out.to_csv(os.path.join(CLEAN, "town_year_ma_inputs.csv"), index=False)
    print(f"[write] town_year_ma_inputs.csv ({len(out)} rows); rates {len(RATES)} columns x {len(CATS)} categories; params {len(PARAMS)}")
    print("  grade sources:", out.grade_source.value_counts().to_dict())
    print("  missing eqv:", int(out.equalized_valuation.isna().sum()), "| missing income:", int(out.aggregate_household_income.isna().sum()),
          "| missing county:", int(out.county.isna().sum()), "| WAF>1 towns FY2025:", int((out[out.fiscal_year == 2025].wage_adjustment_factor > 1).sum()))


if __name__ == "__main__":
    main()
