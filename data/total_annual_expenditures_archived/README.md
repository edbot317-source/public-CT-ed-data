# Archived district-year total annual expenditures by type

- **Series name:** Archived district-year total annual expenditures by type
- **Grain:** one row per district x fiscal_year
- **Year range:** FY2006-FY2017
- **Source:** EdSight Total Annual Expenditures by Type (archived); https://public-edsight.ct.gov/ada-archived/total-annual-expenditures-by-type-2016-17-and-earlier; https://edsight.ct.gov/SASStoredProcess/do?_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/FinanceReport_SiteCore&_rpttype=listing&_year={YYYY-YY}&_district=All+Districts&_select=Submit
- **Row count:** 2,209
- **Column count:** 12

## Codebook

| Column | Definition | Type |
|---|---|---|
| `District` | District name as reported by EdSight. | string |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2025 corresponds to school year 2024-25. | integer |
| `exp_instructional_staff` | Nominal expenditures in dollars for instructional staff. | number |
| `exp_instructional_supplies` | Nominal expenditures in dollars for instructional supplies. | number |
| `exp_instruction_media` | Nominal expenditures in dollars for instruction media. | number |
| `exp_student_support` | Nominal expenditures in dollars for student support. | number |
| `exp_admin_support` | Nominal expenditures in dollars for admin support. | number |
| `exp_plant` | Nominal expenditures in dollars for plant. | number |
| `exp_transportation` | Nominal expenditures in dollars for transportation. | number |
| `exp_tuitioned_out` | Nominal expenditures in dollars for tuitioned out. | number |
| `exp_other` | Nominal expenditures in dollars for other. | number |
| `total_expenditures` | Total expenditures. | number |

## Provenance and Method

Raw scraped files are stored in `raw/`. The build script stacks and tidies the copied per-year raw exports in `raw/`. Original script(s): `43_download_archived_total_expenditures.py + 44_compare_archived_denominators.py`.

## Data completeness

- **Panel span:** FY2006-FY2017 (2209 district-years across 194 districts).
- **Method:** only *interior* gaps are counted as missing -- years before a district first appears or after it last appears are treated as the district not operating/reporting, not as missing data.

- **Districts with missing interior years (3):**

  - Hartford School District: FY2015, FY2016
  - New Beginnings Inc Family Academy District: FY2015
  - Winchester School District: FY2014, FY2015
