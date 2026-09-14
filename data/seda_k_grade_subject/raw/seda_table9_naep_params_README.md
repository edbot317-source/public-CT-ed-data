# seda_table9_naep_params.csv

Transcription of Table 9, "NAEP Means and Standard Deviations by Year and Grade" (p. 83), from
`SEDA_documentation_2025.2.pdf` (Stanford Education Data Archive 2025.2). SEDA notes these are the
expanded-population estimates, which may differ slightly from the values NAEP reports publicly.

Columns: subject (mth|rla), stat (mean|sd), grade (3-8), year (2007-2019, 2022-2025), value (NAEP scale points).

Used by `code/73_seda_k_and_baselines.py` to compute grade levels per student-level SD exactly as SEDA defines
its CS and GCS scales (documentation Step 7, equations 7.2-7.4): k_{g,b} = SD_{g,b} / growth_b, with SDs and
means averaged over the four reference cohorts that were in 4th grade in 2009, 2011, 2013 and 2015, and
growth_b = (mean grade 8 - mean grade 4) / 4 averaged over those cohorts.
