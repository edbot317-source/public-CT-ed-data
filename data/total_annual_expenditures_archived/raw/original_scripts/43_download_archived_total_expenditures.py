"""
43_download_archived_total_expenditures.py

Downloads TOTAL ANNUAL EXPENDITURES BY TYPE (district-level, nominal dollars)
for the archived years 2005-06 through 2016-17 from CT EdSight.

WHY THIS EXISTS
---------------
The Part 3 "Share of Total Spending on Special Education" figure
(24_part3_sped_share_lines.py) needs a denominator = total district
expenditures. For current years (FY2018-2025) EdSight reports total
expenditures directly. For archived years (<=FY2017) the EdSight per-pupil
export (PerPupilExport, script 09) publishes ONLY a per-pupil figure and NO
pupil base, so 24 currently RECONSTRUCTS the archived total as
    ppe_total (archived per-pupil) x enrollment_total (in-district enrollment)
That reconstruction is unsupported (the archived PPE denominator is not the
in-district enrollment count) and is flagged in the code audit (FIX 7 / P1-3).

This report provides the actual REPORTED total-dollar expenditures for the
archived years, so we no longer have to reconstruct them.

SOURCE
------
Public page:
    https://public-edsight.ct.gov/ada-archived/total-annual-expenditures-by-type-2016-17-and-earlier
Underlying SAS stored process (embedded in that page's iframe):
    https://edsight.ct.gov/SASStoredProcess/do?
      _program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/FinanceReport_SiteCore
      &_rpttype=listing&_year={YYYY-YY}&_district=All+Districts&_select=Submit
Report notes:
    https://edsight.ct.gov/relatedreports/ReportNotes_OverallExpenditures.pdf

The stored process returns an HTML listing table with columns:
    District | Instructional Staff and Services | Instructional Supplies and
    Equipment | Improvement of Instruction and Educational Media Services |
    Student Support Services | Administration and Support Services | Plant
    Operation and Maintenance | Transportation | Students Tuitioned Out |
    Other | Total Expenditures
All dollar columns are NOMINAL (current-year) dollars.

OUTPUT
------
    data/total-annual-expenditures-archived/_raw/total-exp-{YYYY-YY}.html  (raw)
    data/total-annual-expenditures-archived/total-exp-archived-{YYYY-YY}.csv (tidy)
Each tidy CSV: District, fiscal_year, <9 function columns>, total_expenditures
(nominal dollars, integer). "N/A" cells are coerced to missing then 0.
"""

import os
import re
import subprocess
import time

import pandas as pd


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data", "total-annual-expenditures-archived")
RAW_DIR = os.path.join(DATA_DIR, "_raw")
COOKIE_JAR = os.path.join(RAW_DIR, "_cookies.txt")
os.makedirs(RAW_DIR, exist_ok=True)

URL_TEMPLATE = (
    "https://edsight.ct.gov/SASStoredProcess/do?"
    "_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/FinanceReport_SiteCore"
    "&_rpttype=listing&_year={year}&_district=All+Districts&_select=Submit"
)

# The report offers 2005-06 through 2016-17.
YEARS = [f"{y}-{str(y + 1)[-2:]}" for y in range(2005, 2017)]

COL_MAP = {
    "District": "District",
    "Instructional Staff and Services": "exp_instructional_staff",
    "Instructional Supplies and Equipment": "exp_instructional_supplies",
    "Improvement of Instruction and Educational Media Services": "exp_instruction_media",
    "Student Support Services": "exp_student_support",
    "Administration and Support Services": "exp_admin_support",
    "Plant Operation and Maintenance": "exp_plant",
    "Transportation": "exp_transportation",
    "Students Tuitioned Out": "exp_tuitioned_out",
    "Other": "exp_other",
    "Total Expenditures": "total_expenditures",
}


def fiscal_year_from_label(label):
    """'2016-17' -> 2017 (spring of the school year)."""
    return int(label[:2] + label.split("-")[1])


def download_html(year, out_path):
    url = URL_TEMPLATE.format(year=year)
    result = subprocess.run(
        ["curl.exe", "-sS", "-L", "-m", "90",
         "-c", COOKIE_JAR, "-b", COOKIE_JAR,
         "-o", out_path, url],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl error for {year}: {result.stderr.strip()}")
    with open(out_path, "r", encoding="latin-1") as f:
        head = f.read(500)
    if "Total Expenditures" not in open(out_path, "r", encoding="latin-1").read(200000):
        # Basic content validation.
        raise RuntimeError(f"{year}: response missing expected 'Total Expenditures' header")
    return os.path.getsize(out_path)


def parse_html(html_path, year):
    tables = pd.read_html(html_path)
    # The data table is the one with the finance columns.
    data = None
    for t in tables:
        cols = [c[1] if isinstance(c, tuple) else c for c in t.columns]
        if "Total Expenditures" in cols and "District" in cols and len(t) > 20:
            t = t.copy()
            t.columns = cols
            data = t
            break
    if data is None:
        raise RuntimeError(f"{year}: could not find finance data table")

    data = data[[c for c in COL_MAP if c in data.columns]].rename(columns=COL_MAP)
    data["District"] = data["District"].astype(str).str.strip()
    # Drop any trailing all-null row and non-district rows.
    data = data[data["District"].str.len() > 0]
    data = data[~data["District"].str.lower().isin(["nan", "none"])]

    money_cols = [c for c in data.columns if c != "District"]
    for c in money_cols:
        data[c] = (
            data[c].astype(str)
            .str.replace(r"[$,]", "", regex=True)
            .str.replace("N/A", "", regex=False)
            .str.strip()
        )
        data[c] = pd.to_numeric(data[c], errors="coerce")
    # Genuine "N/A" cells mean the district reported nothing in that category.
    data[money_cols] = data[money_cols].fillna(0)
    data = data.dropna(subset=["total_expenditures"])
    data = data[data["total_expenditures"] > 0]

    data.insert(1, "fiscal_year", fiscal_year_from_label(year))

    # Defensive check: components should sum close to reported total.
    comp_cols = [c for c in money_cols if c != "total_expenditures"]
    comp_sum = data[comp_cols].sum(axis=1)
    max_dev = ((comp_sum - data["total_expenditures"]).abs() /
               data["total_expenditures"].replace(0, pd.NA)).max()
    if pd.notna(max_dev) and max_dev > 0.01:
        print(f"    WARNING {year}: max component-vs-total deviation {max_dev:.3%}")
    return data.reset_index(drop=True)


def main():
    n_ok = 0
    for year in YEARS:
        raw_path = os.path.join(RAW_DIR, f"total-exp-{year}.html")
        csv_path = os.path.join(DATA_DIR, f"total-exp-archived-{year}.csv")

        if os.path.exists(csv_path) and os.path.getsize(csv_path) > 500:
            print(f"  {year}: SKIP (csv exists)")
            n_ok += 1
            continue

        try:
            if not (os.path.exists(raw_path) and os.path.getsize(raw_path) > 5000):
                size = download_html(year, raw_path)
                print(f"  {year}: downloaded HTML ({size:,} bytes)")
                time.sleep(1)
            df = parse_html(raw_path, year)
            df.to_csv(csv_path, index=False)
            hps = df[df["District"] == "Hartford School District"]
            hps_total = f"${hps['total_expenditures'].iloc[0]:,.0f}" if len(hps) else "n/a"
            print(f"  {year}: parsed {len(df):>3} districts -> {os.path.basename(csv_path)}"
                  f"  (Hartford total {hps_total})")
            n_ok += 1
        except Exception as e:
            print(f"  {year}: ERROR {e}")

    if os.path.exists(COOKIE_JAR):
        os.remove(COOKIE_JAR)
    print(f"\nDone: {n_ok}/{len(YEARS)} years available.")


if __name__ == "__main__":
    main()
