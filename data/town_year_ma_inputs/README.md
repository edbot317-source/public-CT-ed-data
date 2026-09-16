# Town-year inputs for a Massachusetts Chapter 70 style rule

- **Series name:** Town-year inputs for a Massachusetts Chapter 70 style rule
- **Grain:** one row per town x fiscal_year
- **Year range:** FY2019-FY2027
- **Source:** NCES Common Core of Data enrollment by grade (Urban Institute Education Data Portal API); BLS Quarterly Census of Employment and Wages; Census ACS 5-year table B19025; OPM Equalized Net Grand List by Town; ECS worksheets; https://educationdata.urban.org/api/v1/school-districts/ccd/enrollment/{year}/grade-{g}/?fips=9; https://data.bls.gov/cew/data/api/{year}/a/area/{fips}.csv; https://api.census.gov/data/{vintage}/acs/acs5 (B19025_001E, county subdivisions in state 09); https://data.ct.gov/resource/8rr8-a322
- **Row count:** 1,521
- **Column count:** 22

What a Massachusetts Chapter 70 foundation budget and required local contribution need for each Connecticut town, FY2019-FY2027: the grade mix of resident students (pre-K, kindergarten, 1-5, 6-8, 9-12) from the town's local district plus its share of each regional district it belongs to; the county wage ratio and the resulting wage adjustment factor; equalized valuation (OPM grand list, t-4) and aggregate household income (ACS, t-4); and the ECS resident, FRPL and English-learner counts the rule prices. Built for the Chapter 70 preset of the ECS Formula Explorer; see tools/ecs_formula_explorer/MA_CHAPTER70_ASSUMPTIONS.md for every assumption and limit.

## Codebook

| Column | Definition | Type |
|---|---|---|
| `town_code` | Connecticut town code, 1-169 (alphabetical); equals the local board of education's CSDE district code. | integer |
| `town` | Town name. | string |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2026 corresponds to school year 2025-26. | integer |
| `ccd_year` | NCES Common Core of Data school year (fall) whose enrollment by grade supplies the grade mix; fiscal year t uses t-2, the ECS count date. | integer |
| `grade_source` | Where the grade mix comes from: local (the town's own district), region (its share of a regional district), both, or statewide shares when neither exists. | string |
| `share_pk` | Share of resident students in pre-kindergarten. | number |
| `share_k` | Share of resident students in kindergarten. | number |
| `share_el` | Share of resident students in grades 1-5. | number |
| `share_ms` | Share of resident students in grades 6-8. | number |
| `share_hs` | Share of resident students in grades 9-12. | number |
| `county` | County (the labor-market-area proxy for the wage adjustment factor). | string |
| `wage_year` | Calendar year of the QCEW average pay used (t-2; 2023 is the last county-coded year). | integer |
| `county_wage_ratio` | County average annual pay, all covered jobs, divided by the Connecticut average (BLS QCEW). | number |
| `wage_adjustment_factor` | 1 + (county_wage_ratio - 1)/3, not less than 1 (MGL c.70 s.2 rule with the county as labor market area). | number |
| `eqv_grand_list_year` | Grand-list year of the equalized net grand list used (the latest in the ECS window, t-4). | integer |
| `equalized_valuation` | OPM equalized net grand list, dollars (Chapter 70's equalized valuation). | number |
| `income_vintage` | ACS 5-year vintage of the aggregate household income (t-4). | integer |
| `aggregate_household_income` | ACS 5-year aggregate household income, table B19025, dollars (Chapter 70 uses tax-return personal income). | number |
| `resident_students` | Resident students the town is fiscally responsible for (ECS definition), October-1 count. | number |
| `frpl_count` | Students eligible for free or reduced-price meals, October-1 PSIS. | number |
| `ell_count` | English learners, October-1 PSIS. | number |
| `alliance_or_psd` | 1 if an Alliance District or Priority School District that year (ECS worksheet). | integer |

## Provenance and Method

Raw source workbooks are stored in `raw/` with a download log. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. Original script(s): `75_download_ccd_grade_enrollment.py + 76_download_qcew_wages.py + 77_download_acs_aggregate_income.py + 79_build_ma_inputs.py`.

## Data completeness

- **Panel span:** FY2019-FY2027 (1521 town-years across 169 towns).
- **Method:** only *interior* gaps are counted as missing -- years before a town first appears or after it last appears are treated as not reported, not as missing data.
- **Town-by-town missing years:** none. Every town is complete across its active span.
