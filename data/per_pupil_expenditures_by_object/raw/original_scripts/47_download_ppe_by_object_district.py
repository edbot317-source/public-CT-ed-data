"""
47_download_ppe_by_object_district.py

Downloads CT EdSight "Per Pupil Expenditures by Object (District)" CSVs for all
available years (FY2017-18 through FY2024-25). The by-object report carries the
tuition breakout used in Part 1 / Part 3 spending analyses (read via
03_part1_figures.py, data/per-pupil-expenditures-by-object/).

Same SAS stored-process CSV export mechanism as 45/46 (dashboard "Export to
Excel" titled-CSV format). Verified 2026-08-18: the 179 `"Tuition"` object rows
(the only rows the pipeline consumes, via 03_part1_figures.py's
`Object == "Tuition"` filter) are byte-identical to the committed CSVs. The only
difference is a cosmetic encoding of the em-dash in the non-consumed
`"Other - Includes Tuition"` label rows (committed files carry a mis-encoded
em-dash; a fresh curl returns a plain hyphen). This does not affect any result.

Source URL:
    https://edsight.ct.gov/SASStoredProcess/do?
      _program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/EFSDistrictLevelbyObjectExport
      &_year={YYYY-YY}&_district=All+Districts

Output:
    data/per-pupil-expenditures-by-object/object-{YYYY}-{YYYY}.csv
"""

import os
import subprocess
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data", "per-pupil-expenditures-by-object")
COOKIE_JAR = os.path.join(DATA_DIR, "_cookies.txt")
os.makedirs(DATA_DIR, exist_ok=True)

URL_TEMPLATE = (
    "https://edsight.ct.gov/SASStoredProcess/do?"
    "_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/EFSDistrictLevelbyObjectExport"
    "&_year={year}&_district=All+Districts"
)

EXPECT_TITLE = "Per Pupil Expenditures by Object (District)"

START_YEARS = range(2017, 2025)


def download_one(year_short, year_long, out_path):
    url = URL_TEMPLATE.format(year=year_short)
    result = subprocess.run(
        ["curl.exe", "-sS", "-L",
         "-c", COOKIE_JAR, "-b", COOKIE_JAR,
         "-o", out_path, url],
        capture_output=True, text=True, timeout=60,
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
        print(f"  {year_long}: TOO SMALL ({size})")
        os.remove(out_path)
        return False

    print(f"  {year_long}: OK (size={size:,})")
    return True


def main():
    total = success = 0
    for y in START_YEARS:
        year_short = f"{y}-{str(y + 1)[-2:]}"
        year_long = f"{y}-{y + 1}"
        out_path = os.path.join(DATA_DIR, f"object-{year_long}.csv")

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
