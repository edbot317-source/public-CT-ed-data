"""
Download 2024-25 CT EdSight accountability/growth data.

Outputs raw, reproducible EdSight exports under data/accountability/:
  - Smarter Balanced Growth Model district export
  - Next Generation Accountability all schools/districts export
  - Next Generation Accountability metadata workbook

The stored-process report pages expose these export programs publicly:
  GrowthModelExport
  NGAExport_All
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent
OUT_DIR = BASE / "data" / "accountability"
OUT_DIR.mkdir(parents=True, exist_ok=True)
COOKIE_JAR = OUT_DIR / "_cookies.txt"

MIN_BYTES = 500

DOWNLOADS = [
    (
        "growth_model_2024_25_all_districts.csv",
        "https://edsight.ct.gov/SASStoredProcess/do?"
        "_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/GrowthModelExport"
        "&_year=2024-25&_district=All+Districts&_subgroup=All+Students"
        "&_school=+&_subject=ELA+and+Math&_grade=All+Grades+Combined",
    ),
    (
        "next_generation_accountability_2024_25_all.csv",
        "https://edsight.ct.gov/SASStoredProcess/do?"
        "_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/NGAExport_All"
        "&_year=2024-25",
    ),
    (
        "nextgenmetadata.xlsx",
        "https://edsight.ct.gov/relatedreports/nextgenmetadata.xlsx",
    ),
]


def download(url: str, out_path: Path) -> None:
    result = subprocess.run(
        [
            "curl.exe",
            "-sS",
            "-L",
            "-c",
            str(COOKIE_JAR),
            "-b",
            str(COOKIE_JAR),
            "-o",
            str(out_path),
            url,
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed for {out_path.name}: {result.stderr.strip()}")


def validate_download(path: Path) -> None:
    size = path.stat().st_size
    if size < MIN_BYTES:
        raise RuntimeError(f"{path.name} is too small ({size} bytes)")
    with path.open("rb") as f:
        first = f.read(200).lower()
    if b"<html" in first and path.suffix.lower() != ".html":
        raise RuntimeError(f"{path.name} appears to be HTML, not the expected raw export")


def main() -> None:
    ok = 0
    for filename, url in DOWNLOADS:
        out_path = OUT_DIR / filename
        if out_path.exists() and out_path.stat().st_size > MIN_BYTES:
            print(f"SKIP {filename} ({out_path.stat().st_size:,} bytes)")
            ok += 1
            continue
        print(f"GET  {filename}")
        download(url, out_path)
        validate_download(out_path)
        print(f"OK   {filename} ({out_path.stat().st_size:,} bytes)")
        ok += 1

    if COOKIE_JAR.exists():
        os.remove(COOKIE_JAR)
    print(f"Done: {ok}/{len(DOWNLOADS)} files available")


if __name__ == "__main__":
    main()
