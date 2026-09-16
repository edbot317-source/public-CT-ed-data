# ECS panel validation

Primary worksheets: FY2019 OFA shell (official, received 2026-09-15), FY2020 OFA shell (official, received 2026-09-15), FY2021 OFA shell (official, received 2026-09-15), FY2022 SSFP copy of OFA shell, FY2023 OFA shell (official, received 2026-09-15), FY2024 OFA shell (official, received 2026-09-15), FY2025 OFA shell (official, received 2026-09-15), FY2026 OFA shell (official, received 2026-09-15), FY2027 OFA shell (official, received 2026-09-15).

## 1. Internal arithmetic (parsed inputs -> shell intermediates)

| FY | need students | ENGL factor | MHI factor | wealth adj | base aid ratio | final BAR | base formula aid | fully funded grant |
|---|---|---|---|---|---|---|---|---|
| FY2019 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |
| FY2020 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |
| FY2021 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |
| FY2022 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |
| FY2023 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |
| FY2024 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |
| FY2025 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |
| FY2026 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |
| FY2027 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |

Tolerances: need 0.01 students; factors 1e-4; dollars $1. Base aid ratio uses the alliance/PSD minimum (10%) where the shell flags the town, else 1%. The concentrated-poverty weighted term and (before FY2022) the ELL weighted term are derived columns in some shells (see `derived_columns`); the need-students check therefore also confirms those derivations.

## 1a. Concentrated-poverty and ELL weights (derived columns)

- FY2019: conc-pov weighted = 5% x students above 75%: 169/169 within tol (max |diff| 0.0000); ELL weighted = 15% x ELL: 169/169 within tol (max |diff| 0.0000)
- FY2020: conc-pov weighted = 5% x students above 75%: 169/169 within tol (max |diff| 0.0000); ELL weighted = 15% x ELL: 169/169 within tol (max |diff| 0.0000)
- FY2021: conc-pov weighted = 5% x students above 75%: 169/169 within tol (max |diff| 0.0000); ELL weighted = 15% x ELL: 169/169 within tol (max |diff| 0.0000)
- FY2022: conc-pov weighted = 15% x students above 60%: 169/169 within tol (max |diff| 0.0000); ELL weighted = 25% x ELL: 169/169 within tol (max |diff| 0.0000)
- FY2023: conc-pov weighted = 15% x students above 60%: 169/169 within tol (max |diff| 0.0045); ELL weighted = 25% x ELL: 169/169 within tol (max |diff| 0.0000)
- FY2024: conc-pov weighted = 15% x students above 60%: 169/169 within tol (max |diff| 0.0045); ELL weighted = 25% x ELL: 169/169 within tol (max |diff| 0.0000)
- FY2025: conc-pov weighted = 15% x students above 60%: 169/169 within tol (max |diff| 0.0045); ELL weighted = 25% x ELL: 169/169 within tol (max |diff| 0.0000)
- FY2026: conc-pov weighted = 15% x students above 60%: 169/169 within tol (max |diff| 0.0045); ELL weighted = 25% x ELL: 169/169 within tol (max |diff| 0.0000)
- FY2027: conc-pov weighted = 15% x students above 60%: 169/169 within tol (max |diff| 0.0050); ELL weighted = 25% x ELL: 169/169 within tol (max |diff| 0.0000)

## 1b. Phase-in arithmetic (shell's own FY2017 / prior-year columns -> shell entitlement)

Rule per year (`ecs_parameters.csv`, columns pct_under_applied / pct_over_applied / phase_in_gap_base / phase_in_start_base): FY2019 moves from the FY2017 grant by 4.1% (underfunded) or 25% (overfunded) of the gap to full funding; FY2020-FY2022 move from the prior year by 10.66% / 8.33% of the gap measured against the FY2017 base (overfunded towns held harmless from FY2022); FY2023 on move from the prior year by 16.67%, 20%, 56.5%, 100%, 100% of the gap against the prior year, overfunded towns held harmless. Alliance/PSD towns never fall below the starting point, and from FY2024 never below their FY2017 grant (`hh_floor_fy2017`; the FY2017 floor is redundant before FY2023 and was not applied to the three towns added to the Alliance list in FY2023).

- FY2019 (4.10% / 25.00%, gap vs fy2017, from fy2017): 169/169 within tol (max |diff| 0.0000)
- FY2020 (10.66% / 8.33%, gap vs fy2017, from prior): 168/169 within tol (max |diff| 959.1162)
- FY2021 (10.66% / 8.33%, gap vs fy2017, from prior): 164/169 within tol (max |diff| 20,929.3749)
- FY2022 (10.66% / 0.00%, gap vs fy2017, from prior): 169/169 within tol (max |diff| 0.0000)
- FY2023 (16.67% / 0.00%, gap vs prior, from prior): 169/169 within tol (max |diff| 0.0000)
- FY2024 (20.00% / 0.00%, gap vs prior, from prior): 169/169 within tol (max |diff| 0.4000)
- FY2025 (56.50% / 0.00%, gap vs prior, from prior): 169/169 within tol (max |diff| 0.0000)
- FY2026 (100.00% / 0.00%, gap vs prior, from prior): 169/169 within tol (max |diff| 0.0000)
- FY2027 (100.00% / 0.00%, gap vs prior, from prior): 169/169 within tol (max |diff| 0.0000)

## 2. Shell entitlement vs CSDE published entitlement

- FY2018: no shell entitlement column to compare (FY2018 grants were set by PA 17-2 and the November-2017 holdbacks)
- FY2019 (FY 2018-19): 153/169 within tol (max |diff| 19.2500); within $50: 169/169; totals shell $2,013,828,682 vs CSDE $2,013,828,619
- FY2020 (FY 2019-20): 132/169 within tol (max |diff| 345,359.1464); within $50: 160/169; totals shell $2,054,281,360 vs CSDE $2,054,036,355
- FY2021 (FY 2020-21): 152/169 within tol (max |diff| 17.8110); within $50: 169/169; totals shell $2,093,587,192 vs CSDE $2,093,587,133
- FY2022 (FY 22 OFA Shell): 155/169 within tol (max |diff| 45.3004); within $50: 169/169; totals shell $2,139,188,097 vs CSDE $2,139,188,165
- FY2023 (Current Law): 158/169 within tol (max |diff| 17.7020); within $50: 169/169; totals shell $2,178,566,078 vs CSDE $2,178,565,995
- FY2024 (FY 24): 165/169 within tol (max |diff| 59.0000); within $50: 168/169; totals shell $2,233,420,315 vs CSDE $2,233,420,236
- FY2025 (FY 25): 163/169 within tol (max |diff| 61.7800); within $50: 168/169; totals shell $2,361,569,054 vs CSDE $2,361,568,857
- FY2026 (FY 26): 162/169 within tol (max |diff| 314.0000); within $50: 167/169; totals shell $2,456,046,409 vs CSDE $2,456,045,858
- FY2027 (FY 27): 169/169 within tol (max |diff| 0.0000); within $50: 169/169; totals shell $2,458,690,805 vs CSDE $2,458,690,805

## 2a. Rebuild test: grant recomputed from the parsed inputs under the enacted rule

This is the dashboard's reproduction metric. Each town-year's grant is rebuilt from its worksheet inputs (need students, wealth factors, base aid ratio, bonuses -> fully funded grant) and the enacted phase-in rule, starting from CSDE's ACTUAL prior-year grant (FY2019: the FY2017 grant). 'Chained' instead starts every town at its FY2017 grant and rolls forward on the rebuilt grant with no resets, which is how the dashboard's enacted-policy line and every scenario are computed.

| FY | worksheet | within $1 | within $50 | within 0.5% | chained within 0.5% | largest gap (town) |
|---|---|---|---|---|---|---|
| FY2019 | FY 2018-19 | 157/169 | 169/169 | 169/169 | 169/169 | +19 (Bethany) |
| FY2020 | FY 2019-20 | 147/169 | 159/169 | 165/169 | 165/169 | +345,359 (Bristol) |
| FY2021 | FY 2020-21 | 143/169 | 154/169 | 163/169 | 165/169 | -345,359 (Bristol) |
| FY2022 | FY 22 OFA Shell | 158/169 | 169/169 | 169/169 | 165/169 | -45 (Windham) |
| FY2023 | Current Law | 159/169 | 169/169 | 169/169 | 167/169 | +18 (Bristol) |
| FY2024 | FY 24 | 165/169 | 168/169 | 169/169 | 167/169 | +59 (Bridgeport) |
| FY2025 | FY 25 | 163/169 | 168/169 | 169/169 | 168/169 | +62 (Bristol) |
| FY2026 | FY 26 | 162/169 | 167/169 | 169/169 | 168/169 | +314 (Bridgeport) |
| FY2027 | FY 27 | 169/169 | 169/169 | 169/169 | 168/169 | +0 (Andover) |

FY2020 and FY2021 misses are Alliance/Priority towns whose FY2020 grant CSDE recalculated with revised Public Investment Community rankings (the worksheet carries the earlier ranking); the same dollar gap carries into FY2021 and disappears from FY2022, when the worksheet's prior-year column is CSDE's final. Gaps of $1-$50 are rounding differences between the worksheet and CSDE's payment file.

## 2b. Shell 'prior year entitlement' / FY2017 base vs CSDE

- FY2019: prior-year column vs CSDE FY2018: 169/169 within tol (max |diff| 0.0000) (filled from CSDE); FY2017 base vs CSDE FY2017: 169/169 within tol (max |diff| 0.0000)
- FY2020: prior-year column vs CSDE FY2019: 153/169 within tol (max |diff| 19.2500); FY2017 base vs CSDE FY2017: 169/169 within tol (max |diff| 0.0000)
- FY2021: prior-year column vs CSDE FY2020: 159/169 within tol (max |diff| 345,359.0000); FY2017 base vs CSDE FY2017: 169/169 within tol (max |diff| 0.0000)
- FY2022: prior-year column vs CSDE FY2021: 169/169 within tol (max |diff| 0.0000); FY2017 base vs CSDE FY2017: 169/169 within tol (max |diff| 0.0000)
- FY2023: prior-year column vs CSDE FY2022: 169/169 within tol (max |diff| 0.0000); FY2017 base vs CSDE FY2017: 169/169 within tol (max |diff| 0.0000)
- FY2024: prior-year column vs CSDE FY2023: 169/169 within tol (max |diff| 0.0000); FY2017 base vs CSDE FY2017: 169/169 within tol (max |diff| 0.0000)
- FY2025: prior-year column vs CSDE FY2024: 169/169 within tol (max |diff| 0.0000); FY2017 base vs CSDE FY2017: 169/169 within tol (max |diff| 0.0000)
- FY2026: prior-year column vs CSDE FY2025: 169/169 within tol (max |diff| 0.0000); FY2017 base vs CSDE FY2017: 169/169 within tol (max |diff| 0.0000)
- FY2027: prior-year column vs CSDE FY2026: 169/169 within tol (max |diff| 0.0000); FY2017 base vs CSDE FY2017: 169/169 within tol (max |diff| 0.0000)

## 2c. CSDE entitlement vs OPM 'Estimates of Statutory Aid' (education_cost_sharing)

- FY2025: vs entitlement 27/169 within tol (max |diff| 1,264,089.0000); vs non-Alliance portion 27/169 within tol (max |diff| 77,069,255.0000); vs payment-list local entitlement n/a
- FY2026: vs entitlement 33/169 within tol (max |diff| 592,050.0000); vs non-Alliance portion 33/169 within tol (max |diff| 87,396,731.0000); vs payment-list local entitlement 33/169 within tol (max |diff| 87,396,731.0000)
- FY2027: vs entitlement 169/169 within tol (max |diff| 0.0000); vs non-Alliance portion 135/169 within tol (max |diff| 87,501,360.0000); vs payment-list local entitlement n/a

OPM's statutory-aid file carries the budget-time (OFA) estimates, not CSDE's final entitlements: FY2027 (both estimates) matches exactly, FY2025-FY2026 mostly do not. It is not a validation target for final amounts.

## 3. Primary-series checks

### 3a. ENGL 3-year average vs OPM Equalized Net Grand List by Town

- FY2019 (GL 2013,2014,2015): 169/169 within tol (max |diff| 0.1700); median relative gap 0.00%
    ENGL per capita = engl_avg / population: 169/169 within tol (max |diff| 0.0049)
- FY2020 (GL 2014,2015,2016): 169/169 within tol (max |diff| 0.3000); median relative gap 0.00%
    ENGL per capita = engl_avg / population: 169/169 within tol (max |diff| 0.0050)
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
| FY2019 | 2015 | 2015 | 169/169 | 2017 | 5/169 |
| FY2020 | 2016 | 2016 | 169/169 | 2018 | 2/169 |
| FY2021 | 2017 | 2017 | 169/169 | 2018 | 2/169 |
| FY2022 | 2018 | 2018 | 169/169 | 2018 | 168/169 |
| FY2023 | 2019 | 2019 | 169/169 | 2015 | 1/169 |
| FY2024 | 2020 | 2020 | 169/169 | 2016 | 2/169 |
| FY2025 | 2021 | 2021 | 168/169 | 2021 | 3/169 |
| FY2026 | 2022 | 2022 | 167/169 | 2022 | 2/169 |
| FY2027 | 2023 | 2023 | 165/169 | 2023 | 168/169 |

### 3c. Parsed shell columns vs SSFP backend_data table

- resident_students: 1452/1521 within tol (max |diff| 59.6700)
    rows off, by FY: {2021: 7, 2023: 62}
- frpl_count: 1486/1521 within tol (max |diff| 103.0000)
    rows off, by FY: {2021: 5, 2023: 30}
- ell_count: 1505/1521 within tol (max |diff| 13.0000)
    rows off, by FY: {2023: 16}
- engl_per_capita: 1521/1521 within tol (max |diff| 0.0000)
- mhi: 1521/1521 within tol (max |diff| 0.0000)
- fully_funded_grant: 1333/1521 within tol (max |diff| 13,649,402.0000)
    rows off, by FY: {2019: 7, 2020: 7, 2021: 16, 2022: 8, 2023: 77, 2024: 10, 2025: 12, 2026: 16, 2027: 35}
- final_base_aid_ratio: 845/845 within tol (max |diff| 0.0000)

### 3d. Official OFA shells vs SSFP's republished copies (alternates), column by column

| FY | SSFP sheet | resident | FRPL | ELL | ENGL | population | MHI | need | final BAR | fully funded | entitlement |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FY2020 | `Clean Data (FY 2020)` | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |
| FY2021 | `FY 21 OFA Shell` | 162/169 | 164/169 | 169/169 | 169/169 | 169/169 | 169/169 | 161/169 | 169/169 | 161/169 | 161/169 |
| FY2023 | `FY 23` | 107/169 | 139/169 | 153/169 | 169/169 | 169/169 | 169/169 | 97/169 | 169/169 | 97/169 | 128/169 |
| FY2023 | `FY 23 OFA Shell` | 0/169 | 5/169 | 29/169 | 0/169 | 0/169 | 0/169 | 0/169 | 38/169 | 0/169 | 81/169 |
| FY2024 | `FY 24` | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |
| FY2024 | `FY 24 Adopted` | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |
| FY2025 | `FY 25` | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 167/169 | 169/169 |
| FY2026 | `FY 26` | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |
| FY2026 | `FY 26 CL` | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |
| FY2027 | `FY 27` | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 | 169/169 |

The SSFP copies reproduce the official shells exactly wherever both carry a column, except SSFP's `FY 23` sheet (a projection on preliminary October-2021 counts) and `FY 23 OFA Shell` (built on 10/2020 data). FY2022 has no official shell in hand, so the SSFP copy is the primary source for that year.
