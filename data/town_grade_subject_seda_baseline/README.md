# Town baseline achievement by grade and subject (SEDA)

- **Series name:** Town baseline achievement by grade and subject (SEDA)
- **Grain:** one row per town x grade x subject
- **Year range:** -
- **Source:** Stanford Education Data Archive 2025.2, administrative-district long GCS file, Connecticut rows, all students; https://purl.stanford.edu/np279jm6134; https://stacks.stanford.edu/file/np279jm6134/seda_admindist_long_gcs_2025.2.csv
- **Row count:** 1,821
- **Column count:** 10

Baseline achievement for each Connecticut town by grade (3-8) and subject on SEDA's grade-cohort-standardized scale, averaged over spring 2023-2025, with the mean number of tests as a weight. Towns are mapped as in `district_year_seda_gcs`: local boards of education by name, and the K-12 regional districts (10, 12-18, 20; region 6 through 2024) to their member towns; 162 of 169 towns have at least one cell (small districts SEDA suppresses have none). This is the starting point and weighting for the test-score simulation in `tools/ecs_formula_explorer`.

## Codebook

| Column | Definition | Type |
|---|---|---|
| `town_code` | Connecticut town code, 1-169 (alphabetical); equals the local board of education's CSDE district code. | integer |
| `town` | Town name. | string |
| `grade` | Tested grade, 3-8. | integer |
| `subject` | Subject: mth (math) or rla (reading/language arts). | string |
| `gcs_baseline` | Mean achievement on SEDA's grade-cohort-standardized (GCS) scale for the town's district, this grade and subject, averaged over spring 2023-2025 (all students). | number |
| `vs_national_baseline` | gcs_baseline minus grade: grade levels above (+) or below (-) the national average for the same grade. | number |
| `n_tests` | Mean number of test scores behind the estimate over the years used (weight for aggregation). | number |
| `years_used` | Number of spring test years (of 2023, 2024, 2025) with an estimate. | integer |
| `town_match` | How the estimate was assigned to a town: local district (town board of education), regional district (K-12 regional district serving the town's grades 3-8), or blank (charter, magnet, RESC, secondary-only region). | string |
| `sedaadmin` | SEDA administrative-district id (NCES LEA id). | integer |

## Provenance and Method

Raw source workbooks are stored in `raw/` with a download log. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. Original script(s): `72_download_seda_long.py + 73_seda_k_and_baselines.py`.

## Data completeness

- Not a town-year panel; completeness section not applicable.
