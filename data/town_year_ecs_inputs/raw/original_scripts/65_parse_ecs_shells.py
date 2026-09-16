"""
65_parse_ecs_shells.py

Parses the per-town ECS formula "shells" (the Office of Fiscal Analysis / CSDE
calculation worksheet, one row per town) into one tidy panel, town x fiscal_year,
FY2018..FY2027, with every formula input and intermediate column.

PRIMARY source (from 2026-09-15): the official OFA/CSDE shells received by email
(data/ecs/ofa/, see _provenance.tsv), one workbook per grant year:

  FY2019  ecs shell 2018-19-only.xlsx :: "FY 2018-19"  (10/2017 counts; PA 17-2: 75% conc-pov, 5%, ELL 15%)
  FY2020  ecs shell 2019-2020.xlsx    :: "FY 2019-20"  (10/2018)
  FY2021  ecs shell 2020-21.xlsx      :: "FY 2020-21"  (10/2019)
  FY2023  ecs shell 2022-23.xlsx      :: "Current Law" (10/2021; PA 21-2 JSS weights: 60% conc-pov, 15%, ELL 25%)
  FY2024  FY 2023-2024 ECS shell.xlsx :: "FY 24"       (10/2022)
  FY2025  FY 2024-2025 ECS shell.xlsx :: "FY 25"       (10/2023)
  FY2026  FY 2025-2026 ECS shell.xlsx :: "FY 26"       (10/2024)
  FY2027  FY 2026-2027 ECS shell.xlsx :: "FY 27"       (10/2025)

  FY2022  no official shell was received; the School and State Finance Project's
          copy ("FY 22 OFA Shell" in fy27_town_ecs_model.xlsm) stays primary.
  FY2018  the only official workbook ("ECS Shell 2017-18 Final Version.xls", dated
          November 2016) is a pre-PA 17-2 proposal built on preliminary counts; FY2018
          grants were set by PA 17-2 and the November-2017 holdbacks, not by the
          formula. FY2018 therefore keeps the SSFP backend_data core inputs as primary,
          and the November-2016 shell is parsed as an alternate only.

SSFP's republished shells (downloaded by 61_download_ecs_ssfp.py) are parsed for
every year as ALTERNATES and written to *_alternates.csv; 66_validate_ecs.py
compares them column by column with the official shells (they agree to the cent
wherever both exist, apart from SSFP's FY2023 projection built on preliminary
counts).

Phase-in conventions, verified against CSDE's published entitlements in 66 and against
CGS 10-262h and the OLR analyses of PA 17-2 JSS, PA 21-2 JSS, PA 23-204 and PA 25-168
(STATUTE below; written to ecs_parameters.phase_in_statute):
  FY2019         PA 17-2: FY2017 grant +4.1% of (FF - FY2017) for underfunded towns,
                 -25% of (FY2017 - FF) for overfunded towns
  FY2020-FY2022  prior-year grant +10.66% / -8.33% of the gap measured against the
                 FY2017 base (overfunded towns held harmless from FY2022)
  FY2023-FY2027  prior-year grant + 16.67% / 20% / 56.5% / 100% / 100% of the gap
                 measured against the prior year; overfunded towns held harmless
  Alliance / Priority School Districts never fall below the starting point, and from
                 FY2024 never below their FY2017 grant either.

Every shell has the same logical columns but a different physical layout, so
columns are located by regex on the joined multi-row header text (the header
block sits in the 9 rows above the first town row), with a few sheet-specific
fixups for unlabeled columns. 66_validate_ecs.py recomputes need students, base
aid ratio, fully funded grant and the phase-in from the parsed inputs and requires
an exact match to the shell's own columns, which catches any mis-mapped column.

Inputs:
    data/ecs/ofa/*.xls*                      official shells (received 2026-09-15)
    data/ecs/ssfp/ecs_component_tool.xlsx    SSFP (alternates; backend_data for FY2018 and cross-checks)
    data/ecs/ssfp/fy27_town_ecs_model.xlsm   SSFP (FY2022 primary; other years alternates)
    clean-data/town_year_ecs_entitlement.csv CSDE finals (town names; fills FY2017 base / prior-year where a shell lacks the column)
Outputs:
    clean-data/town_year_ecs_inputs.csv             main panel, FY2018-FY2027
    clean-data/town_year_ecs_inputs_alternates.csv  SSFP copies and superseded shells
    clean-data/ecs_parameters.csv                   per-shell formula parameters and phase-in rules
"""

import os
import re

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSFP = os.path.join(BASE, "data", "ecs", "ssfp")
OFA = os.path.join(BASE, "data", "ecs", "ofa")
CLEAN = os.path.join(BASE, "clean-data")
OUT = CLEAN
os.makedirs(OUT, exist_ok=True)

TOOL = os.path.join(SSFP, "ecs_component_tool.xlsx")
MODEL = os.path.join(SSFP, "fy27_town_ecs_model.xlsm")
SRC_OFA = "OFA shell (official, received 2026-09-15)"
SRC_SSFP = "SSFP copy of OFA shell"

# (file, sheet, fiscal_year, is_primary, source_type)
SHELLS = [
    (os.path.join(OFA, "ecs shell 2018-19-only.xlsx"), "FY 2018-19", 2019, True, SRC_OFA),
    (os.path.join(OFA, "ecs shell 2019-2020.xlsx"), "FY 2019-20", 2020, True, SRC_OFA),
    (os.path.join(OFA, "ecs shell 2020-21.xlsx"), "FY 2020-21", 2021, True, SRC_OFA),
    (MODEL, "FY 22 OFA Shell", 2022, True, SRC_SSFP),
    (os.path.join(OFA, "ecs shell 2022-23.xlsx"), "Current Law", 2023, True, SRC_OFA),
    (os.path.join(OFA, "FY 2023-2024 ECS shell.xlsx"), "FY 24", 2024, True, SRC_OFA),
    (os.path.join(OFA, "FY 2024-2025 ECS shell.xlsx"), "FY 25", 2025, True, SRC_OFA),
    (os.path.join(OFA, "FY 2025-2026 ECS shell.xlsx"), "FY 26", 2026, True, SRC_OFA),
    (os.path.join(OFA, "FY 2026-2027 ECS shell.xlsx"), "FY 27", 2027, True, SRC_OFA),
    # alternates: the November-2016 FY2018 proposal and every SSFP copy
    (os.path.join(OFA, "ECS Shell 2017-18 Final Version.xls"), "Simulation1", 2018, False, SRC_OFA + "; Nov-2016 pre-PA 17-2 proposal"),
    (MODEL, "FY 21 OFA Shell", 2021, False, SRC_SSFP),
    (MODEL, "FY 23 OFA Shell", 2023, False, SRC_SSFP + " (built on 10/2020 data, superseded)"),
    (TOOL, "FY 23", 2023, False, SRC_SSFP + " (projection on preliminary counts)"),
    (TOOL, "FY 24", 2024, False, SRC_SSFP),
    (MODEL, "FY 24 Adopted", 2024, False, SRC_SSFP),
    (TOOL, "FY 25", 2025, False, SRC_SSFP),
    (TOOL, "FY 26", 2026, False, SRC_SSFP),
    (MODEL, "FY 26 CL", 2026, False, SRC_SSFP),
    (TOOL, "FY 27", 2027, False, SRC_SSFP),
]

# Phase-in rule applied in each grant year (verified against CSDE finals in 66):
# (share of gap for underfunded towns, share for overfunded towns, gap base, starting point,
#  Alliance/PSD hold-harmless also floors at the FY2017 grant). The FY2017 floor is redundant
# through FY2022 (every Alliance town's prior grant already exceeds FY2017) and was not applied
# in FY2023 to the three towns added to the Alliance list that year (Plainfield's FY2023 grant
# sits below its FY2017 grant); from FY2024 the worksheets and CSDE apply it.
STATUTE = {
    2018: 'CGS 10-262h, FY2018 paragraph (PA 17-2 June Sp. Sess. secs. 225-230): alliance districts receive the base grant (their FY2017 grant); other towns 95% of it; the November 2017 holdbacks followed. Not a formula year.',
    2019: 'CGS 10-262h, FY2019 paragraph (PA 17-2 June Sp. Sess.): base grant + 4.1% of the grant adjustment if the fully funded grant exceeds the base grant, base grant - 25% of it otherwise; alliance districts below full funding receive the base grant.',
    2020: 'CGS 10-262h, FY2020-21 paragraph (PA 17-2 June Sp. Sess.; unchanged by PA 19-117): previous year + 10.66% / - 8.33% of the grant adjustment, measured against the base (FY2017) grant; alliance districts below full funding receive the base grant.',
    2021: 'CGS 10-262h, FY2020-21 paragraph (PA 17-2 June Sp. Sess.; unchanged by PA 19-117): previous year + 10.66% / - 8.33% of the grant adjustment, measured against the base (FY2017) grant; alliance districts below full funding receive the base grant.',
    2022: 'CGS 10-262h, FY2022 paragraph (PA 21-2 June Sp. Sess. secs. 384-386): previous year + 10.66% of the grant adjustment measured against the base grant; towns whose fully funded grant is below the base grant receive their FY2021 amount (scheduled decreases suspended). The same sections set the need weights (15% of FRPL students above 60%, 25% of English learners) and the endowed-academy bonus from FY2022.',
    2023: "CGS 10-262h, FY2023 paragraph (PA 21-2 June Sp. Sess. secs. 384-386): previous year + 16.67% of the grant adjustment, now measured against the previous year's grant; towns whose fully funded grant is below the previous year receive their FY2022 amount.",
    2024: "CGS 10-262h, FY2024 paragraph (PA 23-204 sec. 356): previous year + 20% of the grant adjustment; towns whose fully funded grant is below the previous year receive their FY2023 amount; alliance districts receive the greater of the calculated amount, the base (FY2017) grant and the previous year's grant.",
    2025: "CGS 10-262h, FY2025 paragraph (PA 23-204 sec. 356, raised from 25% to 56.5%): previous year + 56.5% of the grant adjustment; overfunded towns receive their FY2024 amount; alliance 'greater of' clause as in FY2024.",
    2026: "CGS 10-262h, FY2026 paragraph (PA 23-204 sec. 356: underfunded towns receive their fully funded grant) and PA 25-168 sec. 323 (overfunded towns held at their FY2025 amount; the -14.29% reduction moved to FY2028); alliance 'greater of' clause.",
    2027: "CGS 10-262h, FY2027 paragraph (PA 23-204 sec. 356 and PA 25-168 sec. 323): underfunded towns fully funded; overfunded towns held at their FY2026 amount (reductions resume FY2028, -14.29%, then -16.67%, -20%, -25%, -33.33%, -50%, full funding by FY2034); alliance 'greater of' clause.",
}

PHASE_IN = {
    2018: (np.nan, np.nan, "n/a (PA 17-2 statutory amounts and holdbacks)", "n/a", False),
    2019: (0.041, 0.25, "fy2017", "fy2017", False),
    2020: (0.1066, 0.0833, "fy2017", "prior", False),
    2021: (0.1066, 0.0833, "fy2017", "prior", False),
    2022: (0.1066, 0.0, "fy2017", "prior", False),
    2023: (0.1667, 0.0, "prior", "prior", False),
    2024: (0.20, 0.0, "prior", "prior", True),
    2025: (0.565, 0.0, "prior", "prior", True),
    2026: (1.0, 0.0, "prior", "prior", True),
    2027: (1.0, 0.0, "prior", "prior", True),
}
W_ELL = {fy: (0.15 if fy <= 2021 else 0.25) for fy in range(2018, 2028)}
W_CP = {fy: (0.05 if fy <= 2021 else 0.15) for fy in range(2018, 2028)}

# canonical column -> ordered list of regexes tried against the joined header text
# ("|"-joined header cells, top to bottom). First matching column wins.
PATTERNS = {
    "drg": [r"^DRG$"],
    "psd_flag": [r"^PSD \| Districts$"],
    "alliance_flag": [r"^(\(New 36 Ads\) \| )?Alliance \| Districts$"],
    "reform_flag": [r"^Reform \| Districts$"],
    "wealth_decile": [r"17 Town \| Wealth \| Decile"],
    "pic_rank_raw": [r"^PIC \| FY \d\d$", r"Eligibility \| Index \| Rank"],
    "town_code": [r"^Town \| Code$"],
    "town": [r"^Town \| Name$"],
    "resident_students": [r"Preliminary \| Resident \| Students"],
    "frpl_count": [r"Free and \| Reduced \| Eligibility"],
    "frpl_weighted": [r"Poverty \| Portion of \| Free & \| Reduced", r"Free&Reduced \| Weight"],
    "conc_pov_threshold_students": [r"Net \| Resident \| Students? \| .*\(Col 1 x \| ?\.(60|75)\)"],
    "excess_frpl_students": [r"Excess \| Resident \| Students \| \(Greater of"],
    "excess_frpl_weighted": [r"Excess \| Resident \| Students \| Portion of \| Total Need",
                             r"Additional Need \| Students Due to \| Concentr",
                             r"Need \| Student \| Portion \| Of Excess"],
    "conc_pov_students_above_threshold": [r"Concentrated \| Poverty \| at \d\d%"],
    "ell_count": [r"^\(?\d+\)? \| ELL \| (Students|Count)", r"^ELL \| (Students|\(?10/20\d\d\)?|20\d\d)$"],
    "ell_weighted": [r"ELL \| Portion of \| Total \| Need Students", r"^ELL \| Weight$", r"Need \| Student \| Portion \| Of ELL"],
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
                           r"Additional Base Aid \| Ratio Pts", r"Base Aid \| Ratio Adjustment \| Factor",
                           r"^Base Aid \| Ratio \| Adjustment \| Factor$"],
    "final_base_aid_ratio": [r"Final Base Aid Ratio", r"Base Aid Ratio \| Including Additional",
                             r"Base Aid \| Ratio \| \(Col 17 \+ Col 18\)"],
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
                              r"Fully Funded \| Grant \| With HH Alliance",
                              r"^Fully Funded \| HH Alliance$"],
    "fy2017_actual": [r"2016-17 \| ECS \| ACTUAL", r"2016-17 \| ECS \| Entitlement \| \(P\.A\."],
    "prior_year_entitlement": [r"Prior Year \| ECS \| Entitlement",
                               r"^\(\d+\) \| 20\d\d-(20)?\d\d \| ECS \| Entitlement$"],
    "gap_vs_fy2017": [r"^Fully Funded Less \| FY 17"],
    "grant_adjustment": [r"^\d+ \| Grant \| Adjustment", r"^Grant \| Adjustment \| \(Absolute",
                         r"^\(\d+\) \| Grant \| Adjustment"],
    "ff_greater_than_prior": [r"Fully Funded \| Greater \| Than"],
    "phase_in_amount": [r"^\d+ \| Phase-In \| Amount", r"^Phase-In \| Amount$", r"^\(\d+\) \| Phase-In \| Amount"],
    "entitlement_no_hh": [r"(Fixed )?ECS \| Entitlement \| Without"],
    "entitlement": [r"(Fixed )?ECS \| Entitlement \| With \| ADs HH",
                    r"(Fixed )?ECS \| Entitlement \| With HH Alliance",
                    r"(Fixed )?ECS \| Entitlement \| With Alliance HH",
                    r"Fixed ECS \| Entitlement$",
                    r"increase for winners",
                    r"^\(25\) \| 2017-18 \| ECS \| Entitlement"],
}
TEXT_COLS = {"drg", "town", "ff_greater_than_prior"}
FLAG_COLS = {"psd_flag", "alliance_flag", "reform_flag"}

# sheet-specific column fixups for unlabeled or mislabeled columns (canonical -> regex on header text)
FIXUPS = {
    # FY2019/FY2020 official shells: the column headed "0.04 | 0.03 | PIC add" holds the FINAL base aid
    # ratio (base aid ratio + PIC points); the PIC points themselves are backed out below.
    "FY 2018-19": {"final_base_aid_ratio": r"PIC add$"},
    "FY 2019-20": {"final_base_aid_ratio": r"PIC add$"},
    # FY2021 official shell: unlabeled "(13)" = PIC points, "(14)" = final base aid ratio.
    "FY 2020-21": {"pic_bar_adjustment": r"^\(13\)$", "final_base_aid_ratio": r"^\(14\)$"},
    # FY2018 November-2016 proposal: "(13)" = final base aid ratio.
    "Simulation1": {"final_base_aid_ratio": r"^\(13\)$"},
}

# parameter block (rows 0..15): label regex -> canonical. NOTE the older shells label the
# rate for towns BELOW full funding "Adjustment % for Districts who are Fully Funded"
# (i.e. districts who are to be fully funded) and the rate for towns above it "... not
# Fully Funded"; verified against the shells' own phase-in arithmetic in 66.
PARAM_LABELS = {
    "need_weight_frpl": r"Need Weighting Factor",
    "wealth_threshold_factor": r"Threshold Factor",
    "engl_weight": r"ENGL per Capita Weight",
    "mhi_weight": r"MHI Weight",
    "min_bar_nonalliance": r"Non-Alliance District.*Minimum Aid Ratio",
    "min_bar_alliance": r"^Alliance District.*Minimum Aid Ratio",
    "foundation": r"^Foundation for",
    "adj_pct_underfunded": r"Adjustment % for Districts who are (underfunded|Fully Funded)",
    "adj_pct_overfunded": r"Adjustment % for Districts who are (overfunded|not Fully Funded)",
}


def cell(v):
    return "" if (isinstance(v, float) and np.isnan(v)) or v is None else str(v).replace("\n", " ").strip()


def first_town_row(d):
    for i in range(min(60, len(d))):
        if any(cell(v).upper() == "ANDOVER" for v in d.iloc[i].tolist()):
            return i
    raise ValueError("no Andover row found")


def header_text(d, r0):
    rows = range(max(0, r0 - 9), r0)
    out = []
    for j in range(d.shape[1]):
        parts = [cell(d.iat[i, j]) for i in rows]
        out.append(" | ".join(p for p in parts if p))
    return out


def locate(headers, sheet):
    """canonical -> column index (first matching pattern wins), then sheet-specific fixups."""
    found = {}
    for name, pats in PATTERNS.items():
        for pat in pats:
            hits = [j for j, h in enumerate(headers) if re.search(pat, h)]
            if hits:
                found[name] = hits[0]
                break
    for name, pat in FIXUPS.get(sheet, {}).items():
        hits = [j for j, h in enumerate(headers) if re.search(pat, h)]
        if hits:
            found[name] = hits[0]
    # FY2019-FY2021 official shells: the unlabeled column right after "Concentrated Poverty at 75%
    # (# students above 75%)" is the 5%-weighted concentrated-poverty need term.
    if "excess_frpl_weighted" not in found and "conc_pov_students_above_threshold" in found:
        j = found["conc_pov_students_above_threshold"]
        if j + 1 < len(headers) and headers[j + 1] == "":
            found["excess_frpl_weighted"] = j + 1
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
    """Rows 0..15, label text in some column, value in the first numeric cell to its right."""
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


def town_names():
    e = pd.read_csv(os.path.join(CLEAN, "town_year_ecs_entitlement.csv"))
    # CSDE prints names in capitals; title case matches the Census/ACS and boundary-file spellings
    return e.drop_duplicates("town_code").set_index("town_code")["town"].str.strip().str.title()


def csde_by_year():
    e = pd.read_csv(os.path.join(CLEAN, "town_year_ecs_entitlement.csv"))
    return e.pivot(index="town_code", columns="fiscal_year", values="entitlement")


def parse_shell(path, sheet, fy, source_type, names, csde):
    d = pd.read_excel(path, sheet_name=sheet, header=None)
    r0 = first_town_row(d)
    headers = header_text(d, r0)
    cols = locate(headers, sheet)
    # FY22/FY23 OFA shells (SSFP copies): the endowed-academy block (students, grades, per-pupil,
    # bonus) sits in four UNLABELED columns right after the regional-district bonus,
    # followed by a total-bonus column (see the stray labels in row 8 of the sheet).
    if "endowed_bonus" not in cols and "rsd_bonus" in cols:
        j = cols["rsd_bonus"]
        if j + 5 < len(headers) and all(headers[j + k] == "" for k in range(1, 6)):
            cols["endowed_students"], cols["endowed_grades"] = j + 1, j + 2
            cols["endowed_per_pupil_bonus"], cols["endowed_bonus"] = j + 3, j + 4
            cols["total_bonus"] = j + 5
    missing = [k for k in PATTERNS if k not in cols]
    body = d.iloc[r0:].copy()
    tc = pd.to_numeric(body.iloc[:, cols["town_code"]], errors="coerce")
    nm = body.iloc[:, cols["town"]].map(cell)
    body = body[tc.between(1, 169) & (nm != "")].copy()          # drops the stray totals row in the FY2018 .xls
    rec = pd.DataFrame({"fiscal_year": fy, "source_sheet": sheet, "source_file": os.path.basename(path),
                        "source_type": source_type}, index=body.index)
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
    assert not rec["town_code"].duplicated().any(), f"{sheet}: duplicate town codes"
    rec["town"] = rec["town_code"].map(names)                    # CSDE spelling (shells vary in case/padding)
    derived = []

    pu, po, gap_base, start_base, hh_fy17 = PHASE_IN[fy]
    fy17 = csde[2017].reindex(rec["town_code"]).values
    prior_csde = csde[fy - 1].reindex(rec["town_code"]).values if (fy - 1) in csde.columns else np.nan
    # ---- layout-specific gaps, filled from the shell's own arithmetic (all verified in 66) ----
    if "ell_count" not in missing and rec["ell_count"].isna().any() and rec["ell_count"].notna().any():
        # FY2020 official shell leaves the ELL cell blank for towns with no English learners
        rec["_ell_blank"] = rec["ell_count"].isna()
        rec["ell_count"] = rec["ell_count"].fillna(0)
    if "ell_weighted" in missing and "ell_count" not in missing:
        rec["ell_weighted"] = rec["ell_count"] * W_ELL[fy]
        derived.append(f"ell_weighted=ell_count x {W_ELL[fy]}")
    if "excess_frpl_students" in missing and "conc_pov_students_above_threshold" not in missing:
        rec["excess_frpl_students"] = rec["conc_pov_students_above_threshold"]
        derived.append("excess_frpl_students=conc_pov_students_above_threshold")
    if "excess_frpl_weighted" in missing:
        rec["excess_frpl_weighted"] = (rec["need_students"] - rec["resident_students"]
                                       - rec["frpl_weighted"] - rec["ell_weighted"]).round(4)
        derived.append("excess_frpl_weighted=need-resident-frpl_w-ell_w")
    if "conc_pov_threshold_students" in missing:
        thr = 0.75 if fy <= 2021 else 0.60
        rec["conc_pov_threshold_students"] = rec["resident_students"] * thr
        derived.append(f"conc_pov_threshold_students=resident x {thr}")
    if "pic_bar_adjustment" in missing and "final_base_aid_ratio" not in missing:
        rec["pic_bar_adjustment"] = (rec["final_base_aid_ratio"] - rec["base_aid_ratio"]).round(6)
        derived.append("pic_bar_adjustment=final_base_aid_ratio-base_aid_ratio")
    if "final_base_aid_ratio" in missing and "pic_bar_adjustment" not in missing:
        rec["final_base_aid_ratio"] = rec["base_aid_ratio"] + rec["pic_bar_adjustment"].fillna(0)
        derived.append("final_base_aid_ratio=base_aid_ratio+pic_bar_adjustment")
    if "fy2017_actual" in missing:
        rec["fy2017_actual"] = fy17
        derived.append("fy2017_actual=CSDE FY2017 entitlement")
    if "prior_year_entitlement" in missing and (fy - 1) in csde.columns:
        rec["prior_year_entitlement"] = prior_csde
        derived.append(f"prior_year_entitlement=CSDE FY{fy - 1} entitlement")
    base_amt = rec["fy2017_actual"] if gap_base == "fy2017" else rec["prior_year_entitlement"]
    start_amt = rec["fy2017_actual"] if start_base == "fy2017" else rec["prior_year_entitlement"]
    if "grant_adjustment" in missing and fy >= 2019:
        if "gap_vs_fy2017" not in missing:
            rec["grant_adjustment"] = rec["gap_vs_fy2017"].abs()
            derived.append("grant_adjustment=|gap_vs_fy2017|")
        else:
            rec["grant_adjustment"] = (rec["fully_funded_grant"] - base_amt).abs()
            derived.append(f"grant_adjustment=|fully_funded_grant-{gap_base}|")
    if "ff_greater_than_prior" in missing and fy >= 2019:
        rec["ff_greater_than_prior"] = np.where(rec["fully_funded_grant"] > base_amt, "Yes", "No")
        derived.append(f"ff_greater_than_prior=fully_funded_grant>{gap_base}")
    if "phase_in_amount" in missing and fy >= 2019:
        under = rec["fully_funded_grant"] > base_amt
        rec["phase_in_amount"] = np.where(under, pu * rec["grant_adjustment"], po * rec["grant_adjustment"])
        derived.append(f"phase_in_amount={pu}/{po} x grant_adjustment")
    if "entitlement_no_hh" in missing and fy >= 2019 and "entitlement" not in missing:
        under = rec["fully_funded_grant"] > base_amt
        rec["entitlement_no_hh"] = np.where(under, start_amt + rec["phase_in_amount"], start_amt - rec["phase_in_amount"])
        derived.append(f"entitlement_no_hh={start_base}+/-phase_in_amount")
    if "entitlement" in missing and "entitlement_no_hh" not in missing:
        rec["entitlement"] = rec["entitlement_no_hh"]
        derived.append("entitlement=entitlement_no_hh (shell has no hold-harmless column)")
    if "frpl_pct" not in rec or rec.get("frpl_pct", pd.Series(dtype=float)).isna().all():
        rec["frpl_pct"] = rec["frpl_count"] / rec["resident_students"]
    if "ell_pct" not in rec or rec.get("ell_pct", pd.Series(dtype=float)).isna().all():
        rec["ell_pct"] = rec["ell_count"] / rec["resident_students"]
    rec["derived_columns"] = "; ".join(derived)
    if "_ell_blank" in rec:
        rec.loc[rec["_ell_blank"], "derived_columns"] = (rec.loc[rec["_ell_blank"], "derived_columns"] + "; ell_count=0 (blank cell)").str.lstrip("; ")
        rec = rec.drop(columns=["_ell_blank"])
    rec["phase_in_gap_base"] = gap_base
    rec["phase_in_start_base"] = start_base
    rec["hh_floor_fy2017"] = hh_fy17

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
    m = re.search(r"\((20\d\d)/(\d\d)/(\d\d)\)", headers[cols["engl_avg"]]) if "engl_avg" in cols else None
    p["engl_grand_list_years"] = f"{m.group(1)},20{m.group(2)},20{m.group(3)}" if m else ""
    m = re.search(r"Population \| (20\d\d)", headers[cols["population"]]) if "population" in cols else None
    p["population_year"] = int(m.group(1)) if m else np.nan
    m = re.search(r"\(MHI\) \| (20\d\d)", headers[cols["mhi"]]) if "mhi" in cols else None
    p["mhi_year"] = int(m.group(1)) if m else np.nan
    m = re.search(r"at (\d\d)%", headers[cols["conc_pov_students_above_threshold"]]) if "conc_pov_students_above_threshold" in cols else None
    p["conc_pov_threshold"] = int(m.group(1)) / 100 if m else (0.75 if fy <= 2021 else 0.60)
    p["need_weight_ell"] = W_ELL[fy]
    p["need_weight_conc_pov"] = W_CP[fy]
    p["pct_under_applied"], p["pct_over_applied"] = pu, po
    p["phase_in_gap_base"], p["phase_in_start_base"], p["hh_floor_fy2017"] = gap_base, start_base, hh_fy17
    p["phase_in_statute"] = STATUTE[fy]
    p.update({"fiscal_year": fy, "source_sheet": sheet, "source_file": os.path.basename(path),
              "source_type": source_type, "n_towns": len(rec), "missing_columns": ";".join(missing)})
    for k in ("engl_median", "engl_threshold", "mhi_median", "mhi_threshold", "foundation",
              "count_date", "engl_grand_list_years", "population_year", "mhi_year", "conc_pov_threshold"):
        rec[k] = p.get(k, np.nan)
    print(f"  {sheet:<22} FY{fy}: {len(rec)} towns, {len(cols)} columns mapped"
          + (f", missing: {missing}" if missing else ""))
    return rec, p


def parse_clean_data_fy2020(names):
    """SSFP's flat FY2020 table (alternate); also the source of the FY2018 pre-holdback statutory grant."""
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
    out["town"] = out["town_code"].map(names)
    out["fiscal_year"] = 2020
    out["source_sheet"] = "Clean Data (FY 2020)"
    out["source_file"] = os.path.basename(MODEL)
    out["source_type"] = SRC_SSFP + " (flat table)"
    out["population_year"] = 2016
    out["mhi_year"] = 2016
    out["engl_grand_list_years"] = "2014,2015,2016"
    out["count_date"] = "10/2018"
    out["conc_pov_threshold"] = 0.75
    out["excess_frpl_weighted"] = (out["excess_frpl_students"] * 0.05).round(4)
    out["foundation"] = 11525.0
    out["derived_columns"] = "excess_frpl_weighted=excess_frpl_students x 0.05"
    out["phase_in_gap_base"], out["phase_in_start_base"], out["hh_floor_fy2017"] = PHASE_IN[2020][2:5]
    # 'FY18 Grants' is the statutory FY2018 amount BEFORE the Nov-2017 holdbacks
    # (= FY2017 for Alliance towns, 95% of FY2017 otherwise); CSDE's file has the actual FY2018 entitlement.
    fy18 = out[["town_code", "_fy18_grant"]].rename(columns={"_fy18_grant": "fy2018_statutory_pre_holdback"})
    out = out.drop(columns=["_fy18_grant"])
    print(f"  Clean Data (FY 2020)   FY2020: {len(out)} towns (alternate)")
    return out, fy18


def parse_backend(names):
    b = pd.read_excel(TOOL, sheet_name="backend_data")
    b = b.rename(columns={"ecs_fy_year": "fiscal_year", "_demo_data_year": "demo_data_year",
                          "rsc": "resident_students", "frpl_count": "frpl_count", "frpl_pct": "frpl_pct",
                          "el_count": "ell_count", "el_pct": "ell_pct", "englc": "engl_per_capita",
                          "mhi": "mhi", "pic_score": "pic_score", "pic_rank": "pic_rank_raw",
                          "conc_pov": "excess_frpl_weighted", "full_funded": "fully_funded_grant",
                          "engl": "engl_avg", "base_aid": "final_base_aid_ratio"})
    code = {v.strip().upper(): k for k, v in names.items()}
    b["town_code"] = b["town"].map(lambda s: code.get(str(s).strip().upper()))
    assert b["town_code"].notna().all(), "backend_data town names did not all map to a code"
    b["town_code"] = b["town_code"].astype(int)
    b["town"] = b["town_code"].map(names)
    return b.drop(columns=["town_year"])


def main():
    names = town_names()
    csde = csde_by_year()
    print("[parse] shells")
    recs, params, alts = [], [], []
    for path, sheet, fy, primary, src in SHELLS:
        rec, p = parse_shell(path, sheet, fy, src, names, csde)
        p["is_primary"] = primary
        params.append(p)
        (recs if primary else alts).append(rec)
    fy20, fy18_grants = parse_clean_data_fy2020(names)
    alts.append(fy20)
    panel = pd.concat(recs, ignore_index=True)

    # FY2018 core inputs from backend_data (no formula-driven grant that year), plus a
    # cross-check copy of the backend columns for every year
    b = parse_backend(names)
    early = b[b["fiscal_year"] == 2018].copy()
    early["source_sheet"] = "backend_data"
    early["source_file"] = os.path.basename(TOOL)
    early["source_type"] = SRC_SSFP + " (core inputs only)"
    early["count_date"] = early["demo_data_year"].map(lambda y: f"10/{int(y)}")
    early["foundation"] = 11525.0
    early["conc_pov_threshold"] = 0.75
    early["phase_in_gap_base"], early["phase_in_start_base"], early["hh_floor_fy2017"] = PHASE_IN[2018][2:5]
    early = early.merge(fy18_grants, on="town_code", how="left")
    early["fy2017_actual"] = csde[2017].reindex(early["town_code"]).values
    early["derived_columns"] = "fy2017_actual=CSDE FY2017 entitlement"
    panel = pd.concat([panel, early], ignore_index=True)

    chk = b[["fiscal_year", "town_code", "resident_students", "frpl_count", "ell_count",
             "engl_per_capita", "mhi", "fully_funded_grant", "final_base_aid_ratio", "pic_score"]]
    chk = chk.rename(columns={c: f"backend_{c}" for c in chk.columns if c not in ("fiscal_year", "town_code")})
    panel = panel.merge(chk, on=["fiscal_year", "town_code"], how="left")
    # the FY2023 official shell carries no DRG / wealth decile; DRG is a fixed classification, so
    # fill it from the town's other years (wealth decile is year-specific and stays blank)
    if panel["drg"].isna().any():
        filled = panel.groupby("town_code")["drg"].transform(lambda s: s.ffill().bfill())
        mask = panel["drg"].isna() & filled.notna()
        panel.loc[mask, "drg"] = filled[mask]
        panel.loc[mask, "derived_columns"] = (panel.loc[mask, "derived_columns"].fillna("").str.rstrip("; ")
                                              + "; drg=other years").str.lstrip("; ")

    panel["district_code"] = panel["town_code"]          # local board of education = town
    order = ["town_code", "district_code", "town", "fiscal_year", "source_sheet", "source_file", "source_type",
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
             "fy2017_actual", "fy2018_statutory_pre_holdback", "prior_year_entitlement",
             "phase_in_gap_base", "phase_in_start_base", "hh_floor_fy2017", "grant_adjustment", "ff_greater_than_prior",
             "phase_in_amount", "entitlement_no_hh", "entitlement", "derived_columns"]
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
    alt = pd.concat(alts, ignore_index=True)
    alt = alt.reindex(columns=[c for c in order if c in alt.columns] + [c for c in alt.columns if c not in order])
    alt = alt.sort_values(["fiscal_year", "source_file", "source_sheet", "town_code"]).reset_index(drop=True)
    alt.to_csv(os.path.join(OUT, "town_year_ecs_inputs_alternates.csv"), index=False)
    pcols = ["fiscal_year", "source_sheet", "source_file", "source_type", "is_primary", "n_towns",
             "need_weight_frpl", "need_weight_conc_pov", "need_weight_ell", "conc_pov_threshold",
             "wealth_threshold_factor", "engl_weight", "mhi_weight", "min_bar_nonalliance", "min_bar_alliance",
             "foundation", "adj_pct_underfunded", "adj_pct_overfunded", "pct_under_applied", "pct_over_applied",
             "phase_in_gap_base", "phase_in_start_base", "hh_floor_fy2017", "phase_in_statute", "engl_median", "engl_threshold", "mhi_median", "mhi_threshold",
             "count_date", "engl_grand_list_years", "population_year", "mhi_year", "missing_columns"]
    pdf = pd.DataFrame(params)
    pdf = pdf.reindex(columns=pcols + [c for c in pdf.columns if c not in pcols])
    pdf = pdf.sort_values(["fiscal_year", "is_primary"], ascending=[True, False]).reset_index(drop=True)
    pdf.to_csv(os.path.join(OUT, "ecs_parameters.csv"), index=False)
    print("[write] clean-data/town_year_ecs_inputs.csv, _alternates.csv, ecs_parameters.csv")


if __name__ == "__main__":
    main()
