# District-year Smarter Balanced assessment outcomes

- **Series name:** District-year Smarter Balanced assessment outcomes
- **Grain:** one row per district x fiscal_year x subject x needs_group
- **Year range:** FY2015-FY2025
- **Source:** EdSight Smarter Balanced Assessments; https://edsight.ct.gov/SASStoredProcess/do?_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/SmarterBalancedAssessmentExport&_year={YYYY-YY}&_district=All+Districts&_school=+&_grade=All+Grades&_subgroup={subgroup}
- **Row count:** 10,284
- **Column count:** 19

## Codebook

| Column | Definition | Type |
|---|---|---|
| `district` | District name as reported by EdSight. | string |
| `district_code` | EdSight district code. | integer |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2025 corresponds to school year 2024-25. | integer |
| `subject` | Test subject. | string |
| `needs_group` | Subgroup indicator: All Students, High Needs, or Non-High Needs depending on source export. | string |
| `total_students` | Total students in the assessment denominator. | number |
| `total_tested` | Total students tested. | number |
| `participation_rate` | Assessment participation rate in percent. | number |
| `n_scored` | Number of scored tests. | number |
| `level1_count` | Count for level1. | number |
| `level1_pct` | Percent for level1. | number |
| `level2_count` | Count for level2. | number |
| `level2_pct` | Percent for level2. | number |
| `level3_count` | Count for level3. | number |
| `level3_pct` | Percent for level3. | number |
| `level4_count` | Count for level4. | number |
| `level4_pct` | Percent for level4. | number |
| `level3_4_count` | Count for level3 4. | number |
| `pct_prof` | Percent meeting or exceeding proficiency benchmark. | number |

## Provenance and Method

Raw scraped files are stored in `raw/`. The build script stacks and tidies the copied per-year raw exports in `raw/`. Original script(s): `49_download_sbac_all_students.py + 15_download_sbac_high_needs.py + 14_sbac_high_needs_trends.py`.

## Data completeness

- **Panel span:** FY2015-FY2025 (1726 district-years across 203 districts).
- **Method:** only *interior* gaps are counted as missing -- years before a district first appears or after it last appears are treated as the district not operating/reporting, not as missing data.
- **Grain note:** this series is disaggregated by subject x needs group; a district-year is "present" if at least one cell exists. Individual sub-cells may still be suppressed by CSDE for small counts even when the district-year is present.
- **Statewide structural gap (all districts):** **FY2020** -- COVID-19: Smarter Balanced not administered; **FY2021** -- COVID-19: Smarter Balanced not administered. These years are excluded from the per-district lists below.

- **District-by-district missing years:** none. Every district is complete across its active span (after excluding the statewide gap years above).
