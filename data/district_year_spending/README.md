# District-year net current expenditures by function

- **Series name:** District-year net current expenditures by function
- **Grain:** one row per district x fiscal_year
- **Year range:** FY2018-FY2025
- **Source:** EdSight Net Current Expenditures by Function; https://edsight.ct.gov/SASStoredProcess/do?_program=/CTDOE/EdSight/Release/Reporting/Public/Reports/StoredProcesses/EFSDistrictLevelbyFunctionExport&_year={YYYY-YY}&_district=All+Districts
- **Row count:** 1,561
- **Column count:** 56

## Codebook

| Column | Definition | Type |
|---|---|---|
| `District` | District name as reported by EdSight. | string |
| `District Code` | EdSight district code. | integer |
| `fiscal_year` | Fiscal year ending in the listed calendar year; FY2025 corresponds to school year 2024-25. | integer |
| `total_expenditures` | Total expenditures. | number |
| `ppe_total` | Per-pupil expenditure in nominal dollars for total. | number |
| `pupils_enrolled_plus_outplaced` | Pupils enrolled plus outplaced. | number |
| `pupils_enrolled_in_district` | Pupils enrolled in district. | number |
| `pupils_transported` | Pupils transported. | number |
| `exp_central_and_other_support_services` | Nominal expenditures in dollars for central and other support services. | number |
| `exp_enterprise_operations` | Nominal expenditures in dollars for enterprise operations. | number |
| `exp_food_services` | Nominal expenditures in dollars for food services. | number |
| `exp_instruction` | Nominal expenditures in dollars for instruction. | number |
| `exp_minor_school_construction` | Nominal expenditures in dollars for minor school construction. | number |
| `exp_operation_and_maintenance_of_plant` | Nominal expenditures in dollars for operation and maintenance of plant. | number |
| `exp_student_transportation_services` | Nominal expenditures in dollars for student transportation services. | number |
| `exp_support_services_general_administration` | Nominal expenditures in dollars for support services general administration. | number |
| `exp_support_services_instruction` | Nominal expenditures in dollars for support services instruction. | number |
| `exp_support_services_school_based_administration` | Nominal expenditures in dollars for support services school based administration. | number |
| `exp_support_services_students` | Nominal expenditures in dollars for support services students. | number |
| `ppe_central_and_other_support_services` | Per-pupil expenditure in nominal dollars for central and other support services. | number |
| `ppe_enterprise_operations` | Per-pupil expenditure in nominal dollars for enterprise operations. | number |
| `ppe_food_services` | Per-pupil expenditure in nominal dollars for food services. | number |
| `ppe_instruction` | Per-pupil expenditure in nominal dollars for instruction. | number |
| `ppe_minor_school_construction` | Per-pupil expenditure in nominal dollars for minor school construction. | number |
| `ppe_operation_and_maintenance_of_plant` | Per-pupil expenditure in nominal dollars for operation and maintenance of plant. | number |
| `ppe_student_transportation_services` | Per-pupil expenditure in nominal dollars for student transportation services. | number |
| `ppe_support_services_general_administration` | Per-pupil expenditure in nominal dollars for support services general administration. | number |
| `ppe_support_services_instruction` | Per-pupil expenditure in nominal dollars for support services instruction. | number |
| `ppe_support_services_school_based_administration` | Per-pupil expenditure in nominal dollars for support services school based administration. | number |
| `ppe_support_services_students` | Per-pupil expenditure in nominal dollars for support services students. | number |
| `cpi_u` | Annual average CPI-U (FRED CPIAUCSL). | number |
| `deflator` | Inflation factor equal to CPI-U in 2025 divided by CPI-U in this year; multiply nominal dollars by this to express them in 2025 dollars. | number |
| `ppe_total_real` | Per-pupil expenditure in 2025 dollars for total. | number |
| `total_expenditures_real` | Total expenditures real. | number |
| `exp_central_and_other_support_services_real` | Expenditures in 2025 dollars for central and other support services. | number |
| `exp_enterprise_operations_real` | Expenditures in 2025 dollars for enterprise operations. | number |
| `exp_food_services_real` | Expenditures in 2025 dollars for food services. | number |
| `exp_instruction_real` | Expenditures in 2025 dollars for instruction. | number |
| `exp_minor_school_construction_real` | Expenditures in 2025 dollars for minor school construction. | number |
| `exp_operation_and_maintenance_of_plant_real` | Expenditures in 2025 dollars for operation and maintenance of plant. | number |
| `exp_student_transportation_services_real` | Expenditures in 2025 dollars for student transportation services. | number |
| `exp_support_services_general_administration_real` | Expenditures in 2025 dollars for support services general administration. | number |
| `exp_support_services_instruction_real` | Expenditures in 2025 dollars for support services instruction. | number |
| `exp_support_services_school_based_administration_real` | Expenditures in 2025 dollars for support services school based administration. | number |
| `exp_support_services_students_real` | Expenditures in 2025 dollars for support services students. | number |
| `ppe_central_and_other_support_services_real` | Per-pupil expenditure in 2025 dollars for central and other support services. | number |
| `ppe_enterprise_operations_real` | Per-pupil expenditure in 2025 dollars for enterprise operations. | number |
| `ppe_food_services_real` | Per-pupil expenditure in 2025 dollars for food services. | number |
| `ppe_instruction_real` | Per-pupil expenditure in 2025 dollars for instruction. | number |
| `ppe_minor_school_construction_real` | Per-pupil expenditure in 2025 dollars for minor school construction. | number |
| `ppe_operation_and_maintenance_of_plant_real` | Per-pupil expenditure in 2025 dollars for operation and maintenance of plant. | number |
| `ppe_student_transportation_services_real` | Per-pupil expenditure in 2025 dollars for student transportation services. | number |
| `ppe_support_services_general_administration_real` | Per-pupil expenditure in 2025 dollars for support services general administration. | number |
| `ppe_support_services_instruction_real` | Per-pupil expenditure in 2025 dollars for support services instruction. | number |
| `ppe_support_services_school_based_administration_real` | Per-pupil expenditure in 2025 dollars for support services school based administration. | number |
| `ppe_support_services_students_real` | Per-pupil expenditure in 2025 dollars for support services students. | number |

## Provenance and Method

Raw scraped files are stored in `raw/`. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. For columns ending in `_real`, nominal dollars are converted to 2025 dollars using the CPI-U deflator from `data/cpi_u_deflator/cpi_u_deflator.csv`: real = nominal x (CPI-U 2025 / CPI-U fiscal/calendar year). Original script(s): `45_download_ppe_by_function_district.py + 01_clean_district.py`.
