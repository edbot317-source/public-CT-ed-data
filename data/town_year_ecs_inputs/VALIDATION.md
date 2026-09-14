# ECS panel validation

## 1. Internal arithmetic (parsed inputs -> shell intermediates)

| FY | need students | ENGL factor | MHI factor | wealth adj | base aid ratio | final BAR | base formula aid | fully funded grant |
|---|---|---|---|---|---|---|---|---|
| FY2020 | 169/169 | - | - | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |
| FY2021 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |
| FY2022 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |
| FY2023 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |
| FY2024 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |
| FY2025 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |
| FY2026 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |
| FY2027 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |

Tolerances: need 0.01 students; factors 1e-4; dollars $1. Base aid ratio uses the alliance/PSD minimum (10%) where the shell flags the town, else 1%.

## 1b. Phase-in arithmetic (prior-year entitlement -> shell entitlement, before hold-harmless)

Rule tested is the FY2023+ statute (underfunded: prior + phase-in; overfunded: prior - phase-in). The FY2021-FY2022 shells applied the earlier PA 17-2 / PA 19-117 schedule with different overfunded-town treatment, so their rows are informational.

- FY2020: concentrated-poverty weighted = 5% x students above threshold: 169/169 within tol (max |diff| 0.0000)
- FY2021: concentrated-poverty weighted = 5% x students above threshold: 169/169 within tol (max |diff| 0.0000)
- FY2021: 165/169 within tol (max |diff| 41,858.7498)
- FY2022: 81/169 within tol (max |diff| 623,635.7792)
- FY2023: 169/169 within tol (max |diff| 0.0000)
- FY2024: 169/169 within tol (max |diff| 0.0000)
- FY2025: 169/169 within tol (max |diff| 0.0000)
- FY2026: 169/169 within tol (max |diff| 0.0000)
- FY2027: 169/169 within tol (max |diff| 0.0000)

## 2. Shell entitlement vs CSDE published entitlement

- FY2018: no shell entitlement column to compare
- FY2019: no shell entitlement column to compare
- FY2020: 138/169 within tol (max |diff| 345,359.0000); totals shell $2,054,281,372 vs CSDE $2,054,036,355
- FY2021: 144/169 within tol (max |diff| 1,710.0284); totals shell $2,093,587,718 vs CSDE $2,093,587,133
- FY2022: 155/169 within tol (max |diff| 45.3004); totals shell $2,139,188,097 vs CSDE $2,139,188,165
- FY2023: 124/169 within tol (max |diff| 58,514.1445); totals shell $2,178,800,382 vs CSDE $2,178,565,995
- FY2024: 165/169 within tol (max |diff| 59.0000); totals shell $2,233,420,315 vs CSDE $2,233,420,236
- FY2025: 163/169 within tol (max |diff| 61.7800); totals shell $2,361,569,054 vs CSDE $2,361,568,857
- FY2026: 162/169 within tol (max |diff| 314.0000); totals shell $2,456,046,409 vs CSDE $2,456,045,858
- FY2027: 169/169 within tol (max |diff| 0.0000); totals shell $2,458,690,805 vs CSDE $2,458,690,805

## 2b. Shell 'prior year entitlement' vs CSDE entitlement for FY-1

- FY2020: 153/169 within tol (max |diff| 19.2500)
- FY2021: 159/169 within tol (max |diff| 345,359.0000)
- FY2022: 169/169 within tol (max |diff| 0.0000)
- FY2023: 169/169 within tol (max |diff| 0.0000)
- FY2024: 169/169 within tol (max |diff| 0.0000)
- FY2025: 169/169 within tol (max |diff| 0.0000)
- FY2026: 169/169 within tol (max |diff| 0.0000)
- FY2027: 169/169 within tol (max |diff| 0.0000)

## 2c. CSDE entitlement vs OPM 'Estimates of Statutory Aid' (education_cost_sharing)

- FY2025: vs entitlement 27/169 within tol (max |diff| 1,264,089.0000); vs non-Alliance portion 27/169 within tol (max |diff| 77,069,255.0000); vs payment-list local entitlement n/a
- FY2026: vs entitlement 33/169 within tol (max |diff| 592,050.0000); vs non-Alliance portion 33/169 within tol (max |diff| 87,396,731.0000); vs payment-list local entitlement 33/169 within tol (max |diff| 87,396,731.0000)
- FY2027: vs entitlement 169/169 within tol (max |diff| 0.0000); vs non-Alliance portion 135/169 within tol (max |diff| 87,501,360.0000); vs payment-list local entitlement n/a

OPM's statutory-aid file carries the budget-time (OFA) estimates, not CSDE's final entitlements: FY2027 (both estimates) matches exactly, FY2025-FY2026 mostly do not. It is not a validation target for final amounts.

## 3. Primary-series checks

### 3a. ENGL 3-year average vs OPM Equalized Net Grand List by Town

- FY2020 (GL 2014,2015,2016): 169/169 within tol (max |diff| 0.3000); median relative gap 0.00%
    ENGL per capita = engl_avg / population: 169/169 within tol (max |diff| 0.0000)
- FY2021 (GL 2015,2016,2017): 169/169 within tol (max |diff| 0.4333); median relative gap 0.00%
    ENGL per capita = engl_avg / population: 169/169 within tol (max |diff| 0.0050)
- FY2022 (GL 2016,2017,2018): 169/169 within tol (max |diff| 0.4033); median relative gap 0.00%
    ENGL per capita = engl_avg / population: 169/169 within tol (max |diff| 0.0050)
- FY2023 (GL 2017,2018,2019): 169/169 within tol (max |diff| 0.3100); median relative gap 0.00%
    ENGL per capita = engl_avg / population: 169/169 within tol (max |diff| 0.0050)
- FY2024 (GL 2018,2019,2020): 169/169 within tol (max |diff| 0.1700); median relative gap 0.00%
    ENGL per capita = engl_avg / population: 169/169 within tol (max |diff| 0.0049)
- FY2025 (GL 2019,2020,2021): 169/169 within tol (max |diff| 0.0033); median relative gap 0.00%
    ENGL per capita = engl_avg / population: 169/169 within tol (max |diff| 0.0049)
- FY2026 (GL 2020,2021,2022): 169/169 within tol (max |diff| 0.0033); median relative gap 0.00%
    ENGL per capita = engl_avg / population: 169/169 within tol (max |diff| 0.0050)
- FY2027 (GL 2021,2022,2023): 169/169 within tol (max |diff| 0.0033); median relative gap 0.00%
    ENGL per capita = engl_avg / population: 169/169 within tol (max |diff| 0.0049)

### 3b. Population and MHI vs Census ACS 5-year (county subdivisions)


| FY | shell MHI year | best ACS vintage (MHI) | MHI exact matches | best ACS vintage (pop) | pop within 1 |
|---|---|---|---|---|---|
| FY2020 | 2016 | 2016 | 169/169 | 2018 | 2/169 |
| FY2021 | 2017 | 2017 | 169/169 | 2018 | 2/169 |
| FY2022 | 2018 | 2018 | 169/169 | 2018 | 168/169 |
| FY2023 | 2019 | 2019 | 169/169 | 2015 | 1/169 |
| FY2024 | 2020 | 2020 | 169/169 | 2016 | 2/169 |
| FY2025 | 2021 | 2021 | 168/169 | 2021 | 3/169 |
| FY2026 | 2022 | 2022 | 167/169 | 2022 | 2/169 |
| FY2027 | 2023 | 2023 | 165/169 | 2023 | 168/169 |

### 3c. Parsed shell columns vs SSFP backend_data table

- resident_students: 1352/1352 within tol (max |diff| 0.0000)
- frpl_count: 1352/1352 within tol (max |diff| 0.0000)
- ell_count: 1352/1352 within tol (max |diff| 0.0000)
- engl_per_capita: 1352/1352 within tol (max |diff| 0.0050)
- mhi: 1352/1352 within tol (max |diff| 0.0000)
- fully_funded_grant: 1247/1352 within tol (max |diff| 13,649,402.0000)
    rows off, by FY: {2020: 7, 2021: 8, 2022: 8, 2023: 11, 2024: 10, 2025: 10, 2026: 16, 2027: 35}
- final_base_aid_ratio: 845/845 within tol (max |diff| 0.0000)
