# Public Connecticut Education Data Release

This repository releases a self-contained set of Connecticut education finance, enrollment, accountability, assessment, graduation, special education, Education Cost Sharing (ECS) grant, and CPI deflator datasets assembled for public reuse. The data are statewide Connecticut district-level data, with coverage used in a Hartford-region education finance analysis; topline sources are CT EdSight (`edsight.ct.gov` and `public-edsight.ct.gov`), FRED from the Federal Reserve Bank of St. Louis, the CSDE Bureau of Fiscal Services (ECS entitlements), the official Office of Fiscal Analysis / CSDE per-town ECS calculation worksheets (ECS formula inputs, FY2019-FY2027, received from the state), and the School and State Finance Project's republication of those worksheets (FY2022 and cross-checks).

## Datasets

| Dataset key | Series name | Grain | Year range | Rows |
|---|---|---|---:|---:|
| `district_year_enrollment` | District-year enrollment and demographics | district x fiscal_year | FY2008-FY2026 | 3,772 |
| `district_year_spending` | District-year net current expenditures by function | district x fiscal_year | FY2018-FY2025 | 1,561 |
| `district_year_ppe_archived` | Archived district-year per-pupil expenditures by function | district x fiscal_year | FY2007-FY2017 | 2,029 |
| `district_year_ppe_extended` | Extended district-year total per-pupil expenditures | district x fiscal_year | FY2007-FY2025 | 3,590 |
| `district_year_revenue` | District-year revenue sources | district x fiscal_year | FY2018-FY2025 | 1,561 |
| `district_year_accountability` | District-year accountability and growth metrics | district x fiscal_year | FY2025 | 199 |
| `special_education_expenditures` | Special education expenditures | district x fiscal_year x expenditure_category | FY2007-FY2025 | 38,774 |
| `per_pupil_expenditures_by_object` | District-year net current expenditures by object | district x fiscal_year x object | FY2018-FY2025 | 12,400 |
| `total_annual_expenditures_archived` | Archived district-year total annual expenditures by type | district x fiscal_year | FY2006-FY2017 | 2,209 |
| `sbac` | District-year Smarter Balanced assessment outcomes | district x fiscal_year x subject x needs_group | FY2015-FY2025 | 10,284 |
| `sat` | District-year Connecticut School Day SAT outcomes | district x fiscal_year x subject x needs_group | FY2016-FY2025 | 7,004 |
| `graduation_4yr` | District-year four-year graduation rates | district x fiscal_year x needs_group | FY2012-FY2025 | 5,839 |
| `graduation_5yr` | District-year five-year graduation rates | district x fiscal_year x needs_group | FY2012-FY2023 | 4,990 |
| `swd_outplacement` | Students with disabilities attending out-of-district schools/programs | district x fiscal_year x placement_type | FY2018-FY2025 | 2,624 |
| `cpi_u_deflator` | CPI-U annual average deflator | calendar year | 2006-2025 | 20 |
| `seda_k_grade_subject` | Grade levels per standard deviation, by grade and subject (SEDA) | grade x subject | - | 12 |
| `town_grade_subject_seda_baseline` | Town baseline achievement by grade and subject (SEDA) | town x grade x subject | - | 1,821 |
| `district_year_seda_gcs` | District-year achievement in grade levels (SEDA) | district x fiscal_year x subgroup | FY2009-FY2025 | 18,353 |
| `district_year_ncep` | District-year net current expenditures per pupil | district x fiscal_year | FY2008-FY2025 | 2,675 |
| `town_year_ecs_entitlement` | Town-year ECS entitlements | town x fiscal_year | FY2001-FY2027 | 4,563 |
| `town_year_ecs_payment` | Town-year ECS payment list | town x fiscal_year | FY2026 | 169 |
| `town_year_ecs_inputs` | Town-year ECS formula inputs and calculation | town x fiscal_year | FY2018-FY2027 | 1,690 |
| `ecs_formula_parameters` | ECS formula parameters by shell | shell (fiscal_year x source sheet) | FY2018-FY2027 | 19 |

## How to Load

Python:

```python
import pandas as pd
df = pd.read_csv("data/district_year_spending/district_year_spending.csv")
```

R:

```r
library(readr)
df <- read_csv("data/district_year_spending/district_year_spending.csv")
```

The `datapackage.json` descriptor makes the release loadable with Frictionless tooling. In Python: `from frictionless import Package; Package('datapackage.json')`. In R, use the `frictionless` package to read the same descriptor.

## Provenance

Each dataset directory contains the formatted CSV, a codebook README, a `build.py`, and the copied raw scraped files under `raw/`. For the six datasets that already had verified clean panels in the source analysis repo, the formatted CSVs are copies of those committed panels; their build scripts replay the original cleaner scripts against this repo's copied raw files and reproduced the committed panels in verification.

**ECS datasets (added 2026-09-14; rebuilt on the official worksheets 2026-09-15).** The four `*ecs*` datasets are at TOWN grain (169 towns; `town_code` equals the local board of education's district code, and regional school districts receive no ECS directly). Grant amounts come from CSDE's official spreadsheets. Formula inputs come from the official OFA/CSDE per-town calculation shells for FY2019-FY2021 and FY2023-FY2027 (CSDE does not post them; they were received from the state by email and are stored with SHA-256 hashes under `raw/ofa/`) and from the School and State Finance Project's copy of the FY2022 shell; SSFP's copies equal the official shells to the cent wherever both exist. `data/town_year_ecs_inputs/VALIDATION.md` documents that the parsed inputs reproduce the statutory formula exactly in every year, match OPM's equalized-net-grand-list file and the cited ACS median-income vintages, and that a grant rebuilt from the inputs under each year's enacted phase-in rule lands within 0.5% of CSDE's published entitlement for 169 of 169 towns in FY2019, FY2022, FY2023 and FY2025-FY2027, 168 in FY2024, and 165 / 163 in FY2020 / FY2021 (Alliance towns whose FY2020 grant CSDE recalculated with revised Public Investment Community rankings). FY2018 grants were legislated rather than computed, so FY2018 carries core inputs only.

**Data completeness.** Each district-level dataset's README includes a `## Data completeness` section reporting its panel span and a district-by-district list of missing interior years (years missing *between* a district's first and last appearance; earlier/later non-appearances are treated as the district not operating or reporting, not as missing data). Statewide structural gaps are noted once rather than per district -- most notably, no SAT School Day or Smarter Balanced (SBAC) assessments were administered in FY2020 and FY2021 due to COVID-19. Across the finance and enrollment panels, district-specific missingness is minimal (typically zero to a handful of district-years); the one notable case is Hartford, which is absent from CSDE's archived financial collections for FY2015 and FY2016.

**SEDA-derived simulation inputs (added 2026-09-14).** `seda_k_grade_subject` converts student-level standard deviations to grade levels using the NAEP parameters SEDA publishes in Table 9 of its 2025.2 documentation, exactly as SEDA defines its CS and GCS scales, with a regression cross-check; `town_grade_subject_seda_baseline` gives each town's spring 2023-2025 baseline by grade and subject. Both are built by replaying the original script; the two ~119 MB national SEDA long files behind the cross-check are not redistributed, so the build uses the logged per-year slopes in `raw/`.

## ECS Formula Explorer and test-score simulation

`tools/ecs_formula_explorer/` holds the source, build scripts and built page of an interactive dashboard that rebuilds every town's ECS grant for FY2019-FY2027, every year of the current formula, from the datasets above, lets the user change the formula (sliders and stackable presets), maps and charts the results in constant 2025 dollars, and simulates the effect of the spending change on SEDA test scores using Jackson & Mackevicius (2024). It also contains the Python reference implementation of the simulation with unit tests and a log of every run. See `tools/ecs_formula_explorer/README.md`.

## License and Citation

Released under the Creative Commons Attribution 4.0 International License (`CC-BY-4.0`); see `LICENSE`. Citation metadata are in `CITATION.cff`.
