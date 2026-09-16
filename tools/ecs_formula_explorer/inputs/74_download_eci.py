"""
74_download_eci.py

Downloads the Employment Cost Index for state and local government workers (total
compensation, all industries and occupations; BLS series CIU3010000000000I, index
Dec-2005 = 100, quarterly, not seasonally adjusted) from FRED and writes calendar-year
averages. Used by the ECS Formula Explorer as an alternative to CPI-U for indexing the
$11,525 foundation from 2013: school budgets are mostly compensation, so an
employment-cost index tracks the cost of delivering the same services more closely than
consumer prices.

Source: https://fred.stlouisfed.org/series/CIU3010000000000I (BLS Employment Cost Index)
Output: data/eci-state-local-govt-fred.csv   (year, eci_avg, quarters)
"""
import csv
import os
import subprocess
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CIU3010000000000I"
RAW = os.path.join(BASE, "data", "eci-state-local-govt-fred-quarterly.csv")
OUT = os.path.join(BASE, "data", "eci-state-local-govt-fred.csv")


def main():
    r = subprocess.run(["curl.exe", "-sS", "-L", "-o", RAW, URL], capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    q = defaultdict(list)
    with open(RAW, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            v = row["CIU3010000000000I"]
            if v not in ("", "."):
                q[int(row["observation_date"][:4])].append(float(v))
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["year", "eci_avg", "quarters"])
        for y in sorted(q):
            w.writerow([y, round(sum(q[y]) / len(q[y]), 4), len(q[y])])
    print(f"[write] {OUT}: {min(q)}-{max(q)} ({len(q)} years; last year has {len(q[max(q)])} quarters)")


if __name__ == "__main__":
    main()
