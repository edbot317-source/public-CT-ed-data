"""
17_clean_school_enrollment_race.py

Parses downloaded EdSight school-level enrollment-by-race CSVs and builds
a school-year panel with race counts and shares.

Each school is mapped to its district code.

Input:
    data/enrollment/race-school/enrollment-race-school-YYYY-YY.csv
Output:
    clean-data/school_year_enrollment_race.csv

Race category harmonization (same as district-level 07_clean_enrollment.py):
    2007-08 to 2009-10 (old federal categories):
        Black, not of Hispanic Origin -> n_black
        Hispanic/Latino -> n_hispanic
        White, not of Hispanic Origin -> n_white
        American Indian -> n_native_american
        Asian -> n_asian
        Not Reported -> (dropped)
        n_two_or_more = NA, n_pacific_islander = NA

    2010-11 onward (new federal categories):
        American Indian or Alaska Native -> n_native_american
        Asian -> n_asian
        Black or African American -> n_black
        Hispanic/Latino of any race -> n_hispanic
        Two or More Races -> n_two_or_more
        White -> n_white
        Native Hawaiian or Other Pacific Islander -> n_pacific_islander
"""

import os
import re
import glob
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data", "enrollment", "race-school")
CLEAN_DIR = os.path.join(BASE, "clean-data")
os.makedirs(CLEAN_DIR, exist_ok=True)


def extract_year(fname):
    """Extract fiscal year end from filename like ...-2024-25.csv -> 2025."""
    m = re.search(r"(\d{4})-(\d{2})\.csv$", fname)
    if not m:
        raise ValueError(f"Cannot parse year from {fname}")
    return int(m.group(1)[:2] + m.group(2))


def clean_code(s):
    """Clean district/school code: strip =\"...\", quotes, whitespace."""
    return s.str.replace(r'[="“”]', "", regex=True).str.strip()


def to_numeric_star(s):
    """Convert to numeric, treating '*' and blanks as NaN."""
    return pd.to_numeric(
        s.str.replace(r'[,"\*]', "", regex=True).str.strip().replace("", np.nan),
        errors="coerce",
    )


# Old column names (2007-08 to 2009-10)
OLD_RACE_MAP = {
    "Black, not of Hispanic Origin": "n_black",
    "Hispanic/Latino": "n_hispanic",
    "White, not of Hispanic Origin": "n_white",
    "American Indian": "n_native_american",
    "Asian": "n_asian",
}

# New column names (2010-11 onward)
NEW_RACE_MAP = {
    "American Indian or Alaska Native": "n_native_american",
    "Asian": "n_asian",
    "Black or African American": "n_black",
    "Hispanic/Latino of any race": "n_hispanic",
    "Two or More Races": "n_two_or_more",
    "White": "n_white",
    "Native Hawaiian or Other Pacific Islander": "n_pacific_islander",
}

ALL_RACE_COLS = [
    "n_native_american", "n_asian", "n_black", "n_hispanic",
    "n_two_or_more", "n_white", "n_pacific_islander",
]


def parse_one_file(fpath):
    """Parse a single school-level race enrollment CSV."""
    fy = extract_year(os.path.basename(fpath))

    # Skip header rows: title, filter, year, blank, category header
    df = pd.read_csv(fpath, skiprows=5, dtype=str)
    df.columns = df.columns.str.strip().str.strip('"')

    # Clean string fields
    df["District"] = df["District"].str.strip('"').str.strip()
    df["District Code"] = clean_code(df["District Code"])
    df["School"] = df["School"].str.strip('"').str.strip()
    df["School Code"] = clean_code(df["School Code"])

    # Forward-fill district info for schools listed under the same district
    # (EdSight leaves District/District Code blank for 2nd+ school in a district)
    df["District"] = df["District"].replace("", np.nan).ffill()
    df["District Code"] = df["District Code"].replace("", np.nan).ffill()

    # Drop rows without a valid school code
    df = df[df["School Code"].notna() & (df["School Code"] != "")]

    # Determine old vs new race categories
    if "Black, not of Hispanic Origin" in df.columns:
        race_map = OLD_RACE_MAP
    else:
        race_map = NEW_RACE_MAP

    # Map race columns
    for src_col, dst_col in race_map.items():
        if src_col in df.columns:
            df[dst_col] = to_numeric_star(df[src_col])
        else:
            df[dst_col] = np.nan

    # Ensure all standard race columns exist
    for col in ALL_RACE_COLS:
        if col not in df.columns:
            df[col] = np.nan

    # Total enrollment
    if "Total" in df.columns:
        df["enrollment_total"] = to_numeric_star(df["Total"])
    else:
        df["enrollment_total"] = np.nan

    df["fiscal_year"] = fy

    out_cols = [
        "District", "District Code", "School", "School Code",
        "fiscal_year", "enrollment_total",
    ] + ALL_RACE_COLS

    return df[out_cols].copy()


# ── Main ───────────────────────────────────────────────────────────────────────
files = sorted(glob.glob(os.path.join(DATA_DIR, "enrollment-race-school-*.csv")))
print(f"Found {len(files)} files")

frames = []
for f in files:
    df = parse_one_file(f)
    print(f"  {os.path.basename(f)}: {len(df):,} schools")
    frames.append(df)

panel = pd.concat(frames, ignore_index=True)

# Standardize column names for output
panel = panel.rename(columns={
    "District": "district",
    "District Code": "district_code",
    "School": "school",
    "School Code": "school_code",
})

# Compute derived variables
# n_black_hispanic: Black + Hispanic counts. EdSight suppresses any race cell of
# 1-5 students (CT small-cell rule; threshold = 6). When exactly one of the two
# components is suppressed, impute the midpoint of the suppressed range (3) for
# the masked component -- consistent with the white/Asian magnet imputation in
# scripts 11/37/38/39 -- rather than treating the missing component as 0, which
# silently understates the combined count. When both components are suppressed,
# leave the combined cell missing (NaN) so downstream code applies its own
# imputation.
SUPPRESSION_IMPUTE_MID = 3  # midpoint of CT's 1-5 suppressed range (threshold = 6)
_bh_one_suppressed = panel["n_black"].isna() ^ panel["n_hispanic"].isna()
panel["n_black_hispanic"] = panel["n_black"].add(panel["n_hispanic"], fill_value=0)
panel.loc[_bh_one_suppressed, "n_black_hispanic"] += SUPPRESSION_IMPUTE_MID

for col, num in [
    ("pct_white", "n_white"),
    ("pct_black", "n_black"),
    ("pct_hispanic", "n_hispanic"),
    ("pct_asian", "n_asian"),
    ("pct_native_american", "n_native_american"),
    ("pct_two_or_more", "n_two_or_more"),
    ("pct_pacific_islander", "n_pacific_islander"),
    ("pct_black_hispanic", "n_black_hispanic"),
]:
    panel[col] = panel[num] / panel["enrollment_total"] * 100

panel["pct_nonwhite"] = 100 - panel["pct_white"]

# Sort
panel = panel.sort_values(["fiscal_year", "district", "school"]).reset_index(drop=True)

# Check for duplicates
dupes = panel.duplicated(subset=["school_code", "fiscal_year"], keep=False).sum()
if dupes > 0:
    print(f"\nWARNING: {dupes} duplicate school_code x fiscal_year rows")
    print(panel[panel.duplicated(subset=["school_code", "fiscal_year"], keep=False)]
          .sort_values(["school_code", "fiscal_year"])
          [["district", "school", "school_code", "fiscal_year", "enrollment_total"]]
          .head(20))
else:
    print("\nOK: No duplicate school_code x fiscal_year rows")

# Save
out_path = os.path.join(CLEAN_DIR, "school_year_enrollment_race.csv")
panel.to_csv(out_path, index=False)

print(f"\nSaved: {out_path}")
print(f"  {len(panel):,} rows × {len(panel.columns)} cols")
print(f"  Years: {sorted(panel['fiscal_year'].unique())}")
print(f"  Schools per year:")
for yr in sorted(panel["fiscal_year"].unique()):
    n = len(panel[panel["fiscal_year"] == yr])
    print(f"    {yr}: {n:,}")

# Sanity checks
print("\nSanity check — Hartford schools (2024-25):")
h25 = panel[(panel["district"] == "Hartford School District") & (panel["fiscal_year"] == 2025)]
print(h25[["school", "school_code", "enrollment_total",
           "pct_black", "pct_hispanic", "pct_white"]].to_string(index=False))

print(f"\nHartford district total enrollment (sum of schools): {h25['enrollment_total'].sum():,.0f}")

print("\nDistricts represented (2024-25):")
n_dist = panel[panel["fiscal_year"] == 2025]["district_code"].nunique()
print(f"  {n_dist} unique districts")
