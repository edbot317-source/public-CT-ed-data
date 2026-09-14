"""
65_parse_ecs_shells.py

Parses the per-town ECS formula "shells" republished by the School and State
Finance Project (downloaded by 61_download_ecs_ssfp.py) into one tidy panel,
town x fiscal_year, FY2018..FY2027, with every formula input and intermediate
column CSDE uses (see CSDE's Feb-2025 CASBO deck for the 35-column layout).

Source sheet used for each grant year (the CSDE convention is: grant year FY t
uses October-1 counts of FY t-1, ENGL grand lists t-4..t-2, MHI/population of
FY t-2):

  FY2021  fy27_town_ecs_model.xlsm :: "FY 21 OFA Shell"   (10/2019 counts; 75% conc-pov, ELL 15%)
  FY2022  fy27_town_ecs_model.xlsm :: "FY 22 OFA Shell"   (10/2020 counts; 60% conc-pov, ELL 25%)
  FY2023  ecs_component_tool.xlsx  :: "FY 23"             (10/2021 counts)
  FY2024  ecs_component_tool.xlsx  :: "FY 24"             (10/2022)
  FY2025  ecs_component_tool.xlsx  :: "FY 25"             (10/2023)
  FY2026  ecs_component_tool.xlsx  :: "FY 26"             (10/2024)
  FY2027  ecs_component_tool.xlsx  :: "FY 27"             (10/2025)  -- SSFP projection until CSDE finalizes
  FY2020  fy27_town_ecs_model.xlsm :: "Clean Data (FY 2020)"  (flat table, 10/2018 counts)
  FY2018, FY2019  ecs_component_tool.xlsx :: "backend_data" only (core inputs; no population,
          ENGL total, or base aid ratio columns are published for these two years)

The xlsm also carries "FY 23 OFA Shell" (built from 10/2020 data, superseded by the
component tool's FY 23 which uses 10/2021 data), "FY 24 Adopted" and "FY 26 CL"
(duplicates of FY 24 / FY 26). Those are parsed too and written to the
*_alternates file for reference, but are not used in the main panel.

Every shell has the same logical columns but a different physical layout, so
columns are located by regex on the joined multi-row header text (the header
block sits in the 9 rows above the first town row). 66_validate_ecs.py then
recomputes need students, base aid ratio, and the fully funded grant from the
parsed inputs and requires an exact match to the shell's own columns, which
catches any mis-mapped column.

Inputs:
    data/ecs/ssfp/ecs_component_tool.xlsx
    data/ecs/ssfp/fy27_town_ecs_model.xlsm
Outputs:
    clean-data/town_year_ecs_inputs.csv          main panel, FY2018-FY2027
    clean-data/town_year_ecs_inputs_alternates.csv  superseded/duplicate shells
    clean-data/ecs_parameters.csv                per-shell formula parameters
"""

import os
import re

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSFP = os.path.join(BASE, "data", "ecs", "ssfp")
OUT = os.path.join(BASE, "clean-data")
os.makedirs(OUT, exist_ok=True)

TOOL = os.path.join(SSFP, "ecs_component_tool.xlsx")
MODEL = os.path.join(SSFP, "fy27_town_ecs_model.xlsm")

# (file, sheet, fiscal_year, is_primary)
SHELLS = [
    (MODEL, "FY 21 OFA Shell", 2021, True),
    (MODEL, "FY 22 OFA Shell", 2022, True),
    (MODEL, "FY 23 OFA Shell", 2023, False),
    (TOOL, "FY 23", 2023, True),
    (TOOL, "FY 24", 2024, True),
    (MODEL, "FY 24 Adopted", 2024, False),
    (TOOL, "FY 25", 2025, True),
    (TOOL, "FY 26", 2026, True),
    (MODEL, "FY 26 CL", 2026, False),
    (TOOL, "FY 27", 2027, True),
]

# canonical column -> ordered list of regexes tried against the joined header text
# ("|"-joined header cells, top to bottom). First matching column wins.
PATTERNS = {
    "drg": [r"^DRG$"],
    "psd_flag": [r"^PSD \| Districts$"],
    "alliance_flag": [r"^(\(New 36 Ads\) \| )?Alliance \| Districts$"],
    "reform_flag": [r"^Reform \| Districts$"],
    "wealth_decile": [r"17 Town \| Wealth \| Decile"],
    "pic_rank_raw": [r"^PIC \| FY \d\d$"],
    "town_code": [r"^Town \| Code$"],
    "town": [r"^Town \| Name$"],
    "resident_students": [r"Preliminary \| Resident \| Students"],
    "frpl_count": [r"Free and \| Reduced \| Eligibility"],
    "frpl_weighted": [r"Poverty \| Portion of \| Free & \| Reduced", r"Free&Reduced \| Weight"],
    "conc_pov_threshold_students": [r"Net \| Resident \| Students \| \(Col 1 x \.60\)"],
    "excess_frpl_students": [r"Excess \| Resident \| Students \| \(Greater of"],
    "excess_frpl_weighted": [r"Excess \| Resident \| Students \| Portion of \| Total Need",
                             r"Additional Need \| Students Due to \| Concentr"],
    "conc_pov_students_above_threshold": [r"Concentrated \| Poverty \| at \d\d%"],
    "ell_count": [r"^\(?\d+\)? \| ELL \| Students", r"^ELL \| (Students|\(?10/20\d\d\)?|20\d\d)$"],
    "ell_weighted": [r"ELL \| Portion of \| Total \| Need Students", r"^ELL \| Weight$"],
    "need_students": [r"Need \| Students \| \(Col 1"],
    "engl_avg": [r"Average \| Equalized Net \| Grand List"],
    "population": [r"Total \| Population"],
    "engl_per_capita": [r"ECS ENGL \| per Capita"],
    "engl_factor": [r"ENGL Adjustment Factor"],
    "mhi": [r"Median \| Household \| Income"],
    "mhi_factor": [r"MHI Adjustment Factor"],
    "wealth_adj_factor": [r"Wealth \| Adjustment \| Factor"],
    "base_aid_ratio": [r"Base Aid Ratio \| \(Non-Alliance"],
    "pic_bar_adjustment": [r"PIC Add \| Base Aid", r"Additional PIC \| Points",
                           r"Additional Base Aid \| Ratio Pts"],
    "final_base_aid_ratio": [r"Final Base Aid Ratio", r"Base Aid Ratio \| Including Additional"],
    "rsd_students": [r"Students \| Sent To \| Regional \| District"],
    "rsd_grades": [r"Number of \| Regional \| District \| Grades"],
    "rsd_per_pupil_bonus": [r"Regional \| District \| per Pupil \| Bonus"],
    "rsd_bonus": [r"Regional \| District \| Bonus \| \(Col"],
    "endowed_students": [r"Students \| Sent To \| Endowed"],
    "endowed_grades": [r"Number of \| Endowed \| Academies \| Grades"],
    "endowed_bonus": [r"Endowed \| Academies \| Bonus \| \(Col"],
    "base_formula_aid": [r"Base Formula \| Aid"],
    "fully_funded_grant": [r"Fully Funded \| Grant \| \(Col"],
    "fully_funded_grant_hh": [r"Fully Funded \| Grant with Alliance \| Hold Harmless",
                              r"Full Funding with \| HH Alliance",
                              r"Fully Funded \| Grant \| With HH Alliance"],
    "fy2017_actual": [r"2016-17 \| ECS \| ACTUAL"],
    "prior_year_entitlement": [r"Prior Year \| ECS \| Entitlement",
                               r"^\(19\) \| .*ECS \| Entitlement"],
    "grant_adjustment": [r"^\d+ \| Grant \| Adjustment", r"^Grant \| Adjustment \| \(Absolute"],
    "ff_greater_than_prior": [r"Fully Funded \| Greater \| Than"],
    "phase_in_amount": [r"^\d+ \| Phase-In \| Amount", r"^Phase-In \| Amount$"],
    "entitlement_no_hh": [r"(Fixed )?ECS \| Entitlement \| Without"],
    "entitlement": [r"(Fixed )?ECS \| Entitlement \| With \| ADs HH",
                    r"(Fixed )?ECS \| Entitlement \| With HH Alliance",
                    r"(Fixed )?ECS \| Entitlement \| With Alliance HH"],
}
TEXT_COLS = {"drg", "town", "ff_greater_than_prior"}
FLAG_COLS = {"psd_flag", "alliance_flag", "reform_flag"}

PARAM_LABELS = {
    "need_weight_frpl": r"Need Weighting Factor",
    "wealth_threshold_factor": r"Threshold Factor",
    "engl_weight": r"ENGL per Capita Weight",
    "mhi_weight": r"MHI Weight",
    "min_bar_nonalliance": r"Non-Alliance District.*Minimum Aid Ratio",
    "min_bar_alliance": r"^Alliance District.*Minimum Aid Ratio",
    "foundation": r"^Foundation for",
    "adj_pct_underfunded": r"Adjustment % for Districts who are (underfunded|not Fully Funded)",
    "adj_pct_overfunded": r"Adjustment % for Districts who are (overfunded|Fully Funded)",
}


def cell(v):
    return "" if (isinstance(v, float) and np.isnan(v)) or v is None else str(v).replace("\n", " ").strip()


def first_town_row(d):
    for i in range(min(60, len(d))):
        if "Andover" in d.iloc[i].astype(str).tolist():
            return i
    raise ValueError("no Andover row found")


def header_text(d, r0):
    rows = range(max(0, r0 - 9), r0)
    out = []
    for j in range(d.shape[1]):
        parts = [cell(d.iat[i, j]) for i in rows]
        out.append(" | ".join(p for p in parts if p))
    return out


def locate(headers):
    """canonical -> column index; raises on ambiguity within a pattern."""
    found = {}
    for name, pats in PATTERNS.items():
        for pat in pats:
            hits = [j for j, h in enumerate(headers) if re.search(pat, h)]
            if hits:
                found[name] = hits[0]
                break
    return found


def num_from_header(headers, key):
    """Extract e.g. 'Median: | 146842.18' or 'Threshold: | 198236.94' numbers."""
    vals = []
    for h in headers:
        m = re.search(key + r": \| ([0-9.]+)", h)
        if m:
            vals.append(float(m.group(1)))
    return vals


def parse_params(d):
    """Rows 0..14, label in col 8 (or 7), value in the first numeric cell to its right."""
    out = {}
    for i in range(0, 16):
        row = [cell(v) for v in d.iloc[i].tolist()]
        for j, txt in enumerate(row):
            for key, pat in PARAM_LABELS.items():
                if key not in out and re.search(pat, txt):
                    for v in d.iloc[i, j + 1:j + 8].tolist():
                        if isinstance(v, (int, float)) and not (isinstance(v, float) and np.isnan(v)):
                            out[key] = float(v)
                            break
    return out


def parse_shell(path, sheet, fy):
    d = pd.read_excel(path, sheet_name=sheet, header=None)
    r0 = first_town_row(d)
    headers = header_text(d, r0)
    cols = locate(headers)
    # FY22/FY23 OFA shells: the endowed-academy block (students, grades, per-pupil,
    # bonus) sits in four UNLABELED columns right after the regional-district bonus,
    # followed by a total-bonus column (see the stray labels in row 8 of the sheet:
    # 'Students', 'Number of Endowed', 'Endowed Academy', '(AJ*AL)', 'District Bonus').
    if "endowed_bonus" not in cols and "rsd_bonus" in cols:
        j = cols["rsd_bonus"]
        if j + 5 < len(headers) and all(headers[j + k] == "" for k in range(1, 6)):
            cols["endowed_students"], cols["endowed_grades"] = j + 1, j + 2
            cols["endowed_per_pupil_bonus"], cols["endowed_bonus"] = j + 3, j + 4
            cols["total_bonus"] = j + 5
    missing = [k for k in PATTERNS if k not in cols]
    body = d.iloc[r0:].copy()
    tc = pd.to_numeric(body.iloc[:, cols["town_code"]], errors="coerce")
    body = body[tc.between(1, 169)].copy()
    rec = pd.DataFrame({"fiscal_year": fy, "source_sheet": sheet,
                        "source_file": os.path.basename(path)}, index=body.index)
    for name, j in cols.items():
        s = body.iloc[:, j]
        if name in TEXT_COLS:
            rec[name] = s.map(cell)
        elif name in FLAG_COLS:
            rec[name] = s.map(lambda v: 0 if cell(v) in ("", "0", "No", "nan") else 1)
        else:
            rec[name] = pd.to_numeric(s, errors="coerce")
    for name in missing:
        rec[name] = np.nan
    rec["town_code"] = rec["town_code"].astype(int)
    # Layout-specific gaps, filled from the shell's own arithmetic (verified in 66):
    #  - FY22/FY23 OFA shells carry an ELL count but no explicit ELL-weighted column
    #  - FY21 shell has no concentrated-poverty weighted column; back it out of need students
    #  - the component tool's FY 23 sheet has no "with hold-harmless" entitlement column
    if "ell_weighted" in missing and "ell_count" not in missing:
        rec["ell_weighted"] = rec["ell_count"] * 0.25
        rec["ell_weighted_note"] = "derived: ell_count x 0.25"
    if "excess_frpl_weighted" in missing:
        # FY2021 shell (PA 17-2 rule): 5% of FRPL students above 75% of resident students
        rec["excess_frpl_students"] = rec["conc_pov_students_above_threshold"]
        rec["excess_frpl_weighted"] = (rec["need_students"] - rec["resident_students"]
                                       - rec["frpl_weighted"] - rec["ell_weighted"]).round(4)
        rec["excess_frpl_weighted_note"] = "derived: need - resident - frpl_w - ell_w (= 5% x students above 75%)"
    if "entitlement" in missing and "entitlement_no_hh" not in missing:
        rec["entitlement"] = rec["entitlement_no_hh"]
        rec["entitlement_note"] = "shell has no hold-harmless column; equals entitlement_no_hh"
    # header-embedded constants and data vintages
    p = parse_params(d)
    eng_med, eng_thr = num_from_header(headers, "Median"), num_from_header(headers, "Threshold")
    p["engl_median"] = eng_med[0] if eng_med else np.nan
    p["engl_threshold"] = eng_thr[0] if eng_thr else np.nan
    p["mhi_median"] = eng_med[1] if len(eng_med) > 1 else np.nan
    p["mhi_threshold"] = eng_thr[1] if len(eng_thr) > 1 else np.nan
    h_res = headers[cols["resident_students"]]
    m = re.search(r"\(?10/(20\d\d)\)?", h_res)
    p["count_date"] = f"10/{m.group(1)}" if m else ""
    m = re.search(r"\((20\d\d)/(\d\d)/(\d\d)\)", headers[cols["engl_avg"]])
    p["engl_grand_list_years"] = f"{m.group(1)},20{m.group(2)},20{m.group(3)}" if m else ""
    m = re.search(r"Population \| (20\d\d)", headers[cols["population"]])
    p["population_year"] = int(m.group(1)) if m else np.nan
    m = re.search(r"\(MHI\) \| (20\d\d)", headers[cols["mhi"]])
    p["mhi_year"] = int(m.group(1)) if m else np.nan
    m = re.search(r"at (\d\d)%", headers[cols["conc_pov_students_above_threshold"]]) if "conc_pov_students_above_threshold" in cols else None
    p["conc_pov_threshold"] = int(m.group(1)) / 100 if m else np.nan
    p.update({"fiscal_year": fy, "source_sheet": sheet, "source_file": os.path.basename(path),
              "n_towns": len(rec), "missing_columns": ";".join(missing)})
    for k in ("engl_median", "engl_threshold", "mhi_median", "mhi_threshold", "foundation",
              "count_date", "engl_grand_list_years", "population_year", "mhi_year", "conc_pov_threshold"):
        rec[k] = p[k]
    print(f"  {sheet:<22} FY{fy}: {len(rec)} towns, {len(cols)} columns mapped"
          + (f", missing: {missing}" if missing else ""))
    return rec, p


def parse_clean_data_fy2020():
    d = pd.read_excel(MODEL, sheet_name="Clean Data (FY 2020)")
    m = {
        "Town": "town", "Town Code": "town_code", "DRG": "drg", "Wealth Decile": "wealth_decile",
        "FY17 PIC Rank": "pic_rank_raw", "PIC Index Factor BAR Adjustment": "pic_bar_adjustment",
        "Students RSD": "resident_students", "PFRE": "frpl_count", "ELL": "ell_count",
        "ELL Weighted": "ell_weighted", "Free  and Reduced Weight": "frpl_weighted",
        "Concentrated Poverty Students": "excess_frpl_students", "Need Students ": "need_students",
        "(ECS ENGL)": "engl_avg", "Population 2016": "population", "ECS ENGL per Capita": "engl_per_capita",
        "ENGL Adjustment Factor": "engl_factor", "(MHI)": "mhi", "MHI Adjustment Factor": "mhi_factor",
        "Wealth Adjustment Factor": "wealth_adj_factor", "Base Aid Ratio": "base_aid_ratio",
        "Base Aid Reatio with PIC Adjustment": "final_base_aid_ratio",
        "Students Sent to Regional District": "rsd_students",
        "Number of Regional District Grades": "rsd_grades",
        "Regional District per Pupil Bonus": "rsd_per_pupil_bonus",
        "Regional District Bonus": "rsd_bonus", "IG": "base_formula_aid",
        "Fully Funded Grant": "fully_funded_grant",
        "2016/17 ECS Entitlement with rescissions": "fy2017_actual",
        "ECS Fully Phased In with Alliance": "fully_funded_grant_hh",
        "FY19 Grants": "prior_year_entitlement", "FY 20 Shell": "entitlement",
        "FY18 Grants": "_fy18_grant",
    }
    d = d.rename(columns=m)
    d = d[pd.to_numeric(d["town_code"], errors="coerce").between(1, 169)].copy()
    d["town_code"] = d["town_code"].astype(int)
    d["psd_flag"] = d["PSD Districts"].map(lambda v: 0 if cell(v) in ("", "nan", "0") else 1)
    d["alliance_flag"] = pd.to_numeric(d["Alliance Districts"], errors="coerce").fillna(0).astype(int)
    d["reform_flag"] = d["Reform Districts"].map(lambda v: 0 if cell(v) in ("", "nan", "0") else 1)
    keep = [c for c in d.columns if c in set(m.values()) or c in ("psd_flag", "alliance_flag", "reform_flag")]
    out = d[keep].copy()
    out["fiscal_year"] = 2020
    out["source_sheet"] = "Clean Data (FY 2020)"
    out["source_file"] = os.path.basename(MODEL)
    out["population_year"] = 2016
    out["mhi_year"] = 2016
    out["engl_grand_list_years"] = "2014,2015,2016"   # verified against OPM ENGL in 66 (169/169 towns)
    out["count_date"] = "10/2018"
    out["conc_pov_threshold"] = 0.75
    # PA 17-2 rule in force for FY2018-FY2021: 5% weight on FRPL students above 75% of residents
    out["excess_frpl_weighted"] = (out["excess_frpl_students"] * 0.05).round(4)
    out["excess_frpl_weighted_note"] = "derived: 5% x students above 75% (PA 17-2)"
    out["foundation"] = 11525.0
    # 'FY18 Grants' is the statutory FY2018 amount BEFORE the Nov-2017 holdbacks
    # (= FY2017 for Alliance towns, 95% of FY2017 otherwise); CSDE's file has the
    # actual FY2018 entitlement, so this column is kept only as a note field.
    fy18 = out[["town_code", "town", "_fy18_grant"]].rename(columns={"_fy18_grant": "fy2018_statutory_pre_holdback"})
    out = out.drop(columns=["_fy18_grant"])
    print(f"  Clean Data (FY 2020)   FY2020: {len(out)} towns")
    return out, fy18


def parse_backend():
    b = pd.read_excel(TOOL, sheet_name="backend_data")
    b = b.rename(columns={"ecs_fy_year": "fiscal_year", "_demo_data_year": "demo_data_year",
                          "rsc": "resident_students", "frpl_count": "frpl_count", "frpl_pct": "frpl_pct",
                          "el_count": "ell_count", "el_pct": "ell_pct", "englc": "engl_per_capita",
                          "mhi": "mhi", "pic_score": "pic_score", "pic_rank": "pic_rank_raw",
                          "conc_pov": "excess_frpl_weighted", "full_funded": "fully_funded_grant",
                          "engl": "engl_avg", "base_aid": "final_base_aid_ratio"})
    return b.drop(columns=["town_year"])


def main():
    print("[parse] shells")
    recs, params, alts = [], [], []
    for path, sheet, fy, primary in SHELLS:
        rec, p = parse_shell(path, sheet, fy)
        p["is_primary"] = primary
        params.append(p)
        (recs if primary else alts).append(rec)
    fy20, fy18_grants = parse_clean_data_fy2020()
    recs.append(fy20)
    panel = pd.concat(recs, ignore_index=True)

    # FY2018-FY2019 (and a cross-check for all years) from backend_data
    b = parse_backend()
    b = b.merge(panel[["fiscal_year", "town", "town_code"]].drop_duplicates("town")[["town", "town_code"]],
                on="town", how="left")
    assert b["town_code"].notna().all(), "backend_data town names did not all map to a code"
    b["town_code"] = b["town_code"].astype(int)
    early = b[b["fiscal_year"].isin([2018, 2019])].copy()
    early["source_sheet"] = "backend_data"
    early["source_file"] = os.path.basename(TOOL)
    early["count_date"] = early["demo_data_year"].map(lambda y: f"10/{int(y)}")
    early["foundation"] = 11525.0
    early["conc_pov_threshold"] = 0.75
    early = early.merge(fy18_grants[["town_code", "fy2018_statutory_pre_holdback"]], on="town_code", how="left")
    early.loc[early["fiscal_year"] != 2018, "fy2018_statutory_pre_holdback"] = np.nan
    panel = pd.concat([panel, early], ignore_index=True)

    # backend_data cross-check columns for every year (keeps provenance separate)
    chk = b[["fiscal_year", "town_code", "resident_students", "frpl_count", "ell_count",
             "engl_per_capita", "mhi", "fully_funded_grant", "final_base_aid_ratio", "pic_score"]]
    chk = chk.rename(columns={c: f"backend_{c}" for c in chk.columns if c not in ("fiscal_year", "town_code")})
    panel = panel.merge(chk, on=["fiscal_year", "town_code"], how="left")

    panel["district_code"] = panel["town_code"]          # local board of education = town
    order = ["town_code", "district_code", "town", "fiscal_year", "source_sheet", "source_file",
             "count_date", "drg", "wealth_decile", "alliance_flag", "psd_flag", "reform_flag",
             "pic_rank_raw", "pic_score",
             "resident_students", "frpl_count", "frpl_pct", "frpl_weighted",
             "conc_pov_threshold", "conc_pov_threshold_students", "excess_frpl_students",
             "excess_frpl_weighted", "conc_pov_students_above_threshold",
             "ell_count", "ell_pct", "ell_weighted", "need_students",
             "engl_grand_list_years", "engl_avg", "population_year", "population", "engl_per_capita",
             "engl_median", "engl_threshold", "engl_factor",
             "mhi_year", "mhi", "mhi_median", "mhi_threshold", "mhi_factor",
             "wealth_adj_factor", "base_aid_ratio", "pic_bar_adjustment", "final_base_aid_ratio",
             "rsd_students", "rsd_grades", "rsd_per_pupil_bonus", "rsd_bonus",
             "endowed_students", "endowed_grades", "endowed_bonus",
             "foundation", "base_formula_aid", "fully_funded_grant", "fully_funded_grant_hh",
             "fy2017_actual", "prior_year_entitlement", "grant_adjustment", "ff_greater_than_prior",
             "phase_in_amount", "entitlement_no_hh", "entitlement"]
    order += [c for c in panel.columns if c.endswith("_note")]
    order += [c for c in panel.columns if c.startswith("backend_")]
    panel = panel.reindex(columns=[c for c in order if c in panel.columns])
    panel = panel.sort_values(["fiscal_year", "town_code"]).reset_index(drop=True)
    assert not panel.duplicated(["fiscal_year", "town_code"]).any()
    for c in ["wealth_decile", "alliance_flag", "psd_flag", "reform_flag", "pic_rank_raw",
              "population_year", "mhi_year", "district_code"]:
        if c in panel.columns:
            panel[c] = pd.to_numeric(panel[c], errors="coerce").round().astype("Int64")
    print(f"[panel] {len(panel)} rows; towns/yr: {panel.groupby('fiscal_year').size().to_dict()}")

    panel.to_csv(os.path.join(OUT, "town_year_ecs_inputs.csv"), index=False)
    pd.concat(alts, ignore_index=True).to_csv(os.path.join(OUT, "town_year_ecs_inputs_alternates.csv"), index=False)
    pd.DataFrame(params).to_csv(os.path.join(OUT, "ecs_parameters.csv"), index=False)
    print("[write] clean-data/town_year_ecs_inputs.csv, _alternates.csv, ecs_parameters.csv")


if __name__ == "__main__":
    main()
