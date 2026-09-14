"""
73_seda_k_and_baselines.py

From the SEDA long files (72):
  1. k_{g,b}, grade levels per student-level SD, taken directly from SEDA's scale definitions:
     k = SD_{g,b} / growth_b using the national NAEP means and SDs SEDA publishes in Table 9 of the
     2025.2 documentation (transcribed to data/seda/seda_table9_naep_params.csv), averaged over the
     four reference cohorts (4th grade in 2009/11/13/15). Cross-checked against the slope of GCS on CS
     across ALL U.S. districts within grade x subject x year (flag if the two differ by > 0.05).
  2. Build Connecticut grade-specific baselines: mean GCS by town x grade x subject averaged over
     spring 2023-2025 (post-2019 years included; logged), with test counts as weights, mapped to
     towns the same way as 71 (local board by name; K-12 regional districts to member towns).
  3. Aggregation check: the test-weighted mean over grades and subjects of (gcs_mn_all - grade)
     from the long file, per district-year, against the pooled annual estimate
     (gcs_mn_avg_eb - 5.5) used elsewhere on the dashboard.

Outputs:
    clean-data/seda_k_grade_subject.csv
    clean-data/town_grade_subject_seda_baseline.csv
    output/ecs/sim/k_by_year.csv, output/ecs/sim/aggregation_check.md
"""

import os
import sys

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "seda")
CLEAN = os.path.join(BASE, "clean-data")
OUTD = os.path.join(BASE, "output", "ecs", "sim")
os.makedirs(OUTD, exist_ok=True)
sys.path.insert(0, os.path.join(BASE, "output", "ecs", "dashboard", "sim"))
from seda_spending_sim import estimate_k, k_from_naep_params  # noqa: E402

BASELINE_YEARS = [2023, 2024, 2025]

# same town mapping as 71
REGIONAL_K12 = {
    "Regional School District 10": ["Burlington", "Harwinton"],
    "Regional School District 12": ["Bridgewater", "Roxbury", "Washington"],
    "Regional School District 13": ["Durham", "Middlefield"],
    "Regional School District 14": ["Bethlehem", "Woodbury"],
    "Regional School District 15": ["Middlebury", "Southbury"],
    "Regional School District 16": ["Beacon Falls", "Prospect"],
    "Regional School District 17": ["Haddam", "Killingworth"],
    "Regional School District 18": ["Lyme", "Old Lyme"],
    "Regional School District 20": ["Goshen", "Litchfield", "Morris", "Warren"],
    "Regional School District 06": ["Goshen", "Morris", "Warren"],
}
REGION_YEARS = {"Regional School District 06": (None, 2024), "Regional School District 20": (2025, None)}


def town_map(names_df, towns):
    name_to_code = dict(zip(towns.town, towns.town_code))
    rows = []
    for r in names_df.itertuples():
        name = r.sedaadminname
        local = name.replace(" School District", "") if name.endswith(" School District") else None
        if local in name_to_code:
            rows.append((r.sedaadmin, name_to_code[local], local, "local district", None, None))
        elif name in REGIONAL_K12:
            lo, hi = REGION_YEARS.get(name, (None, None))
            for t in REGIONAL_K12[name]:
                rows.append((r.sedaadmin, name_to_code[t], t, "regional district", lo, hi))
    return pd.DataFrame(rows, columns=["sedaadmin", "town_code", "town", "town_match", "yr_from", "yr_to"])


def main():
    # ---- 1. k from SEDA's published scale parameters, cross-checked against the national GCS-on-CS slope
    params = pd.read_csv(os.path.join(RAW, "seda_table9_naep_params.csv"))
    k = k_from_naep_params(params)
    nat_g, nat_c = (os.path.join(RAW, f"seda_admindist_long_{s}_2025.2_national_all.csv") for s in ("gcs", "cs"))
    if os.path.exists(nat_g) and os.path.exists(nat_c):
        g = pd.read_csv(nat_g)
        c = pd.read_csv(nat_c)
        kr, per = estimate_k(g[["sedaadmin", "subject", "grade", "year", "gcs_mn_all"]], c[["sedaadmin", "subject", "grade", "year", "cs_mn_all"]])
    else:
        # the national long files are ~119 MB each and are not redistributed; fall back to the logged per-year slopes
        per = pd.read_csv(os.path.join(OUTD, "k_by_year.csv"))
        kr = per.groupby(["grade", "subject"], as_index=False).agg(k=("k", "mean"), k_min=("k", "min"), k_max=("k", "max"), years=("year", "nunique"))
        kr["flag"] = ~kr["k"].between(2.5, 3.5)
        print("[k] national long files not present; regression cross-check read from output/ecs/sim/k_by_year.csv")
    kr = kr.rename(columns={"k": "k_regression", "k_min": "k_regression_min", "k_max": "k_regression_max", "years": "regression_years"}).drop(columns="flag")
    k = k.merge(kr, on=["grade", "subject"], how="left")
    k["flag"] = (k.k - k.k_regression).abs() > 0.05
    k = k[["subject", "grade", "k", "naep_mean_ref", "naep_sd_ref", "naep_growth_per_grade", "k_regression", "k_regression_min", "k_regression_max", "regression_years", "flag"]]
    k.to_csv(os.path.join(CLEAN, "seda_k_grade_subject.csv"), index=False)
    per.to_csv(os.path.join(OUTD, "k_by_year.csv"), index=False)
    print("[k] grade levels per SD = NAEP SD / per-grade NAEP growth (SEDA 2025.2 doc Table 9), vs GCS-on-CS slope:")
    print(k.to_string(index=False))
    print(f"  mean k = {k.k.mean():.3f} (regression {k.k_regression.mean():.3f}); max |diff| = {(k.k - k.k_regression).abs().max():.4f}; flagged: {int(k.flag.sum())}")

    # ---- 2. CT grade-specific baselines
    ct = pd.read_csv(os.path.join(RAW, "seda_admindist_long_gcs_2025.2_CT.csv"))
    ct = ct[["sedaadmin", "sedaadminname", "subject", "grade", "year", "tot_asmt_all", "gcs_mn_all", "gcs_mn_se_all"]].dropna(subset=["gcs_mn_all"])
    towns = pd.read_csv(os.path.join(CLEAN, "town_year_ecs_inputs.csv"))[["town_code", "town"]].drop_duplicates()
    m = town_map(ct.drop_duplicates(["sedaadmin", "sedaadminname"]), towns)
    x = ct.merge(m, on="sedaadmin", how="inner")
    for col in ("yr_from", "yr_to"):
        x[col] = pd.to_numeric(x[col], errors="coerce")
    ok = (x.yr_from.isna() | (x.year >= x.yr_from)) & (x.yr_to.isna() | (x.year <= x.yr_to))
    x = x[ok]
    # local board wins over region if both exist for a town-year-grade-subject
    x["pri"] = (x.town_match == "local district").astype(int)
    x = x.sort_values("pri", ascending=False).drop_duplicates(["town_code", "year", "grade", "subject"])
    b = x[x.year.isin(BASELINE_YEARS)].copy()
    b["vs_national"] = b["gcs_mn_all"] - b["grade"]
    base = (b.groupby(["town_code", "town", "grade", "subject"])
             .agg(gcs_baseline=("gcs_mn_all", "mean"), vs_national_baseline=("vs_national", "mean"),
                  n_tests=("tot_asmt_all", "mean"), years_used=("year", "nunique"), town_match=("town_match", "first"),
                  sedaadmin=("sedaadmin", "first"))
             .reset_index())
    base.to_csv(os.path.join(CLEAN, "town_grade_subject_seda_baseline.csv"), index=False)
    print(f"[baseline] {len(base)} town-grade-subject rows for {base.town_code.nunique()} towns, years {BASELINE_YEARS}; "
          f"{(base.years_used < 3).sum()} rows with fewer than 3 years")

    # ---- 3. aggregation check vs the pooled annual file
    ann = pd.read_csv(os.path.join(CLEAN, "district_year_seda_gcs.csv"))
    ann = ann[(ann.subgroup == "all")][["sedaadmin", "fiscal_year", "grade_levels_vs_national", "tot_asmts"]]
    lg = ct.copy(); lg["vs"] = lg.gcs_mn_all - lg.grade
    agg = (lg.assign(w=lg.tot_asmt_all * lg.vs).groupby(["sedaadmin", "year"])
             .agg(w=("w", "sum"), n=("tot_asmt_all", "sum"), cells=("vs", "size")).reset_index())
    agg["vs_from_grades"] = agg.w / agg.n
    chk = agg.merge(ann, left_on=["sedaadmin", "year"], right_on=["sedaadmin", "fiscal_year"])
    chk["diff"] = chk.vs_from_grades - chk.grade_levels_vs_national
    lines = ["# Aggregation check: grade-specific SEDA files vs the pooled annual estimates", "",
             f"District-years compared: {len(chk)} (Connecticut, all students).",
             "The pooled annual estimate is SEDA's GLS/empirical-Bayes pooling over grades and subjects; the reconstruction "
             "is the test-count-weighted mean of the grade x subject means minus grade. They should agree closely but not exactly.", "",
             f"- correlation: {chk.vs_from_grades.corr(chk.grade_levels_vs_national):.4f}",
             f"- mean difference (reconstruction minus pooled): {chk['diff'].mean():+.4f} grade levels",
             f"- mean absolute difference: {chk['diff'].abs().mean():.4f}; 95th percentile: {chk['diff'].abs().quantile(.95):.4f}; max: {chk['diff'].abs().max():.4f}",
             f"- district-years within 0.10 grade levels: {(chk['diff'].abs() <= 0.10).mean():.1%}", ""]
    for fy in BASELINE_YEARS:
        d = chk[chk.year == fy]
        lines.append(f"- {fy}: n={len(d)}, corr={d.vs_from_grades.corr(d.grade_levels_vs_national):.4f}, mean abs diff={d['diff'].abs().mean():.4f}")
    worst = chk.reindex(chk["diff"].abs().sort_values(ascending=False).index).head(8)
    lines += ["", "Largest gaps:", "", "| sedaadmin | year | from grades | pooled | diff | cells |", "|---|---|---|---|---|---|"]
    lines += [f"| {r.sedaadmin} | {r.year} | {r.vs_from_grades:+.3f} | {r.grade_levels_vs_national:+.3f} | {r.diff:+.3f} | {r.cells} |" for r in worst.itertuples()]
    open(os.path.join(OUTD, "aggregation_check.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines[:9]))


if __name__ == "__main__":
    main()
