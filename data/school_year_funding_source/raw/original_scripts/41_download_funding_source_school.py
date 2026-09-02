"""
41_download_funding_source_school.py

Downloads CT EdSight school-level "Per Pupil Expenditures by Funding Source
(Summary)" CSVs for all districts, all schools, all available years.

This report differs from the "by Function (School)" report in that it allocates
each school's share of district central expenditures (central office and
to/from-home transportation) down to the school, and reports total PPE split
into Federal Funds vs. State/Local/Other Funds. At the DISTRICT level the
by-function and by-source totals are identical; they diverge only at the
SCHOOL level because of that central-cost allocation.

Source (SAS stored process, CSV export):
    https://edsight.ct.gov/SASStoredProcess/do?
      _program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/EFSReportCardExport
      &_year={YYYY-YY}&_district=All+Districts&_school=All+Schools

Output:
    data/per-pupil-expenditures-by-funding-source-school/funding-source-school-YYYY-YYYY.csv
"""

import os
import subprocess
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data", "per-pupil-expenditures-by-funding-source-school")
COOKIE_JAR = os.path.join(DATA_DIR, "_cookies.txt")
os.makedirs(DATA_DIR, exist_ok=True)

URL_TEMPLATE = (
    "https://edsight.ct.gov/SASStoredProcess/do?"
    "_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/EFSReportCardExport"
    "&_year={year}&_district=All+Districts&_school=All+Schools"
)

# Same coverage window as the by-function school report: 2017-18 through 2024-25.
YEARS = [f"{y}-{y+1}" for y in range(2017, 2025)]


def main():
    ok = 0
    for year in YEARS:
        y0, y1 = year.split("-")
        short = f"{y0}-{y1[-2:]}"  # e.g. 2017-18 for the stored-process param
        out_path = os.path.join(DATA_DIR, f"funding-source-school-{y0}-{y1}.csv")

        if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
            print(f"  {year}: SKIP (exists, {os.path.getsize(out_path):,} bytes)")
            ok += 1
            continue

        url = URL_TEMPLATE.format(year=short)
        result = subprocess.run(
            ["curl.exe", "-sS", "-L", "-c", COOKIE_JAR, "-b", COOKIE_JAR, "-o", out_path, url],
            capture_output=True, text=True, timeout=90,
        )
        if result.returncode != 0:
            print(f"  {year}: CURL ERROR: {result.stderr.strip()}")
            continue

        with open(out_path, "r", encoding="utf-8", errors="ignore") as f:
            first = f.readline().strip()
        if "<!DOCTYPE" in first or "<html" in first.lower():
            print(f"  {year}: GOT HTML (no data for this year?) - removing")
            os.remove(out_path)
            continue

        size = os.path.getsize(out_path)
        print(f"  {year}: OK ({size:,} bytes)")
        ok += 1
        time.sleep(1)

    if os.path.exists(COOKIE_JAR):
        os.remove(COOKIE_JAR)
    print(f"\nDone: {ok}/{len(YEARS)} year files present")


if __name__ == "__main__":
    main()
