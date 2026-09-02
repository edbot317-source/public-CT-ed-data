# District-year five-year graduation rates

- **Series name:** District-year five-year graduation rates
- **Grain:** one row per district x fiscal_year x needs_group
- **Year range:** FY2012-FY2023
- **Source:** EdSight Graduation; https://edsight.ct.gov/SASStoredProcess/do?_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/GraduationReport_SiteCore&_rpttype=listing&_gradcat=grad&_rate=5&_year={YYYY-YY}&_district=All+Districts&_subgroup={subgroup}&_school=&_select=Submit
- **Row count:** 4,990
- **Column count:** 6

## Codebook

| Column | Definition | Type |
|---|---|---|
| `district` | District name as reported by EdSight. | string |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2025 corresponds to school year 2024-25. | integer |
| `needs_group` | Subgroup indicator: All Students, High Needs, or Non-High Needs depending on source export. | string |
| `cohort_count` | Graduation cohort count. | number |
| `graduation_count` | Number of students graduating. | number |
| `graduation_rate` | Graduation rate in percent. | number |

## Provenance and Method

Raw scraped files are stored in `raw/`. The build script stacks and tidies the copied per-year raw exports in `raw/`. Original script(s): `54_download_grad5_by_year.py`.
