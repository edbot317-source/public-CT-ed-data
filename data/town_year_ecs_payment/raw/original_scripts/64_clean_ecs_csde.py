"""
64_clean_ecs_csde.py

Cleans the official CSDE ECS spreadsheets (from 60_download_ecs_csde.py) into
tidy town x fiscal_year panels.

  town_year_ecs_entitlement.csv   FY2001..FY2027: entitlement (dollars), plus the
                                  Alliance / Education-Diversity / non-Alliance split
                                  where CSDE publishes it (FY2012..FY2027).
  town_year_ecs_payment.csv       FY2026 April payment list: entitlement, Alliance
                                  set-aside, comp-ed set-aside, local entitlement,
                                  prior payments, SpEd prior-year adjustment, payment.

fiscal_year is the END year of the school year (2025-26 -> 2026), matching the
rest of this repo's panels. CSDE's "District Code" for ECS is the town code
(1..169); it equals the local board of education's district code. Regional
school districts receive no ECS directly (member towns do), so there is no
district-level ECS beyond the town's own board.
"""

import os
import re

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "ecs", "csde")
OUT = os.path.join(BASE, "clean-data")


def fy_end(label):
    """'2012-13' -> 2013, '2019-2020' -> 2020, '2000-01' -> 2001."""
    m = re.match(r"\s*(\d{4})\s*-\s*(\d{2,4})\s*$", str(label))
    if not m:
        return None
    a, b = m.group(1), m.group(2)
    return int(b) if len(b) == 4 else int(a[:2] + b)


def header_row(d, must_contain):
    """First row whose cells contain `must_contain`; the sentinel '-' means
    'a fiscal-year label like 2012-13' (so a date cell in the title block does
    not qualify)."""
    for i in range(min(15, len(d))):
        vals = [str(v) for v in d.iloc[i].tolist()]
        if must_contain == "-":
            if sum(1 for v in vals if fy_end(v)) >= 2:
                return i
        elif any(must_contain in v for v in vals):
            return i
    raise ValueError(f"header containing {must_contain!r} not found")


def clean_entitlements():
    x = pd.ExcelFile(os.path.join(RAW, "ecsentit_excel.xlsx"))
    sheets = {s: x.parse(s, header=None) for s in x.sheet_names}
    x.close()
    parts = []
    for sheet, d in sheets.items():
        r = header_row(d, "-")                              # row with '2000-01' style labels
        hdr = d.iloc[r].tolist()
        body = d.iloc[r + 1:].copy()
        body.columns = hdr
        code_col, name_col = hdr[0], hdr[1]
        body["town_code"] = pd.to_numeric(body[code_col], errors="coerce")
        body = body[body["town_code"].between(1, 169)].copy()
        body["town_code"] = body["town_code"].astype(int)
        body["town"] = body[name_col].astype(str).str.strip()
        year_cols = [c for c in hdr if fy_end(c)]
        long = body.melt(id_vars=["town_code", "town"], value_vars=year_cols,
                         var_name="fy_label", value_name="entitlement")
        long["fiscal_year"] = long["fy_label"].map(fy_end)
        long["entitlement"] = pd.to_numeric(long["entitlement"], errors="coerce")
        parts.append(long.drop(columns="fy_label"))
        print(f"  entitlements sheet {sheet!r}: {len(body)} towns x {len(year_cols)} years")
    ent = pd.concat(parts, ignore_index=True)
    ent = ent.drop_duplicates(["town_code", "fiscal_year"], keep="last")
    return ent


def clean_alliance_split():
    x = pd.ExcelFile(os.path.join(RAW, "ecs-alliance-nonalliance_excel.xlsx"))
    sheets = {s: x.parse(s, header=None) for s in x.sheet_names}
    x.close()
    rows = []
    for sheet, d in sheets.items():
        r = header_row(d, "Total ECS")
        hdr = [str(v).replace("\n", " ").strip() for v in d.iloc[r].tolist()]
        body = d.iloc[r + 1:].copy()
        body.columns = hdr
        code_col = hdr[0]
        body["town_code"] = pd.to_numeric(body[code_col], errors="coerce")
        body = body[body["town_code"].between(1, 169)].copy()
        for c in hdr[2:]:
            m = re.search(r"(Total ECS\s+Entitlement|Alliance Portion|Non-\s*Alliance Portion|Education Diversity Portion)\s+(\d{4}-\d{2,4})", c)
            if not m:
                continue
            kind, fy = m.group(1), fy_end(m.group(2))
            var = {"Total ECS": "entitlement_split_total", "Alliance": "alliance_portion",
                   "Non-": "non_alliance_portion", "Education": "education_diversity_portion"}[
                re.match(r"(Total ECS|Alliance|Non-|Education)", kind).group(1)]
            for tc, v in zip(body["town_code"], body[c]):
                rows.append((int(tc), fy, var, pd.to_numeric(v, errors="coerce")))
        print(f"  alliance sheet {sheet!r}: {len(body)} towns")
    s = pd.DataFrame(rows, columns=["town_code", "fiscal_year", "var", "value"])
    return s.pivot_table(index=["town_code", "fiscal_year"], columns="var", values="value").reset_index()


def clean_payment_list():
    d = pd.read_excel(os.path.join(RAW, "ecspay_april_excel.xlsx"), header=None)
    r = header_row(d, "District Code")
    hdr = [str(v).replace("\n", " ").strip() for v in d.iloc[r].tolist()]
    body = d.iloc[r + 1:].copy()
    body.columns = hdr
    body["town_code"] = pd.to_numeric(body[hdr[0]], errors="coerce")
    body = body[body["town_code"].between(1, 169)].copy()
    ren = {}
    for c in hdr:
        cl = c.lower()
        if "ecs entitlement" in cl and "(1)" in cl:
            ren[c] = "entitlement"
        elif "alliance district setaside" in cl:
            ren[c] = "alliance_setaside"
        elif "comp ed" in cl:
            ren[c] = "comp_ed_setaside"
        elif "local entitlement" in cl:
            ren[c] = "local_entitlement"
        elif "previous local payments" in cl:
            ren[c] = "previous_local_payments"
        elif "special ed prior year" in cl:
            ren[c] = "sped_prior_year_adjustment"
        elif "payment" in cl and "previous" not in cl:
            ren.setdefault(c, "payment_this_period")
    out = body.rename(columns=ren)
    keep = ["town_code"] + [v for v in ren.values() if v in out.columns]
    out = out[keep].copy()
    out["town"] = body[hdr[1]].astype(str).str.strip().values
    m = re.search(r"(\d{4})-(\d{4})", " ".join(str(v) for v in d.iloc[:r].values.ravel()))
    out["fiscal_year"] = int(m.group(2)) if m else 2026
    for c in out.columns:
        if c not in ("town",):
            out[c] = pd.to_numeric(out[c], errors="coerce")
    out["town_code"] = out["town_code"].astype(int)
    print(f"  payment list: {len(out)} towns, FY{out['fiscal_year'].iat[0]}, cols {list(ren.values())}")
    return out


def main():
    print("[clean] CSDE ECS files")
    ent = clean_entitlements()
    split = clean_alliance_split()
    ent = ent.merge(split, on=["town_code", "fiscal_year"], how="left")
    bad = ent.dropna(subset=["entitlement_split_total"])
    bad = bad[(bad["entitlement"] - bad["entitlement_split_total"]).abs() > 1]
    if len(bad):
        print(f"  WARNING: {len(bad)} town-years where the split-file total != entitlement file")
        print(bad[["town", "fiscal_year", "entitlement", "entitlement_split_total"]].head())
    ent["district_code"] = ent["town_code"]
    cols = ["town_code", "district_code", "town", "fiscal_year", "entitlement", "alliance_portion",
            "education_diversity_portion", "non_alliance_portion"]
    ent = ent.reindex(columns=cols).sort_values(["fiscal_year", "town_code"])
    ent.to_csv(os.path.join(OUT, "town_year_ecs_entitlement.csv"), index=False)
    print(f"[write] town_year_ecs_entitlement.csv: {len(ent)} rows, FY{ent.fiscal_year.min()}-FY{ent.fiscal_year.max()}, "
          f"{ent.town_code.nunique()} towns")
    pay = clean_payment_list()
    pay["district_code"] = pay["town_code"]
    pay.to_csv(os.path.join(OUT, "town_year_ecs_payment.csv"), index=False)
    print("[write] town_year_ecs_payment.csv")


if __name__ == "__main__":
    main()
