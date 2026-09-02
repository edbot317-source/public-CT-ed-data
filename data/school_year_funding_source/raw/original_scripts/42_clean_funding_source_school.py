"""
42_clean_funding_source_school.py

Parses raw EdSight school-level "by Funding Source (Summary)" CSVs into a tidy
school-year panel, CPI-adjusted to 2025$, and attaches enrollment from the
by-function school panel (clean-data/school_year_spending.csv) via School Code.

The by-source report has no enrollment column, so enrollment is merged on
(school_code, fiscal_year) from the by-function school file.

Input:
    data/per-pupil-expenditures-by-funding-source-school/funding-source-school-*.csv
    clean-data/school_year_spending.csv  (for enrollment by school-year)
    data/cpi-u-annual-avg-fred.csv
Output:
    clean-data/school_year_funding_source.csv
"""

import os, re, glob
import pandas as pd
from io import StringIO

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE, "data", "per-pupil-expenditures-by-funding-source-school")
CPI_PATH = os.path.join(BASE, "data", "cpi-u-annual-avg-fred.csv")
CLEAN_DIR = os.path.join(BASE, "clean-data")
BYFUNC_PATH = os.path.join(CLEAN_DIR, "school_year_spending.csv")


def parse_one_file(path):
    fname = os.path.basename(path)
    m = re.search(r"funding-source-school-(\d{4})-(\d{4})\.csv", fname)
    fy = int(m.group(2))
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    data_start = None
    for i, line in enumerate(lines):
        if '"District","District Code","School' in line:
            data_start = i
            break
    df = pd.read_csv(StringIO("".join(lines[data_start:])), dtype=str)
    df.columns = df.columns.str.strip().str.strip('"')
    for col in ["District Code", "School Code"]:
        df[col] = df[col].str.replace(r'[=""]', "", regex=True).str.strip()
    for col in ["District", "School/Category"]:
        df[col] = df[col].str.strip('"').str.strip()
    money = ["Federal Funds", "State, Local, and Other Funds", "Total"]
    for col in money:
        df[col] = pd.to_numeric(df[col].str.replace(r'[$,"]', "", regex=True).str.strip(), errors="coerce")
    df = df.rename(columns={
        "District": "district", "District Code": "district_code",
        "School/Category": "school", "School Code": "school_code",
        "Federal Funds": "ppe_federal",
        "State, Local, and Other Funds": "ppe_state_local_other",
        "Total": "ppe_total_source",
    })
    df["fiscal_year"] = fy
    return df[["district", "district_code", "school", "school_code",
               "ppe_federal", "ppe_state_local_other", "ppe_total_source", "fiscal_year"]]


files = sorted(glob.glob(os.path.join(RAW_DIR, "funding-source-school-*.csv")))
print(f"Found {len(files)} raw by-source school files")
long = pd.concat([parse_one_file(f) for f in files], ignore_index=True)

# CPI adjustment -> 2025$
cpi = pd.read_csv(CPI_PATH)
cpi["year"] = pd.to_datetime(cpi["observation_date"]).dt.year
cpi = cpi.rename(columns={"CPIAUCSL": "cpi_u"})
long = long.merge(cpi[["year", "cpi_u"]], left_on="fiscal_year", right_on="year", how="left").drop(columns=["year"])
cpi_2025 = cpi.loc[cpi["year"] == 2025, "cpi_u"].values[0]
long["deflator"] = cpi_2025 / long["cpi_u"]
for col in ["ppe_federal", "ppe_state_local_other", "ppe_total_source"]:
    long[f"{col}_real"] = long[col] * long["deflator"]

# Attach enrollment from by-function school panel (on school_code + year)
byfunc = pd.read_csv(BYFUNC_PATH, dtype={"school_code": str, "district_code": str})
enr = byfunc[["school_code", "fiscal_year", "enrollment"]].drop_duplicates()
long = long.merge(enr, on=["school_code", "fiscal_year"], how="left")

matched = long["enrollment"].notna().sum()
print(f"Enrollment matched for {matched}/{len(long)} school-year rows "
      f"({100*matched/len(long):.1f}%)")
missing = long[long["enrollment"].isna()]
if len(missing):
    print(f"  Unmatched rows (no enrollment): {len(missing)} "
          f"(schools appearing in by-source but not by-function report)")

out_path = os.path.join(CLEAN_DIR, "school_year_funding_source.csv")
long.to_csv(out_path, index=False)
print(f"Saved: {out_path} ({len(long):,} rows)")
