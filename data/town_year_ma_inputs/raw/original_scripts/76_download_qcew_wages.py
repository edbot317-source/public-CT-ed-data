"""
76_download_qcew_wages.py

Downloads average annual pay for all covered jobs (all industries, all ownerships)
for Connecticut's eight counties and for the state from the BLS Quarterly Census
of Employment and Wages open-data API, calendar years 2016-2023. Massachusetts'
Chapter 70 wage adjustment factor compares the average annual wage of a
municipality's labor market area with the statewide average (MGL c.70 s.2); for
the Connecticut simulation the county stands in for the labor market area.
County-coded QCEW files end with 2023: from 2024 BLS reports Connecticut by
planning region (area codes 09110-09190), so 2023 is the last comparable year.

API: https://data.bls.gov/cew/data/api/{year}/a/area/{area_fips}.csv (annual averages)
Rows kept: own_code 0 (total covered), industry_code 10 (all industries).

Outputs:
    data/ma/qcew_ct_county_wages.csv   (year, area_fips, area, avg_annual_pay, annual_avg_emplvl)
"""
import csv
import datetime as dt
import io
import os
import subprocess
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "data", "ma")
os.makedirs(OUT_DIR, exist_ok=True)
AREAS = {"09000": "Connecticut", "09001": "Fairfield County", "09003": "Hartford County", "09005": "Litchfield County",
         "09007": "Middlesex County", "09009": "New Haven County", "09011": "New London County",
         "09013": "Tolland County", "09015": "Windham County"}
YEARS = range(2016, 2024)


def fetch(year, fips, tries=3):
    url = f"https://data.bls.gov/cew/data/api/{year}/a/area/{fips}.csv"
    for t in range(tries):
        r = subprocess.run(["curl.exe", "-sS", "-L", url], capture_output=True, text=True, timeout=120)
        if r.returncode == 0 and r.stdout.startswith('"area_fips"'):
            return r.stdout, url
        time.sleep(2 + 2 * t)
    raise RuntimeError(f"failed: {url}")


def main():
    out, log = [], []
    for y in YEARS:
        for fips, name in AREAS.items():
            txt, url = fetch(y, fips)
            for r in csv.DictReader(io.StringIO(txt)):
                if r["own_code"] == "0" and r["industry_code"] == "10":
                    out.append({"year": y, "area_fips": fips, "area": name, "avg_annual_pay": int(r["avg_annual_pay"]),
                                "annual_avg_emplvl": int(r["annual_avg_emplvl"])})
            log.append(f"{dt.datetime.now():%Y-%m-%d %H:%M}\tqcew\t{url}")
        print(f"  {y}: done")
    with open(os.path.join(OUT_DIR, "qcew_ct_county_wages.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["year", "area_fips", "area", "avg_annual_pay", "annual_avg_emplvl"]); w.writeheader(); w.writerows(out)
    with open(os.path.join(OUT_DIR, "_download_log.tsv"), "a", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")
    print(f"[write] {OUT_DIR}/qcew_ct_county_wages.csv ({len(out)} rows)")


if __name__ == "__main__":
    main()
