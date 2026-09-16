# Massachusetts net school spending compliance by district (FY2024-FY2025)

- **Series name:** Massachusetts net school spending compliance by district (FY2024-FY2025)
- **Grain:** one row per district x fiscal_year
- **Year range:** FY2024-FY2025
- **Source:** Massachusetts DESE Office of School Finance, net school spending compliance summaries (comply-fy2024.xlsx, comply-fy2025.xlsx, sheet ComplySum, data as of July 2026); https://www.doe.mass.edu/finance/chapter70/ (comply-fy2024.xlsx, comply-fy2025.xlsx; downloaded 2026-09-16)
- **Row count:** 638
- **Column count:** 8

For every operating Massachusetts district: required net school spending (required local contribution plus Chapter 70 aid), actual net school spending as reported on the end-of-year financial report, the foundation budget, and the two ratios. Massachusetts' floor binds where poverty is high (Springfield, Worcester, Lawrence and New Bedford spend within 1% of the requirement; Holyoke and Brockton fall 3-4% short) and is far below spending elsewhere (median 1.31 x required, 1.39 x foundation; 18 of 319 districts below in FY2025). The FY2025 median actual/foundation ratio is the target of the explorer's spending-calibrated foundation level. Net school spending counts spending from local revenue and Chapter 70 aid on administration, instruction, support, athletics, operations and maintenance, health insurance and retirement for current employees, tuition and charter/choice assessments, whether paid by the school committee or the municipality; it excludes transportation, capital, debt service, federal grants and state grants other than Chapter 70, and nets out tuition received (603 CMR 10.06).

## Codebook

| Column | Definition | Type |
|---|---|---|
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2026 corresponds to school year 2025-26. | integer |
| `lea_id` | DESE four-digit LEA code (operating districts only). | string |
| `district` | District name as printed in the CSDE report (title case). | string |
| `required_nss` | Required net school spending: required local contribution plus Chapter 70 aid, nominal dollars. | number |
| `actual_nss` | Actual net school spending reported on the end-of-year financial report (spending from local revenue and Chapter 70 aid on the categories allowed by 603 CMR 10.06), nominal dollars. | number |
| `foundation_budget` | Chapter 70 foundation budget, nominal dollars. | number |
| `actual_to_required` | actual_nss / required_nss (below 1 = shortfall, carried forward under 603 CMR 10.06). | number |
| `actual_to_foundation` | actual_nss / foundation_budget; the FY2025 median is the target of the explorer's spending-calibrated foundation level. | number |

## Provenance and Method

Raw source workbooks are stored in `raw/` with a download log. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. Original script(s): `80_parse_ma_nss_compliance.py`.

## Data completeness

- Not a town-year panel; completeness section not applicable.
