"""
06_download_enrollment.py

Downloads CT EdSight enrollment data by subgroup for all available years.
Uses curl with cookie jar for CAS authentication.

Output:
    data/enrollment/all-students/enrollment-all-students-YYYY-YY.csv
    data/enrollment/race/enrollment-race-YYYY-YY.csv
    data/enrollment/ell/enrollment-ell-YYYY-YY.csv
    data/enrollment/lunch/enrollment-lunch-YYYY-YY.csv
    data/enrollment/special-education/enrollment-special-education-YYYY-YY.csv

Source URL:
    https://edsight.ct.gov/SASStoredProcess/do?
      _program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/EnrollmentYearExport
      &_year={YYYY-YY}&_district=All+Districts&_school=+&display=1&_subgroup={subgroup}
"""

import os
import subprocess
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data", "enrollment")
COOKIE_JAR = os.path.join(BASE, "data", "enrollment", "_cookies.txt")

URL_TEMPLATE = (
    "https://edsight.ct.gov/SASStoredProcess/do?"
    "_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/EnrollmentYearExport"
    "&_year={year}&_district=All+Districts&_school=+&display=1&_subgroup={subgroup_encoded}"
)

# 2007-08 through 2024-25 (2006-07 returns no data)
YEARS = [f"{y}-{str(y+1)[-2:]}" for y in range(2007, 2026)]

SUBGROUPS = {
    "all-students": "All Students",
    "race": "Race",
    "ell": "ELL",
    "lunch": "Lunch",
    # Special Education status subgroup: returns a district-level crosstab titled
    # "Student Counts by District and Special Education Status" (IEP vs non-IEP).
    # Read by 07_clean_enrollment.py for the SWD enrollment denominators.
    "special-education": "Special Education",
}


def download_one(year, subgroup_key, subgroup_value, out_path):
    """Download a single enrollment CSV via curl."""
    from urllib.parse import quote
    url = URL_TEMPLATE.format(year=year, subgroup_encoded=quote(subgroup_value))
    result = subprocess.run(
        ["curl.exe", "-sS", "-L",
         "-c", COOKIE_JAR, "-b", COOKIE_JAR,
         "-o", out_path, url],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        print(f"  CURL ERROR: {result.stderr.strip()}")
        return False

    size = os.path.getsize(out_path)
    with open(out_path, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()

    if "<!DOCTYPE" in first_line or "<html" in first_line.lower():
        print(f"  {year} {subgroup_key}: GOT HTML (size={size}) — likely error page")
        os.remove(out_path)
        return False

    if "did not contain any results" in open(out_path, "r", encoding="utf-8").read():
        print(f"  {year} {subgroup_key}: NO DATA")
        os.remove(out_path)
        return False

    print(f"  {year} {subgroup_key}: OK (size={size:,})")
    return True


def main():
    total = 0
    success = 0

    for subgroup_key, subgroup_value in SUBGROUPS.items():
        sub_dir = os.path.join(DATA_DIR, subgroup_key)
        os.makedirs(sub_dir, exist_ok=True)

        for year in YEARS:
            out_path = os.path.join(sub_dir, f"enrollment-{subgroup_key}-{year}.csv")

            # Skip if already downloaded
            if os.path.exists(out_path) and os.path.getsize(out_path) > 200:
                print(f"  {year} {subgroup_key}: SKIP (exists)")
                total += 1
                success += 1
                continue

            total += 1
            ok = download_one(year, subgroup_key, subgroup_value, out_path)
            if ok:
                success += 1

            # Brief pause between requests
            time.sleep(1)

    # Clean up cookie jar
    if os.path.exists(COOKIE_JAR):
        os.remove(COOKIE_JAR)

    print(f"\nDone: {success}/{total} files downloaded successfully")


if __name__ == "__main__":
    main()
