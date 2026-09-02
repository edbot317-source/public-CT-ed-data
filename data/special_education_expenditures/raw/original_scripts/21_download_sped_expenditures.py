"""
21_download_sped_expenditures.py

Downloads special education expenditure data from CT EdSight.

Two sources:
  - Archived (2006-07 to 2016-17): SpecialEducationExport
  - Current (2017-18 to 2024-25): EFSSpecialEducationExpendituresExport

Filename lineage (must match the published analysis scripts 24/25/30/31):
  - Archived years are consumed under TWO names: 24_part3_sped_share_lines.py
    globs `sped-exp-archived-*.csv`, while 31_part3_hps_classroom_vs_tuition.py
    reads bare `sped-exp-{year}.csv`. Both names hold identical content, so the
    archived download is written under both.
  - Current years are consumed as `sped-exp-new-*.csv` by 24/25/30/31 (the
    line-item current-era export). Earlier this script wrote bare
    `sped-exp-{year}.csv` for the current era, which NO reader consumes; it now
    writes `sped-exp-new-{year}.csv` so the download actually feeds the pipeline.

Output:
    data/special-education-expenditures/sped-exp-archived-YYYY-YY.csv   (archived)
    data/special-education-expenditures/sped-exp-YYYY-YY.csv            (archived, bare copy for script 31)
    data/special-education-expenditures/sped-exp-new-YYYY-YY.csv        (current, line-item)
"""

import os
import shutil
import subprocess
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data", "special-education-expenditures")
COOKIE_JAR = os.path.join(DATA_DIR, "_cookies.txt")
os.makedirs(DATA_DIR, exist_ok=True)

# Archived stored process (2006-07 to 2016-17)
URL_ARCHIVED = (
    "https://edsight.ct.gov/SASStoredProcess/do?"
    "_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/SpecialEducationExport"
    "&_year={year}&_district=All+Districts"
)

# Current stored process (2017-18+)
URL_CURRENT = (
    "https://edsight.ct.gov/SASStoredProcess/do?"
    "_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/EFSSpecialEducationExpendituresExport"
    "&_year={year}&_district=All+Districts"
)

ARCHIVED_YEARS = [f"{y}-{str(y+1)[-2:]}" for y in range(2006, 2017)]
CURRENT_YEARS = [f"{y}-{str(y+1)[-2:]}" for y in range(2017, 2025)]


def download_one(url, out_path, label):
    result = subprocess.run(
        ["curl.exe", "-sS", "-L",
         "-c", COOKIE_JAR, "-b", COOKIE_JAR,
         "-o", out_path, url],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        print(f"  {label}: CURL ERROR: {result.stderr.strip()}")
        return False

    size = os.path.getsize(out_path)
    with open(out_path, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()

    if "<!DOCTYPE" in first_line or "<html" in first_line.lower():
        print(f"  {label}: GOT HTML — error page ({size} bytes)")
        os.remove(out_path)
        return False

    if size < 500:
        print(f"  {label}: TOO SMALL ({size})")
        os.remove(out_path)
        return False

    print(f"  {label}: OK (size={size:,})")
    return True


def main():
    total = 0
    success = 0

    # Archived years: written under BOTH `sped-exp-archived-{year}.csv` (read by
    # script 24) and bare `sped-exp-{year}.csv` (read by script 31). Identical
    # content; download once, then copy to the bare name.
    print("=== Archived (SpecialEducationExport) ===")
    for year in ARCHIVED_YEARS:
        out_path = os.path.join(DATA_DIR, f"sped-exp-archived-{year}.csv")
        bare_path = os.path.join(DATA_DIR, f"sped-exp-{year}.csv")
        if os.path.exists(out_path) and os.path.getsize(out_path) > 500:
            print(f"  {year}: SKIP (exists)")
            total += 1
            success += 1
            if not (os.path.exists(bare_path) and os.path.getsize(bare_path) > 500):
                shutil.copyfile(out_path, bare_path)
                print(f"  {year}: copied -> {os.path.basename(bare_path)}")
            continue
        total += 1
        url = URL_ARCHIVED.format(year=year)
        if download_one(url, out_path, year):
            success += 1
            shutil.copyfile(out_path, bare_path)
            print(f"  {year}: copied -> {os.path.basename(bare_path)}")
        time.sleep(1.5)

    # Current years: written as `sped-exp-new-{year}.csv`, the line-item current-era
    # export consumed by scripts 24/25/30/31.
    print("\n=== Current (EFSSpecialEducationExpendituresExport) ===")
    for year in CURRENT_YEARS:
        out_path = os.path.join(DATA_DIR, f"sped-exp-new-{year}.csv")
        if os.path.exists(out_path) and os.path.getsize(out_path) > 500:
            print(f"  {year}: SKIP (exists)")
            total += 1
            success += 1
            continue
        total += 1
        url = URL_CURRENT.format(year=year)
        if download_one(url, out_path, year):
            success += 1
        time.sleep(1.5)

    if os.path.exists(COOKIE_JAR):
        os.remove(COOKIE_JAR)

    print(f"\nDone: {success}/{total} files downloaded")


if __name__ == "__main__":
    main()
