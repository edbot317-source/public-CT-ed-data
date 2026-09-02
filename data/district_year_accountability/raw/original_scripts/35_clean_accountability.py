"""
Clean 2024-25 EdSight accountability/growth exports.

Creates clean-data/district_year_accountability.csv with one row per district:
  District, District Code, fiscal_year, ela_growth, math_growth,
  accountability_index

Growth is the CT accountability Indicator 2 all-students rate, expressed on a
0-100 scale. It matches the Smarter Balanced Growth Model export's "Average
Percentage of Target Achieved" field.
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd


BASE = Path(__file__).resolve().parent.parent
RAW_DIR = BASE / "data" / "accountability"
CLEAN_DIR = BASE / "clean-data"
OUT_PATH = CLEAN_DIR / "district_year_accountability.csv"

FISCAL_YEAR = 2025


def clean_code(value) -> str:
    if pd.isna(value):
        return np.nan
    text = str(value).strip().strip('"')
    text = text.replace("=", "").replace('"', "").strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text.zfill(7) if text.isdigit() else text


def read_edsight_csv(path: Path, required_columns: set[str]) -> pd.DataFrame:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        cols = {c.strip().strip('"') for c in line.split(",")}
        if required_columns.issubset(cols):
            header_idx = i
            break
    if header_idx is None:
        raise RuntimeError(f"Could not find CSV header in {path}")
    return pd.read_csv(StringIO("\n".join(lines[header_idx:])), dtype=str)


def pct_to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace("%", "", regex=False).str.replace(",", "", regex=False).str.strip(),
        errors="coerce",
    )


def load_growth() -> pd.DataFrame:
    path = RAW_DIR / "growth_model_2024_25_all_districts.csv"
    growth = read_edsight_csv(path, {"District Code", "District", "Subject"})
    growth.columns = growth.columns.str.strip().str.strip('"')
    growth["District Code"] = growth["District Code"].map(clean_code)
    growth["District"] = growth["District"].str.strip()
    growth["Subject"] = growth["Subject"].str.strip()
    growth["growth_target_pct"] = pct_to_number(growth["Average Percentageof Target Achieved"])

    wide = growth.pivot_table(
        index=["District", "District Code"],
        columns="Subject",
        values="growth_target_pct",
        aggfunc="first",
    ).reset_index()
    wide.columns.name = None
    wide = wide.rename(columns={"ELA": "ela_growth", "Math": "math_growth"})
    return wide


def load_accountability() -> pd.DataFrame:
    path = RAW_DIR / "next_generation_accountability_2024_25_all.csv"
    acc = read_edsight_csv(path, {"RptngDistrictName", "ReportingDistrictCode", "SchoolName"})
    acc.columns = acc.columns.str.strip().str.strip('"')
    district = acc[
        (acc["SchoolName"].astype(str).str.strip() == "District")
        & (acc["SchoolOrgType"].astype(str).str.strip() == "District")
    ].copy()
    district["District"] = district["RptngDistrictName"].str.strip()
    district["District Code"] = district["ReportingDistrictCode"].map(clean_code)
    total_points = pd.to_numeric(district["TotalPoints"], errors="coerce")
    possible_points = pd.to_numeric(district["TotalPossiblePoints"], errors="coerce")
    district["accountability_index"] = total_points / possible_points * 100

    # Retain the all-students Indicator 2 rates as a cross-check for the
    # Smarter Balanced Growth Model export; rates are stored as 0-1 decimals.
    district["nga_ela_growth"] = pd.to_numeric(district["Ind2ELA_All_Rate"], errors="coerce") * 100
    district["nga_math_growth"] = pd.to_numeric(district["Ind2Math_All_Rate"], errors="coerce") * 100
    return district[
        ["District", "District Code", "accountability_index", "nga_ela_growth", "nga_math_growth"]
    ]


def main() -> None:
    growth = load_growth()
    acc = load_accountability()

    out = growth.merge(acc, on=["District", "District Code"], how="outer", validate="one_to_one")

    for subj in ["ela", "math"]:
        gcol = f"{subj}_growth"
        acol = f"nga_{subj}_growth"
        both = out[[gcol, acol]].dropna()
        if not both.empty:
            max_diff = (both[gcol] - both[acol]).abs().max()
            if max_diff > 0.11:
                raise RuntimeError(f"{gcol} disagrees with NGA Indicator 2 export by {max_diff:.3f} pp")
        out = out.drop(columns=[acol])

    out["fiscal_year"] = FISCAL_YEAR
    out = out[["District", "District Code", "fiscal_year", "ela_growth", "math_growth", "accountability_index"]]
    out = out.sort_values(["District"]).reset_index(drop=True)

    CLEAN_DIR.mkdir(exist_ok=True)
    out.to_csv(OUT_PATH, index=False)

    print(f"Wrote {OUT_PATH.relative_to(BASE)} ({len(out):,} rows)")
    for col in ["ela_growth", "math_growth", "accountability_index"]:
        vals = out[col].dropna()
        print(f"  {col}: n={len(vals):,}, min={vals.min():.1f}, max={vals.max():.1f}")


if __name__ == "__main__":
    main()
