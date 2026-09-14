"""
69_clean_ncep.py

Parses the NCEP reports downloaded by 68_download_ncep.py into one tidy panel:

    clean-data/district_year_ncep.csv
        district_code, district, fiscal_year, adm, nce, ncep, source

fiscal_year is the END year of the school year (2024-25 -> 2025). Two report
layouts exist: 2007-08 .. 2013-14 list towns only (code, name, ADM, NCE, NCEP,
rank); 2015-16 onward list NCE, ADM, NCEP plus excess-cost basic contributions
and include the regional school districts (codes 201-220). Rows are parsed by
regex from the PDF text; the three numbers are assigned by magnitude (NCE is
the largest, ADM the smallest) and every row is checked against NCEP = NCE/ADM.

For the latest year the CSDE Excel file (which CSDE revises in place, e.g. after
audited EFS figures arrive) takes precedence over the archived PDF; `source`
records which file each row came from.
"""

import glob
import os
import re

import pandas as pd
import pdfplumber

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "ncep")
OUT = os.path.join(BASE, "clean-data")
os.makedirs(OUT, exist_ok=True)

# a value must carry a thousands separator or decimals, so the "1" in "DISTRICT NO. 1" stays part of the name
NUM = r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+)"
ROW = re.compile(r"^\s*(\d{1,3})\s+(.+?)\s+" + NUM + r"\s+" + NUM + r"\s+" + NUM + r"(?:\s|$)")


def num(s):
    return float(s.replace(",", ""))


def assign(n1, n2, n3):
    vals = sorted([n1, n2, n3])
    adm, ncep, nce = vals[0], vals[1], vals[2]
    return adm, nce, ncep


def parse_pdf(path, fy):
    rows = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for line in (page.extract_text() or "").splitlines():
                m = ROW.match(line)
                if not m:
                    continue
                code = int(m.group(1))
                if not (1 <= code <= 169 or 201 <= code <= 299):
                    continue
                adm, nce, ncep = assign(num(m.group(3)), num(m.group(4)), num(m.group(5)))
                rows.append({"district_code": code, "district": m.group(2).strip().title(),
                             "fiscal_year": fy, "adm": adm, "nce": nce, "ncep": ncep,
                             "source": os.path.basename(path)})
    return rows


def parse_xls(path):
    d = pd.read_excel(path, header=None)
    hdr = next(i for i in range(20) if any("ADM" in str(v) for v in d.iloc[i].tolist()))
    title = " ".join(str(v) for v in d.iloc[:hdr].values.ravel() if str(v) != "nan")
    fy = int(re.search(r"(\d{4})-(\d{4}) Net Current", title).group(2))
    body = d.iloc[hdr + 1:].copy()
    body.columns = ["district_code", "district", "nce", "adm", "ncep"] + list(body.columns[5:])
    body["district_code"] = pd.to_numeric(body["district_code"], errors="coerce")
    body = body[body["district_code"].between(1, 299)].copy()
    out = body[["district_code", "district", "nce", "adm", "ncep"]].copy()
    out["district_code"] = out["district_code"].astype(int)
    out["district"] = out["district"].astype(str).str.strip().str.title()
    for c in ("nce", "adm", "ncep"):
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out["fiscal_year"] = fy
    out["source"] = os.path.basename(path)
    return out


def main():
    frames = []
    for f in sorted(glob.glob(os.path.join(RAW, "ncep_*.pdf"))):
        m = re.search(r"ncep_(\d{4})-(\d{2})\.pdf", f)
        fy = int(m.group(1)[:2] + m.group(2))
        rows = parse_pdf(f, fy)
        print(f"  {os.path.basename(f)}: FY{fy} {len(rows)} rows")
        frames.append(pd.DataFrame(rows))
    x = parse_xls(os.path.join(RAW, "csde_basiccon_excel.xls"))
    print(f"  csde_basiccon_excel.xls: FY{x.fiscal_year.iat[0]} {len(x)} rows (takes precedence for that year)")
    frames.append(x)
    df = pd.concat(frames, ignore_index=True)
    # CSDE current file wins over the archived PDF for the same year
    df["_pri"] = (df["source"] == "csde_basiccon_excel.xls").astype(int)
    df = df.sort_values(["district_code", "fiscal_year", "_pri"]).drop_duplicates(["district_code", "fiscal_year"], keep="last").drop(columns="_pri")
    # integrity: NCEP = NCE / ADM
    chk = (df["nce"] / df["adm"] - df["ncep"]).abs()
    bad = df[chk > 1.0]
    if len(bad):
        print(f"  WARNING: {len(bad)} rows where NCE/ADM != NCEP by more than $1")
        print(bad.head().to_string())
    df["ncep"] = df["ncep"].round(2)
    df = df.sort_values(["fiscal_year", "district_code"])[["district_code", "district", "fiscal_year", "adm", "nce", "ncep", "source"]]
    df.to_csv(os.path.join(OUT, "district_year_ncep.csv"), index=False)
    print(f"[write] district_year_ncep.csv: {len(df)} rows, FY{df.fiscal_year.min()}-FY{df.fiscal_year.max()}, "
          f"{df.district_code.nunique()} districts; rows/yr {df.groupby('fiscal_year').size().to_dict()}")


if __name__ == "__main__":
    main()
