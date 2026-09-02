# District-year accountability and growth metrics

- **Series name:** District-year accountability and growth metrics
- **Grain:** one row per district x fiscal_year
- **Year range:** FY2025
- **Source:** EdSight Next Generation Accountability and Smarter Balanced Growth Model; https://edsight.ct.gov/SASStoredProcess/do? Next Generation Accountability / Growth Model exports for 2024-25; see raw filenames
- **Row count:** 199
- **Column count:** 6

## Codebook

| Column | Definition | Type |
|---|---|---|
| `District` | District name as reported by EdSight. | string |
| `District Code` | EdSight district code. | integer |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2025 corresponds to school year 2024-25. | integer |
| `ela_growth` | Ela growth. | number |
| `math_growth` | Math growth. | number |
| `accountability_index` | Accountability index. | number |

## Provenance and Method

Raw scraped files are stored in `raw/`. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. Original script(s): `34_download_accountability.py + 35_clean_accountability.py`.
