"""
50_download_cpi_fred.py

Downloads the CPI-U annual-average series (FRED series CPIAUCSL, annual
frequency, average aggregation) used to deflate spending to constant dollars
throughout the pipeline (read by 01, 02, 10, 25, 30, 31, 42, ...).

The FRED graph CSV endpoint returns exactly the two-column format the clean
scripts expect: observation_date,CPIAUCSL (one row per calendar year, dated
YYYY-01-01).

Two robustness details:
  - FRED's annual-frequency export includes the CURRENT (incomplete) calendar
    year with an EMPTY value (e.g. "2026-01-01,"). An annual average for an
    incomplete year is meaningless, so rows with an empty value are dropped.
    This also reproduces the committed data/ file exactly (2006..last complete
    year), verified 2026-08-18.
  - Fetch uses curl.exe first (reliable here, as with the EdSight downloaders)
    and falls back to urllib if curl is unavailable, so it still works on a
    machine without curl.

Source URL:
    https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL&fq=Annual&fam=avg&cosd=2006-01-01

Output:
    data/cpi-u-annual-avg-fred.csv
"""

import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(BASE, "data", "cpi-u-annual-avg-fred.csv")

URL = (
    "https://fred.stlouisfed.org/graph/fredgraph.csv"
    "?id=CPIAUCSL&fq=Annual&fam=avg&cosd=2006-01-01"
)


def fetch(url, attempts=4, timeout=60):
    """Fetch via curl.exe if present (reliable here), else urllib. Retries."""
    last_err = None
    use_curl = shutil.which("curl.exe") or shutil.which("curl")
    for i in range(1, attempts + 1):
        try:
            if use_curl:
                res = subprocess.run(
                    [os.path.basename(use_curl), "-sS", "-L",
                     "--max-time", str(timeout), url],
                    capture_output=True, text=True, timeout=timeout + 10,
                )
                if res.returncode != 0:
                    raise OSError(res.stderr.strip() or f"curl exit {res.returncode}")
                return res.stdout
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8")
        except (subprocess.SubprocessError, urllib.error.URLError,
                TimeoutError, OSError) as e:
            last_err = e
            print(f"  attempt {i}/{attempts} failed ({e}); retrying...")
            time.sleep(2 * i)
    raise SystemExit(f"FRED download failed after {attempts} attempts: {last_err}")


def main():
    raw = fetch(URL)

    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    header = lines[0].replace('"', "")
    if not header.lower().startswith("observation_date"):
        raise SystemExit(f"Unexpected FRED header: {header!r}")
    if "CPIAUCSL" not in header:
        raise SystemExit(f"CPIAUCSL column missing in header: {header!r}")

    # Keep only complete years: FRED emits the current incomplete year with an
    # empty value (e.g. "2026-01-01,"); drop any row without a numeric value.
    kept = [header]
    dropped = 0
    for row in lines[1:]:
        parts = row.split(",")
        if len(parts) < 2 or parts[1].strip() == "":
            dropped += 1
            continue
        kept.append(row)

    data_rows = kept[1:]
    if len(data_rows) < 15:
        raise SystemExit(f"Too few complete CPI rows returned ({len(data_rows)})")

    with open(OUT_PATH, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(kept) + "\n")

    print(f"OK: wrote {len(data_rows)} annual CPI rows "
          f"(dropped {dropped} incomplete-year row(s)) -> {OUT_PATH}")
    print(f"  first: {data_rows[0]}   last: {data_rows[-1]}")


if __name__ == "__main__":
    main()
