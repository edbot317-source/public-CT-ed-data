# Town-year ECS formula inputs and calculation

- **Series name:** Town-year ECS formula inputs and calculation
- **Grain:** one row per town x fiscal_year
- **Year range:** FY2018-FY2027
- **Source:** School and State Finance Project workbooks republishing the Office of Fiscal Analysis ECS calculation shells; https://schoolstatefinance.org/hubfs/Reports/ECS%20Formula%20Component%20Comparison%20Tool%20and%20Data%20Trend%20Model.xlsx; https://schoolstatefinance.org/reports/interactive-model-of-ecs-formula (FY 2027 Town ECS Model .xlsm)
- **Row count:** 1,690
- **Column count:** 73

Every input and intermediate column of the per-town ECS grant calculation (resident students, low-income and English-learner counts, need students, three-year equalized net grand list, population, median household income, wealth factors, base aid ratio, regional and endowed-academy bonuses, fully funded grant, phase-in and entitlement), FY2018-FY2027. Full worksheets are available from FY2020; FY2018-FY2019 carry core inputs only. Parsed from the OFA shells republished by the School and State Finance Project because CSDE does not post per-town worksheets; validated against the statutory formula, CSDE's published entitlements, OPM's equalized-net-grand-list file and Census ACS (see VALIDATION.md).

## Codebook

| Column | Definition | Type |
|---|---|---|
| `town_code` | Connecticut town code, 1-169 (alphabetical); equals the local board of education's CSDE district code. | integer |
| `district_code` | Local board of education district code (= town_code). Regional school districts receive no ECS directly. | integer |
| `town` | Town name. | string |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2026 corresponds to school year 2025-26. | integer |
| `source_sheet` | Worksheet the row was parsed from (OFA/SSFP shell name). | string |
| `source_file` | Workbook the row was parsed from. | string |
| `count_date` | October-1 PSIS count date used for the student inputs (MM/YYYY). | string |
| `drg` | District Reference Group (A-I). | string |
| `wealth_decile` | OFA wealth decile of the town (1 = poorest). | integer |
| `alliance_flag` | 1 if the town's district is an Alliance District that year. | integer |
| `psd_flag` | 1 if a Priority School District. | integer |
| `reform_flag` | 1 if a reform district (older shells). | integer |
| `pic_rank_raw` | Public Investment Community index rank as printed in the shell (0 = not in that year's ranked set). | integer |
| `pic_score` | Public Investment Community index score (SSFP backend table). | number |
| `resident_students` | Resident students the town is fiscally responsible for (ECS definition), October-1 count. | number |
| `frpl_count` | Students eligible for free or reduced-price meals, October-1 PSIS. | number |
| `frpl_pct` | frpl_count / resident_students. | number |
| `frpl_weighted` | frpl_count x 0.30 (low-income need weight). | number |
| `conc_pov_threshold` | Concentrated-poverty threshold share of resident students (0.75 through FY2021; 0.60 after). | number |
| `conc_pov_threshold_students` | resident_students x conc_pov_threshold. | number |
| `excess_frpl_students` | FRPL students above the concentrated-poverty threshold (0 if below). | number |
| `excess_frpl_weighted` | Concentrated-poverty need add-on: excess_frpl_students x 0.05 (through FY2021) or x 0.15. | number |
| `conc_pov_students_above_threshold` | Shell's own count of FRPL students above the threshold. | number |
| `ell_count` | English learners, October-1 PSIS. | number |
| `ell_pct` | ell_count / resident_students. | number |
| `ell_weighted` | ell_count x 0.15 (through FY2021) or x 0.25. | number |
| `need_students` | Total need students: resident + weighted low-income + concentrated-poverty + ELL terms. | number |
| `engl_grand_list_years` | Grand-list years averaged for the ENGL input (comma-separated). | string |
| `engl_avg` | Three-year average equalized net grand list, dollars. | number |
| `population_year` | Year of the population estimate used. | integer |
| `population` | Town population used by the formula (DPH/OPM estimate series). | number |
| `engl_per_capita` | engl_avg / population. | number |
| `engl_median` | Statewide median ENGL per capita that year. | number |
| `engl_threshold` | engl_median x 1.35. | number |
| `engl_factor` | engl_per_capita / engl_threshold. | number |
| `mhi_year` | ACS 5-year vintage of the median household income input. | integer |
| `mhi` | Town median household income (ACS 5-year), dollars. | number |
| `mhi_median` | Statewide median of town MHI that year. | number |
| `mhi_threshold` | mhi_median x 1.35. | number |
| `mhi_factor` | mhi / mhi_threshold. | number |
| `wealth_adj_factor` | 1 - (0.70 x engl_factor + 0.30 x mhi_factor). | number |
| `base_aid_ratio` | max(wealth_adj_factor, minimum aid ratio: 0.10 Alliance/PSD, 0.01 other). | number |
| `pic_bar_adjustment` | Base-aid-ratio bonus for the 19 highest-ranked Public Investment Communities (0.03-0.06). | number |
| `final_base_aid_ratio` | base_aid_ratio + pic_bar_adjustment. | number |
| `rsd_students` | Students the town sends to regional school districts, October-1. | number |
| `rsd_grades` | Number of grades in those regional districts. | number |
| `rsd_per_pupil_bonus` | Regional-district per-pupil bonus (pre-FY2022 form of the bonus). | number |
| `rsd_bonus` | Regional school district bonus, dollars (students x grades x $100 from FY2022). | number |
| `endowed_students` | Students the town sends to endowed academies, October-1. | number |
| `endowed_grades` | Number of grades at those endowed academies. | number |
| `endowed_bonus` | Endowed-academy bonus, dollars (students x grades x $100). | number |
| `foundation` | Foundation amount per need student, dollars ($11,525). | number |
| `base_formula_aid` | need_students x final_base_aid_ratio x foundation, dollars. | number |
| `fully_funded_grant` | base_formula_aid + rsd_bonus + endowed_bonus, dollars. | number |
| `fully_funded_grant_hh` | Fully funded grant with the Alliance/PSD hold-harmless applied, dollars. | number |
| `fy2017_actual` | FY2017 ECS entitlement (statutory base grant), dollars. | number |
| `prior_year_entitlement` | Prior fiscal year's ECS entitlement (CSDE final), dollars. | number |
| `grant_adjustment` | Absolute gap between the fully funded grant and the prior-year entitlement, dollars. | number |
| `ff_greater_than_prior` | Yes if the fully funded grant exceeds the prior-year entitlement (underfunded town). | string |
| `phase_in_amount` | Dollars of the gap phased in that year under the statutory schedule. | number |
| `entitlement_no_hh` | Entitlement computed by the shell before the Alliance/PSD hold-harmless, dollars. | number |
| `entitlement` | ECS entitlement, nominal dollars (CSDE; excludes prior-year adjustments). | number |
| `excess_frpl_weighted_note` | Set when the concentrated-poverty weighted term was derived from the shell's own arithmetic. | string |
| `ell_weighted_note` | Set when ell_weighted was derived from ell_count x 0.25 (FY2022-FY2023 OFA shells lack the column). | string |
| `entitlement_note` | Set when the shell has no hold-harmless column (entitlement = entitlement_no_hh). | string |
| `backend_resident_students` | Cross-check: resident students from SSFP's backend_data table. | number |
| `backend_frpl_count` | Cross-check: FRPL count from SSFP's backend_data table. | number |
| `backend_ell_count` | Cross-check: ELL count from SSFP's backend_data table. | number |
| `backend_engl_per_capita` | Cross-check: ENGL per capita from SSFP's backend_data table. | number |
| `backend_mhi` | Cross-check: MHI from SSFP's backend_data table. | number |
| `backend_fully_funded_grant` | Cross-check: fully funded grant from SSFP's backend_data table. | number |
| `backend_final_base_aid_ratio` | Cross-check: final base aid ratio from SSFP's backend_data table (FY2023+). | number |
| `backend_pic_score` | Cross-check: PIC score from SSFP's backend_data table. | number |

## Source sheets by fiscal year

| FY | source_sheet | October count | Grand lists | MHI year | Formula variant |
|---|---|---|---|---|---|
| 2018, 2019 | `backend_data` | 10/2016, 10/2017 | (per-capita only) | 2014, 2015 | PA 17-2 |
| 2020 | `Clean Data (FY 2020)` | 10/2018 | 2014-2016 | 2016 | PA 17-2: 75% threshold, 5% weight, ELL 15% |
| 2021 | `FY 21 OFA Shell` | 10/2019 | 2015-2017 | 2017 | PA 17-2 |
| 2022 | `FY 22 OFA Shell` | 10/2020 | 2016-2018 | 2018 | PA 19-117: 60% threshold, 15% weight, ELL 25% |
| 2023-2027 | `FY 23` ... `FY 27` | 10/2021 ... 10/2025 | t-4 to t-2 | t-4 | PA 19-117; formula fully funded from FY2026 |

For grant **amounts** use `town_year_ecs_entitlement` (CSDE final). The `entitlement` column here is what the worksheet computed at the time; it equals the CSDE final within $1 for 155-169 towns per year from FY2022 (FY2023: 124, a projection built on preliminary counts), and differs for 25-31 towns in FY2020-FY2021 because of the revised-PIC-ranking recalculation. The FY2027 sheet is a projection until CSDE finalizes.

**Validation** (`VALIDATION.md`): recomputing the formula from the parsed inputs reproduces every intermediate column for all 169 towns in every year FY2020-FY2027; ENGL equals OPM's Equalized Net Grand List by Town (data.ct.gov 8rr8-a322) within $1 for all towns and years; MHI equals the cited ACS 5-year vintage for 165-169 towns per year; population follows the DPH/OPM estimate series, not ACS.

## Provenance and Method

Raw source workbooks are stored in `raw/` with a download log. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. Original script(s): `61_download_ecs_ssfp.py + 65_parse_ecs_shells.py`.

## Data completeness

- **Panel span:** FY2018-FY2027 (1690 town-years across 169 towns).
- **Method:** only *interior* gaps are counted as missing -- years before a town first appears or after it last appears are treated as not reported, not as missing data.
- **Town-by-town missing years:** none. Every town is complete across its active span.
