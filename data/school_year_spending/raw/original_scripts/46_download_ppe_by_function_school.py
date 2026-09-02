"""
46_download_ppe_by_function_school.py

Downloads CT EdSight "Per Pupil Expenditures by Function (School)" CSVs for all
available years (FY2017-18 through FY2024-25).

This is the school-level spending input read by 02_clean_school.py. Like the
district file (45), the raw CSVs came from the SAS stored-process CSV export
(the dashboard "Export to Excel" titled-CSV format). NOTE: the school-level
stored process REQUIRES &_school=All+Schools; without it the export returns an
empty report. Verified 2026-08-18 to return byte-identical output to the
committed data/ CSVs.

Source URL:
    https://edsight.ct.gov/SASStoredProcess/do?
      _program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/EFSSchoolLevelbyFunctionExport
      &_year={YYYY-YY}&_district=All+Districts&_school=All+Schools

Output:
    data/per-pupil-expenditures-by-function-school/spending-school-{YYYY}-{YYYY}.csv
"""

import os
import subprocess
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data", "per-pupil-expenditures-by-function-school")
COOKIE_JAR = os.path.join(DATA_DIR, "_cookies.txt")
os.makedirs(DATA_DIR, exist_ok=True)

URL_TEMPLATE = (
    "https://edsight.ct.gov/SASStoredProcess/do?"
    "_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/EFSSchoolLevelbyFunctionExport"
    "&_year={year}&_district=All+Districts&_school=All+Schools"
)

EXPECT_TITLE = "Per Pupil Expenditures by Function (School)"

START_YEARS = range(2017, 2025)


def download_one(year_short, year_long, out_path):
    url = URL_TEMPLATE.format(year=year_short)
    result = subprocess.run(
        ["curl.exe", "-sS", "-L",
         "-c", COOKIE_JAR, "-b", COOKIE_JAR,
         "-o", out_path, url],
        capture_output=True, text=True, timeout=90,
    )
    if result.returncode != 0:
        print(f"  {year_long}: CURL ERROR: {result.stderr.strip()}")
        return False

    size = os.path.getsize(out_path)
    with open(out_path, "r", encoding="utf-8") as f:
        head = f.read(4000)
    first_line = head.splitlines()[0].strip() if head else ""

    if "<!DOCTYPE" in first_line or "<html" in first_line.lower():
        print(f"  {year_long}: GOT HTML error page ({size} bytes)")
        os.remove(out_path)
        return False
    if EXPECT_TITLE not in head:
        print(f"  {year_long}: TITLE MISMATCH (expected '{EXPECT_TITLE}')")
        os.remove(out_path)
        return False
    if year_short not in head:
        print(f"  {year_long}: YEAR '{year_short}' not found in title block")
        os.remove(out_path)
        return False
    if size < 1000:
        print(f"  {year_long}: TOO SMALL ({size}) — did you omit _school=All+Schools?")
        os.remove(out_path)
        return False

    print(f"  {year_long}: OK (size={size:,})")
    return True


def main():
    total = success = 0
    for y in START_YEARS:
        year_short = f"{y}-{str(y + 1)[-2:]}"
        year_long = f"{y}-{y + 1}"
        out_path = os.path.join(DATA_DIR, f"spending-school-{year_long}.csv")

        total += 1
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            print(f"  {year_long}: SKIP (exists)")
            success += 1
            continue

        if download_one(year_short, year_long, out_path):
            success += 1
        time.sleep(1)

    if os.path.exists(COOKIE_JAR):
        os.remove(COOKIE_JAR)
    print(f"\nDone: {success}/{total} files downloaded")


if __name__ == "__main__":
    main()
