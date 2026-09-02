"""
02_clean_school.py

Reads raw CT EdSight school-level per-pupil expenditure CSVs and builds a
school-year panel adjusted to 2025$.

Input:
    data/per-pupil-expenditures-by-function-school/spending-school-*.csv
    data/cpi-u-annual-avg-fred.csv
Output:
    clean-data/school_year_spending.csv
"""

import os, re, glob
import pandas as pd
from io import StringIO

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE, "data", "per-pupil-expenditures-by-function-school")
CPI_PATH = os.path.join(BASE, "data", "cpi-u-annual-avg-fred.csv")
CLEAN_DIR = os.path.join(BASE, "clean-data")
os.makedirs(CLEAN_DIR, exist_ok=True)


def parse_one_file(path):
    fname = os.path.basename(path)
    m = re.search(r"spending-school-(\d{4})-(\d{4})\.csv", fname)
    fy = int(m.group(2))
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    data_start = None
    for i, line in enumerate(lines):
        if '"District","District Code","School' in line:
            data_start = i
            break
    df = pd.read_csv(StringIO("".join(lines[data_start:])), dtype=str)
    df.columns = df.columns.str.strip().str.strip('"')
    for col in ["District Code", "School Code"]:
        if col in df.columns:
            df[col] = df[col].str.replace(r'[=""]', "", regex=True).str.strip()
    for col in ["District", "School/Category", "Low Grade", "High Grade"]:
        if col in df.columns:
            df[col] = df[col].str.strip('"').str.strip()
    df["Enrollment"] = pd.to_numeric(df["Enrollment"].str.replace(r'[",]', "", regex=True).str.strip(), errors="coerce")
    df["% High Needs"] = pd.to_numeric(df["% High Needs"].str.replace(r'["%]', "", regex=True).str.strip(), errors="coerce")
    id_cols = ["District", "District Code", "School/Category", "School Code", "Low Grade", "High Grade", "Enrollment", "% High Needs"]
    for col in [c for c in df.columns if c not in id_cols]:
        df[col] = pd.to_numeric(df[col].str.replace(r'[$,"]', "", regex=True).str.strip(), errors="coerce")
    df["fiscal_year"] = fy
    return df


files = sorted(glob.glob(os.path.join(RAW_DIR, "spending-school-*.csv")))
print(f"Found {len(files)} raw school-level files")
long = pd.concat([parse_one_file(f) for f in files], ignore_index=True)

def clean_col_name(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower().strip()).strip("_")

rename_map = {
    "District": "district", "District Code": "district_code",
    "School/Category": "school", "School Code": "school_code",
    "Low Grade": "low_grade", "High Grade": "high_grade",
    "Enrollment": "enrollment", "% High Needs": "pct_high_needs",
    "fiscal_year": "fiscal_year",
}
id_cols_orig = list(rename_map.keys())
for col in [c for c in long.columns if c not in id_cols_orig]:
    clean = clean_col_name(col)
    rename_map[col] = "ppe_total" if clean == "total" else f"ppe_{clean}"
long = long.rename(columns=rename_map)

# CPI adjustment
cpi = pd.read_csv(CPI_PATH)
cpi["year"] = pd.to_datetime(cpi["observation_date"]).dt.year
cpi = cpi.rename(columns={"CPIAUCSL": "cpi_u"})
long = long.merge(cpi[["year", "cpi_u"]], left_on="fiscal_year", right_on="year", how="left")
long.drop(columns=["year"], inplace=True)
cpi_2025 = cpi.loc[cpi["year"] == 2025, "cpi_u"].values[0]
long["deflator"] = cpi_2025 / long["cpi_u"]
for col in [c for c in long.columns if c.startswith("ppe_")]:
    long[f"{col}_real"] = long[col] * long["deflator"]

out_path = os.path.join(CLEAN_DIR, "school_year_spending.csv")
long.to_csv(out_path, index=False)
print(f"Saved: {out_path} ({len(long):,} rows)")
