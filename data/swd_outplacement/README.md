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

## Data completeness

- **Panel span:** FY2018-FY2025 (1312 district-years across 171 districts).
- **Method:** only *interior* gaps are counted as missing -- years before a district first appears or after it last appears are treated as the district not operating/reporting, not as missing data.
- **Grain note:** this series is disaggregated by placement type; a district-year is "present" if at least one cell exists. Individual sub-cells may still be suppressed by CSDE for small counts even when the district-year is present.

- **Districts with missing interior years (11):**

  - Andover School District: FY2019
  - Canaan School District: FY2021
  - Chaplin School District: FY2023
  - Connecticut Technical Education and Career System: FY2019, FY2020, FY2021, FY2022, FY2024
  - Easton School District: FY2024
  - Hebron School District: FY2022
  - Kent School District: FY2020, FY2021, FY2022, FY2024
  - Norfolk School District: FY2021, FY2022, FY2023
  - Salisbury School District: FY2022, FY2023
  - Sharon School District: FY2022, FY2023
  - Union School District: FY2019
