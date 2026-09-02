# Special education expenditures

- **Series name:** Special education expenditures
- **Grain:** one row per district x fiscal_year x expenditure_category
- **Year range:** FY2007-FY2025
- **Source:** EdSight Special Education Expenditures; https://edsight.ct.gov/SASStoredProcess/do?_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/SpecialEducationExport&_year={YYYY-YY}&_district=All+Districts; https://edsight.ct.gov/SASStoredProcess/do?_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/EFSSpecialEducationExpendituresExport&_year={YYYY-YY}&_district=All+Districts
- **Row count:** 38,774
- **Column count:** 9

## Codebook

| Column | Definition | Type |
|---|---|---|
| `district` | District name as reported by EdSight. | string |
| `district_code` | EdSight district code. | integer |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2025 corresponds to school year 2024-25. | integer |
| `expenditure_category` | Special education expenditure line item/category. | string |
| `amount` | Nominal dollar amount. | integer |
| `source_format` | Raw source layout, archived wide export or current long export. | string |
| `cpi_u` | Annual average CPI-U (FRED CPIAUCSL). | number |
| `deflator` | Inflation factor equal to CPI-U in 2025 divided by CPI-U in this year; multiply nominal dollars by this to express them in 2025 dollars. | number |
| `amount_real` | Dollar amount in 2025 dollars using CPI-U deflator. | number |

## Provenance and Method

Raw scraped files are stored in `raw/`. The build script stacks and tidies the copied per-year raw exports in `raw/`. For columns ending in `_real`, nominal dollars are converted to 2025 dollars using the CPI-U deflator from `data/cpi_u_deflator/cpi_u_deflator.csv`: real = nominal x (CPI-U 2025 / CPI-U fiscal/calendar year). Original script(s): `21_download_sped_expenditures.py; parsed for analysis by 22/23/24/26/29/30/33`.
