# Simulating a Massachusetts Chapter 70 aid rule for Connecticut towns: assumptions, limits and review

Built 2026-09-16. Code: `code/75`-`79` (downloads and input build), `output/ecs/dashboard/sim/ma_chapter70.py`
(engine, unit-tested), the `ma` preset in `output/ecs/dashboard/ecs_dashboard_template.html` (a line-for-line
JavaScript mirror), `sim/run_sim.py --scenario ma` (logged reference runs), `sim/ma_analysis.py`
(results tables in `output/ecs/ma_chapter70_results.md`). Public copies live in
`public-CT-ed-data/tools/ecs_formula_explorer/` and the datasets `town_year_ma_inputs`,
`ma_fy2025_foundation_rates` and `ma_chapter70_parameters`.

## 1. What is simulated

For each Connecticut town and fiscal year FY2019-FY2027 the rule computes

    B_i  = foundation budget (DESE FY2025 rates x the town's resident students by grade band, English learners,
           low-income concentration group, assumed special-education shares, wage adjustment factor; rates indexed
           to the year with the chosen price index, capped at 4.5% a year)
    T_i  = target local contribution = min( rho_P x EQV_i + rho_Y x INC_i , 0.825 x B_i ), with rho_P and rho_Y
           solved each year so that property and income yield equal amounts and the capped targets sum to
           lambda x sum(B) (lambda = 0.59 in Massachusetts; a slider on the page)
    Aid_i = max( B_i - T_i , Aid_i(t-1) + m x foundation pupils )   (m = $104 in FY2025; a slider)

with Aid_i(t-1) chained from the town's actual ECS grant in the year before the start year. The aid change
against enacted ECS feeds the existing test-score simulation exactly as any other scenario does.

## 2. Validation against Massachusetts' own calculation

- **Foundation budget arithmetic.** Applying the parsed FY2025 rate table to DESE's published worked example
  (Plymouth: thirteen enrollment columns, wage factor 1.036, low-income group 6) reproduces the published total,
  $112,170,810, to the dollar.
- **Contribution solve.** Applying the solve to DESE's FY2025 townwide data (351 municipalities: equalized
  valuation, income, foundation budget) reproduces DESE's uniform rates (0.39056 percent of valuation,
  1.43119 percent of income) to ten decimals and every municipality's target contribution within $1, summing to
  the published $8,575,711,006.
- **Aid step.** Reproduces Boston's and Lexington's FY2025 Chapter 70 aid from their published foundation
  budgets, required contributions, prior aid and enrollment.
- **Data.** Grade-band shares from NCES CCD enrollment by grade (Urban Institute mirror), county wages from
  BLS QCEW, aggregate income from ACS table B19025, valuations from OPM's equalized net grand list; every
  download is logged with its source URL.

What is *not* validated: the mapping of Connecticut students, wealth and prices onto Massachusetts'
definitions. That is where the assumptions below live.

## 3. Key assumptions

| # | Assumption | Why it matters | Alternative |
|---|---|---|---|
| A1 | **Massachusetts' FY2025 dollar rates are used unchanged in Connecticut**, indexed to other years by CPI-U or the state-and-local ECI with the 4.5% cap. | The foundation budget is the "adequate" spending level. In FY2025 it comes to a median $13,357 per foundation pupil across Connecticut towns (Union $11,582 to Bridgeport $21,697), against Massachusetts' own average of $16,051 and Connecticut's actual median net current expenditure of about $22,700 per pupil. The rule therefore defines adequacy at roughly 60% of what Connecticut towns spend. Only 5 of 148 towns with local boards spend below it. | Scale the rates to Connecticut cost levels (e.g. to the statewide average NCE per pupil, or to a Connecticut cost study); the page's index selector only moves rates through time, not across states. |
| A2 | **Low-income basis is selectable**: ECS FRPL-eligible students (default; the same 185%-of-poverty line Massachusetts uses, identified partly through meal applications), free-lunch-eligible students only (EdSight; 130% of poverty or direct certification; a lower bound), or directly certified students (CSDE's CEP identified-student percentage, SNAP / TFA / Medicaid / foster / homeless / migrant matches, applied to resident students; CEP data cover 2023-24 to 2025-26 and the nearest year is used elsewhere; 31 small towns absent from the CEP list fall back to the free-lunch count). Massachusetts identifies low income through administrative matches at 185% of poverty plus a verification form, without meal applications. | Statewide FY2025 shares of resident students: FRPL 43.2%, free lunch 37.4%, direct certification 34.2%; Massachusetts' own share is 45.6%. The basis mainly moves towns near a tier boundary; see the sensitivity table in the results file. | Massachusetts' supplemental verification form has no Connecticut analogue; a survey-based 185% child-poverty share (ACS B17024) would be independent of school identification. |
| A3 | **The town is the unit** for the foundation budget and the low-income group, using ECS resident students. Massachusetts computes foundation budgets by operating district (municipal or regional) and apportions regional contributions to member towns. | Per-pupil rates are additive, so the only differences are the concentration group (town-level FRPL share rather than the region's) and the wage factor; both are second-order. Charter and magnet residents are given the town's own grade mix. | Compute by operating district and apportion. |
| A4 | **Grade mix** comes from the town's local district plus its share of each regional district it belongs to (share = students sent, from the ECS worksheet), CCD year t-2; 3 towns with no district data (27 town-years) use statewide shares. Pre-K is priced at the pre-school rate. | Rates differ by band (high school $11,334 vs elementary $9,806), so the mix moves a town's budget by a few percent. | Grade-level resident counts from PSIS if obtainable. |
| A5 | **Special education** enters only as Massachusetts' assumed shares (3.93% in-district, 1% tuitioned-out of K-12) at Massachusetts' rates. Vocational enrollment is zero because Connecticut's technical high schools are state-run and outside the resident count. | Connecticut's identification rate (about 16%) is well above the assumed 3.93%; the foundation budget carries no town-specific special-education cost, exactly as in Massachusetts. | A Connecticut-specific special-education weight. |
| A6 | **Wage adjustment factor** uses the county's QCEW average pay relative to the state (2023 is the last county-coded year; later years reuse it). Only Fairfield County exceeds the state average (factor 1.096); every other county gets 1. | Massachusetts uses labor market areas and blends the town's own average; a county proxy flattens intra-county differences (Stamford vs Bridgeport get the same factor). | BLS QCEW by planning region (2024 onward) or LAUS labor market areas. |
| A7 | **Equalized valuation** = OPM's equalized net grand list for the latest grand-list year in the ECS window (t-4, the ECS convention); Massachusetts uses valuations two years prior. **Income** = ACS 5-year aggregate household income, vintage t-4; Massachusetts uses total personal income from state tax returns two years prior. | Both lag more than Massachusetts' inputs, and ACS aggregate income (household income, survey-based) is not tax-return income; the property/income split still yields equal halves by construction. | DRS adjusted gross income by town; a shorter lag. |
| A8 | **Steady-state contributions**: every town's required contribution equals its target every year. Massachusetts moves each town from its prior-year requirement by a municipal revenue growth factor plus effort increments (1-2% of foundation when more than 2.5% or 7.5% below target), and removes excess effort at 100% (FY2025). | The transition mostly affects the timing of local requirements, not aid, except in the first years; the aid floor (prior aid plus $104 per pupil) does the smoothing on the state side. | Add the MRGF transition using OPM Municipal Fiscal Indicators. |
| A9 | **The 59% statewide local share and the 82.5% cap are Massachusetts' values.** | With Connecticut's wealth distribution, 94 of 169 towns hit the cap in FY2025 and the uniform rates settle at 3.57 mills on valuation and 1.53% of aggregate income (Massachusetts FY2025: 3.91 mills and 1.43% of tax-return income). State aid equals 41% of foundation budgets, $3.29B in FY2025 against $2.36B of ECS. | The lambda slider; a lower cap. |
| A10 | **Aid never falls** (prior aid plus minimum aid), chaining from the FY2018 ECS grant. | In FY2019 73 towns receive less than their enacted FY2019 ECS because the rule gives them minimum aid on a FY2018 base; by FY2025 only 16 towns are below enacted ECS (Hamden the largest, $8.2M). | Start the chain later, or from the fully funded ECS grant. |
| A11 | **Only state aid changes spending** in the test-score simulation, at the pass-through rate; the required local contribution is not enforced as spending. | Massachusetts' net-school-spending requirement would also raise spending in towns below foundation, but almost no Connecticut town is below the transplanted foundation budget (A1), so this matters little here. | Model NSS enforcement if rates are scaled up. |
| A12 | The **minimum aid** per pupil ($104) is applied to foundation pupils (pre-K at 0.5) and not indexed. | Small. | Index it. |
| A13 | **Foundation level is selectable**: the straight transplant applies DESE's FY2025 rates as they are; the spending-calibrated option multiplies every category by one factor (about 1.23 with the FRPL basis) chosen so that Connecticut's median town spends the same multiple of its foundation budget (net current expenditures over foundation, FY2025) as Massachusetts' median district spends of its own (actual net school spending over foundation budget, 1.389 in FY2025 from DESE's compliance file, where the median district is 31% above its required NSS and 18 of 319 fall short). The factor is recomputed for the chosen low-income basis and price index. | Calibrated FY2025 foundation budgets total $9.06B (transplant $7.37B), aid under the rule $3.94B (transplant $3.29B, enacted ECS $2.36B); median foundation per pupil $16,407 vs $13,357. | The calibration treats the foundation as what it is in Massachusetts, a floor most districts clear, not a cost estimate. NCE counts federal and other revenue that net school spending excludes, so the factor is an upper bound; an NSS-style Connecticut spending measure (NCE less federal and non-ECS state grant spending, municipal-paid benefits included) would lower it. |

## 4. Limits

- **Adequacy is defined by another state's costs.** Everything the rule says about "gaps" and "state share" is
  relative to a foundation budget calibrated to Massachusetts wages, class sizes and benefits in FY2025. Because
  Connecticut towns spend far more than that budget, the rule redistributes aid by wealth without asserting that
  any town is underfunded. Do not read the foundation budget as an adequacy standard for Connecticut. The
  Massachusetts standard itself is a 1993 model-school staffing budget (class sizes of 22, 25 and 17; fixed staff
  per 1,000 pupils) priced at then-current salaries, reconstituted into per-pupil rates in FY2007 and patched by
  the 2015 Foundation Budget Review Commission and the 2019 Student Opportunity Act (benefits at GIC trend,
  special-education shares, English-learner and low-income increments); it is not tied to any outcome target. The
  spending-calibrated option (A13) re-bases it to Connecticut spending rather than re-doing that construction.
- **Distributional pattern.** The rule sends the largest gains to high-poverty, low-wealth cities (Bridgeport
  +$96M, Waterbury +$82M, Hartford +$72M in FY2025) and to high-need Fairfield County towns that also get the
  wage factor (Danbury +$50M, Norwalk +$37M, Stamford +$29M), and it guarantees every town 17.5% of its
  foundation budget (Greenwich $22.5M against $0.9M of ECS). Towns that lose relative to enacted ECS are mostly
  mid-wealth towns whose ECS grew faster than the rule's floor.
- **No behavioral response.** Towns are assumed not to change local effort when required contributions or aid
  change, and school budgets are assumed to move with aid at the pass-through rate.
- **Regional districts** are handled by apportioning member towns, not as operating districts (A3).
- **Years before FY2019 and after FY2027** are outside the panel; the rates are FY2025 values moved by a price
  index, not the Student Opportunity Act phase-in that Massachusetts itself was still completing in FY2025.

## 5. Review from the standpoint of Massachusetts and Connecticut school finance

*Where the implementation is faithful.* The foundation budget mechanics, the wage-factor rule (one plus a
third of the wage gap, floored at one, excluding materials, benefits and special-education tuition), the
twelve low-income tiers, the assumed special-education shares, the two-rate contribution solve with the 82.5%
cap and the aid step all match DESE's FY2025 workbook and reproduce its published figures. The engine is the
same in Python and on the page.

*Where a Massachusetts expert would object.*

1. Transplanting nominal rates ignores that Connecticut's average teacher salary and benefit costs exceed
   Massachusetts' only modestly while its actual spending per pupil is far higher; the foundation budget
   should be re-based before any adequacy claim is made (A1). The right first step is a scale factor that
   sets the statewide foundation total to a Connecticut benchmark.
2. Massachusetts' low-income definition since the Student Opportunity Act uses the same 185%-of-poverty line
   as school-meals eligibility but identifies students through administrative matches; the selector offers the
   Connecticut counts that bracket it, and the choice moves towns near tier boundaries (A2).
3. The wage factor matters much less in Connecticut with a county proxy (one county above one) than in
   Massachusetts, where labor-market-area wages spread widely around Boston (A6).
4. Chapter 70's local side is a *requirement*; the simulation treats it only as the aid offset. In
   Massachusetts the requirement is what forces low-effort towns to spend; here, with a low transplanted
   foundation, it rarely binds (A11).

*Where a Connecticut expert would object.*

1. ECS resident students include children educated in magnets, charters and Open Choice; the foundation
   budget prices them as if educated by the town, while the town's actual cost for them is tuition. The
   same in-district/out-of-district issue flagged for the ECS simulation applies.
2. Connecticut has no municipal revenue growth factor, no levy limit and no net-school-spending statute; the
   minimum budget requirement is the only local floor. A Chapter 70 transplant therefore imports a local
   contribution concept Connecticut law does not have (A8, A11).
3. Ninety-four towns at the cap means the rule's wealth measure barely discriminates among the top half of
   Connecticut towns; the 17.5% floor then guarantees substantial aid to towns ECS gives almost nothing.
   Whether that is a feature (universal buy-in) or a flaw (money to Greenwich) is a policy judgment the
   dashboard leaves to the user.
4. The Alliance District set-aside, the minimum budget requirement and Connecticut's other categorical
   grants are unchanged in the simulation; a real transplant would replace or reconcile them.

*Suggested next steps if the rule is to be taken seriously:* re-base the rates (A1), test the low-income bases against each other (A2), add the MRGF transition from current local education revenue (A8, using
`district_year_revenue`), and compute regional districts as operating units (A3).

## 6. Data sources

- DESE, FY2025 Chapter 70 complete formula spreadsheet (`chapter-2025.xlsm`), white paper and summary charts,
  https://www.doe.mass.edu/finance/chapter70/fy2025/ (downloaded 2026-09-16, in `data/ma/dese/`).
- MGL c.70 s.2 (definitions: wage adjustment factor, foundation budget, foundation inflation index, target
  local contribution, maximum local contribution, minimum aid).
- NCES Common Core of Data, LEA enrollment by grade 2018-2023, via https://educationdata.urban.org (API).
- BLS Quarterly Census of Employment and Wages, county and state annual averages 2016-2023,
  https://data.bls.gov/cew/data/api/.
- Census ACS 5-year table B19025 (aggregate household income), county subdivisions, vintages 2015-2023.
- OPM Equalized Net Grand List by Town (data.ct.gov 8rr8-a322); ECS worksheets (this repository).
- DESE net school spending compliance summaries, `comply-fy2024.xlsx` and `comply-fy2025.xlsx` (required and actual
  NSS and foundation budget by district; https://www.doe.mass.edu/finance/chapter70/; downloaded 2026-09-16, in
  `data/ma/dese/`; parsed by `80_parse_ma_nss_compliance.py` to `clean-data/ma_nss_compliance.csv`), and 603 CMR
  10.06 (what counts toward net school spending).
- CSDE net current expenditures (`district_year_ncep`, CGS 10-261(a)(3)) for the Connecticut side of the calibration.
