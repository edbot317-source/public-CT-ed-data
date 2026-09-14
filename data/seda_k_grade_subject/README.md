# Grade levels per standard deviation, by grade and subject (SEDA)

- **Series name:** Grade levels per standard deviation, by grade and subject (SEDA)
- **Grain:** one row per grade x subject
- **Year range:** -
- **Source:** Stanford Education Data Archive 2025.2 technical documentation, Table 9 (national NAEP means and SDs by year and grade) and Step 7 scale definitions; regression cross-check from the SEDA admin-district long GCS and CS files; https://purl.stanford.edu/np279jm6134 (SEDA_documentation_2025.2.pdf, p. 83; seda_admindist_long_gcs_2025.2.csv; seda_admindist_long_cs_2025.2.csv)
- **Row count:** 12
- **Column count:** 11

Conversion factor from student-level standard deviations (SEDA's cohort-standardized CS scale) to grade levels (SEDA's grade-cohort-standardized GCS scale) for each grade 3-8 and subject, computed exactly as SEDA defines the two scales: k = national NAEP SD for the grade and subject divided by the subject's per-grade NAEP growth, using the Table 9 parameters averaged over the four reference cohorts (in 4th grade in 2009, 2011, 2013 and 2015). Values run from 2.70 (grade 3 math) to 3.71 (grade 8 math); SEDA's own rule of thumb is about 3 grade levels per SD. The regression columns are a cross-check (slope of GCS on CS across all U.S. administrative districts within grade, subject and year, averaged over years) and agree with the documented ratio to within 0.009 everywhere. The two national long files behind the cross-check are about 119 MB each and are not redistributed here; `raw/k_gcs_on_cs_by_year.csv` holds the per-year slopes so the build reproduces the panel without them. Used by the test-score simulation in `tools/ecs_formula_explorer` to translate spending effects estimated in SD units (Jackson & Mackevicius 2024) into grade levels.

## Codebook

| Column | Definition | Type |
|---|---|---|
| `subject` | Subject: mth (math) or rla (reading/language arts). | string |
| `grade` | Tested grade, 3-8. | integer |
| `k` | Grade levels per student-level standard deviation for this grade and subject: national NAEP SD (naep_sd_ref) divided by per-grade NAEP growth (naep_growth_per_grade), from SEDA 2025.2 documentation Table 9 and equations 7.2-7.4. | number |
| `naep_mean_ref` | National NAEP mean for the grade and subject, averaged over the four SEDA reference cohorts (in 4th grade in 2009, 2011, 2013, 2015), NAEP scale points. | number |
| `naep_sd_ref` | National NAEP student-level standard deviation for the grade and subject, averaged over the four reference cohorts, NAEP scale points. | number |
| `naep_growth_per_grade` | Per-grade NAEP growth for the subject: (grade 8 mean - grade 4 mean) / 4 averaged over the four reference cohorts, NAEP scale points. | number |
| `k_regression` | Cross-check: slope of SEDA's GCS on CS district means across all U.S. administrative districts within grade x subject x year, averaged over years. | number |
| `k_regression_min` | Minimum of the yearly regression slopes. | number |
| `k_regression_max` | Maximum of the yearly regression slopes. | number |
| `regression_years` | Number of test years in the regression cross-check. | integer |
| `flag` | True if k and k_regression differ by more than 0.05 grade levels per SD (none do). | boolean |

## Provenance and Method

Raw source workbooks are stored in `raw/` with a download log. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. Original script(s): `72_download_seda_long.py + 73_seda_k_and_baselines.py`.

## Data completeness

- Not a town-year panel; completeness section not applicable.
