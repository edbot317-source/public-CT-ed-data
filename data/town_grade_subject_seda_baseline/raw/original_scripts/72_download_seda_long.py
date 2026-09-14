"""
72_download_seda_long.py

Streams the SEDA 2025.2 administrative-district LONG files (one row per district x
subject x grade x year) on the GCS and CS scales and keeps two extracts of each:

  data/seda/seda_admindist_long_{gcs,cs}_2025.2_national_all.csv
      every district, ALL-STUDENT columns only (sedaadmin, subject, grade, year, fips,
      stateabb, tot_asmt_all, {gcs,cs}_mn_all, {gcs,cs}_mn_se_all) -- used to estimate
      k_{g,b}, the grade-levels-per-SD conversion, nationally (GCS on CS slope).
  data/seda/seda_admindist_long_{gcs,cs}_2025.2_CT.csv
      Connecticut rows, all columns -- grade-specific baselines for the simulation.

Source: https://stacks.stanford.edu/file/np279jm6134/seda_admindist_long_{gcs,cs}_2025.2.csv
(Reardon et al. 2026). The national files are ~1 GB each and are not stored.
Read by 73_seda_k_and_baselines.py.
"""

import csv
import datetime as dt
import io
import os
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "data", "seda")
os.makedirs(OUT_DIR, exist_ok=True)
STACKS = "https://stacks.stanford.edu/file/np279jm6134/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ct-school-finance research download"


def stream(scale):
    name = f"seda_admindist_long_{scale}_2025.2.csv"
    keep = ["sedaadmin", "subject", "grade", "year", "fips", "stateabb", "tot_asmt_all",
            f"{scale}_mn_all", f"{scale}_mn_se_all"]
    req = urllib.request.Request(STACKS + name, headers={"User-Agent": UA})
    nat = os.path.join(OUT_DIR, name.replace(".csv", "_national_all.csv"))
    ct = os.path.join(OUT_DIR, name.replace(".csv", "_CT.csv"))
    n_in = n_ct = 0
    with urllib.request.urlopen(req, timeout=1800) as resp, \
            open(nat, "w", encoding="utf-8", newline="") as fn, open(ct, "w", encoding="utf-8", newline="") as fc:
        reader = csv.reader(io.TextIOWrapper(resp, encoding="utf-8", newline=""))
        header = next(reader)
        idx = [header.index(c) for c in keep]
        st = header.index("stateabb")
        wn, wc = csv.writer(fn), csv.writer(fc)
        wn.writerow(keep)
        wc.writerow(header)
        for row in reader:
            n_in += 1
            wn.writerow([row[i] for i in idx])
            if row[st] == "CT":
                wc.writerow(row)
                n_ct += 1
    print(f"  {name}: streamed {n_in:,} rows; national all-student slim -> {os.path.basename(nat)}; CT rows {n_ct:,} -> {os.path.basename(ct)}")
    return name, n_in, n_ct


def main():
    log = []
    for scale in ("gcs", "cs"):
        name, n_in, n_ct = stream(scale)
        log.append(f"{dt.datetime.now():%Y-%m-%d}\t{name}\t{STACKS + name}\trows {n_in}; CT rows {n_ct}")
    with open(os.path.join(OUT_DIR, "_download_log.tsv"), "a", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")


if __name__ == "__main__":
    main()
