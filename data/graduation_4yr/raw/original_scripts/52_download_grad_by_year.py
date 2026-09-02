"""
52_download_grad_by_year.py

Downloads CT EdSight Four-Year Graduation Rates for ALL STUDENTS and High
Needs Status, district level, for 2011-12 through 2024-25. The SiteCore report
returns an HTML listing table, so this mirrors the pd.read_html pattern in
43_download_archived_total_expenditures.py.

Output:
    data/grad-by-year/_raw/grad-{YYYY-YY}.html
    data/grad-by-year/grad-{YYYY-YY}.csv
    data/grad-by-year-high-needs/_raw/grad-high-needs-{YYYY-YY}.html
    data/grad-by-year-high-needs/grad-high-needs-{YYYY-YY}.csv
"""

import os
import subprocess
import time
from urllib.parse import urlencode, quote_plus

import pandas as pd


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_ALL = os.path.join(BASE, "data", "grad-by-year")
DATA_HN = os.path.join(BASE, "data", "grad-by-year-high-needs")
RAW_ALL = os.path.join(DATA_ALL, "_raw")
RAW_HN = os.path.join(DATA_HN, "_raw")
for d in [DATA_ALL, DATA_HN, RAW_ALL, RAW_HN]:
    os.makedirs(d, exist_ok=True)

BASE_URL = "https://edsight.ct.gov/SASStoredProcess/do?"
REPORT = "/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/GraduationReport_SiteCore"
YEARS = [f"{y}-{str(y + 1)[-2:]}" for y in range(2011, 2025)]


def fiscal_year_from_label(label):
    """'2024-25' -> 2025 (spring of the school year)."""
    return int(label[:2] + label.split("-")[1])


def clean_number(s):
    s = str(s).replace("$", "").replace(",", "").replace("%", "").strip()
    if s in ["", "*", "N/A", "nan", "None"]:
        return pd.NA
    return s


def col_text(col):
    if isinstance(col, tuple):
        parts = [str(p).strip() for p in col if not str(p).startswith("Unnamed")]
        return " ".join(parts)
    return str(col).strip()


def find_col(cols, *needles):
    for i, c in enumerate(cols):
        text = col_text(c).replace("\n", " ")
        if all(n in text for n in needles):
            return i
    raise RuntimeError(f"could not find column containing {needles}")


def url_for(year, subgroup):
    # For this SiteCore report, blank _school is what returns the district-level
    # subgroup listing; _school=+ returns the prompt/SAS source page for High Needs.
    params = {
        "_program": REPORT,
        "_rpttype": "listing",
        "_year": year,
        "_district": "All Districts",
        "_subgroup": subgroup,
        "_school": "",
        "_select": "Submit",
    }
    return BASE_URL + urlencode(params, quote_via=quote_plus)


def download_html(year, subgroup, out_path, cookie_jar):
    url = url_for(year, subgroup)
    result = subprocess.run(
        ["curl.exe", "-sS", "-L", "-m", "90",
         "-c", cookie_jar, "-b", cookie_jar,
         "-o", out_path, url],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl error for {year}: {result.stderr.strip()}")

    with open(out_path, "r", encoding="latin-1") as f:
        head = f.read(200000)
    if "Four-Year Graduation Rates" not in head:
        raise RuntimeError(f"{year}: response missing graduation title")
    if "Graduation Rate" not in head:
        raise RuntimeError(f"{year}: response missing rate header")
    size = os.path.getsize(out_path)
    if size < 5000:
        raise RuntimeError(f"{year}: response too small ({size})")
    return size


def parse_html(html_path, year, high_needs=False):
    tables = pd.read_html(html_path)
    data = None
    for t in tables:
        cols = list(t.columns)
        texts = [col_text(c) for c in cols]
        if "District" in texts and any("Graduation Rate" in x for x in texts):
            data = t.copy()
            break
    if data is None:
        raise RuntimeError(f"{year}: could not find graduation listing table")

    cols = list(data.columns)
    idx_district = find_col(cols, "District")
    idx_cohort = find_col(cols, "Four-Year Cohort Count")
    idx_grad_count = find_col(cols, "Graduation Count")
    idx_grad_rate = find_col(cols, "Graduation Rate")

    out = pd.DataFrame({
        "District": data.iloc[:, idx_district].astype(str).str.strip(),
        "fiscal_year": fiscal_year_from_label(year),
        "cohort_count": data.iloc[:, idx_cohort].map(clean_number),
        "graduation_count": data.iloc[:, idx_grad_count].map(clean_number),
        "graduation_rate": data.iloc[:, idx_grad_rate].map(clean_number),
    })

    if high_needs:
        idx_hn = find_col(cols, "High Needs Status")
        out.insert(2, "needs_group", data.iloc[:, idx_hn].astype(str).str.strip())
        out = out[out["needs_group"].isin(["High Needs", "Non-High Needs"])]

    out = out[~out["District"].str.lower().isin(["nan", "none", ""])]
    for c in ["cohort_count", "graduation_count", "graduation_rate"]:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    if len(out) < 100:
        raise RuntimeError(f"{year}: only {len(out)} graduation rows parsed")
    return out.reset_index(drop=True)


def run_group(label, data_dir, raw_dir, subgroup, high_needs=False):
    n_ok = 0
    cookie_jar = os.path.join(raw_dir, "_cookies.txt")
    for year in YEARS:
        prefix = "grad-high-needs" if high_needs else "grad"
        raw_path = os.path.join(raw_dir, f"{prefix}-{year}.html")
        csv_path = os.path.join(data_dir, f"{prefix}-{year}.csv")

        if os.path.exists(csv_path) and os.path.getsize(csv_path) > 500:
            print(f"  {label} {year}: SKIP (csv exists)")
            n_ok += 1
            continue

        try:
            if not (os.path.exists(raw_path) and os.path.getsize(raw_path) > 5000):
                size = download_html(year, subgroup, raw_path, cookie_jar)
                print(f"  {label} {year}: downloaded HTML ({size:,} bytes)")
                time.sleep(1)
            df = parse_html(raw_path, year, high_needs=high_needs)
            df.to_csv(csv_path, index=False)
            print(f"  {label} {year}: parsed {len(df):>3} rows")
            n_ok += 1
        except Exception as e:
            print(f"  {label} {year}: ERROR {e}")

    if os.path.exists(cookie_jar):
        os.remove(cookie_jar)
    print(f"{label}: {n_ok}/{len(YEARS)} files available")
    return n_ok, len(YEARS)


def main():
    all_ok = run_group("Graduation all students", DATA_ALL, RAW_ALL, "All Students")
    hn_ok = run_group("Graduation high needs", DATA_HN, RAW_HN, "High Needs ", high_needs=True)
    print(f"\nDone: {all_ok[0] + hn_ok[0]}/{all_ok[1] + hn_ok[1]} graduation tidy files available.")


if __name__ == "__main__":
    main()
