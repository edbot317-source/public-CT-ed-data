# Town-year ECS formula inputs and calculation

- **Series name:** Town-year ECS formula inputs and calculation
- **Grain:** one row per town x fiscal_year
- **Year range:** FY2018-FY2027
- **Source:** Official Office of Fiscal Analysis / CSDE per-town ECS calculation shells (FY2019-FY2021, FY2023-FY2027), the School and State Finance Project's republished copy of the FY2022 shell, and SSFP's backend table for FY2018 core inputs; official OFA/CSDE per-town ECS calculation shells FY2018-FY2027 (except FY2022), received from the state by email on 2026-09-15, not posted online; copies with SHA-256 hashes in raw/ofa/; https://schoolstatefinance.org/hubfs/Reports/ECS%20Formula%20Component%20Comparison%20Tool%20and%20Data%20Trend%20Model.xlsx; https://schoolstatefinance.org/reports/interactive-model-of-ecs-formula (FY 2027 Town ECS Model .xlsm)
- **Row count:** 1,690
- **Column count:** 76

Every input and intermediate column of the per-town ECS grant calculation (resident students, low-income and English-learner counts, need students, three-year equalized net grand list, population, median household income, wealth factors, base aid ratio, regional and endowed-academy bonuses, fully funded grant, phase-in and entitlement), FY2018-FY2027. Full worksheets for every formula year FY2019-FY2027: the official OFA/CSDE shells for FY2019-FY2021 and FY2023-FY2027 (received from the state on 2026-09-15; CSDE does not post them) and the School and State Finance Project's copy for FY2022, which equals the official shells to the cent wherever both exist. FY2018 grants were legislated by PA 17-2 with holdbacks rather than computed, so FY2018 carries core inputs only. Each row records the phase-in rule applied that year (gap base, starting point, hold-harmless floor) and which columns were derived. Validated against the statutory formula, CSDE's published entitlements, OPM's equalized-net-grand-list file and Census ACS; the rebuild test in VALIDATION.md reproduces CSDE's grant within 0.5% for 163-169 of 169 towns in every year FY2019-FY2027.

## Codebook

| Column | Definition | Type |
|---|---|---|
| `town_code` | Connecticut town code, 1-169 (alphabetical); equals the local board of education's CSDE district code. | integer |
| `district_code` | Local board of education district code (= town_code). Regional school districts receive no ECS directly. | integer |
| `town` | Town name. | string |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2026 corresponds to school year 2025-26. | integer |
| `source_sheet` | Worksheet the row was parsed from (OFA/SSFP shell name). | string |
| `source_file` | Workbook the row was parsed from. | string |
| `source_type` | Provenance of the worksheet: official OFA shell received from the state (2026-09-15), or the School and State Finance Project's republished copy. | string |
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
| `fy2018_statutory_pre_holdback` | FY2018 only: statutory FY2018 grant before the November-2017 holdbacks (FY2017 for Alliance towns, 95% of FY2017 otherwise), dollars. | number |
| `prior_year_entitlement` | Prior fiscal year's ECS entitlement as carried in the worksheet (CSDE final; filled from CSDE where the sheet has no such column), dollars. | number |
| `phase_in_gap_base` | Amount the phase-in gap is measured against that year: fy2017 (FY2019-FY2022, PA 17-2) or prior (FY2023 on). | string |
| `phase_in_start_base` | Amount the phase-in moves from that year: fy2017 (FY2019 only) or prior. | string |
| `hh_floor_fy2017` | True if the Alliance/PSD hold-harmless also floors the grant at the FY2017 amount that year (the "greater of" clause in the FY2024 and later paragraphs of CGS 10-262h, PA 23-204 sec. 356). | boolean |
| `grant_adjustment` | Absolute gap between the fully funded grant and the phase-in gap base (FY2017 grant through FY2022, prior year after), dollars. | number |
| `ff_greater_than_prior` | Yes if the fully funded grant exceeds the phase-in gap base (underfunded town). | string |
| `phase_in_amount` | Dollars of the gap phased in that year under the statutory schedule. | number |
| `entitlement_no_hh` | Entitlement computed by the shell before the Alliance/PSD hold-harmless, dollars. | number |
| `entitlement` | ECS entitlement, nominal dollars (CSDE; excludes prior-year adjustments). In town_year_ecs_inputs: the entitlement the worksheet computed at the time. | number |
| `derived_columns` | Columns of this row filled from the worksheet's own arithmetic or from CSDE because the sheet lacks them (semicolon-separated, e.g. ell_weighted=ell_count x 0.15). | string |
| `backend_resident_students` | Cross-check: resident students from SSFP's backend_data table. | number |
| `backend_frpl_count` | Cross-check: FRPL count from SSFP's backend_data table. | number |
| `backend_ell_count` | Cross-check: ELL count from SSFP's backend_data table. | number |
| `backend_engl_per_capita` | Cross-check: ENGL per capita from SSFP's backend_data table. | number |
| `backend_mhi` | Cross-check: MHI from SSFP's backend_data table. | number |
| `backend_fully_funded_grant` | Cross-check: fully funded grant from SSFP's backend_data table. | number |
| `backend_final_base_aid_ratio` | Cross-check: final base aid ratio from SSFP's backend_data table (FY2023+). | number |
| `backend_pic_score` | Cross-check: PIC score from SSFP's backend_data table. | number |

## Source sheets by fiscal year

| FY | source_sheet | source | October count | Grand lists | MHI year | Formula variant | Phase-in rule |
|---|---|---|---|---|---|---|---|
| 2018 | `backend_data` | SSFP (core inputs only) | 10/2016 | (per-capita only) | 2014 | grants legislated (PA 17-2 amounts and holdbacks) | none |
| 2019 | `FY 2018-19` | official OFA shell | 10/2017 | 2013-2015 | 2015 | PA 17-2: 75% threshold, 5% weight, ELL 15% | from FY2017: +4.1% / -25% of gap |
| 2020 | `FY 2019-20` | official OFA shell | 10/2018 | 2014-2016 | 2016 | PA 17-2 | from prior year: +10.66% / -8.33% of gap vs FY2017 |
| 2021 | `FY 2020-21` | official OFA shell | 10/2019 | 2015-2017 | 2017 | PA 17-2 | same |
| 2022 | `FY 22 OFA Shell` | SSFP copy | 10/2020 | 2016-2018 | 2018 | PA 21-2 JSS secs. 384-386: 60% threshold, 15% weight, ELL 25% | +10.66% of gap vs FY2017; overfunded held harmless (PA 21-2) |
| 2023 | `Current Law` | official OFA shell | 10/2021 | 2017-2019 | 2019 | PA 21-2 JSS weights | from prior year: +16.67% of gap vs prior; held harmless (PA 21-2) |
| 2024-2027 | `FY 24` ... `FY 27` | official OFA shells | 10/2022 ... 10/2025 | t-4 to t-2 | t-4 | PA 21-2 JSS weights; PA 23-204 sec. 356 schedule | +20%, 56.5%, 100%, 100%; held harmless (PA 23-204, PA 25-168 sec. 323); Alliance floor at the FY2017 base grant (PA 23-204) |

For grant **amounts** use `town_year_ecs_entitlement` (CSDE final). The `entitlement` column here is what the worksheet computed at the time; it equals the CSDE final within $50 for every town in FY2019, FY2021-FY2023 and FY2027 and for 160-168 towns in the other years. The FY2020 worksheet differs from CSDE's final for nine Alliance towns because CSDE recalculated that grant with revised Public Investment Community rankings; the gap carries into FY2021 and disappears in FY2022. The FY2027 sheet awaits CSDE's final calculation.

**Validation** (`VALIDATION.md`): recomputing the formula from the parsed inputs reproduces every intermediate column for all 169 towns in every year FY2019-FY2027, and the phase-in rule reproduces each worksheet's own entitlement; the rebuild test (grant recomputed from inputs and the enacted rule, starting from CSDE's actual prior-year grant) lands within 0.5% of CSDE's final for 169/169 towns in FY2019, FY2022, FY2023 and FY2025-FY2027, 168 in FY2024, and 165 / 163 in FY2020 / FY2021. ENGL equals OPM's Equalized Net Grand List by Town (data.ct.gov 8rr8-a322) within $1 for all towns and years; MHI equals the cited ACS 5-year vintage for 165-169 towns per year; population follows the DPH/OPM estimate series, not ACS. The SSFP copies equal the official shells to the cent wherever both exist (except SSFP's FY2023 projection).

## Provenance and Method

Raw source workbooks are stored in `raw/` with a download log. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. Original script(s): `61_download_ecs_ssfp.py + 65_parse_ecs_shells.py`.

## Data completeness

- **Panel span:** FY2018-FY2027 (1690 town-years across 169 towns).
- **Method:** only *interior* gaps are counted as missing -- years before a town first appears or after it last appears are treated as not reported, not as missing data.
- **Town-by-town missing years:** none. Every town is complete across its active span.
