# District-year revenue sources

- **Series name:** District-year revenue sources
- **Grain:** one row per district x fiscal_year
- **Year range:** FY2018-FY2025
- **Source:** EdSight Revenues; https://edsight.ct.gov/SASStoredProcess/do?_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/RevenueSourceExport&_year={YYYY-YY}&_district=All+Districts&_schoolconstr=All
- **Row count:** 1,561
- **Column count:** 12

## Codebook

| Column | Definition | Type |
|---|---|---|
| `District` | District name as reported by EdSight. | string |
| `District Code` | EdSight district code. | integer |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2025 corresponds to school year 2024-25. | integer |
| `rev_local` | Nominal revenue dollars: local. | number |
| `rev_state` | Nominal revenue dollars: state. | number |
| `rev_federal` | Nominal revenue dollars: federal. | number |
| `rev_tuition_other` | Nominal revenue dollars: tuition other. | number |
| `rev_total` | Nominal revenue dollars: total. | number |
| `pct_local` | Percent/share measure: local. | number |
| `pct_state` | Percent/share measure: state. | number |
| `pct_federal` | Percent/share measure: federal. | number |
| `pct_tuition_other` | Percent/share measure: tuition other. | number |

## Provenance and Method

Raw scraped files are stored in `raw/`. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. Original script(s): `48_download_revenue_sources.py + 04_clean_revenue.py`.
