"""
60_download_ecs_csde.py

Downloads the CSDE Bureau of Fiscal Services ECS (Education Cost Sharing)
spreadsheets that are the OFFICIAL source for grant amounts by town:

  ecsentit_excel.xlsx                 ECS entitlements by town, FY2000-01 .. FY2026-27
                                      (3 sheets: "2000 thru 2011", "2012 - 2024", "2025-2027")
  ecs-alliance-nonalliance_excel.xlsx Alliance / Education-Diversity / non-Alliance
                                      split of each town's entitlement, FY2011-12 .. FY2026-27
  ecspay_april_excel.xlsx             FY2025-26 April payment list (entitlement, Alliance
                                      set-aside, comp-ed set-aside, local entitlement,
                                      prior payments, SpEd prior-year adjustment)

Linked from:
    https://portal.ct.gov/SDE/Fiscal-Services/Education-Cost-Sharing-Grant-ECS-MBR/Documents

These are static files under portal.ct.gov/-/media/ and download fine with curl.exe
(verified 2026-09-14). CSDE overwrites them in place when a new fiscal year is
added, so the download date is recorded in data/ecs/csde/_download_log.txt.

Read by 64_clean_ecs.py.

Output:
    data/ecs/csde/<file>
"""

import datetime as dt
import os
import subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "data", "ecs", "csde")
os.makedirs(OUT_DIR, exist_ok=True)

FILES = {
    "ecsentit_excel.xlsx":
        "https://portal.ct.gov/-/media/sde/grants-management/ecsmbr/ecsentit_excel.xlsx",
    "ecs-alliance-nonalliance_excel.xlsx":
        "https://portal.ct.gov/-/media/sde/grants-management/ecsmbr/ecs-alliance-nonalliance_excel.xlsx",
    "ecspay_april_excel.xlsx":
        "https://portal.ct.gov/-/media/sde/grants-management/ecsmbr/ecspay_april_excel.xlsx",
}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ct-school-finance research download"


def download_one(name, url):
    out = os.path.join(OUT_DIR, name)
    r = subprocess.run(["curl.exe", "-sS", "-L", "-A", UA, "-o", out, url],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print(f"  {name}: CURL ERROR {r.stderr.strip()}")
        return False
    size = os.path.getsize(out)
    with open(out, "rb") as f:
        magic = f.read(4)
    if magic[:2] != b"PK" or size < 10_000:       # xlsx is a zip container
        print(f"  {name}: NOT AN XLSX (size={size}, magic={magic!r})")
        os.remove(out)
        return False
    print(f"  {name}: OK (size={size:,})")
    return True


def main():
    ok = 0
    for name, url in FILES.items():
        ok += download_one(name, url)
    with open(os.path.join(OUT_DIR, "_download_log.txt"), "a", encoding="utf-8") as f:
        f.write(f"{dt.datetime.now():%Y-%m-%d %H:%M} downloaded {ok}/{len(FILES)} files\n")
    print(f"done: {ok}/{len(FILES)}")


if __name__ == "__main__":
    main()
