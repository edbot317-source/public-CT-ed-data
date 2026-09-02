# Public Connecticut Education Data Release

This repository releases a self-contained set of Connecticut education finance, enrollment, accountability, assessment, graduation, special education, and CPI deflator datasets assembled for public reuse. The data are statewide Connecticut district and school data, with coverage used in a Hartford-region education finance analysis; topline sources are CT EdSight (`edsight.ct.gov` and `public-edsight.ct.gov`) and FRED from the Federal Reserve Bank of St. Louis.

## Datasets

| Dataset key | Series name | Grain | Year range | Rows |
|---|---|---|---:|---:|
| `district_year_enrollment` | District-year enrollment and demographics | district x fiscal_year | FY2008-FY2026 | 3,772 |
| `district_year_spending` | District-year net current expenditures by function | district x fiscal_year | FY2018-FY2025 | 1,561 |
| `district_year_ppe_archived` | Archived district-year per-pupil expenditures by function | district x fiscal_year | FY2007-FY2017 | 2,029 |
| `district_year_ppe_extended` | Extended district-year total per-pupil expenditures | district x fiscal_year | FY2007-FY2025 | 3,590 |
| `district_year_revenue` | District-year revenue sources | district x fiscal_year | FY2018-FY2025 | 1,561 |
| `district_year_accountability` | District-year accountability and growth metrics | district x fiscal_year | FY2025 | 199 |
| `school_year_enrollment_race` | School-year enrollment by race | school x fiscal_year | FY2008-FY2026 | 25,055 |
| `school_year_spending` | School-year net current expenditures by function | school x fiscal_year | FY2018-FY2025 | 7,948 |
| `school_year_funding_source` | School-year per-pupil expenditures by funding source | school x fiscal_year | FY2018-FY2025 | 7,955 |
| `special_education_expenditures` | Special education expenditures | district x fiscal_year x expenditure_category | FY2007-FY2025 | 38,774 |
| `per_pupil_expenditures_by_object` | District-year net current expenditures by object | district x fiscal_year x object | FY2018-FY2025 | 12,400 |
| `total_annual_expenditures_archived` | Archived district-year total annual expenditures by type | district x fiscal_year | FY2006-FY2017 | 2,209 |
| `sbac` | District-year Smarter Balanced assessment outcomes | district x fiscal_year x subject x needs_group | FY2015-FY2025 | 10,284 |
| `sat` | District-year Connecticut School Day SAT outcomes | district x fiscal_year x subject x needs_group | FY2016-FY2025 | 7,004 |
| `graduation_4yr` | District-year four-year graduation rates | district x fiscal_year x needs_group | FY2012-FY2025 | 5,839 |
| `graduation_5yr` | District-year five-year graduation rates | district x fiscal_year x needs_group | FY2012-FY2023 | 4,990 |
| `swd_outplacement` | Students with disabilities attending out-of-district schools/programs | district x fiscal_year x placement_type | FY2018-FY2025 | 2,624 |
| `cpi_u_deflator` | CPI-U annual average deflator | calendar year | 2006-2025 | 20 |

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

Each dataset directory contains the formatted CSV, a codebook README, a `build.py`, and the copied raw scraped files under `raw/`. For the nine datasets that already had verified clean panels in the source analysis repo, the formatted CSVs are copies of those committed panels; their build scripts replay the original cleaner scripts against this repo's copied raw files and reproduced the committed panels in verification.

**Data completeness.** Each district-level dataset's README includes a `## Data completeness` section reporting its panel span and a district-by-district list of missing interior years (years missing *between* a district's first and last appearance; earlier/later non-appearances are treated as the district not operating or reporting, not as missing data). Statewide structural gaps are noted once rather than per district -- most notably, no SAT School Day or Smarter Balanced (SBAC) assessments were administered in FY2020 and FY2021 due to COVID-19. Across the finance and enrollment panels, district-specific missingness is minimal (typically zero to a handful of district-years); the one notable case is Hartford, which is absent from CSDE's archived financial collections for FY2015 and FY2016.

## License and Citation

Released under the Creative Commons Attribution 4.0 International License (`CC-BY-4.0`); see `LICENSE`. Citation metadata are in `CITATION.cff`.
