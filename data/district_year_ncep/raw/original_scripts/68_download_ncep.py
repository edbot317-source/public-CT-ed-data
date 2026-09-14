"""
68_download_ncep.py

Downloads CSDE's annual "Net Current Expenditures (NCE) per Pupil (NCEP)" reports:

  - the CURRENT year from CSDE (Excel + PDF), which CSDE overwrites in place:
      https://portal.ct.gov/-/media/sde/grants-management/report1/basiccon_excel.xls
      https://portal.ct.gov/-/media/sde/grants-management/report1/basiccon_pdf.pdf
  - the ARCHIVE of prior years as republished by the School and State Finance
    Project (one PDF per school year, 2007-08 .. 2024-25; 2014-15 and 2020-21 are
    not in their archive):
      https://schoolstatefinance.org/resources/local-public-school-district-net-current-expenditures-per-pupil-ct-state-department-of-education

NCEP = NCE / ADM. ADM (average daily membership, CGS 10-261(a)(2)) is the resident-
student count -- the same count the ECS formula uses -- so NCEP is total current
spending per resident student on a denominator consistent with ECS dollars per
resident student. Read by 69_clean_ncep.py.

Output:
    data/ncep/csde_basiccon_excel.xls, csde_basiccon_pdf.pdf
    data/ncep/ncep_<YYYY>-<YY>.pdf  (archive)
    data/ncep/_download_log.tsv
"""

import datetime as dt
import os
import re
import subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "data", "ncep")
os.makedirs(OUT_DIR, exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ct-school-finance research download"
ARCHIVE_PAGE = ("https://schoolstatefinance.org/resources/"
                "local-public-school-district-net-current-expenditures-per-pupil-ct-state-department-of-education")
CSDE = {
    "csde_basiccon_excel.xls": "https://portal.ct.gov/-/media/sde/grants-management/report1/basiccon_excel.xls",
    "csde_basiccon_pdf.pdf": "https://portal.ct.gov/-/media/sde/grants-management/report1/basiccon_pdf.pdf",
}


def curl(url, out=None):
    args = ["curl.exe", "-sS", "-L", "-A", UA, url]
    if out:
        args[3:3] = ["-o", out]
    r = subprocess.run(args, capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout


def main():
    log = []
    for name, url in CSDE.items():
        out = os.path.join(OUT_DIR, name)
        curl(url, out)
        print(f"  {name}: {os.path.getsize(out):,} bytes")
        log.append(f"{dt.datetime.now():%Y-%m-%d}\t{name}\t{url}")
    html = curl(ARCHIVE_PAGE)
    links = sorted(set(re.findall(r'href="(https://schoolstatefinance\.org/hubfs/Resources/[^"]*Net%20Current%20Expenditures[^"]*\.pdf)"', html)))
    for url in links:
        m = re.search(r"Resources/(\d{4})[%20-]+(\d{2})%20Net", url)
        if not m:
            print(f"  skip (no year): {url}")
            continue
        name = f"ncep_{m.group(1)}-{m.group(2)}.pdf"
        out = os.path.join(OUT_DIR, name)
        curl(url, out)
        with open(out, "rb") as f:
            ok = f.read(5) == b"%PDF-"
        print(f"  {name}: {os.path.getsize(out):,} bytes{'' if ok else '  NOT A PDF'}")
        log.append(f"{dt.datetime.now():%Y-%m-%d}\t{name}\t{url}")
    with open(os.path.join(OUT_DIR, "_download_log.tsv"), "a", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")
    print(f"done: {len(links)} archive PDFs + CSDE current files")


if __name__ == "__main__":
    main()
