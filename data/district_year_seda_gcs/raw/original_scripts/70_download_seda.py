"""
70_download_seda.py

Downloads the Stanford Education Data Archive (SEDA) 2025.2 administrative-
district achievement estimates on the GCS ("grade cohort standardized") scale
and keeps the CONNECTICUT rows, plus the codebook, crosswalk codebook and the
technical documentation.

  SEDA 2025.2 (Educational Opportunity Trends release), purl.stanford.edu/np279jm6134
  Reardon, Fahle, Ho, Shear, Saliba, Min, Shim & Kalogrides (2026).
  Files pulled from https://stacks.stanford.edu/file/np279jm6134/:
    seda_admindist_annual_gcs_2025.2.csv     (333 MB, all states, 2009-2025, grades 3-8 pooled,
                                              all students + race/gender/ECD subgroups)
    seda_admindist_annualsub_gcs_2025.2.csv  (535 MB, same by subject: math / RLA)
    seda_codebook_admindist_2025.2.xlsx, seda_codebook_crosswalk_2025.2.xlsx,
    SEDA_documentation_2025.2.pdf

The two big CSVs are streamed and filtered to stateabb == "CT" on the fly so
only the Connecticut extract (a few MB) is stored under data/seda/. Re-run to
refresh; the full national files are not kept.

GCS scale: a district's mean is expressed in grade levels, where the national
average for grade g equals g; the annual files pool grades 3-8 (gradecenter =
5.5), so (gcs_mn_avg - 5.5) is the district's distance from the national
average in grade-level units. Read by 71_clean_seda_ct.py.

Output:
    data/seda/seda_admindist_annual_gcs_2025.2_CT.csv
    data/seda/seda_admindist_annualsub_gcs_2025.2_CT.csv
    data/seda/seda_codebook_admindist_2025.2.xlsx, seda_codebook_crosswalk_2025.2.xlsx,
    data/seda/SEDA_documentation_2025.2.pdf, _download_log.tsv
"""

import csv
import datetime as dt
import io
import os
import subprocess
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "data", "seda")
os.makedirs(OUT_DIR, exist_ok=True)
STACKS = "https://stacks.stanford.edu/file/np279jm6134/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ct-school-finance research download"
SMALL = ["seda_codebook_admindist_2025.2.xlsx", "seda_codebook_crosswalk_2025.2.xlsx",
         "SEDA_documentation_2025.2.pdf"]
BIG = ["seda_admindist_annual_gcs_2025.2.csv", "seda_admindist_annualsub_gcs_2025.2.csv"]


def curl(url, out):
    r = subprocess.run(["curl.exe", "-sS", "-L", "-A", UA, "-o", out, url],
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())


def stream_filter_ct(url, out):
    """Stream the national CSV and write only Connecticut rows."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    n_in = n_out = 0
    with urllib.request.urlopen(req, timeout=600) as resp, \
            open(out, "w", encoding="utf-8", newline="") as f:
        reader = csv.reader(io.TextIOWrapper(resp, encoding="utf-8", newline=""))
        writer = csv.writer(f)
        header = next(reader)
        writer.writerow(header)
        col = header.index("stateabb")
        for row in reader:
            n_in += 1
            if row[col] == "CT":
                writer.writerow(row)
                n_out += 1
    return n_in, n_out


def main():
    log = []
    for name in SMALL:
        out = os.path.join(OUT_DIR, name)
        curl(STACKS + name, out)
        print(f"  {name}: {os.path.getsize(out):,} bytes")
        log.append(f"{dt.datetime.now():%Y-%m-%d}\t{name}\t{STACKS + name}")
    for name in BIG:
        out = os.path.join(OUT_DIR, name.replace(".csv", "_CT.csv"))
        n_in, n_out = stream_filter_ct(STACKS + name, out)
        print(f"  {name}: streamed {n_in:,} rows, kept {n_out:,} Connecticut rows -> {os.path.basename(out)}")
        log.append(f"{dt.datetime.now():%Y-%m-%d}\t{os.path.basename(out)}\t{STACKS + name}\tCT rows only: {n_out} of {n_in}")
    with open(os.path.join(OUT_DIR, "_download_log.tsv"), "a", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")


if __name__ == "__main__":
    main()
