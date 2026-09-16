"""
75_download_ccd_grade_enrollment.py

Downloads public-school enrollment by grade for every Connecticut LEA from the
NCES Common Core of Data (CCD) as served by the Urban Institute Education Data
Portal API, school years 2018-19 through 2023-24 (CCD year = fall of the school
year; CCD 2023 = FY2024). Used to split each town's ECS resident-student count
into the grade bands a Massachusetts Chapter 70 foundation budget needs
(pre-K, kindergarten, elementary 1-5, middle 6-8, high school 9-12).

Also downloads the CCD directory (LEA names and types) for the same years so
LEAs can be matched to ECS towns and to regional school districts.

API: https://educationdata.urban.org/documentation/school-districts.html
     GET /api/v1/school-districts/ccd/enrollment/{year}/grade-{g}/?fips=9
     GET /api/v1/school-districts/ccd/directory/{year}/?fips=9
No key required. Each call is small (about 180 rows).

Outputs:
    data/ma/ccd_grade_enrollment_ct.csv   (year, leaid, grade, enrollment)
    data/ma/ccd_directory_ct.csv          (year, leaid, lea_name, agency_type, enrollment, ...)
    data/ma/_download_log.tsv
"""
import csv
import datetime as dt
import json
import os
import subprocess
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "data", "ma")
os.makedirs(OUT_DIR, exist_ok=True)
API = "https://educationdata.urban.org/api/v1/school-districts/ccd"
YEARS = range(2018, 2024)
GRADES = ["pk", "k"] + [str(g) for g in range(1, 13)]


def get(url, tries=3):
    for t in range(tries):
        r = subprocess.run(["curl.exe", "-sS", "-L", url], capture_output=True, text=True, timeout=120)
        if r.returncode == 0 and r.stdout.strip().startswith("{"):
            return json.loads(r.stdout)
        time.sleep(2 + 2 * t)
    raise RuntimeError(f"failed: {url}\n{r.stderr[:200]}")


def main():
    rows, direc, log = [], [], []
    for y in YEARS:
        d = get(f"{API}/directory/{y}/?fips=9")
        for x in d["results"]:
            direc.append({"year": y, "leaid": x["leaid"], "lea_name": x.get("lea_name"), "agency_type": x.get("agency_type"),
                          "enrollment": x.get("enrollment"), "lowest_grade_offered": x.get("lowest_grade_offered"),
                          "highest_grade_offered": x.get("highest_grade_offered"), "county_code": x.get("county_code")})
        n = 0
        for g in GRADES:
            d = get(f"{API}/enrollment/{y}/grade-{g}/?fips=9")
            for x in d["results"]:
                if x.get("race") in (99, None) and x.get("sex") in (99, None):
                    rows.append({"year": y, "leaid": x["leaid"], "grade": g, "enrollment": x["enrollment"]}); n += 1
        print(f"  {y}: {len(d['results'])} LEAs in directory; {n} grade rows")
        log.append(f"{dt.datetime.now():%Y-%m-%d %H:%M}\tccd {y}\t{API}/enrollment/{y}/grade-{{pk,k,1..12}}/?fips=9 and /directory/{y}/?fips=9")
    with open(os.path.join(OUT_DIR, "ccd_grade_enrollment_ct.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["year", "leaid", "grade", "enrollment"]); w.writeheader(); w.writerows(rows)
    with open(os.path.join(OUT_DIR, "ccd_directory_ct.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(direc[0].keys())); w.writeheader(); w.writerows(direc)
    with open(os.path.join(OUT_DIR, "_download_log.tsv"), "a", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")
    print(f"[write] {OUT_DIR}/ccd_grade_enrollment_ct.csv ({len(rows)} rows), ccd_directory_ct.csv ({len(direc)} rows)")


if __name__ == "__main__":
    main()
