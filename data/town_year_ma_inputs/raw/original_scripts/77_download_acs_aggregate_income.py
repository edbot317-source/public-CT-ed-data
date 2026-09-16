"""
77_download_acs_aggregate_income.py

Downloads ACS 5-year aggregate household income (table B19025) and population
(B01003) for Connecticut county subdivisions (towns), vintages 2015-2023. This is
the town income measure for the Massachusetts-style required local contribution
(Chapter 70 uses total personal income from state tax returns; Connecticut's
closest public equivalent by town at these vintages is the ACS aggregate).
Vintage t-4 is used for fiscal year t, matching the ECS median-income convention.

Census API key: CENSUS_API_KEY in the environment or the repo-root .env.

Output:
    data/ecs/acs/acs5_agg_income_ct_towns_{vintage}.csv
"""
import os
import subprocess
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "data", "ecs", "acs")
os.makedirs(OUT_DIR, exist_ok=True)
VINTAGES = range(2015, 2024)
VARS = ["NAME", "B19025_001E", "B01003_001E"]


def key():
    k = os.environ.get("CENSUS_API_KEY")
    if not k:
        env = os.path.join(BASE, ".env")
        if os.path.exists(env):
            for line in open(env, encoding="utf-8"):
                if line.startswith("CENSUS_API_KEY") and "=" in line:
                    k = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not k:
        raise SystemExit("CENSUS_API_KEY not set (env var or repo-root .env)")
    return k


def fetch(url, tries=4):
    for t in range(tries):
        r = subprocess.run(["curl.exe", "-sS", "-L", url], capture_output=True, text=True, timeout=120)
        if r.returncode == 0 and r.stdout.lstrip().startswith("[["):
            return r.stdout
        time.sleep(3 + 3 * t)
    raise RuntimeError(f"failed: {url[:120]}")


def main():
    k = key()
    for v in VINTAGES:
        url = (f"https://api.census.gov/data/{v}/acs/acs5?get={','.join(VARS)}"
               f"&for=county%20subdivision:*&in=state:09&key={k}")
        txt = fetch(url)
        import json, csv
        rows = json.loads(txt)
        out = os.path.join(OUT_DIR, f"acs5_agg_income_ct_towns_{v}.csv")
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerows(rows)
        print(f"  {v}: {len(rows) - 1} county subdivisions -> {os.path.basename(out)}")


if __name__ == "__main__":
    main()
