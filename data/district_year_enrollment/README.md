# District-year enrollment and demographics

- **Series name:** District-year enrollment and demographics
- **Grain:** one row per district x fiscal_year
- **Year range:** FY2008-FY2026
- **Source:** EdSight Enrollment; https://edsight.ct.gov/SASStoredProcess/do?_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/EnrollmentYearExport&_year={YYYY-YY}&_district=All+Districts&_school=+&display=1&_subgroup={subgroup}
- **Row count:** 3,772
- **Column count:** 30

## Codebook

| Column | Definition | Type |
|---|---|---|
| `District` | District name as reported by EdSight. | string |
| `District Code` | EdSight district code. | integer |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2025 corresponds to school year 2024-25. | integer |
| `enrollment_total` | Enrollment count. | number |
| `n_black` | Student count: black. | number |
| `n_hispanic` | Student count: hispanic. | number |
| `n_white` | Student count: white. | number |
| `n_native_american` | Student count: native american. | number |
| `n_asian` | Student count: asian. | number |
| `n_two_or_more` | Student count: two or more. | number |
| `n_pacific_islander` | Student count: pacific islander. | number |
| `n_ell` | Student count: ell. | number |
| `n_free_lunch` | Student count: free lunch. | number |
| `n_reduced_lunch` | Student count: reduced lunch. | number |
| `n_sped` | Student count: sped. | number |
| `n_frpl` | Student count: frpl. | number |
| `n_black_hispanic` | Student count: black hispanic. | number |
| `pct_white` | Percent/share measure: white. | number |
| `pct_black` | Percent/share measure: black. | number |
| `pct_hispanic` | Percent/share measure: hispanic. | number |
| `pct_asian` | Percent/share measure: asian. | number |
| `pct_native_american` | Percent/share measure: native american. | number |
| `pct_two_or_more` | Percent/share measure: two or more. | number |
| `pct_pacific_islander` | Percent/share measure: pacific islander. | number |
| `pct_black_hispanic` | Percent/share measure: black hispanic. | number |
| `pct_ell` | Percent/share measure: ell. | number |
| `pct_free_lunch` | Percent/share measure: free lunch. | number |
| `pct_frpl` | Percent/share measure: frpl. | number |
| `pct_sped` | Percent/share measure: sped. | number |
| `pct_nonwhite` | Percent/share measure: nonwhite. | number |

## Provenance and Method

Raw scraped files are stored in `raw/`. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. Original script(s): `06_download_enrollment.py + 07_clean_enrollment.py`.
