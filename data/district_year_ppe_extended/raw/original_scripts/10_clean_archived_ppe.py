"""
10_clean_archived_ppe.py

Parses archived EdSight per-pupil expenditure CSVs (2006-07 to 2016-17)
and appends them to the existing district-year spending panel.

The archived format differs from the current format:
  - Values are already per-pupil (not total expenditures)
  - Different function categories (older classification)
  - No district codes in the export

This script extracts total PPE and the archived function-level PPE,
merges district codes from the enrollment panel, and produces a
long-run PPE panel.

Input:
    data/per-pupil-expenditures-archived/ppe-archived-*.csv
    clean-data/district_year_enrollment.csv  (for district code crosswalk)
    clean-data/district_year_spending.csv    (for appending)
Output:
    clean-data/district_year_ppe_extended.csv
"""

import os, re, glob
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCH_DIR = os.path.join(BASE, "data", "per-pupil-expenditures-archived")
CLEAN_DIR = os.path.join(BASE, "clean-data")
os.makedirs(CLEAN_DIR, exist_ok=True)

# Archived CSV column mapping (old function names -> standardized)
ARCH_COLS = {
    "Type": "District",
    "Instructional Staff and Services": "ppe_instructional_staff",
    "Instructional Supplies and Equipment": "ppe_instructional_supplies",
    "Instruction and Educational Media Services": "ppe_instruction_media",
    "Student Support Services": "ppe_student_support",
    "Administration and Support Services": "ppe_admin_support",
    "Plant Operation and Management": "ppe_plant",
    "Transportation": "ppe_transportation",
    "Other": "ppe_other",
    "Total Expenditures": "ppe_total",
}


def parse_one_archived(path):
    """Parse a single archived PPE CSV."""
    fname = os.path.basename(path)
    m = re.search(r"ppe-archived-(\d{4})-(\d{2})\.csv$", fname)
    if not m:
        raise ValueError(f"Cannot parse year from {fname}")
    fy = int(m.group(1)[:2] + m.group(2))

    # Skip header lines (title, district filter, blank, column group headers, column names)
    # Row 0: "Per Pupil Expenditures, YYYY-YY"
    # Row 1: "All Districts"
    # Row 2: blank
    # Row 3: "","_","_",...  (group headers)
    # Row 4: "Type","Instructional Staff..."  (column names)
    # Row 5+: data
    df = pd.read_csv(path, skiprows=5, header=None, dtype=str)

    # Read column names from row 4
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == 4:
                # Parse the header
                import csv
                reader = csv.reader([line])
                col_names = next(reader)
                break

    col_names = [c.strip().strip('"') for c in col_names]
    df.columns = col_names[:len(df.columns)]

    # Rename columns
    rename = {k: v for k, v in ARCH_COLS.items() if k in df.columns}
    df = df.rename(columns=rename)

    # Clean district name
    df["District"] = (
        df["District"]
        .str.replace(r'^[="]+', "", regex=True)
        .str.replace(r'[""]+$', "", regex=True)
        .str.strip()
    )

    # Drop empty/total rows
    df = df[df["District"].str.len() > 0].copy()
    df = df[~df["District"].isin(["Total", "State of Connecticut"])].copy()

    # Convert numeric columns
    num_cols = [c for c in df.columns if c.startswith("ppe_")]
    for col in num_cols:
        df[col] = pd.to_numeric(
            df[col].str.replace(r'[,$"N/A]', "", regex=True).str.strip().replace("", np.nan),
            errors="coerce",
        )

    df["fiscal_year"] = fy
    return df


# ── Parse all archived files ──────────────────────────────────────────────────
files = sorted(glob.glob(os.path.join(ARCH_DIR, "ppe-archived-*.csv")))
if not files:
    raise FileNotFoundError(f"No archived PPE CSVs in {ARCH_DIR}")
print(f"Found {len(files)} archived PPE files")

frames = []
for f in files:
    df = parse_one_archived(f)
    print(f"  {os.path.basename(f)}: {len(df)} districts")
    frames.append(df)

archived = pd.concat(frames, ignore_index=True)
print(f"\nArchived panel: {len(archived):,} rows")

# ── Merge district codes from enrollment data ────────────────────────────────
enroll = pd.read_csv(os.path.join(CLEAN_DIR, "district_year_enrollment.csv"),
                     usecols=["District", "District Code"])
xwalk = enroll.drop_duplicates(subset=["District"], keep="last")[["District", "District Code"]]

archived = archived.merge(xwalk, on="District", how="left")
n_matched = archived["District Code"].notna().sum()
n_unmatched = len(archived) - n_matched
print(f"District code merge: {n_matched:,} matched, {n_unmatched:,} unmatched")
if n_unmatched > 0:
    missing = archived.loc[archived["District Code"].isna(), "District"].unique()
    print(f"  Unmatched: {list(missing[:20])}")

# ── Load current spending panel and build extended PPE series ─────────────────
spending = pd.read_csv(os.path.join(CLEAN_DIR, "district_year_spending.csv"))

# From the current panel, keep: District, District Code, fiscal_year, ppe_total
current = spending[["District", "District Code", "fiscal_year", "ppe_total"]].copy()

# From archived, keep same columns
arch_slim = archived[["District", "District Code", "fiscal_year", "ppe_total"]].copy()

# Also keep archived function-level PPE for potential use
arch_full = archived.copy()

# Combine: archived years + current years (no overlap — archived ends 2017, current starts 2018)
extended = pd.concat([arch_slim, current], ignore_index=True)
extended = extended.sort_values(["District", "fiscal_year"]).reset_index(drop=True)

# Verify no duplicates
dupes = extended.duplicated(subset=["District Code", "fiscal_year"], keep=False)
dupe_valid = dupes & extended["District Code"].notna()
if dupe_valid.sum() > 0:
    print(f"\nWARNING: {dupe_valid.sum()} duplicate District Code × fiscal_year rows")
    print(extended[dupe_valid][["District", "District Code", "fiscal_year", "ppe_total"]].head(10))

# ── CPI adjustment ────────────────────────────────────────────────────────────
cpi = pd.read_csv(os.path.join(BASE, "data", "cpi-u-annual-avg-fred.csv"))
cpi["year"] = pd.to_datetime(cpi["observation_date"]).dt.year
cpi = cpi.rename(columns={"CPIAUCSL": "cpi_u"})
extended = extended.merge(cpi[["year", "cpi_u"]], left_on="fiscal_year", right_on="year", how="left")
extended.drop(columns=["year"], inplace=True)
cpi_2025 = cpi.loc[cpi["year"] == 2025, "cpi_u"].values[0]
extended["deflator"] = cpi_2025 / extended["cpi_u"]
extended["ppe_total_real"] = extended["ppe_total"] * extended["deflator"]

# Save extended PPE panel
out_path = os.path.join(CLEAN_DIR, "district_year_ppe_extended.csv")
extended.to_csv(out_path, index=False)

print(f"\nSaved: {out_path}")
print(f"  {len(extended):,} rows")
print(f"  Years: {sorted(extended['fiscal_year'].unique())}")
print(f"  Districts per year:")
for yr in sorted(extended["fiscal_year"].unique()):
    n = len(extended[extended["fiscal_year"] == yr])
    print(f"    {yr}: {n}")

# Save full archived panel separately (with all function columns)
arch_out = os.path.join(CLEAN_DIR, "district_year_ppe_archived.csv")
arch_full.to_csv(arch_out, index=False)
print(f"\nAlso saved full archived panel: {arch_out}")

# Sanity check: Hartford
print("\nHartford PPE total over time:")
h = extended[extended["District"] == "Hartford School District"].sort_values("fiscal_year")
print(h[["fiscal_year", "ppe_total", "ppe_total_real"]].to_string(index=False))
