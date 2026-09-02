"""
Download SBAC High Needs subgroup data from EdSight.
Uses SmarterBalancedAssessmentExport stored process.
"""
import os
import subprocess
import time

BASE = r'C:\Users\seth\Dropbox\CT-school-finance\ct-school-finance-post'
DATA_DIR = os.path.join(BASE, "data", "sbac-by-year-high-needs")
COOKIE_JAR = os.path.join(DATA_DIR, "_cookies.txt")
os.makedirs(DATA_DIR, exist_ok=True)

URL_TEMPLATE = (
    "https://edsight.ct.gov/SASStoredProcess/do?"
    "_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/SmarterBalancedAssessmentExport"
    "&_year={year}&_district=All+Districts&_subgroup=High+Needs+(F,+R,+ELL+or+SWD)+"
    "&_school=+&_subject=ELA+and+Math&_grade=All+Grades+Combined"
)

YEARS = [
    "2014-15", "2015-16", "2016-17", "2017-18", "2018-19",
    "2021-22", "2022-23", "2023-24", "2024-25",
]


def main():
    total = 0
    success = 0

    for year in YEARS:
        out_path = os.path.join(DATA_DIR, f"sbac-high-needs-{year}.csv")

        if os.path.exists(out_path) and os.path.getsize(out_path) > 500:
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
            print(f"  {year}: GOT HTML — error page ({size} bytes)")
            os.remove(out_path)
            continue

        if size < 500:
            print(f"  {year}: TOO SMALL ({size})")
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
