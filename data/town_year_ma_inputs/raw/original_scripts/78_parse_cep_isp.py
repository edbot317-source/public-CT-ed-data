"""
78_parse_cep_isp.py

Parses CSDE's Community Eligibility Provision (CEP) annual notification of LEAs, which lists each
district's proxy districtwide Identified Student Percentage (ISP): students directly certified through
SNAP, Temporary Family Assistance, Medicaid, foster care, homeless or migrant status, as a share of
enrollment. This is the Connecticut count closest to Massachusetts' low-income definition (administrative
matches at 185% of poverty, no meal applications), used as the "direct certification" low-income basis
of the Chapter 70 simulation.

Source PDFs (portal.ct.gov/SDE/Nutrition/Community-Eligibility-Provision): districtwide data for school
years 2023-24, 2024-25 and 2025-26 (data/ma/cep/cep_lea_{sy}.pdf, downloaded 2026-09-16).

Output: data/ma/cep_isp_by_lea.csv  (school_year, fiscal_year, lea_id, lea_name, isp)
LEA IDs are CSDE's 5-digit codes: the first three digits are the town code (001-169) or 2xx for
regional school districts.
"""
import csv
import os
import re

from pypdf import PdfReader

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CEP = os.path.join(BASE, "data", "ma", "cep")
FILES = {"2023-24": 2024, "2024-25": 2025, "2025-26": 2026}


def main():
    rows = []
    for sy, fy in FILES.items():
        path = os.path.join(CEP, f"cep_lea_{sy}.pdf")
        if not os.path.exists(path):
            print("  missing", path)
            continue
        text = "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
        text = re.sub(r"\s+", " ", text)
        n = 0
        for m in re.finditer(r"(\d{5}) ((?:(?!\d{5} ).){3,80}?) (\d{1,3}\.\d{2})%", text):
            lea, name, isp = m.group(1), m.group(2).strip(), float(m.group(3))
            rows.append({"school_year": sy, "fiscal_year": fy, "lea_id": lea, "lea_name": name, "isp": isp / 100})
            n += 1
        print(f"  {sy}: {n} LEAs parsed")
    out = os.path.join(BASE, "data", "ma", "cep_isp_by_lea.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["school_year", "fiscal_year", "lea_id", "lea_name", "isp"])
        w.writeheader(); w.writerows(rows)
    print(f"[write] {out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
