# Town-year ECS entitlements

- **Series name:** Town-year ECS entitlements
- **Grain:** one row per town x fiscal_year
- **Year range:** FY2001-FY2027
- **Source:** CSDE Bureau of Fiscal Services ECS entitlement and Alliance/non-Alliance breakout spreadsheets; https://portal.ct.gov/-/media/sde/grants-management/ecsmbr/ecsentit_excel.xlsx; https://portal.ct.gov/-/media/sde/grants-management/ecsmbr/ecs-alliance-nonalliance_excel.xlsx; https://portal.ct.gov/-/media/sde/grants-management/ecsmbr/ecspay_april_excel.xlsx
- **Row count:** 4,563
- **Column count:** 8

Education Cost Sharing (ECS) grant entitlements by town, FY2001-FY2027, as published by the Connecticut State Department of Education, with the Alliance District / Education Diversity / non-Alliance split where published (FY2012+). ECS is the state's main equalization grant to towns; the town code equals the local board of education's district code.

## Codebook

| Column | Definition | Type |
|---|---|---|
| `town_code` | Connecticut town code, 1-169 (alphabetical); equals the local board of education's CSDE district code. | integer |
| `district_code` | Local board of education district code (= town_code). Regional school districts receive no ECS directly. | integer |
| `town` | Town name. | string |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2026 corresponds to school year 2025-26. | integer |
| `entitlement` | ECS entitlement, nominal dollars (CSDE; excludes prior-year adjustments). | number |
| `alliance_portion` | Alliance District portion of the entitlement, nominal dollars (FY2012+). | number |
| `education_diversity_portion` | Education Diversity portion of the entitlement, nominal dollars (FY2025+). | number |
| `non_alliance_portion` | Non-Alliance portion of the entitlement, nominal dollars (FY2012+). | number |

## Provenance and Method

Raw source workbooks are stored in `raw/` with a download log. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. Original script(s): `60_download_ecs_csde.py + 64_clean_ecs_csde.py`.

## Data completeness

- **Panel span:** FY2001-FY2027 (4563 town-years across 169 towns).
- **Method:** only *interior* gaps are counted as missing -- years before a town first appears or after it last appears are treated as not reported, not as missing data.
- **Town-by-town missing years:** none. Every town is complete across its active span.
