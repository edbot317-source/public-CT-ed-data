# Massachusetts Chapter 70 formula parameters (FY2025)

- **Series name:** Massachusetts Chapter 70 formula parameters (FY2025)
- **Grain:** one row per parameter
- **Year range:** FY2025
- **Source:** Massachusetts DESE FY2025 Chapter 70 formula spreadsheet (parameters and Foundation Budget sheets); MGL c.70 s.2; https://www.doe.mass.edu/finance/chapter70/fy2025/ (chapter-2025.xlsm, Rates, parameters and Foundation Budget sheets; downloaded 2026-09-16)
- **Row count:** 14
- **Column count:** 3

The scalar and list parameters of the Chapter 70 rule as applied in FY2025: low-income group thresholds, assumed special-education shares, the 0.5 weight for pre-K and half-day kindergarten, the 59% statewide local share, the 82.5% contribution cap and the 175% combined-effort-yield test, the effort thresholds and increments, the 100% effort reduction, the $104 minimum aid per pupil, the 4.5% inflation cap and the wage-adjustment rule, each with its source.

## Codebook

| Column | Definition | Type |
|---|---|---|
| `parameter` | Parameter name. | string |
| `value` | Parameter value (number or comma-separated list). | string |
| `source` | File the row was parsed from (CSDE current-year workbook, or an archived annual PDF). | string |

## Provenance and Method

Raw source workbooks are stored in `raw/` with a download log. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. Original script(s): `79_build_ma_inputs.py`.

## Data completeness

- Not a town-year panel; completeness section not applicable.
