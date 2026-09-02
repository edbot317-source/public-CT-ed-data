# Students with disabilities attending out-of-district schools/programs

- **Series name:** Students with disabilities attending out-of-district schools/programs
- **Grain:** one row per district x fiscal_year x placement_type
- **Year range:** FY2018-FY2025
- **Source:** EdSight Students with Disabilities Out-of-District; https://public-edsight.ct.gov/students/primary-disability/out-of-district; https://edsight-v.ct.gov/SWDOutOfDistrictReport.html
- **Row count:** 2,624
- **Column count:** 6

## Codebook

| Column | Definition | Type |
|---|---|---|
| `district` | District name as reported by EdSight. | string |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2025 corresponds to school year 2024-25. | integer |
| `school_year` | School year label from source export. | string |
| `placement_type` | Out-of-district placement category. | string |
| `count` | Student count in placement category. | number |
| `percent` | Percent in placement category. | number |

## Provenance and Method

Raw scraped files are stored in `raw/`. The build script stacks and tidies the copied per-year raw exports in `raw/`. Original script(s): `27_download_swd_outplacement.py`.
