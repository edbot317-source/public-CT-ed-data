# District-year Connecticut School Day SAT outcomes

- **Series name:** District-year Connecticut School Day SAT outcomes
- **Grain:** one row per district x fiscal_year x subject x needs_group
- **Year range:** FY2016-FY2025
- **Source:** EdSight CT School Day SAT; https://edsight.ct.gov/SASStoredProcess/do?_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/CTSchoolDaySATReport_SiteCore&_rpttype=listing&_year={YYYY-YY}&_district=All+Districts&_subject={ELA|Math}&_subgroup={subgroup}&_school=&_select=Submit
- **Row count:** 7,004
- **Column count:** 10

## Codebook

| Column | Definition | Type |
|---|---|---|
| `district` | District name as reported by EdSight. | string |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2025 corresponds to school year 2024-25. | integer |
| `subject` | Test subject. | string |
| `needs_group` | Subgroup indicator: All Students, High Needs, or Non-High Needs depending on source export. | string |
| `total_students` | Total students in the assessment denominator. | number |
| `total_tested` | Total students tested. | number |
| `participation_rate` | Assessment participation rate in percent. | number |
| `n_scored` | Number of scored tests. | number |
| `pct_prof` | Percent meeting or exceeding proficiency benchmark. | number |
| `avg_score` | Average scale score. | number |

## Provenance and Method

Raw scraped files are stored in `raw/`. The build script stacks and tidies the copied per-year raw exports in `raw/`. Original script(s): `51_download_sat_by_year.py`.
