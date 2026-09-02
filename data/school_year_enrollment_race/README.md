# School-year enrollment by race

- **Series name:** School-year enrollment by race
- **Grain:** one row per school x fiscal_year
- **Year range:** FY2008-FY2026
- **Source:** EdSight Enrollment; https://edsight.ct.gov/SASStoredProcess/do?_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/EnrollmentYearExport&_year={YYYY-YY}&_district=All+Districts&_school=All+Schools&display=1&_subgroup=Race
- **Row count:** 25,055
- **Column count:** 23

## Codebook

| Column | Definition | Type |
|---|---|---|
| `district` | District name as reported by EdSight. | string |
| `district_code` | EdSight district code. | integer |
| `school` | School name as reported by EdSight. | string |
| `school_code` | EdSight school code. | integer |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2025 corresponds to school year 2024-25. | integer |
| `enrollment_total` | Enrollment count. | number |
| `n_native_american` | Student count: native american. | number |
| `n_asian` | Student count: asian. | number |
| `n_black` | Student count: black. | number |
| `n_hispanic` | Student count: hispanic. | number |
| `n_two_or_more` | Student count: two or more. | number |
| `n_white` | Student count: white. | number |
| `n_pacific_islander` | Student count: pacific islander. | number |
| `n_black_hispanic` | Student count: black hispanic. | number |
| `pct_white` | Percent/share measure: white. | number |
| `pct_black` | Percent/share measure: black. | number |
| `pct_hispanic` | Percent/share measure: hispanic. | number |
| `pct_asian` | Percent/share measure: asian. | number |
| `pct_native_american` | Percent/share measure: native american. | number |
| `pct_two_or_more` | Percent/share measure: two or more. | number |
| `pct_pacific_islander` | Percent/share measure: pacific islander. | number |
| `pct_black_hispanic` | Percent/share measure: black hispanic. | number |
| `pct_nonwhite` | Percent/share measure: nonwhite. | number |

## Provenance and Method

Raw scraped files are stored in `raw/`. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. Original script(s): `16_download_school_enrollment_race.py + 17_clean_school_enrollment_race.py`.
