"""
04_clean_revenue.py

Reads raw CT EdSight Revenue Sources CSVs, builds a district-year panel
with revenue categories as columns. Merges district codes from the
existing spending panel.

Input:
    data/revenue-sources/revenue-*.csv
    clean-data/district_year_spending.csv  (for district code crosswalk)
Output:
    clean-data/district_year_revenue.csv

Revenue categories (per year per district):
    rev_local, rev_state, rev_federal, rev_tuition_other, rev_total  (dollar amounts)
    pct_local, pct_state, pct_federal, pct_tuition_other             (percent of total)

Source URL pattern:
    https://edsight.ct.gov/SASStoredProcess/do?_program=/CTDOE/EdSight/Release/
    Reporting/Public/Reports/StoredProcesses/RevenueSourceExport
    &_year={YYYY-YY}&_district=All+Districts&_schoolconstr=All
"""

import os, re, glob
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE, "data", "revenue-sources")
CLEAN_DIR = os.path.join(BASE, "clean-data")
SPENDING_PATH = os.path.join(CLEAN_DIR, "district_year_spending.csv")
os.makedirs(CLEAN_DIR, exist_ok=True)


def parse_one_file(path):
    """Parse a single revenue-sources CSV into a DataFrame."""
    fname = os.path.basename(path)
    m = re.search(r"revenue-(\d{4})-(\d{2,4})\.csv", fname)
    if not m:
        raise ValueError(f"Cannot parse year from filename: {fname}")
    fy = int(m.group(2)) if len(m.group(2)) == 4 else int(m.group(1)[:2] + m.group(2))

    # Read file — skip the two header rows, assign our own column names
    # Row 0: "","Local",,"State",,"Federal",,"Tuition & Other",,"Total",
    # Row 1: "District","Amount","Percent","Amount","Percent",...
    df = pd.read_csv(
        path,
        skiprows=2,
        header=None,
        names=[
            "District",
            "rev_local", "pct_local",
            "rev_state", "pct_state",
            "rev_federal", "pct_federal",
            "rev_tuition_other", "pct_tuition_other",
            "rev_total", "pct_total",
        ],
        dtype=str,
    )

    # Clean district name: strip leading =, quotes, whitespace
    df["District"] = (
        df["District"]
        .str.replace(r'^[="]+', "", regex=True)
        .str.replace(r'[""]+$', "", regex=True)
        .str.strip()
    )

    # Drop rows where district is empty
    df = df[df["District"].str.len() > 0].copy()

    # Convert numeric columns
    num_cols = [c for c in df.columns if c != "District"]
    for col in num_cols:
        df[col] = pd.to_numeric(
            df[col].str.replace(r'[,$""]', "", regex=True).str.strip(),
            errors="coerce",
        )

    # Drop rows where all revenue values are NaN (N/A districts)
    df = df.dropna(subset=["rev_total"])

    # Drop the pct_total column (always 100)
    df.drop(columns=["pct_total"], inplace=True)

    df["fiscal_year"] = fy
    return df


# --- Load and stack all years ---
files = sorted(glob.glob(os.path.join(RAW_DIR, "revenue-*.csv")))
if not files:
    raise FileNotFoundError(f"No revenue CSVs found in {RAW_DIR}")
print(f"Found {len(files)} revenue source files")

frames = []
for f in files:
    df = parse_one_file(f)
    print(f"  {os.path.basename(f)}: {len(df)} districts")
    frames.append(df)

panel = pd.concat(frames, ignore_index=True)
print(f"\nStacked panel: {len(panel):,} rows")

# --- Merge district codes from spending data ---
if os.path.exists(SPENDING_PATH):
    spending = pd.read_csv(SPENDING_PATH, usecols=["District", "District Code", "fiscal_year"])
    # Build crosswalk: district name → code (use most recent year per district)
    xwalk = (
        spending.sort_values("fiscal_year")
        .drop_duplicates(subset=["District"], keep="last")[["District", "District Code"]]
    )
    n_before = len(panel)
    panel = panel.merge(xwalk, on="District", how="left")
    n_matched = panel["District Code"].notna().sum()
    n_unmatched = n_before - n_matched
    print(f"Merged district codes: {n_matched:,} matched, {n_unmatched:,} unmatched")
    if n_unmatched > 0:
        missing = panel.loc[panel["District Code"].isna(), "District"].unique()
        print(f"  Unmatched districts: {missing[:20]}")

    # Reorder columns
    cols = ["District", "District Code", "fiscal_year",
            "rev_local", "rev_state", "rev_federal", "rev_tuition_other", "rev_total",
            "pct_local", "pct_state", "pct_federal", "pct_tuition_other"]
    panel = panel[cols]
else:
    print(f"WARNING: Spending file not found at {SPENDING_PATH}, skipping district code merge")

# --- Save ---
out_path = os.path.join(CLEAN_DIR, "district_year_revenue.csv")
panel.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")
print(f"  {len(panel):,} rows × {len(panel.columns)} cols")
print(f"  Years: {sorted(panel['fiscal_year'].unique())}")
print(f"  Districts per year:")
for yr in sorted(panel["fiscal_year"].unique()):
    n = len(panel[panel["fiscal_year"] == yr])
    print(f"    {yr}: {n}")
