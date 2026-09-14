# Town-year ECS payment list

- **Series name:** Town-year ECS payment list
- **Grain:** one row per town x fiscal_year
- **Year range:** FY2026
- **Source:** CSDE Bureau of Fiscal Services ECS April payment list; https://portal.ct.gov/-/media/sde/grants-management/ecsmbr/ecspay_april_excel.xlsx
- **Row count:** 169
- **Column count:** 10

FY2026 ECS payment list by town: entitlement, Alliance District and compensatory-education set-asides, local entitlement, prior local payments and special-education prior-year adjustment. CSDE overwrites this file each payment cycle; the copy here is the April 2026 list.

## Codebook

| Column | Definition | Type |
|---|---|---|
| `town_code` | Connecticut town code, 1-169 (alphabetical); equals the local board of education's CSDE district code. | integer |
| `entitlement` | ECS entitlement, nominal dollars (CSDE; excludes prior-year adjustments). | number |
| `alliance_setaside` | Alliance District set-aside paid to the board of education rather than the town, nominal dollars. | number |
| `comp_ed_setaside` | Compensatory-education ECS set-aside, nominal dollars. | number |
| `local_entitlement` | Entitlement paid to the town: entitlement minus the two set-asides. | number |
| `previous_local_payments` | Local payments made earlier in the fiscal year. | number |
| `sped_prior_year_adjustment` | Special-education prior-year adjustment applied in this payment. | number |
| `town` | Town name. | string |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2026 corresponds to school year 2025-26. | integer |
| `district_code` | Local board of education district code (= town_code). Regional school districts receive no ECS directly. | integer |

## Provenance and Method

Raw source workbooks are stored in `raw/` with a download log. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. Original script(s): `60_download_ecs_csde.py + 64_clean_ecs_csde.py`.

## Data completeness

- **Panel span:** FY2026-FY2026 (169 town-years across 169 towns).
- **Method:** only *interior* gaps are counted as missing -- years before a town first appears or after it last appears are treated as not reported, not as missing data.
- **Town-by-town missing years:** none. Every town is complete across its active span.
