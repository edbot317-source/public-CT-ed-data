"""
80_parse_ma_nss_compliance.py

Parses DESE's net school spending (NSS) compliance summaries (comply-fyYYYY.xlsx, sheet ComplySum) into a
district-year panel: required NSS (required local contribution + Chapter 70 aid), actual NSS, foundation
budget, and the two ratios. Used to calibrate the Connecticut foundation level (the "spending-calibrated"
option scales the transplanted foundation so Connecticut's median town spends the same multiple of its
foundation budget as Massachusetts' median district) and to describe how the NSS floor binds in Massachusetts.

Source: https://www.doe.mass.edu/finance/chapter70/comply-fy2024.xlsx and comply-fy2025.xlsx (downloaded
2026-09-16 to data/ma/dese/). Each file carries the prior year's actuals and the current year's budgets;
only actuals are kept here. State totals and non-operating districts (no required NSS) are dropped.

Output: clean-data/ma_nss_compliance.csv
    fiscal_year, lea_id, district, required_nss, actual_nss, foundation_budget, actual_to_required, actual_to_foundation
"""
import os

import openpyxl
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESE = os.path.join(BASE, "data", "ma", "dese")
FILES = {2024: "comply-fy2024.xlsx", 2025: "comply-fy2025.xlsx"}


def parse(fy, path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = list(wb["ComplySum"].iter_rows(values_only=True))
    hdr = next(i for i, r in enumerate(rows) if r and str(r[0]).strip() == "LEA")
    cols = [str(c).strip() if c is not None else "" for c in rows[hdr]]
    df = pd.DataFrame([list(r)[:len(cols)] for r in rows[hdr + 1:]], columns=cols)
    df = df[df["LEA"].astype(str).str.match(r"^\d{4}$", na=False)].copy()
    req, act, fnd = f"FY{fy % 100} Required NSS", f"FY{fy % 100} Actual NSS", f"FY{fy % 100} Foundation Budget"
    out = pd.DataFrame({"fiscal_year": fy, "lea_id": df["LEA"].astype(str).str.zfill(4), "district": df["District Name"].astype(str).str.strip(),
                        "required_nss": pd.to_numeric(df[req], errors="coerce"), "actual_nss": pd.to_numeric(df[act], errors="coerce"),
                        "foundation_budget": pd.to_numeric(df[fnd], errors="coerce")})
    out = out[out.required_nss.gt(0) & out.actual_nss.notna()].copy()
    out["actual_to_required"] = out.actual_nss / out.required_nss
    out["actual_to_foundation"] = out.actual_nss / out.foundation_budget
    return out


def main():
    parts = [parse(fy, os.path.join(DESE, f)) for fy, f in FILES.items() if os.path.exists(os.path.join(DESE, f))]
    df = pd.concat(parts, ignore_index=True)
    out = os.path.join(BASE, "clean-data", "ma_nss_compliance.csv")
    df.round(6).to_csv(out, index=False)
    for fy, g in df.groupby("fiscal_year"):
        print(f"  FY{fy}: {len(g)} districts; below required {(g.actual_to_required < 1).sum()}; "
              f"median actual/required {g.actual_to_required.median():.3f}; median actual/foundation {g.actual_to_foundation.median():.3f}")
    print(f"[write] {out} ({len(df)} rows)")


if __name__ == "__main__":
    main()
