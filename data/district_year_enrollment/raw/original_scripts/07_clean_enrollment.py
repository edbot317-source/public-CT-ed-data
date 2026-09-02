"""
07_clean_enrollment.py

Parses downloaded EdSight enrollment CSVs (all-students, race, ell, lunch)
and builds a district-year panel with demographic variables.

Input:
    data/enrollment/all-students/*.csv
    data/enrollment/race/*.csv
    data/enrollment/ell/*.csv
    data/enrollment/lunch/*.csv
Output:
    clean-data/district_year_enrollment.csv

Race category harmonization:
    2007-08 to 2009-10 (old federal categories):
        Black not of Hispanic Origin -> n_black
        Hispanic/Latino -> n_hispanic
        White not of Hispanic Origin -> n_white
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

import os, re, glob
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data", "enrollment")
CLEAN_DIR = os.path.join(BASE, "clean-data")
os.makedirs(CLEAN_DIR, exist_ok=True)


def extract_year(fname):
    """Extract fiscal year end from filename like enrollment-race-2024-25.csv -> 2025."""
    m = re.search(r"(\d{4})-(\d{2})\.csv$", fname)
    if not m:
        raise ValueError(f"Cannot parse year from {fname}")
    return int(m.group(1)[:2] + m.group(2))


def clean_district_code(s):
    """Clean district code: strip =\"...\", quotes, whitespace."""
    return s.str.replace(r'[=""]', "", regex=True).str.strip()


def to_numeric_star(s):
    """Convert to numeric, treating '*' as NaN."""
    return pd.to_numeric(
        s.str.replace(r'[,"\*]', "", regex=True).str.strip().replace("", np.nan),
        errors="coerce",
    )


# ── Parse All Students ────────────────────────────────────────────────────────
def parse_all_students():
    files = sorted(glob.glob(os.path.join(DATA_DIR, "all-students", "*.csv")))
    frames = []
    for f in files:
        fy = extract_year(os.path.basename(f))
        df = pd.read_csv(f, skiprows=4, dtype=str)
        df.columns = df.columns.str.strip().str.strip('"')
        df["District"] = df["District"].str.strip('"').str.strip()
        df["District Code"] = clean_district_code(df["District Code"])
        df["enrollment_total"] = to_numeric_star(df["Count"])
        df["fiscal_year"] = fy
        df = df[df["District"].str.len() > 0]
        frames.append(df[["District", "District Code", "fiscal_year", "enrollment_total"]])
    return pd.concat(frames, ignore_index=True)


# ── Parse Race ─────────────────────────────────────────────────────────────────
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


def parse_race():
    files = sorted(glob.glob(os.path.join(DATA_DIR, "race", "*.csv")))
    frames = []
    for f in files:
        fy = extract_year(os.path.basename(f))
        # Skip the first 4 header lines, then row 0 is the category header, row 1 is column names
        df = pd.read_csv(f, skiprows=5, dtype=str)
        df.columns = df.columns.str.strip().str.strip('"')
        df["District"] = df["District"].str.strip('"').str.strip()
        df["District Code"] = clean_district_code(df["District Code"])
        df["fiscal_year"] = fy
        df = df[df["District"].str.len() > 0]

        # Determine old vs new categories
        if "Black, not of Hispanic Origin" in df.columns:
            race_map = OLD_RACE_MAP
        else:
            race_map = NEW_RACE_MAP

        out_cols = ["District", "District Code", "fiscal_year"]
        for src_col, dst_col in race_map.items():
            if src_col in df.columns:
                df[dst_col] = to_numeric_star(df[src_col])
            else:
                df[dst_col] = np.nan
            out_cols.append(dst_col)

        # Ensure all standard columns exist
        for col in ["n_black", "n_hispanic", "n_white", "n_asian",
                     "n_native_american", "n_two_or_more", "n_pacific_islander"]:
            if col not in df.columns:
                df[col] = np.nan
            if col not in out_cols:
                out_cols.append(col)

        frames.append(df[out_cols])
    return pd.concat(frames, ignore_index=True)


# ── Parse ELL ──────────────────────────────────────────────────────────────────
def parse_ell():
    files = sorted(glob.glob(os.path.join(DATA_DIR, "ell", "*.csv")))
    frames = []
    for f in files:
        fy = extract_year(os.path.basename(f))
        df = pd.read_csv(f, skiprows=5, dtype=str)
        df.columns = df.columns.str.strip().str.strip('"')
        df["District"] = df["District"].str.strip('"').str.strip()
        df["District Code"] = clean_district_code(df["District Code"])
        df["fiscal_year"] = fy
        df = df[df["District"].str.len() > 0]

        # Find the ELL column (name varies slightly)
        ell_col = [c for c in df.columns if "English Learner" in c and "Not" not in c]
        if ell_col:
            df["n_ell"] = to_numeric_star(df[ell_col[0]])
        else:
            df["n_ell"] = np.nan

        frames.append(df[["District", "District Code", "fiscal_year", "n_ell"]])
    return pd.concat(frames, ignore_index=True)


# ── Parse Lunch ────────────────────────────────────────────────────────────────
def parse_lunch():
    files = sorted(glob.glob(os.path.join(DATA_DIR, "lunch", "*.csv")))
    frames = []
    for f in files:
        fy = extract_year(os.path.basename(f))
        df = pd.read_csv(f, skiprows=5, dtype=str)
        df.columns = df.columns.str.strip().str.strip('"')
        df["District"] = df["District"].str.strip('"').str.strip()
        df["District Code"] = clean_district_code(df["District Code"])
        df["fiscal_year"] = fy
        df = df[df["District"].str.len() > 0]

        df["n_free_lunch"] = to_numeric_star(df["Free"])
        df["n_reduced_lunch"] = to_numeric_star(df["Reduced"])

        frames.append(df[["District", "District Code", "fiscal_year",
                          "n_free_lunch", "n_reduced_lunch"]])
    return pd.concat(frames, ignore_index=True)


# ── Parse Special Education ─────────────────────────────────────────────────────
def parse_sped():
    files = sorted(glob.glob(os.path.join(DATA_DIR, "special-education", "*.csv")))
    frames = []
    for f in files:
        fy = extract_year(os.path.basename(f))
        df = pd.read_csv(f, skiprows=5, dtype=str)
        df.columns = df.columns.str.strip().str.strip('"')
        df["District"] = df["District"].str.strip('"').str.strip()
        df["District Code"] = clean_district_code(df["District Code"])
        df["fiscal_year"] = fy
        df = df[df["District"].str.len() > 0].copy()

        # Find the special ed column
        sped_col = [c for c in df.columns if "Disabilities" in c and "without" not in c.lower()]
        if sped_col:
            df["n_sped"] = to_numeric_star(df[sped_col[0]])
        else:
            df["n_sped"] = np.nan

        frames.append(df[["District", "District Code", "fiscal_year", "n_sped"]])
    return pd.concat(frames, ignore_index=True)


# ── Main ───────────────────────────────────────────────────────────────────────
print("Parsing all-students...")
all_students = parse_all_students()
print(f"  {len(all_students):,} rows")

print("Parsing race...")
race = parse_race()
print(f"  {len(race):,} rows")

print("Parsing ELL...")
ell = parse_ell()
print(f"  {len(ell):,} rows")

print("Parsing lunch...")
lunch = parse_lunch()
print(f"  {len(lunch):,} rows")

print("Parsing special education...")
sped = parse_sped()
print(f"  {len(sped):,} rows")

# Drop rows with missing district codes (e.g. "Total", "Dept of Mental Health")
all_students = all_students[all_students["District Code"].notna() & (all_students["District Code"] != "")]
race = race[race["District Code"].notna() & (race["District Code"] != "")]
ell = ell[ell["District Code"].notna() & (ell["District Code"] != "")]
lunch = lunch[lunch["District Code"].notna() & (lunch["District Code"] != "")]

# Merge all on District Code × fiscal_year
panel = all_students.copy()
panel = panel.merge(race.drop(columns=["District"]), on=["District Code", "fiscal_year"], how="left")
panel = panel.merge(ell.drop(columns=["District"]), on=["District Code", "fiscal_year"], how="left")
panel = panel.merge(lunch.drop(columns=["District"]), on=["District Code", "fiscal_year"], how="left")
panel = panel.merge(sped.drop(columns=["District"]), on=["District Code", "fiscal_year"], how="left")

# Verify no duplicates
dupes = panel.duplicated(subset=["District Code", "fiscal_year"], keep=False).sum()
assert dupes == 0, f"Unexpected duplicates: {dupes}"

# Compute derived variables
panel["n_frpl"] = panel["n_free_lunch"].add(panel["n_reduced_lunch"], fill_value=0)

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
    ("pct_ell", "n_ell"),
    ("pct_free_lunch", "n_free_lunch"),
    ("pct_frpl", "n_frpl"),
    ("pct_sped", "n_sped"),
]:
    panel[col] = panel[num] / panel["enrollment_total"] * 100

panel["pct_nonwhite"] = 100 - panel["pct_white"]

# Sort
panel = panel.sort_values(["fiscal_year", "District"]).reset_index(drop=True)

# Save
out_path = os.path.join(CLEAN_DIR, "district_year_enrollment.csv")
panel.to_csv(out_path, index=False)

print(f"\nSaved: {out_path}")
print(f"  {len(panel):,} rows × {len(panel.columns)} cols")
print(f"  Years: {sorted(panel['fiscal_year'].unique())}")
print(f"  Districts per year:")
for yr in sorted(panel["fiscal_year"].unique()):
    n = len(panel[panel["fiscal_year"] == yr])
    print(f"    {yr}: {n}")

# Sanity checks
print("\nSanity checks:")
h = panel[panel["District"] == "Hartford School District"]
print("Hartford School District:")
print(h[["fiscal_year", "enrollment_total", "pct_black_hispanic", "pct_white",
         "pct_ell", "pct_frpl"]].to_string(index=False))
