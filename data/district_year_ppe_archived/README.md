# Archived district-year per-pupil expenditures by function

- **Series name:** Archived district-year per-pupil expenditures by function
- **Grain:** one row per district x fiscal_year
- **Year range:** FY2007-FY2017
- **Source:** EdSight archived Per Pupil Expenditures; https://edsight.ct.gov/SASStoredProcess/do?_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/PerPupilExport&_year={YYYY-YY}&_district=All+Districts
- **Row count:** 2,029
- **Column count:** 12

## Codebook

| Column | Definition | Type |
|---|---|---|
| `District` | District name as reported by EdSight. | string |
| `ppe_instructional_staff` | Per-pupil expenditure in nominal dollars for instructional staff. | integer |
| `ppe_instructional_supplies` | Per-pupil expenditure in nominal dollars for instructional supplies. | integer |
| `ppe_instruction_media` | Per-pupil expenditure in nominal dollars for instruction media. | integer |
| `ppe_student_support` | Per-pupil expenditure in nominal dollars for student support. | integer |
| `ppe_admin_support` | Per-pupil expenditure in nominal dollars for admin support. | integer |
| `ppe_plant` | Per-pupil expenditure in nominal dollars for plant. | integer |
| `ppe_transportation` | Per-pupil expenditure in nominal dollars for transportation. | number |
| `ppe_other` | Per-pupil expenditure in nominal dollars for other. | integer |
| `ppe_total` | Per-pupil expenditure in nominal dollars for total. | integer |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2025 corresponds to school year 2024-25. | integer |
| `District Code` | EdSight district code. | number |

## Provenance and Method

Raw scraped files are stored in `raw/`. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. Original script(s): `09_download_archived_ppe.py + 10_clean_archived_ppe.py`.
