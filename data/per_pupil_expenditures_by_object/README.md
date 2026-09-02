# District-year net current expenditures by object

- **Series name:** District-year net current expenditures by object
- **Grain:** one row per district x fiscal_year x object
- **Year range:** FY2018-FY2025
- **Source:** EdSight Net Current Expenditures by Object; https://edsight.ct.gov/SASStoredProcess/do?_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/EFSDistrictLevelbyObjectExport&_year={YYYY-YY}&_district=All+Districts
- **Row count:** 12,400
- **Column count:** 12

## Codebook

| Column | Definition | Type |
|---|---|---|
| `district` | District name as reported by EdSight. | string |
| `district_code` | EdSight district code. | integer |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2025 corresponds to school year 2024-25. | integer |
| `object` | Expenditure object category. | string |
| `expenditures` | Nominal expenditures in dollars. | integer |
| `pupils` | Pupil denominator reported for the row. | integer |
| `pupil_basis` | EdSight pupil-basis code; object/function reports document the denominator used for PPE. | integer |
| `ppe` | Per-pupil expenditure in nominal dollars. | integer |
| `cpi_u` | Annual average CPI-U (FRED CPIAUCSL). | number |
| `deflator` | Inflation factor equal to CPI-U in 2025 divided by CPI-U in this year; multiply nominal dollars by this to express them in 2025 dollars. | number |
| `expenditures_real` | Expenditures in 2025 dollars using CPI-U deflator. | number |
| `ppe_real` | Per-pupil expenditure in 2025 dollars using CPI-U deflator. | number |

## Provenance and Method

Raw scraped files are stored in `raw/`. The build script stacks and tidies the copied per-year raw exports in `raw/`. For columns ending in `_real`, nominal dollars are converted to 2025 dollars using the CPI-U deflator from `data/cpi_u_deflator/cpi_u_deflator.csv`: real = nominal x (CPI-U 2025 / CPI-U fiscal/calendar year). Original script(s): `47_download_ppe_by_object_district.py; tuition parsing in 03_part1_figures.py`.
