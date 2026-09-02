"""
16_download_school_enrollment_race.py

Downloads CT EdSight school-level enrollment data by race for all available years.
Adapts 06_download_enrollment.py for school-level pulls (_school=All+Schools).

Output:
    data/enrollment/race-school/enrollment-race-school-YYYY-YY.csv

Source URL:
    https://edsight.ct.gov/SASStoredProcess/do?
      _program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/EnrollmentYearExport
      &_year={YYYY-YY}&_district=All+Districts&_school=All+Schools&display=1&_subgroup=Race
"""

import os
import subprocess
import time
from urllib.parse import quote

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data", "enrollment", "race-school")
COOKIE_JAR = os.path.join(DATA_DIR, "_cookies.txt")

URL_TEMPLATE = (
    "https://edsight.ct.gov/SASStoredProcess/do?"
    "_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/EnrollmentYearExport"
    "&_year={year}&_district=All+Districts&_school=All+Schools&display=1&_subgroup=Race"
)

# 2007-08 through 2025-26
YEARS = [f"{y}-{str(y+1)[-2:]}" for y in range(2007, 2026)]


def download_one(year, out_path):
    """Download a single school-level enrollment-by-race CSV via curl."""
    url = URL_TEMPLATE.format(year=year)
    result = subprocess.run(
        ["curl.exe", "-sS", "-L",
         "-c", COOKIE_JAR, "-b", COOKIE_JAR,
         "-o", out_path, url],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        print(f"  CURL ERROR: {result.stderr.strip()}")
        return False

    size = os.path.getsize(out_path)
    with open(out_path, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()

    if "<!DOCTYPE" in first_line or "<html" in first_line.lower():
        print(f"  {year}: GOT HTML (size={size}) — likely error page")
        os.remove(out_path)
        return False

    if "did not contain any results" in open(out_path, "r", encoding="utf-8").read():
        print(f"  {year}: NO DATA")
        os.remove(out_path)
        return False

    print(f"  {year}: OK (size={size:,})")
    return True


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    total = 0
    success = 0

    for year in YEARS:
        out_path = os.path.join(DATA_DIR, f"enrollment-race-school-{year}.csv")

        # Skip if already downloaded
        if os.path.exists(out_path) and os.path.getsize(out_path) > 500:
            print(f"  {year}: SKIP (exists)")
            total += 1
            success += 1
            continue

        total += 1
        ok = download_one(year, out_path)
        if ok:
            success += 1

        # Brief pause between requests
        time.sleep(1.5)

    # Clean up cookie jar
    if os.path.exists(COOKIE_JAR):
        os.remove(COOKIE_JAR)

    print(f"\nDone: {success}/{total} files downloaded successfully")


if __name__ == "__main__":
    main()
