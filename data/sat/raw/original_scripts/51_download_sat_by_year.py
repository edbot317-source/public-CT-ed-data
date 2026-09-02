"""
51_download_sat_by_year.py

Downloads CT EdSight Connecticut School Day SAT results for ALL STUDENTS and
the High Needs subgroup, DISTRICT level, ELA + Math, for every tested year.

EdSight's CTSchoolDaySATReport_SiteCore report publishes an authoritative
DISTRICT-level rollup when the `_school` parameter is left blank (the same
convention the graduation SiteCore report uses). We use that district rollup
rather than pulling `_school=All Schools` and re-aggregating school rows,
because EdSight applies its own suppression rules at the district level; a
naive scored-test-weighted average over only the *unsuppressed* schools drops
suppressed cells and biases small operators (e.g. CREC) badly. The SiteCore
report returns an HTML listing table, so this mirrors the pd.read_html pattern
in 43_download_archived_total_expenditures.py.

The all-students pull returns one row per district. The High Needs subgroup
pull returns two rows per district, tagged Y (High Needs) / N (Non-High Needs)
in a category column.

No SAT School Day testing occurred in 2019-20 or 2020-21 (COVID), so those
years are skipped.

Output:
    data/sat-by-year/_raw/sat-{SUBJECT}-{YYYY-YY}.html
    data/sat-by-year/sat-{SUBJECT}-{YYYY-YY}.csv
    data/sat-by-year-high-needs/_raw/sat-high-needs-{SUBJECT}-{YYYY-YY}.html
    data/sat-by-year-high-needs/sat-high-needs-{SUBJECT}-{YYYY-YY}.csv
"""

import os
import subprocess
import time
from urllib.parse import urlencode, quote_plus

import pandas as pd


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_ALL = os.path.join(BASE, "data", "sat-by-year")
DATA_HN = os.path.join(BASE, "data", "sat-by-year-high-needs")
RAW_ALL = os.path.join(DATA_ALL, "_raw")
RAW_HN = os.path.join(DATA_HN, "_raw")
for d in [DATA_ALL, DATA_HN, RAW_ALL, RAW_HN]:
    os.makedirs(d, exist_ok=True)

COOKIE_JAR = os.path.join(RAW_ALL, "_cookies.txt")

BASE_URL = "https://edsight.ct.gov/SASStoredProcess/do?"
REPORT = "/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/CTSchoolDaySATReport_SiteCore"
YEARS = [
    "2015-16", "2016-17", "2017-18", "2018-19",
    "2021-22", "2022-23", "2023-24", "2024-25",
]
SUBJECTS = ["ELA", "Math"]


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


def url_for(year, subject, subgroup):
    # Blank _school => EdSight district-level rollup listing.
    params = {
        "_program": REPORT,
        "_rpttype": "listing",
        "_year": year,
        "_district": "All Districts",
        "_subject": subject,
        "_subgroup": subgroup,
        "_school": "",
        "_select": "Submit",
    }
    return BASE_URL + urlencode(params, quote_via=quote_plus)


def download_html(year, subject, subgroup, out_path, cookie_jar):
    url = url_for(year, subject, subgroup)
    result = subprocess.run(
        ["curl.exe", "-sS", "-L", "-m", "90",
         "-c", cookie_jar, "-b", cookie_jar,
         "-o", out_path, url],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl error for {year} {subject}: {result.stderr.strip()}")

    with open(out_path, "r", encoding="latin-1") as f:
        head = f.read(200000)
    if "CT School Day SAT" not in head:
        raise RuntimeError(f"{year} {subject}: response missing SAT title")
    if "Level 3&amp;4" not in head and "Level 3&4" not in head:
        raise RuntimeError(f"{year} {subject}: response missing proficiency header")
    size = os.path.getsize(out_path)
    if size < 5000:
        raise RuntimeError(f"{year} {subject}: response too small ({size})")
    return size


def parse_html(html_path, year, subject, high_needs=False):
    tables = pd.read_html(html_path)
    # The page renders the district listing table twice (fixed header + body).
    # Pick the single widest data table with the most rows; do NOT concat, or
    # every district would be duplicated.
    candidates = []
    for t in tables:
        cols = [col_text(c) for c in t.columns]
        if any("District" in c for c in cols) and any("AverageScore" in c for c in cols):
            candidates.append(t)
    if not candidates:
        raise RuntimeError(f"{year} {subject}: could not find SAT district listing table")
    data = max(candidates, key=lambda t: t.shape[0]).copy()

    cols = list(data.columns)
    idx_district = find_col(cols, "District")
    idx_total_students = find_col(cols, "TotalNumberofStudents")
    idx_total_tested = find_col(cols, "TotalNumberTested")
    idx_participation = find_col(cols, "ParticipationRate")
    idx_scored = find_col(cols, "TotalNumberwithScoredTests")
    idx_prof = find_col(cols, "Level 3&4", "%")
    idx_avg = find_col(cols, "AverageScore")

    out = pd.DataFrame({
        "District": data.iloc[:, idx_district].astype(str).str.strip(),
        "fiscal_year": fiscal_year_from_label(year),
        "subject": subject,
        "total_students": data.iloc[:, idx_total_students].map(clean_number),
        "total_tested": data.iloc[:, idx_total_tested].map(clean_number),
        "participation_rate": data.iloc[:, idx_participation].map(clean_number),
        "n_scored": data.iloc[:, idx_scored].map(clean_number),
        "pct_prof": data.iloc[:, idx_prof].map(clean_number),
        "avg_score": data.iloc[:, idx_avg].map(clean_number),
    })

    if high_needs:
        idx_hn = find_col(cols, "High Needs")
        grp = data.iloc[:, idx_hn].astype(str).str.strip()
        # Y = High Needs, N = Non-High Needs (EdSight subgroup category codes).
        out.insert(3, "needs_group", grp.map({"Y": "High Needs", "N": "Non-High Needs"}))
        out = out[out["needs_group"].notna()]

    out = out[~out["District"].str.lower().isin(["nan", "none", ""])]
    numeric_cols = ["total_students", "total_tested", "participation_rate",
                    "n_scored", "pct_prof", "avg_score"]
    for c in numeric_cols:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out = out.drop_duplicates().reset_index(drop=True)

    min_rows = 100 if high_needs else 50  # ~149 districts all-students; ~2x for Y/N
    if len(out) < min_rows:
        raise RuntimeError(f"{year} {subject}: only {len(out)} district rows parsed")
    return out


def run_group(label, data_dir, raw_dir, subgroup, high_needs=False):
    n_ok = 0
    total = len(YEARS) * len(SUBJECTS)
    cookie_jar = os.path.join(raw_dir, "_cookies.txt")
    for year in YEARS:
        for subject in SUBJECTS:
            prefix = "sat-high-needs" if high_needs else "sat"
            raw_path = os.path.join(raw_dir, f"{prefix}-{subject}-{year}.html")
            csv_path = os.path.join(data_dir, f"{prefix}-{subject}-{year}.csv")

            if os.path.exists(csv_path) and os.path.getsize(csv_path) > 500:
                print(f"  {label} {subject} {year}: SKIP (csv exists)")
                n_ok += 1
                continue

            try:
                if not (os.path.exists(raw_path) and os.path.getsize(raw_path) > 5000):
                    size = download_html(year, subject, subgroup, raw_path, cookie_jar)
                    print(f"  {label} {subject} {year}: downloaded HTML ({size:,} bytes)")
                    time.sleep(1)
                df = parse_html(raw_path, year, subject, high_needs=high_needs)
                df.to_csv(csv_path, index=False)
                print(f"  {label} {subject} {year}: parsed {len(df):>3} rows")
                n_ok += 1
            except Exception as e:
                print(f"  {label} {subject} {year}: ERROR {e}")

    if os.path.exists(cookie_jar):
        os.remove(cookie_jar)
    print(f"{label}: {n_ok}/{total} files available")
    return n_ok, total


def main():
    all_ok = run_group("SAT all students", DATA_ALL, RAW_ALL, "All Students ")
    hn_ok = run_group("SAT high needs", DATA_HN, RAW_HN,
                      "High Needs (F, R, ELL or SWD) ", high_needs=True)
    if os.path.exists(COOKIE_JAR):
        os.remove(COOKIE_JAR)
    print(f"\nDone: {all_ok[0] + hn_ok[0]}/{all_ok[1] + hn_ok[1]} SAT tidy files available.")


if __name__ == "__main__":
    main()
