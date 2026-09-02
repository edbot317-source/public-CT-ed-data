"""
49_download_sbac_all_students.py

Downloads CT EdSight Smarter Balanced (SBAC) results for the ALL STUDENTS
subgroup, district level, ELA + Math, all grades combined, for every tested
year. Read by 03_part1_figures.py and 14_sbac_high_needs_trends.py
(data/sbac-by-year/).

This is the all-students companion to 15_download_sbac_high_needs.py, which
pulls the High Needs subgroup. Both use the SmarterBalancedAssessmentExport
stored process; they differ only in the &_subgroup value.

IMPORTANT: the all-students subgroup value has a TRAILING SPACE ("All Students ")
and the export also requires _school / _subject / _grade params, exactly as in
script 15. Verified 2026-08-18.

No SBAC testing occurred in 2019-20 or 2020-21 (COVID), so those years are
skipped.

Source URL:
    https://edsight.ct.gov/SASStoredProcess/do?
      _program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/SmarterBalancedAssessmentExport
      &_year={YYYY-YY}&_district=All+Districts&_subgroup=All+Students+
      &_school=+&_subject=ELA+and+Math&_grade=All+Grades+Combined

Output:
    data/sbac-by-year/sbac-{YYYY-YY}.csv
"""

import os
import subprocess
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data", "sbac-by-year")
COOKIE_JAR = os.path.join(DATA_DIR, "_cookies.txt")
os.makedirs(DATA_DIR, exist_ok=True)

URL_TEMPLATE = (
    "https://edsight.ct.gov/SASStoredProcess/do?"
    "_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/SmarterBalancedAssessmentExport"
    "&_year={year}&_district=All+Districts&_subgroup=All+Students+"
    "&_school=+&_subject=ELA+and+Math&_grade=All+Grades+Combined"
)

EXPECT_TITLE = "Smarter Balanced Assessments"

YEARS = [
    "2014-15", "2015-16", "2016-17", "2017-18", "2018-19",
    "2021-22", "2022-23", "2023-24", "2024-25",
]


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
    if EXPECT_TITLE not in head:
        print(f"  {year_short}: TITLE MISMATCH (expected '{EXPECT_TITLE}')")
        os.remove(out_path)
        return False
    if "All Students" not in head:
        print(f"  {year_short}: subgroup label 'All Students' missing — check trailing space")
        os.remove(out_path)
        return False
    if size < 1000:
        print(f"  {year_short}: TOO SMALL ({size})")
        os.remove(out_path)
        return False

    print(f"  {year_short}: OK (size={size:,})")
    return True


def main():
    total = success = 0
    for year_short in YEARS:
        out_path = os.path.join(DATA_DIR, f"sbac-{year_short}.csv")

        total += 1
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
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
