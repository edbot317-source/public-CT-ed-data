# School-year per-pupil expenditures by funding source

- **Series name:** School-year per-pupil expenditures by funding source
- **Grain:** one row per school x fiscal_year
- **Year range:** FY2018-FY2025
- **Source:** EdSight Per Pupil Expenditures by Funding Source (Summary); https://edsight.ct.gov/SASStoredProcess/do?_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/EFSSchoolLevelbyFundingSourceExport&_year={YYYY-YY}&_district=All+Districts&_school=All+Schools
- **Row count:** 7,955
- **Column count:** 14

## Codebook

| Column | Definition | Type |
|---|---|---|
| `district` | District name as reported by EdSight. | string |
| `district_code` | EdSight district code. | integer |
| `school` | School name as reported by EdSight. | string |
| `school_code` | EdSight school code. | integer |
| `ppe_federal` | Per-pupil expenditure in nominal dollars for federal. | integer |
| `ppe_state_local_other` | Per-pupil expenditure in nominal dollars for state local other. | integer |
| `ppe_total_source` | Per-pupil expenditure in nominal dollars for total source. | integer |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2025 corresponds to school year 2024-25. | integer |
| `cpi_u` | Annual average CPI-U (FRED CPIAUCSL). | number |
| `deflator` | Inflation factor equal to CPI-U in 2025 divided by CPI-U in this year; multiply nominal dollars by this to express them in 2025 dollars. | number |
| `ppe_federal_real` | Per-pupil expenditure in 2025 dollars for federal. | number |
| `ppe_state_local_other_real` | Per-pupil expenditure in 2025 dollars for state local other. | number |
| `ppe_total_source_real` | Per-pupil expenditure in 2025 dollars for total source. | number |
| `enrollment` | Enrollment count. | number |

## Provenance and Method

Raw scraped files are stored in `raw/`. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. For columns ending in `_real`, nominal dollars are converted to 2025 dollars using the CPI-U deflator from `data/cpi_u_deflator/cpi_u_deflator.csv`: real = nominal x (CPI-U 2025 / CPI-U fiscal/calendar year). Original script(s): `41_download_funding_source_school.py + 42_clean_funding_source_school.py`.
