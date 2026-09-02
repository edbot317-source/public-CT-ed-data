"""
54_download_grad5_by_year.py

Downloads CT EdSight FIVE-Year Graduation Rates for ALL STUDENTS and High
Needs Status, district level. This is the same SAS stored process used by the
four-year downloader (52_download_grad_by_year.py); the five-year cohort is
selected with the extra parameters `_gradcat=grad&_rate=5` (the four-year report
is the `_rate=4` default). The report returns an HTML listing table, so this
mirrors the pd.read_html pattern in 52.

Five-year rates lag the four-year series by one year: as of 2026 the latest
published year is 2022-23. Later years return an EdSight prompt/error page (no
"Five-Year Graduation Rates, <year>" title), which is treated as "not yet
published" and skipped cleanly rather than counted as a hard error.

Output:
    data/grad5-by-year/_raw/grad5-{YYYY-YY}.html
    data/grad5-by-year/grad5-{YYYY-YY}.csv
    data/grad5-by-year-high-needs/_raw/grad5-high-needs-{YYYY-YY}.html
    data/grad5-by-year-high-needs/grad5-high-needs-{YYYY-YY}.csv
"""

import os
import re
import subprocess
import time
from urllib.parse import urlencode, quote_plus

import pandas as pd


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_ALL = os.path.join(BASE, "data", "grad5-by-year")
DATA_HN = os.path.join(BASE, "data", "grad5-by-year-high-needs")
RAW_ALL = os.path.join(DATA_ALL, "_raw")
RAW_HN = os.path.join(DATA_HN, "_raw")
for d in [DATA_ALL, DATA_HN, RAW_ALL, RAW_HN]:
    os.makedirs(d, exist_ok=True)

BASE_URL = "https://edsight.ct.gov/SASStoredProcess/do?"
REPORT = "/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/GraduationReport_SiteCore"
# Five-year cohort is available 2011-12 through 2022-23 as of 2026; later years
# are requested too and skip cleanly if EdSight has not published them yet.
YEARS = [f"{y}-{str(y + 1)[-2:]}" for y in range(2011, 2024)]

FIVE_TITLE = "Five-Year Graduation Rates"
# A real data page carries the titled year, e.g. "Five-Year Graduation Rates, 2022-23".
# EdSight's not-yet-published response shows the bare heading with no year, so the
# titled-year pattern cleanly distinguishes real data from the placeholder page.
FIVE_TITLE_YEAR = re.compile(r"Five-Year Graduation Rates,\s*\d{4}")


def fiscal_year_from_label(label):
    """'2022-23' -> 2023 (spring of the school year)."""
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
    # Blank _school returns the district-level subgroup listing; _rate=5 selects
    # the five-year cohort within the shared graduation stored process.
    params = {
        "_program": REPORT,
        "_rpttype": "listing",
        "_gradcat": "grad",
        "_rate": "5",
        "_year": year,
        "_district": "All Districts",
        "_subgroup": subgroup,
        "_school": "",
        "_select": "Submit",
    }
    return BASE_URL + urlencode(params, quote_via=quote_plus)


class NotPublishedYet(Exception):
    """Raised when EdSight has no five-year data for a requested year."""


def validate_raw(year, out_path):
    """Confirm a saved raw HTML is a real five-year data page.

    Run on every pass (freshly downloaded OR pre-existing on disk) so a lingering
    not-published placeholder can never be parsed as data. Raises NotPublishedYet
    for the placeholder page and RuntimeError for other malformed responses.
    """
    with open(out_path, "r", encoding="latin-1") as f:
        head = f.read(600000)
    if not FIVE_TITLE_YEAR.search(head):
        # EdSight returns a prompt/error page for years it has not published.
        raise NotPublishedYet(f"{year}: no titled '{FIVE_TITLE}, <year>' (not published yet)")
    if "Graduation Rate" not in head:
        raise RuntimeError(f"{year}: response missing rate header")
    size = os.path.getsize(out_path)
    if size < 5000:
        raise RuntimeError(f"{year}: response too small ({size})")
    return size


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
    return validate_raw(year, out_path)


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
    idx_cohort = find_col(cols, "Five-Year Cohort Count")
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
    n_avail = 0
    cookie_jar = os.path.join(raw_dir, "_cookies.txt")
    for year in YEARS:
        prefix = "grad5-high-needs" if high_needs else "grad5"
        raw_path = os.path.join(raw_dir, f"{prefix}-{year}.html")
        csv_path = os.path.join(data_dir, f"{prefix}-{year}.csv")

        if os.path.exists(csv_path) and os.path.getsize(csv_path) > 500:
            print(f"  {label} {year}: SKIP (csv exists)")
            n_ok += 1
            n_avail += 1
            continue

        try:
            if not (os.path.exists(raw_path) and os.path.getsize(raw_path) > 5000):
                size = download_html(year, subgroup, raw_path, cookie_jar)
                print(f"  {label} {year}: downloaded HTML ({size:,} bytes)")
                time.sleep(1)
            else:
                # Re-validate a pre-existing raw so a stale not-published
                # placeholder is never parsed as if it were data.
                validate_raw(year, raw_path)
            df = parse_html(raw_path, year, high_needs=high_needs)
            df.to_csv(csv_path, index=False)
            print(f"  {label} {year}: parsed {len(df):>3} rows")
            n_ok += 1
            n_avail += 1
        except NotPublishedYet as e:
            # Clean up the non-data response so re-runs re-check the year.
            # Best-effort: a cloud-sync client (Dropbox) can briefly lock the
            # just-written file on Windows, so never let cleanup crash the run.
            try:
                if os.path.exists(raw_path):
                    os.remove(raw_path)
            except OSError:
                pass
            print(f"  {label} {year}: NOT PUBLISHED YET (skipped)")
        except Exception as e:
            print(f"  {label} {year}: ERROR {e}")
            n_avail += 1

    if os.path.exists(cookie_jar):
        os.remove(cookie_jar)
    print(f"{label}: {n_ok} five-year files available")
    return n_ok


def main():
    all_ok = run_group("Grad5 all students", DATA_ALL, RAW_ALL, "All Students ")
    hn_ok = run_group("Grad5 high needs", DATA_HN, RAW_HN, "High Needs ", high_needs=True)
    print(f"\nDone: {all_ok + hn_ok} five-year graduation tidy files available.")


if __name__ == "__main__":
    main()
