"""
61_download_ecs_ssfp.py

Downloads the two School and State Finance Project (SSFP) workbooks that carry
per-town ECS FORMULA INPUTS. CSDE does not post its per-town calculation
worksheet; SSFP republishes the legislature's Office of Fiscal Analysis (OFA)
ECS "shells", which are the same 30-something-column worksheet CSDE uses
(compare CSDE's Feb-2025 CASBO deck, which shows the layout with sample towns).

  ecs_component_tool.xlsx   "ECS Formula Component Comparison Tool and Data Trend Model"
      - sheet backend_data : 169 towns x FY2018..FY2027 core inputs (resident students,
                             FRPL, ELL, ENGL per capita, MHI, PIC, base aid ratio, fully funded)
      - sheets FY 23..FY 27: full shells (one row per town, ~75-90 columns)
  fy27_town_ecs_model.xlsm  "FY 2027 Town ECS Model" (Dropbox link on the SSFP page)
      - sheets FY 21 OFA Shell, FY 22 OFA Shell, FY 23 OFA Shell, FY 24 Adopted,
        FY 26 CL, FY 27, PIC Index FY 20/21/23/26, Clean Data (FY 2020)

Source pages (the Dropbox link for the .xlsm is rotated when SSFP updates the model;
if it 404s, re-scrape the link from the report page):
    https://schoolstatefinance.org/reports/education-cost-sharing-ecs-formula-component-and-data-trend-tools
    https://schoolstatefinance.org/reports/interactive-model-of-ecs-formula

Each download is logged with its SHA-256 and date so later refreshes can be
compared. Read by 65_parse_ecs_shells.py.

Output:
    data/ecs/ssfp/<file>
"""

import datetime as dt
import hashlib
import os
import re
import subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "data", "ecs", "ssfp")
os.makedirs(OUT_DIR, exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ct-school-finance research download"

TOOL_URL = ("https://schoolstatefinance.org/hubfs/Reports/"
            "ECS%20Formula%20Component%20Comparison%20Tool%20and%20Data%20Trend%20Model.xlsx")
MODEL_PAGE = "https://schoolstatefinance.org/reports/interactive-model-of-ecs-formula"


def curl(url, out=None):
    args = ["curl.exe", "-sS", "-L", "-A", UA, url]
    if out:
        args[3:3] = ["-o", out]
    r = subprocess.run(args, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_xlsx(path):
    with open(path, "rb") as f:
        magic = f.read(2)
    size = os.path.getsize(path)
    if magic != b"PK" or size < 100_000:
        raise RuntimeError(f"{os.path.basename(path)} is not a workbook (size={size})")
    return size


def model_link():
    """Scrape the current Dropbox link for the .xlsm from the SSFP report page."""
    html = curl(MODEL_PAGE)
    m = re.search(r'href="(https://www\.dropbox\.com/[^"]+\.xlsm[^"]*)"', html)
    if not m:
        raise RuntimeError("could not find the .xlsm Dropbox link on the SSFP model page")
    url = m.group(1).replace("&amp;", "&")
    url = re.sub(r"dl=0", "dl=1", url)          # force direct download
    return url


def main():
    log = []
    for name, url in [("ecs_component_tool.xlsx", TOOL_URL),
                      ("fy27_town_ecs_model.xlsm", model_link())]:
        out = os.path.join(OUT_DIR, name)
        curl(url, out)
        size = check_xlsx(out)
        digest = sha256(out)
        print(f"  {name}: OK (size={size:,}) sha256={digest[:16]}...")
        log.append(f"{dt.datetime.now():%Y-%m-%d %H:%M}\t{name}\t{size}\t{digest}\t{url}")
    with open(os.path.join(OUT_DIR, "_download_log.tsv"), "a", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")


if __name__ == "__main__":
    main()
