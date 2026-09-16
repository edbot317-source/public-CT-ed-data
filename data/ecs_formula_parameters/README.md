# ECS formula parameters by shell

- **Series name:** ECS formula parameters by shell
- **Grain:** one row per shell (fiscal_year x source sheet)
- **Year range:** FY2018-FY2027
- **Source:** Official Office of Fiscal Analysis / CSDE per-town ECS calculation shells and the School and State Finance Project's republished copies; official OFA/CSDE per-town ECS calculation shells FY2018-FY2027 (except FY2022), received from the state by email on 2026-09-15, not posted online; copies with SHA-256 hashes in raw/ofa/; https://schoolstatefinance.org/hubfs/Reports/ECS%20Formula%20Component%20Comparison%20Tool%20and%20Data%20Trend%20Model.xlsx; https://schoolstatefinance.org/reports/interactive-model-of-ecs-formula (FY 2027 Town ECS Model .xlsm)
- **Row count:** 19
- **Column count:** 33

Per-worksheet ECS formula parameters: need weights (FRPL, concentrated poverty, ELL), wealth threshold factor, ENGL/MHI weights, minimum aid ratios, foundation, statewide medians and thresholds, the phase-in percentages as printed and as applied, the phase-in gap base and starting point, the hold-harmless floor, the statutory basis of each year's rule (CGS 10-262h and PA 17-2 JSS, PA 21-2 JSS, PA 23-204, PA 25-168), and the data vintages (count date, grand-list years, population and MHI years) used in each fiscal year's calculation. One row per parsed worksheet, official and SSFP copies alike; is_primary marks the sheet that feeds town_year_ecs_inputs.

## Codebook

| Column | Definition | Type |
|---|---|---|
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2026 corresponds to school year 2025-26. | integer |
| `source_sheet` | Worksheet the row was parsed from (OFA/SSFP shell name). | string |
| `source_file` | Workbook the row was parsed from. | string |
| `source_type` | Provenance of the worksheet: official OFA shell received from the state (2026-09-15), or the School and State Finance Project's republished copy. | string |
| `is_primary` | True if this shell feeds the main inputs panel for its fiscal year. | boolean |
| `n_towns` | Number of town rows parsed from the shell. | integer |
| `need_weight_frpl` | Weight on FRPL students in need students. | number |
| `need_weight_conc_pov` | Weight on FRPL students above the concentrated-poverty threshold (0.05 through FY2021, 0.15 after). | number |
| `need_weight_ell` | Weight on English learners in need students (0.15 through FY2021, 0.25 after). | number |
| `conc_pov_threshold` | Concentrated-poverty threshold share of resident students (0.75 through FY2021; 0.60 after). | number |
| `wealth_threshold_factor` | Multiplier applied to the statewide median ENGL per capita and MHI (1.35). | number |
| `engl_weight` | Weight on the ENGL factor in the wealth adjustment factor. | number |
| `mhi_weight` | Weight on the MHI factor in the wealth adjustment factor. | number |
| `min_bar_nonalliance` | Minimum base aid ratio, non-Alliance / non-PSD towns. | number |
| `min_bar_alliance` | Minimum base aid ratio, Alliance Districts and PSDs. | number |
| `foundation` | Foundation amount per need student, dollars ($11,525). | number |
| `adj_pct_underfunded` | Phase-in share for towns below full funding as printed in the worksheet's parameter block (blank where the sheet states it only in a column header). | number |
| `adj_pct_overfunded` | Phase-out share for towns above full funding as printed in the worksheet's parameter block; not applied where the budget act held towns harmless (see pct_over_applied). | number |
| `pct_under_applied` | Share of the gap actually phased in for underfunded towns that year (verified against CSDE's grants). | number |
| `pct_over_applied` | Share of the gap actually phased out for overfunded towns that year (0 = held harmless). | number |
| `phase_in_gap_base` | Amount the phase-in gap is measured against that year: fy2017 (FY2019-FY2022, PA 17-2) or prior (FY2023 on). | string |
| `phase_in_start_base` | Amount the phase-in moves from that year: fy2017 (FY2019 only) or prior. | string |
| `hh_floor_fy2017` | True if the Alliance/PSD hold-harmless also floors the grant at the FY2017 amount that year (the "greater of" clause in the FY2024 and later paragraphs of CGS 10-262h, PA 23-204 sec. 356). | boolean |
| `phase_in_statute` | Statutory basis of the year's phase-in and hold-harmless rule: CGS 10-262h paragraph and the public act(s) that set it, checked against the codified statute and the OLR bill analyses on 2026-09-16. | string |
| `engl_median` | Statewide median ENGL per capita that year. | number |
| `engl_threshold` | engl_median x 1.35. | number |
| `mhi_median` | Statewide median of town MHI that year. | number |
| `mhi_threshold` | mhi_median x 1.35. | number |
| `count_date` | October-1 PSIS count date used for the student inputs (MM/YYYY). | string |
| `engl_grand_list_years` | Grand-list years averaged for the ENGL input (comma-separated). | string |
| `population_year` | Year of the population estimate used. | integer |
| `mhi_year` | ACS 5-year vintage of the median household income input. | integer |
| `missing_columns` | Canonical columns absent from this shell's layout (semicolon-separated). | string |

## Provenance and Method

Raw source workbooks are stored in `raw/` with a download log. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. Original script(s): `61_download_ecs_ssfp.py + 65_parse_ecs_shells.py`.

## Data completeness

- Not a town-year panel; completeness section not applicable.
