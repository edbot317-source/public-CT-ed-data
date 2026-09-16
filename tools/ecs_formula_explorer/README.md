# ECS Formula Explorer and test-score simulation

Source and build for the interactive dashboard that rebuilds every Connecticut town's Education Cost Sharing (ECS)
grant from the state's own calculation worksheets for FY2019-FY2027 (every year of the current formula; FY2018 grants
were legislated, not computed), lets the user change the formula, and simulates the effect of the resulting spending
change on test scores. Everything here runs from the datasets in `../../data/`.

## Files

| File | What it is |
|---|---|
| `ecs_formula_explorer.html` | The built, self-contained page (open it in a browser; loads d3 from cdnjs and fonts from Google Fonts). |
| `ecs_dashboard_template.html` | Page source with `/*__DATA__*/` and `/*__GEO__*/` placeholders. |
| `build_dash_data.py` | Builds `ecs_dash_data.json` from the public datasets (`town_year_ecs_inputs`, `ecs_formula_parameters` for each year's weights and phase-in rule, `town_year_ecs_entitlement`, `district_year_ncep`, `district_year_seda_gcs`, `seda_k_grade_subject`, `town_grade_subject_seda_baseline`, `cpi_u_deflator`) plus the ACS mean-income files in `inputs/`. |
| `inject.py` | Inlines the JSON and GeoJSON into the template to produce the page. |
| `ecs_dash_data.json` | Built data file: per-town inputs and entitlements by fiscal year, policy parameters by year, CPI-U, SEDA scores, and simulation parameters. |
| `ct_towns.geojson` | Town boundaries from the Census Bureau's 2023 cartographic boundary file for Connecticut county subdivisions (`cb_2023_09_cousub_500k`), converted with pyshp. |
| `inputs/eci-state-local-govt-fred.csv` | Employment Cost Index, state and local government total compensation (BLS CIU3010000000000I via FRED), calendar-year averages; the alternative to CPI-U for indexing the foundation (`inputs/74_download_eci.py` rebuilds it). |
| `inputs/acs5_subject_ct_towns_{vintage}.csv` | ACS 5-year subject table S1901 (mean household income, `S1901_C01_013E`) for Connecticut towns, vintages 2015-2023 (FY t uses vintage t-4); used only by the "average household income" option. |
| `sim/seda_spending_sim.py` | Simulation engine (exposure, dose, effect size, deflation, income multiplier, k from SEDA Table 9) with unit tests: `python sim/seda_spending_sim.py`. |
| `sim/run_sim.py` | Python reference run of the dashboard's scenario engine and simulation; logs every run under `sim/runs/` and in `sim/RUNS.md`. |
| `sim/k_by_year.csv`, `sim/aggregation_check.md` | Regression cross-check of k by year, and the check that the grade-level SEDA files aggregate to the pooled annual estimates (corr 0.993). |
| `sim/runs/` | Logged runs with their assumptions, outputs and figures. |
| `sim/ma_chapter70.py` | Massachusetts Chapter 70 rule (foundation budget, contribution solve, aid step), unit-tested against DESE's FY2025 workbook: `python sim/ma_chapter70.py`. `sim/ma_analysis.py` writes `sim/ma_chapter70_results.md` and `sim/ma_chapter70_fy2025_by_town.csv`. Assumptions and limits: `MA_CHAPTER70_ASSUMPTIONS.md`. |

## Rebuild

```
python build_dash_data.py      # writes ecs_dash_data.json
python inject.py               # writes ecs_formula_explorer.html (and ecs_dashboard.html, an identical copy)
python sim/seda_spending_sim.py                              # unit tests
python sim/run_sim.py --scenario f13087 --start 2023         # reference simulation run
python sim/run_sim.py --scenario inflation+fullhh --start 2019 --index eci --passthrough 0.5 --linear   # every option
python sim/run_sim.py --scenario ma --start 2019 --set ma_lam=0.59 --set ma_min=104 --li dc                 # Massachusetts Chapter 70 rule (--li frpl|free|dc)
```

Scripts detect this layout automatically (they also run inside the original analysis repository).

## What the dashboard does

- **Formula rebuild.** Need students = resident + 0.30 x FRPL + concentrated-poverty add-on + ELL add-on (PA 17-2 through FY2021:
  0.05 x FRPL above 75% of residents and 0.15 x English learners; PA 19-117 from FY2022: 0.15 x FRPL above 60% and 0.25 x ELL);
  wealth factors from equalized net grand list per capita and median household income against 1.35 x the statewide median;
  base aid ratio = max(1 - (0.7 x ENGL factor + 0.3 x MHI factor), 0.10 for Alliance/Priority districts or 0.01 otherwise) plus the
  Public Investment Community bonus; fully funded grant = need x ratio x $11,525 foundation + regional and endowed bonuses; the
  phase-in as applied each year (FY2019: from the FY2017 grant, +4.1% / -25% of the gap; FY2020-FY2022: from the prior year,
  +10.66% / -8.33% of the gap measured against FY2017, overfunded towns held harmless from FY2022; FY2023-FY2027: from the prior
  year, 16.67%, 20%, 56.5%, 100%, 100% of the gap, held harmless) and the Alliance/Priority hold-harmless (never below the starting
  point; from FY2024 never below FY2017). Sliders left at their default apply each year's enacted need weights. Town-years where
  the rebuild matches CSDE's published entitlement within $1 are flagged exact, within 0.5% near-exact.
- **Scenarios.** Sliders on every weight, threshold, foundation and phase-in; stackable presets (inflation-adjusted foundation
  compounding from 2013 by CPI-U or by the state-and-local-government Employment Cost Index, the $13,087 foundation, full formula
  with no phase-in either holding every town harmless at its prior grant (the state's FY2026 approach) or paying exact formula
  amounts with no hold-harmless; a Massachusetts Chapter 70 rule with sliders for the statewide local share and the minimum aid per pupil and a selector for the low-income basis: FRPL, free lunch only, or direct certification); hold-harmless for Alliance districts, none, or all; a start year for the change; mean instead
  of median household income. All dollars are constant 2025 dollars (CPI-U).
- **Charts.** Statewide ECS and statewide achievement series (test-weighted mean of town SEDA scores, spring 2019-2025, with the scenario's simulated effect added); town series (FY2019-FY2027, with each town's SEDA achievement history from spring 2019). Achievement charts annotate the observed decline from the first to the last scored year and how much of it the scenario would have offset (omitted where scores did not fall); a clickable map; ECS per resident student (or CSDE net current expenditures per pupil)
  against the low-income share with fitted slopes under enacted and scenario policy; SEDA achievement in grade levels against
  funding and need, enacted and scenario. Achievement axes fit the data by default (a toggle restores a zero-anchored axis) so that small movements are visible; the town achievement series marks every observed year.
- **Test-score simulation.** The scenario's ECS change per resident student, deflated to 2018 dollars and treated as operating
  spending, is mapped to achievement with the noncapital effect from Jackson & Mackevicius (2024, *AEJ: Applied* 16(1), Table 3);
  the change can now start as early as FY2019, giving cohorts up to seven policy years by FY2025:
  0.0343 student-level SD per $1,000 per pupil at four years of exposure, ramped linearly over exposure years (min of policy year and
  grade + 1), and converted to grade levels with k from `seda_k_grade_subject`. Statewide and FRPL-tercile results are weighted by
  tests taken. An income-heterogeneity sensitivity scales the effect by each town's FRPL share; a pass-through slider scales the ECS change reaching school budgets in non-Alliance towns (Alliance/Priority towns always 100%; default 100%); a "linear score growth" option removes the plateau after four years of exposure. Statewide and tercile figures give each member town of a regional district the region's tests in proportion to its resident students. No uncertainty bands are shown.
  The horizon is FY2023-FY2025 because both the ECS panel's observed years and SEDA's scores end in 2025.

The page's own "Assumptions" section lists every modeling choice; `sim/runs/*/assumptions_log.md` records them per run.

## Sources

CSDE ECS entitlement files; official OFA/CSDE per-town ECS calculation shells (FY2019-FY2021, FY2023-FY2027) and the School and
State Finance Project's copy of the FY2022 shell; OPM equalized net grand list;
Census ACS 5-year tables B19013 and S1901; CSDE net current expenditure reports; Stanford Education Data Archive 2025.2
(Reardon, Fahle, Ho, Shear, Saliba, Min, Shim & Kalogrides); FRED CPIAUCSL; Jackson, C. K. and C. Mackevicius (2024),
"What Impacts Can We Expect from School Spending Policy? Evidence from Evaluations in the United States," *American Economic
Journal: Applied Economics* 16(1): 412-446.
