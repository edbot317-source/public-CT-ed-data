"""
01_clean_district.py

Reads raw CT EdSight per-pupil expenditure CSVs, builds a district-year panel
with spending categories as columns, adjusts to 2025 dollars using CPI-U.

Input:
    data/per-pupil-expenditures-by-function/spending-*.csv
    data/cpi-u-annual-avg-fred.csv
Output:
    clean-data/district_year_spending.csv
"""

import os, re, glob
import pandas as pd
from io import StringIO

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE, "data", "per-pupil-expenditures-by-function")
CPI_PATH = os.path.join(BASE, "data", "cpi-u-annual-avg-fred.csv")
CLEAN_DIR = os.path.join(BASE, "clean-data")
os.makedirs(CLEAN_DIR, exist_ok=True)


def parse_one_file(path):
    fname = os.path.basename(path)
    m = re.search(r"spending-(\d{4})-(\d{4})\.csv", fname)
    fy = int(m.group(2))
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    data_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith('"District","District Code"'):
            data_start = i
            break
    df = pd.read_csv(StringIO("".join(lines[data_start:])), dtype=str)
    df.columns = df.columns.str.strip().str.strip('"')
    df["District Code"] = df["District Code"].str.replace(r'[=""]', "", regex=True).str.strip()
    for col in ["Expenditures", "PPE"]:
        df[col] = pd.to_numeric(df[col].str.replace(r'[$,"]', "", regex=True).str.strip(), errors="coerce")
    df["Pupils"] = pd.to_numeric(df["Pupils"].str.replace(r'[",]', "", regex=True).str.strip(), errors="coerce")
    df["Pupil Basis"] = pd.to_numeric(df["Pupil Basis"].str.replace(r'[",]', "", regex=True).str.strip(), errors="coerce")
    df["District"] = df["District"].str.strip('"').str.strip()
    df["Function"] = df["Function"].str.strip('"').str.strip()
    df["fiscal_year"] = fy
    return df


files = sorted(glob.glob(os.path.join(RAW_DIR, "spending-*.csv")))
print(f"Found {len(files)} raw files")
long = pd.concat([parse_one_file(f) for f in files], ignore_index=True)

# Extract pupil bases
pupils_b1 = long[long["Pupil Basis"] == 1].groupby(["District", "District Code", "fiscal_year"])["Pupils"].first().reset_index().rename(columns={"Pupils": "pupils_enrolled_plus_outplaced"})
pupils_b2 = long[long["Pupil Basis"] == 2].groupby(["District", "District Code", "fiscal_year"])["Pupils"].first().reset_index().rename(columns={"Pupils": "pupils_enrolled_in_district"})
pupils_b3 = long[long["Pupil Basis"] == 3].groupby(["District", "District Code", "fiscal_year"])["Pupils"].first().reset_index().rename(columns={"Pupils": "pupils_transported"})

totals = long[long["Function"] == "Total"][["District", "District Code", "fiscal_year", "Expenditures", "PPE"]].rename(columns={"Expenditures": "total_expenditures", "PPE": "ppe_total"})
totals = totals.merge(pupils_b1, on=["District", "District Code", "fiscal_year"], how="left")
totals = totals.merge(pupils_b2, on=["District", "District Code", "fiscal_year"], how="left")
totals = totals.merge(pupils_b3, on=["District", "District Code", "fiscal_year"], how="left")

def clean_func_name(s):
    s = re.sub(r"[^a-z0-9]+", "_", s.lower().strip()).strip("_")
    return s

functions = long[long["Function"] != "Total"].copy()
functions["func_col"] = functions["Function"].apply(clean_func_name)

exp_wide = functions.pivot_table(index=["District", "District Code", "fiscal_year"], columns="func_col", values="Expenditures", aggfunc="first").reset_index()
exp_wide.columns.name = None
spending_cols = [c for c in exp_wide.columns if c not in ("District", "District Code", "fiscal_year")]
exp_wide = exp_wide.rename(columns={c: f"exp_{c}" for c in spending_cols})

ppe_wide = functions.pivot_table(index=["District", "District Code", "fiscal_year"], columns="func_col", values="PPE", aggfunc="first").reset_index()
ppe_wide.columns.name = None
ppe_cols = [c for c in ppe_wide.columns if c not in ("District", "District Code", "fiscal_year")]
ppe_wide = ppe_wide.rename(columns={c: f"ppe_{c}" for c in ppe_cols})

panel = totals.merge(exp_wide, on=["District", "District Code", "fiscal_year"], how="left")
panel = panel.merge(ppe_wide, on=["District", "District Code", "fiscal_year"], how="left")

# CPI adjustment
cpi = pd.read_csv(CPI_PATH)
cpi["year"] = pd.to_datetime(cpi["observation_date"]).dt.year
cpi = cpi.rename(columns={"CPIAUCSL": "cpi_u"})
panel = panel.merge(cpi[["year", "cpi_u"]], left_on="fiscal_year", right_on="year", how="left")
panel.drop(columns=["year"], inplace=True)
cpi_2025 = cpi.loc[cpi["year"] == 2025, "cpi_u"].values[0]
panel["deflator"] = cpi_2025 / panel["cpi_u"]
panel["ppe_total_real"] = panel["ppe_total"] * panel["deflator"]
panel["total_expenditures_real"] = panel["total_expenditures"] * panel["deflator"]
for col in panel.columns:
    if col.startswith("exp_") or (col.startswith("ppe_") and col not in ("ppe_total", "ppe_total_real")):
        panel[f"{col}_real"] = panel[col] * panel["deflator"]

out_path = os.path.join(CLEAN_DIR, "district_year_spending.csv")
panel.to_csv(out_path, index=False)
print(f"Saved: {out_path} ({len(panel):,} rows)")
