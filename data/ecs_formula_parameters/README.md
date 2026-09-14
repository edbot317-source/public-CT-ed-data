# ECS formula parameters by shell

- **Series name:** ECS formula parameters by shell
- **Grain:** one row per shell (fiscal_year x source sheet)
- **Year range:** FY2021-FY2027
- **Source:** School and State Finance Project workbooks republishing the Office of Fiscal Analysis ECS calculation shells; https://schoolstatefinance.org/hubfs/Reports/ECS%20Formula%20Component%20Comparison%20Tool%20and%20Data%20Trend%20Model.xlsx; https://schoolstatefinance.org/reports/interactive-model-of-ecs-formula (FY 2027 Town ECS Model .xlsm)
- **Row count:** 10
- **Column count:** 24

Per-worksheet ECS formula parameters: need weights, wealth threshold factor, ENGL/MHI weights, minimum aid ratios, foundation, statewide medians and thresholds, phase-in percentages, and the data vintages (count date, grand-list years, population and MHI years) used in each fiscal year's calculation.

## Codebook

| Column | Definition | Type |
|---|---|---|
| `need_weight_frpl` | Weight on FRPL students in need students. | number |
| `wealth_threshold_factor` | Multiplier applied to the statewide median ENGL per capita and MHI (1.35). | number |
| `engl_weight` | Weight on the ENGL factor in the wealth adjustment factor. | number |
| `mhi_weight` | Weight on the MHI factor in the wealth adjustment factor. | number |
| `min_bar_nonalliance` | Minimum base aid ratio, non-Alliance / non-PSD towns. | number |
| `min_bar_alliance` | Minimum base aid ratio, Alliance Districts and PSDs. | number |
| `foundation` | Foundation amount per need student, dollars ($11,525). | number |
| `adj_pct_overfunded` | Share of the gap phased out for overfunded towns that year. | number |
| `adj_pct_underfunded` | Share of the gap phased in for underfunded towns that year. | number |
| `engl_median` | Statewide median ENGL per capita that year. | number |
| `engl_threshold` | engl_median x 1.35. | number |
| `mhi_median` | Statewide median of town MHI that year. | number |
| `mhi_threshold` | mhi_median x 1.35. | number |
| `count_date` | October-1 PSIS count date used for the student inputs (MM/YYYY). | string |
| `engl_grand_list_years` | Grand-list years averaged for the ENGL input (comma-separated). | string |
| `population_year` | Year of the population estimate used. | integer |
| `mhi_year` | ACS 5-year vintage of the median household income input. | integer |
| `conc_pov_threshold` | Concentrated-poverty threshold share of resident students (0.75 through FY2021; 0.60 after). | number |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2026 corresponds to school year 2025-26. | integer |
| `source_sheet` | Worksheet the row was parsed from (OFA/SSFP shell name). | string |
| `source_file` | Workbook the row was parsed from. | string |
| `n_towns` | Number of town rows parsed from the shell. | integer |
| `missing_columns` | Canonical columns absent from this shell's layout (semicolon-separated). | string |
| `is_primary` | True if this shell feeds the main inputs panel for its fiscal year. | boolean |

## Provenance and Method

Raw source workbooks are stored in `raw/` with a download log. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. Original script(s): `61_download_ecs_ssfp.py + 65_parse_ecs_shells.py`.

## Data completeness

- Not a town-year panel; completeness section not applicable.
