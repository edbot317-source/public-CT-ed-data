# CPI-U annual average deflator

- **Series name:** CPI-U annual average deflator
- **Grain:** one row per calendar year
- **Year range:** 2006-2025
- **Source:** FRED CPIAUCSL; https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL&fq=Annual&fam=avg&cosd=2006-01-01
- **Row count:** 20
- **Column count:** 4

## Codebook

| Column | Definition | Type |
|---|---|---|
| `year` | Calendar year. | year |
| `observation_date` | FRED observation date for the annual CPI-U value. | string |
| `cpi_u` | Annual average CPI-U (FRED CPIAUCSL). | number |
| `deflator` | Inflation factor equal to CPI-U in 2025 divided by CPI-U in this year; multiply nominal dollars by this to express them in 2025 dollars. | number |

## Provenance and Method

Raw scraped files are stored in `raw/`. The build script stacks and tidies the copied per-year raw exports in `raw/`. Original script(s): `50_download_cpi_fred.py`.
