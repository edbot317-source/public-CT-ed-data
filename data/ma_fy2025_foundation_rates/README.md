# Massachusetts FY2025 Chapter 70 foundation budget rates

- **Series name:** Massachusetts FY2025 Chapter 70 foundation budget rates
- **Grain:** one row per foundation enrollment column
- **Year range:** FY2025
- **Source:** Massachusetts DESE FY2025 Chapter 70 complete formula spreadsheet, Rates sheet; https://www.doe.mass.edu/finance/chapter70/fy2025/ (chapter-2025.xlsm, Rates, parameters and Foundation Budget sheets; downloaded 2026-09-16)
- **Row count:** 24
- **Column count:** 15

DESE's FY2025 per-pupil foundation allotments for the eleven cost categories, one row per enrollment column: the seven grade bands (pre-school and half-day kindergarten at half rates), assumed special-education in-district and tuitioned-out pupils, English learners by band, and the twelve low-income concentration groups. The total and the wage-adjustable part of each row are what the simulation uses. Copied from the state's workbook without change; the parsed Plymouth example in DESE's white paper reproduces to the dollar.

## Codebook

| Column | Definition | Type |
|---|---|---|
| `column` | Foundation enrollment column: pk, k_half, k_full, el, ms, hs, voc, sped_in, sped_out, el_pk5, el_68, el_hs, li_1 .. li_12. | string |
| `label` | DESE's label for the enrollment column. | string |
| `Adminis-tration` | Adminis-tration | number |
| `Instructional Leadership` | Instructional Leadership | number |
| `Classroom & Specialist Teachers` | Classroom & Specialist Teachers | number |
| `Other Teaching Services` | Other Teaching Services | number |
| `Professional Development` | Professional Development | number |
| `Instructional Materials, Equipment & Technology` | Instructional Materials, Equipment & Technology | number |
| `Guidance & Psychological Services` | Guidance & Psychological Services | number |
| `Pupil Services` | Pupil Services | number |
| `Operations & Maintenance` | Operations & Maintenance | number |
| `Employee Benefits/Fixed Charges` | Employee Benefits/Fixed Charges | number |
| `Special Education Tuition` | Special Education Tuition | number |
| `total` | Total FY2025 foundation allotment per pupil across the eleven categories, dollars. | number |
| `waf_applicable` | Part of the total to which the wage adjustment factor applies (all categories except instructional materials, employee benefits and special-education tuition), dollars. | number |

## Provenance and Method

Raw source workbooks are stored in `raw/` with a download log. The build script replays the original numbered cleaner from `raw/original_scripts/` in a temporary local layout and writes this formatted CSV. Original script(s): `79_build_ma_inputs.py`.

## Data completeness

- Not a town-year panel; completeness section not applicable.
