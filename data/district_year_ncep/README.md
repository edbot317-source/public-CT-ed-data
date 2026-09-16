# District-year net current expenditures per pupil

- **Series name:** District-year net current expenditures per pupil
- **Grain:** one row per district x fiscal_year
- **Year range:** FY2008-FY2025
- **Source:** CSDE Bureau of Fiscal Services annual NCEP / Excess Cost basic-contribution reports (current year from CSDE; prior years as archived by the School and State Finance Project); https://portal.ct.gov/-/media/sde/grants-management/report1/basiccon_excel.xls; https://schoolstatefinance.org/resources/local-public-school-district-net-current-expenditures-per-pupil-ct-state-department-of-education
- **Row count:** 2,675
- **Column count:** 7

Net current expenditures (NCE), average daily membership (ADM) and NCE per pupil (NCEP) for every town board of education and regional school district, FY2008-FY2025, as computed by CSDE for the Special Education Excess Cost grant. ADM is the resident-student count used by the ECS formula, so NCEP is total current spending on a denominator consistent with ECS dollars per resident student. FY2015 and FY2021 are absent from the archive; regional districts appear from FY2016; the latest year comes from CSDE's own workbook (revised in place) and earlier years from archived PDFs. district_code 1-169 are towns (= ECS town_code); 201-220 are regional school districts.

## Codebook

| Column | Definition | Type |
|---|---|---|
| `district_code` | CSDE district code: 1-169 town boards of education (equal to the ECS town_code), 201-220 regional school districts. | integer |
| `district` | District name as printed in the CSDE report (title case). | string |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2026 corresponds to school year 2025-26. | integer |
| `adm` | Average daily membership (CGS 10-261(a)(2)): resident students educated in and out of district, adjusted for sessions over 180 days, free summer school and Open Choice; the October count of the spending year. | number |
| `nce` | Net current expenditures, nominal dollars: all-source current spending net of tuition revenue, capital outlay, debt service and reimbursable regular-education transportation (CGS 10-261(a)(3)). | number |
| `ncep` | Net current expenditures per pupil = nce / adm, nominal dollars. | number |
| `source` | File the row was parsed from (CSDE current-year workbook, or an archived annual PDF). | string |

## Provenance and Method

Raw source workbooks are stored in `raw/` with a download log. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. Original script(s): `68_download_ncep.py + 69_clean_ncep.py`.

## Data completeness

- **Panel span:** FY2008-FY2025 (2675 district-years across 187 districts).
- **Method:** only *interior* gaps are counted as missing -- years before a district first appears or after it last appears are treated as not reported, not as missing data.
- **Statewide gaps:** FY2015 and FY2021 reports are not in the archive (every district); regional districts are listed only from FY2016.
- **District-by-district missing years:** none beyond the statewide gaps listed above.
