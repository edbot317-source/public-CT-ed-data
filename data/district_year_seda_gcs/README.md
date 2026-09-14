# District-year achievement in grade levels (SEDA)

- **Series name:** District-year achievement in grade levels (SEDA)
- **Grain:** one row per district x fiscal_year x subgroup
- **Year range:** FY2009-FY2025
- **Source:** Stanford Education Data Archive 2025.2 (Reardon, Fahle, Ho, Shear, Saliba, Min, Shim & Kalogrides, 2026), administrative-district annual and annual-by-subject GCS files, Connecticut rows; https://purl.stanford.edu/np279jm6134; https://stacks.stanford.edu/file/np279jm6134/seda_admindist_annual_gcs_2025.2.csv; https://stacks.stanford.edu/file/np279jm6134/seda_admindist_annualsub_gcs_2025.2.csv
- **Row count:** 18,353
- **Column count:** 22

Connecticut administrative-district average achievement in grades 3-8, spring 2009-2025 (no tests in 2020-2021; 2014 absent), on SEDA's grade-cohort-standardized (GCS) scale, for all students and by economic-disadvantage and race subgroups. grade_levels_vs_national subtracts the grade center (5.5), giving grade levels above or below the national average of the 2009-2015 cohorts for the same grades. Each estimate is assigned to the ECS town it serves: town boards by name, and the 21 towns whose grades 3-8 are run by a K-12 regional district (Regions 10, 12-18, 20; Region 6 through 2024) to that region. Charter, magnet, RESC and secondary-only regional districts are kept without a town. The raw folder holds only the Connecticut rows of the two national files (333 MB and 535 MB at the URLs above).

## Codebook

| Column | Definition | Type |
|---|---|---|
| `sedaadmin` | SEDA administrative-district id (NCES LEA id). | integer |
| `district` | District name as printed in the CSDE report (title case). | string |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2026 corresponds to school year 2025-26. | integer |
| `subcat` | Subgroup category: all, ecd (economic disadvantage) or race. | string |
| `subgroup` | Subgroup: all; ecd / nec (economically disadvantaged / not); asn, blk, hsp, wht, nam, mtr (race/ethnicity). | string |
| `gradecenter` | Grade center of the pooled estimate (5.5 for grades 3-8). | number |
| `tot_asmts` | Number of test scores underlying the estimate. | integer |
| `gcs_mn_avg_eb` | Mean achievement, grades 3-8 pooled over math and RLA, GCS scale, empirical-Bayes estimate. | number |
| `gcs_mn_avg_eb_se` | Standard error of gcs_mn_avg_eb. | number |
| `gcs_mn_avg_ol` | Same mean, ordinary least squares estimate. | number |
| `gcs_mn_avg_ol_se` | Standard error of gcs_mn_avg_ol. | number |
| `grade_levels_vs_national` | gcs_mn_avg_eb minus gradecenter: grade levels above (+) or below (-) the national average of the 2009-2015 cohorts in the same grades. | number |
| `grade_levels_vs_national_ol` | Same, from the OLS estimate. | number |
| `gcs_mn_avg_mth_eb` | Math mean, grades 3-8 pooled, GCS scale, empirical Bayes. | number |
| `gcs_mn_avg_mth_eb_se` | Standard error of the math mean. | number |
| `gcs_mn_avg_rla_eb` | Reading/language-arts mean, grades 3-8 pooled, GCS scale, empirical Bayes. | number |
| `gcs_mn_avg_rla_eb_se` | Standard error of the RLA mean. | number |
| `grade_levels_vs_national_mth` | Math grade levels vs the national average (gcs_mn_avg_mth_eb - gradecenter). | number |
| `grade_levels_vs_national_rla` | RLA grade levels vs the national average (gcs_mn_avg_rla_eb - gradecenter). | number |
| `town_code` | Connecticut town code, 1-169 (alphabetical); equals the local board of education's CSDE district code. | integer |
| `town` | Town name. | string |
| `town_match` | How the estimate was assigned to a town: local district (town board of education), regional district (K-12 regional district serving the town's grades 3-8), or blank (charter, magnet, RESC, secondary-only region). | string |

## Provenance and Method

Raw source workbooks are stored in `raw/` with a download log. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. Original script(s): `70_download_seda.py + 71_clean_seda_ct.py`.

## Data completeness

- **Panel span:** FY2009-FY2025 (2529 district-years across 182 districts).
- **Method:** only *interior* gaps are counted as missing -- years before a district first appears or after it last appears are treated as not reported, not as missing data.
- **Statewide gaps:** no 2014 estimates in this release and no tests were given in 2020-2021 (every district); completeness below is for all-student rows, years 2014, 2020 and 2021 omitted.
- **District-by-district missing years** (2014, 2020 and 2021 are statewide gaps, listed once above and omitted here):
  - Odyssey Community School District: FY2022
  - Side By Side Charter School District: FY2023
  - Trailblazers Academy District: FY2018
  - Andover School District: FY2022, FY2023
  - Barkhamsted School District: FY2017
  - Chaplin School District: FY2015
  - Chester School District: FY2022
  - Colebrook School District: FY2015, FY2016
  - Eastford School District: FY2022
  - Hampton School District: FY2015
  - Madison School District: FY2016
  - Newtown School District: FY2013
  - Sherman School District: FY2015, FY2016, FY2023
