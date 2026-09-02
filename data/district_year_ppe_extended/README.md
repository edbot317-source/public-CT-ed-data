# Extended district-year total per-pupil expenditures

- **Series name:** Extended district-year total per-pupil expenditures
- **Grain:** one row per district x fiscal_year
- **Year range:** FY2007-FY2025
- **Source:** EdSight archived Per Pupil Expenditures and current Net Current Expenditures by Function; https://edsight.ct.gov/SASStoredProcess/do?_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/PerPupilExport&_year={YYYY-YY}&_district=All+Districts; https://edsight.ct.gov/SASStoredProcess/do?_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/EFSDistrictLevelbyFunctionExport&_year={YYYY-YY}&_district=All+Districts
- **Row count:** 3,590
- **Column count:** 7

## Codebook

| Column | Definition | Type |
|---|---|---|
| `District` | District name as reported by EdSight. | string |
| `District Code` | EdSight district code. | number |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2025 corresponds to school year 2024-25. | integer |
| `ppe_total` | Per-pupil expenditure in nominal dollars for total. | number |
| `cpi_u` | Annual average CPI-U (FRED CPIAUCSL). | number |
| `deflator` | Inflation factor equal to CPI-U in 2025 divided by CPI-U in this year; multiply nominal dollars by this to express them in 2025 dollars. | number |
| `ppe_total_real` | Per-pupil expenditure in 2025 dollars for total. | number |

## Provenance and Method

Raw scraped files are stored in `raw/`. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. For columns ending in `_real`, nominal dollars are converted to 2025 dollars using the CPI-U deflator from `data/cpi_u_deflator/cpi_u_deflator.csv`: real = nominal x (CPI-U 2025 / CPI-U fiscal/calendar year). Original script(s): `09_download_archived_ppe.py + 10_clean_archived_ppe.py + 45_download_ppe_by_function_district.py + 01_clean_district.py`.
