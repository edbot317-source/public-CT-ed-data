# ECS Formula Explorer and test-score simulation

Source and build for the interactive dashboard that rebuilds every Connecticut town's Education Cost Sharing (ECS)
grant from the state's own worksheet inputs for FY2023-FY2027, lets the user change the formula, and simulates the
effect of the resulting spending change on test scores. Everything here runs from the datasets in `../../data/`.

## Files

| File | What it is |
|---|---|
| `ecs_formula_explorer.html` | The built, self-contained page (open it in a browser; loads d3 from cdnjs and fonts from Google Fonts). |
| `ecs_dashboard_template.html` | Page source with `/*__DATA__*/` and `/*__GEO__*/` placeholders. |
| `build_dash_data.py` | Builds `ecs_dash_data.json` from the public datasets (`town_year_ecs_inputs`, `town_year_ecs_entitlement`, `district_year_ncep`, `district_year_seda_gcs`, `seda_k_grade_subject`, `town_grade_subject_seda_baseline`, `cpi_u_deflator`) plus the ACS mean-income files in `inputs/`. |
| `inject.py` | Inlines the JSON and GeoJSON into the template to produce the page. |
| `ecs_dash_data.json` | Built data file: per-town inputs and entitlements by fiscal year, policy parameters by year, CPI-U, SEDA scores, and simulation parameters. |
| `ct_towns.geojson` | Town boundaries from the Census Bureau's 2023 cartographic boundary file for Connecticut county subdivisions (`cb_2023_09_cousub_500k`), converted with pyshp. |
| `inputs/acs5_subject_ct_towns_{vintage}.csv` | ACS 5-year subject table S1901 (mean household income, `S1901_C01_013E`) for Connecticut towns, vintages 2016-2023; used only by the "average household income" option. |
| `sim/seda_spending_sim.py` | Simulation engine (exposure, dose, effect size, deflation, income multiplier, k from SEDA Table 9) with unit tests: `python sim/seda_spending_sim.py`. |
| `sim/run_sim.py` | Python reference run of the dashboard's scenario engine and simulation; logs every run under `sim/runs/` and in `sim/RUNS.md`. |
| `sim/k_by_year.csv`, `sim/aggregation_check.md` | Regression cross-check of k by year, and the check that the grade-level SEDA files aggregate to the pooled annual estimates (corr 0.993). |
| `sim/runs/` | Logged runs with their assumptions, outputs and figures. |

## Rebuild

```
python build_dash_data.py      # writes ecs_dash_data.json
python inject.py               # writes ecs_formula_explorer.html (and ecs_dashboard.html, an identical copy)
python sim/seda_spending_sim.py                              # unit tests
python sim/run_sim.py --scenario f13087 --start 2023         # reference simulation run
```

Scripts detect this layout automatically (they also run inside the original analysis repository).

## What the dashboard does

- **Formula rebuild.** Need students = resident + 0.30 x FRPL + 0.15 x FRPL above 60% of residents + 0.25 x English learners;
  wealth factors from equalized net grand list per capita and median household income against 1.35 x the statewide median;
  base aid ratio = max(1 - (0.7 x ENGL factor + 0.3 x MHI factor), 0.10 for Alliance/Priority districts or 0.01 otherwise) plus the
  Public Investment Community bonus; fully funded grant = need x ratio x $11,525 foundation + regional and endowed bonuses; the
  statutory phase-in (16.67%, 20%, 56.5%, 100%, 100% for FY2023-FY2027 for towns below target; 0% phase-out above target) and the
  Alliance/Priority hold-harmless. Town-years where the rebuild matches CSDE's published entitlement within $1 are flagged exact.
- **Scenarios.** Sliders on every weight, threshold, foundation and phase-in; stackable presets (inflation-adjusted foundation
  compounding from 2013, the $13,087 foundation, full formula with no phase-in); hold-harmless for Alliance districts, none, or all;
  a start year for the change; mean instead of median household income. All dollars are constant 2025 dollars (CPI-U).
- **Charts.** Statewide and town series; a clickable map; ECS per resident student (or CSDE net current expenditures per pupil)
  against the low-income share with fitted slopes under enacted and scenario policy; SEDA achievement in grade levels against
  funding and need, enacted and scenario.
- **Test-score simulation.** The scenario's ECS change per resident student, deflated to 2018 dollars and treated as operating
  spending, is mapped to achievement with the noncapital effect from Jackson & Mackevicius (2024, *AEJ: Applied* 16(1), Table 3):
  0.0343 student-level SD per $1,000 per pupil at four years of exposure, ramped linearly over exposure years (min of policy year and
  grade + 1), and converted to grade levels with k from `seda_k_grade_subject`. Statewide and FRPL-tercile results are weighted by
  tests taken. An income-heterogeneity sensitivity scales the effect by each town's FRPL share. No uncertainty bands are shown.
  The horizon is FY2023-FY2025 because both the ECS panel's observed years and SEDA's scores end in 2025.

The page's own "Assumptions" section lists every modeling choice; `sim/runs/*/assumptions_log.md` records them per run.

## Sources

CSDE ECS entitlement files; School and State Finance Project copies of the OFA calculation shells; OPM equalized net grand list;
Census ACS 5-year tables B19013 and S1901; CSDE net current expenditure reports; Stanford Education Data Archive 2025.2
(Reardon, Fahle, Ho, Shear, Saliba, Min, Shim & Kalogrides); FRED CPIAUCSL; Jackson, C. K. and C. Mackevicius (2024),
"What Impacts Can We Expect from School Spending Policy? Evidence from Evaluations in the United States," *American Economic
Journal: Applied Economics* 16(1): 412-446.
