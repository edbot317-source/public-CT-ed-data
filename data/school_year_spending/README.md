# School-year net current expenditures by function

- **Series name:** School-year net current expenditures by function
- **Grain:** one row per school x fiscal_year
- **Year range:** FY2018-FY2025
- **Source:** EdSight Net Current Expenditures by Function, school level; https://edsight.ct.gov/SASStoredProcess/do?_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/EFSSchoolLevelbyFunctionExport&_year={YYYY-YY}&_district=All+Districts&_school=All+Schools
- **Row count:** 7,948
- **Column count:** 33

## Codebook

| Column | Definition | Type |
|---|---|---|
| `district` | District name as reported by EdSight. | string |
| `district_code` | EdSight district code. | integer |
| `school` | School name as reported by EdSight. | string |
| `school_code` | EdSight school code. | integer |
| `low_grade` | Lowest/highest grade span reported for the school. | string |
| `high_grade` | Lowest/highest grade span reported for the school. | string |
| `enrollment` | Enrollment count. | integer |
| `pct_high_needs` | Percent/share measure: high needs. | number |
| `ppe_instruction` | Per-pupil expenditure in nominal dollars for instruction. | integer |
| `ppe_support_services_students` | Per-pupil expenditure in nominal dollars for support services students. | integer |
| `ppe_improvement_of_instruction` | Per-pupil expenditure in nominal dollars for improvement of instruction. | integer |
| `ppe_library_and_media_services` | Per-pupil expenditure in nominal dollars for library and media services. | integer |
| `ppe_support_services_instruction` | Per-pupil expenditure in nominal dollars for support services instruction. | integer |
| `ppe_support_services_school_based_administration` | Per-pupil expenditure in nominal dollars for support services school based administration. | integer |
| `ppe_operation_and_maintenance_of_plant` | Per-pupil expenditure in nominal dollars for operation and maintenance of plant. | integer |
| `ppe_transportation_other_than_to_from_home` | Per-pupil expenditure in nominal dollars for transportation other than to from home. | integer |
| `ppe_enterprise_operations` | Per-pupil expenditure in nominal dollars for enterprise operations. | integer |
| `ppe_minor_school_construction` | Per-pupil expenditure in nominal dollars for minor school construction. | number |
| `ppe_total` | Per-pupil expenditure in nominal dollars for total. | integer |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2025 corresponds to school year 2024-25. | integer |
| `cpi_u` | Annual average CPI-U (FRED CPIAUCSL). | number |
| `deflator` | Inflation factor equal to CPI-U in 2025 divided by CPI-U in this year; multiply nominal dollars by this to express them in 2025 dollars. | number |
| `ppe_instruction_real` | Per-pupil expenditure in 2025 dollars for instruction. | number |
| `ppe_support_services_students_real` | Per-pupil expenditure in 2025 dollars for support services students. | number |
| `ppe_improvement_of_instruction_real` | Per-pupil expenditure in 2025 dollars for improvement of instruction. | number |
| `ppe_library_and_media_services_real` | Per-pupil expenditure in 2025 dollars for library and media services. | number |
| `ppe_support_services_instruction_real` | Per-pupil expenditure in 2025 dollars for support services instruction. | number |
| `ppe_support_services_school_based_administration_real` | Per-pupil expenditure in 2025 dollars for support services school based administration. | number |
| `ppe_operation_and_maintenance_of_plant_real` | Per-pupil expenditure in 2025 dollars for operation and maintenance of plant. | number |
| `ppe_transportation_other_than_to_from_home_real` | Per-pupil expenditure in 2025 dollars for transportation other than to from home. | number |
| `ppe_enterprise_operations_real` | Per-pupil expenditure in 2025 dollars for enterprise operations. | number |
| `ppe_minor_school_construction_real` | Per-pupil expenditure in 2025 dollars for minor school construction. | number |
| `ppe_total_real` | Per-pupil expenditure in 2025 dollars for total. | number |

## Provenance and Method

Raw scraped files are stored in `raw/`. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. For columns ending in `_real`, nominal dollars are converted to 2025 dollars using the CPI-U deflator from `data/cpi_u_deflator/cpi_u_deflator.csv`: real = nominal x (CPI-U 2025 / CPI-U fiscal/calendar year). Original script(s): `46_download_ppe_by_function_school.py + 02_clean_school.py`.
