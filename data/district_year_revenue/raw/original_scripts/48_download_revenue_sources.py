"""
48_download_revenue_sources.py

Downloads CT EdSight "Revenue Sources" district CSVs for all available years
(FY2017-18 through FY2024-25). Read by 04_clean_revenue.py.

Uses the RevenueSourceExport SAS stored process (CSV export). The stored-process
name and URL pattern were already documented in 04_clean_revenue.py's docstring;
this script makes the download reproducible.

Source URL:
    https://edsight.ct.gov/SASStoredProcess/do?
      _program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/RevenueSourceExport
      &_year={YYYY-YY}&_district=All+Districts&_schoolconstr=All

Output:
    data/revenue-sources/revenue-{YYYY-YY}.csv
"""

import os
import subprocess
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data", "revenue-sources")
COOKIE_JAR = os.path.join(DATA_DIR, "_cookies.txt")
os.makedirs(DATA_DIR, exist_ok=True)

URL_TEMPLATE = (
    "https://edsight.ct.gov/SASStoredProcess/do?"
    "_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/RevenueSourceExport"
    "&_year={year}&_district=All+Districts&_schoolconstr=All"
)

# FY2017-18 through FY2024-25
START_YEARS = range(2017, 2025)


def download_one(year_short, out_path):
    url = URL_TEMPLATE.format(year=year_short)
    result = subprocess.run(
        ["curl.exe", "-sS", "-L",
         "-c", COOKIE_JAR, "-b", COOKIE_JAR,
         "-o", out_path, url],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        print(f"  {year_short}: CURL ERROR: {result.stderr.strip()}")
        return False

    size = os.path.getsize(out_path)
    with open(out_path, "r", encoding="utf-8") as f:
        head = f.read(4000)
    first_line = head.splitlines()[0].strip() if head else ""

    if "<!DOCTYPE" in first_line or "<html" in first_line.lower():
        print(f"  {year_short}: GOT HTML error page ({size} bytes)")
        os.remove(out_path)
        return False
    # Revenue export header row lists the source categories (Local/State/Federal).
    if "Local" not in head or "State" not in head:
        print(f"  {year_short}: UNEXPECTED CONTENT (no Local/State header)")
        os.remove(out_path)
        return False
    if size < 500:
        print(f"  {year_short}: TOO SMALL ({size})")
        os.remove(out_path)
        return False

    print(f"  {year_short}: OK (size={size:,})")
    return True


def main():
    total = success = 0
    for y in START_YEARS:
        year_short = f"{y}-{str(y + 1)[-2:]}"
        out_path = os.path.join(DATA_DIR, f"revenue-{year_short}.csv")

        total += 1
        if os.path.exists(out_path) and os.path.getsize(out_path) > 500:
            print(f"  {year_short}: SKIP (exists)")
            success += 1
            continue

        if download_one(year_short, out_path):
            success += 1
        time.sleep(1)

    if os.path.exists(COOKIE_JAR):
        os.remove(COOKIE_JAR)
    print(f"\nDone: {success}/{total} files downloaded")


if __name__ == "__main__":
    main()
