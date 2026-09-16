"""
62_download_ecs_ctdata.py

Downloads two CT Open Data (Socrata) datasets used to VALIDATE the ECS formula
inputs against primary series:

  engl_by_town.csv        OPM "Equalized Net Grand List by Town (2011-2024 GL)"
                          https://data.ct.gov/Local-Government/Equalized-Net-Grand-List-by-Town-2011-2024-GL-/8rr8-a322
                          one row per town x grand-list year; total_equalized is the ENGL.
                          ECS uses the average of the grand lists 2, 3 and 4 years before
                          the grant fiscal year, divided by population.
  statutory_aid_by_town.csv  OPM "Estimates of Statutory Aid to Municipalities"
                          https://data.ct.gov/d/sdcm-adr4
                          one row per town x fiscal year (FY2025, FY2026 actual; FY2027 estimate)
                          with an education_cost_sharing column -> cross-check of CSDE entitlements.

Both are pulled through the Socrata SODA API as CSV with $limit above the row count
(2,380 and 771 rows on 2026-09-14). No token needed at this volume.

Read by 66_validate_ecs.py.

Output:
    data/ecs/ctdata/engl_by_town.csv
    data/ecs/ctdata/statutory_aid_by_town.csv
"""

import os
import subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "data", "ecs", "ctdata")
os.makedirs(OUT_DIR, exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ct-school-finance research download"

DATASETS = {
    "engl_by_town.csv": "https://data.ct.gov/resource/8rr8-a322.csv?$limit=50000",
    "statutory_aid_by_town.csv": "https://data.ct.gov/resource/sdcm-adr4.csv?$limit=50000",
}


def main():
    for name, url in DATASETS.items():
        out = os.path.join(OUT_DIR, name)
        r = subprocess.run(["curl.exe", "-sS", "-L", "-A", UA, "-o", out, url],
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            print(f"  {name}: CURL ERROR {r.stderr.strip()}")
            continue
        with open(out, "r", encoding="utf-8") as f:
            head = f.readline()
            n = sum(1 for _ in f)
        if "town" not in head.lower() and "grantee" not in head.lower():
            print(f"  {name}: UNEXPECTED HEADER: {head[:120]}")
            continue
        print(f"  {name}: OK ({n:,} rows) header={head.strip()[:90]}")


if __name__ == "__main__":
    main()
