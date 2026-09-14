# Aggregation check: grade-specific SEDA files vs the pooled annual estimates

District-years compared: 2478 (Connecticut, all students).
The pooled annual estimate is SEDA's GLS/empirical-Bayes pooling over grades and subjects; the reconstruction is the test-count-weighted mean of the grade x subject means minus grade. They should agree closely but not exactly.

- correlation: 0.9931
- mean difference (reconstruction minus pooled): +0.0087 grade levels
- mean absolute difference: 0.0964; 95th percentile: 0.3372; max: 1.6732
- district-years within 0.10 grade levels: 70.5%

- 2023: n=174, corr=0.9920, mean abs diff=0.1361
- 2024: n=177, corr=0.9932, mean abs diff=0.1301
- 2025: n=175, corr=0.9949, mean abs diff=0.1108

Largest gaps:

| sedaadmin | year | from grades | pooled | diff | cells |
|---|---|---|---|---|---|
| 901890 | 2011 | -0.598 | +1.075 | -1.673 | 4 |
| 901890 | 2009 | -0.265 | +1.357 | -1.622 | 2 |
| 900004 | 2009 | -7.200 | -5.683 | -1.516 | 2 |
| 901890 | 2010 | -0.020 | +1.176 | -1.196 | 2 |
| 900221 | 2017 | -0.469 | -1.619 | +1.150 | 6 |
| 901590 | 2018 | -0.481 | +0.545 | -1.026 | 2 |
| 900150 | 2025 | -0.213 | +0.777 | -0.990 | 5 |
| 902940 | 2010 | +0.403 | +1.389 | -0.986 | 4 |
