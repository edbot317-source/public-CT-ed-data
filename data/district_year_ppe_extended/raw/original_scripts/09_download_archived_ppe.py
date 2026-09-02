"""
09_download_archived_ppe.py

Downloads archived per-pupil expenditure data from CT EdSight (2006-07 to 2016-17).
These use the older PerPupilExport stored process with different function categories.

Output:
    data/per-pupil-expenditures-archived/ppe-archived-YYYY-YY.csv

Source URL:
    https://edsight.ct.gov/SASStoredProcess/do?
      _program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/PerPupilExport
      &_year={YYYY-YY}&_district=All+Districts
"""

import os
import subprocess
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data", "per-pupil-expenditures-archived")
COOKIE_JAR = os.path.join(DATA_DIR, "_cookies.txt")
os.makedirs(DATA_DIR, exist_ok=True)

URL_TEMPLATE = (
    "https://edsight.ct.gov/SASStoredProcess/do?"
    "_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/PerPupilExport"
    "&_year={year}&_district=All+Districts"
)

YEARS = [f"{y}-{str(y+1)[-2:]}" for y in range(2006, 2017)]


def main():
    total = 0
    success = 0

    for year in YEARS:
        out_path = os.path.join(DATA_DIR, f"ppe-archived-{year}.csv")

        if os.path.exists(out_path) and os.path.getsize(out_path) > 200:
            print(f"  {year}: SKIP (exists)")
            total += 1
            success += 1
            continue

        total += 1
        url = URL_TEMPLATE.format(year=year)
        result = subprocess.run(
            ["curl.exe", "-sS", "-L",
             "-c", COOKIE_JAR, "-b", COOKIE_JAR,
             "-o", out_path, url],
            capture_output=True, text=True, timeout=30,
        )

        if result.returncode != 0:
            print(f"  {year}: CURL ERROR: {result.stderr.strip()}")
            continue

        size = os.path.getsize(out_path)
        with open(out_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()

        if "<!DOCTYPE" in first_line or "<html" in first_line.lower():
            print(f"  {year}: GOT HTML — error page")
            os.remove(out_path)
            continue

        print(f"  {year}: OK (size={size:,})")
        success += 1
        time.sleep(1)

    if os.path.exists(COOKIE_JAR):
        os.remove(COOKIE_JAR)

    print(f"\nDone: {success}/{total} files downloaded")


if __name__ == "__main__":
    main()
