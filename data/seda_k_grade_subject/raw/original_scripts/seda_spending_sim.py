"""
seda_spending_sim.py -- core mapping from a per-pupil operating-spending change to
predicted SEDA test-score changes, per the instructions in
ct_seda_simulation_instructions.md (Jackson & Mackevicius 2024, AEJ: Applied 16(1), Table 3).

Units: beta is student-level SD per $1,000 per pupil (2018$) sustained for four years.
All functions are pure; CONFIG is the single source of parameters.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

CONFIG = {
    # Jackson & Mackevicius (2024) Table 3 col 2, constant term: NONCAPITAL (operational) marginal effect.
    "beta": 0.0343, "beta_se": 0.00681, "beta_tau": 0.0211,
    # headline pooled estimate (col 1) -- NOT used, recorded for reference
    "beta_pooled_reference": 0.0316,
    # Table 3 col 3: income heterogeneity (student-level SD per $1,000, 4 years)
    "beta_low_income": 0.0312, "beta_non_low_income": 0.0161, "beta_col3_constant": 0.0359,
    # exposure: linear ramp to 4 years, flat thereafter (user assumption)
    "dose_years": 4,
    # grade levels per student-level SD: k_{g,b} = SD_{g,b} / growth_b from SEDA's published NAEP parameters
    # (SEDA 2025.2 documentation Table 9, eqs 7.2-7.4); fallback 3.0 (the documentation's rule of thumb)
    "k_fallback": 3.0,
    # SEDA reference cohorts: in 4th grade in 2009, 2011, 2013, 2015 -> kindergarten springs
    "seda_reference_cohorts_k_year": [2005, 2007, 2009, 2011],
    # dollars: shock expressed in 2018$ via CPI-U annual averages (CPIAUCSL from FRED)
    "dollar_base_year": 2018,
    "grades": [3, 4, 5, 6, 7, 8], "subjects": ["mth", "rla"],
}


def exposure_years(policy_year: int, grade: int) -> int:
    """Years a student tested in `grade` in policy year t (t=1 is the first policy year)
    has been exposed, assuming no churn since kindergarten: min(t, grade + 1)."""
    if policy_year < 1:
        return 0
    return int(min(policy_year, grade + 1))


def dose(exposure: float, dose_years: int = CONFIG["dose_years"]) -> float:
    """Linear in exposure up to `dose_years`, flat thereafter."""
    return float(min(max(exposure, 0), dose_years)) / dose_years


def effect_sd(delta_dollars_2018: float, exposure: float, beta: float = CONFIG["beta"]) -> float:
    """Student-level SD effect of a constant per-pupil operating increase (2018$)."""
    return beta * (delta_dollars_2018 / 1000.0) * dose(exposure)


def effect_sd_path(delta_path_2018: list[float], policy_year: int, grade: int, beta: float = CONFIG["beta"]) -> float:
    """Same mapping when the per-pupil increase varies by year (e.g. a phase-in).
    delta_path_2018[i] is the increase in policy year i+1. A student's dose is the sum of
    1/dose_years per exposed year, so the effect is beta/dose_years x sum over the last
    min(exposure, dose_years) policy years of (delta/1000). With a constant delta this
    equals effect_sd()."""
    e = exposure_years(policy_year, grade)
    n = int(min(e, CONFIG["dose_years"]))
    if n <= 0:
        return 0.0
    window = delta_path_2018[policy_year - n:policy_year]
    return beta / CONFIG["dose_years"] * sum(d / 1000.0 for d in window)


def deflate_to_base(nominal: float, year: int, cpi: dict, base_year: int = CONFIG["dollar_base_year"]) -> float:
    """Nominal dollars of calendar/fiscal `year` -> base-year dollars using CPI-U annual averages."""
    y = min(year, max(cpi))
    return nominal * cpi[base_year] / cpi[y]


def income_multiplier(share_low_income: float) -> float:
    """Option A district multiplier: beta_d = beta x [s*(0.0312/0.0359) + (1-s)*(0.0161/0.0359)]."""
    c = CONFIG
    return share_low_income * (c["beta_low_income"] / c["beta_col3_constant"]) + \
        (1 - share_low_income) * (c["beta_non_low_income"] / c["beta_col3_constant"])


def k_from_naep_params(params: pd.DataFrame, cohorts=None) -> pd.DataFrame:
    """k_{g,b} directly from SEDA's scale definitions (SEDA 2025.2 documentation, Step 7).

    CS_{g,b}  = (NAEP - mean_{g,b}) / sd_{g,b}                                             (eq. 7.2)
    GCS_{g,b} = 4 + (NAEP - mean_{4,b}) / growth_b,  growth_b = (mean_{8,b} - mean_{4,b}) / 4   (eqs. 7.3-7.4)
    so one CS unit (one student-level SD) equals sd_{g,b} / growth_b grade levels. Means and SDs are the
    national NAEP values averaged over the four reference cohorts (in 4th grade in 2009, 2011, 2013, 2015);
    a cohort with kindergarten spring c is in grade g in year c + g. `params` is the transcription of Table 9
    with columns subject, stat (mean|sd), grade, year, value."""
    cohorts = cohorts or CONFIG["seda_reference_cohorts_k_year"]
    P = params.pivot_table(index=["subject", "stat", "grade"], columns="year", values="value")
    rows = []
    for b in CONFIG["subjects"]:
        growth = np.mean([P.loc[(b, "mean", 8), c + 8] - P.loc[(b, "mean", 4), c + 4] for c in cohorts]) / 4
        for g in CONFIG["grades"]:
            sd = np.mean([P.loc[(b, "sd", g), c + g] for c in cohorts])
            mn = np.mean([P.loc[(b, "mean", g), c + g] for c in cohorts])
            rows.append({"grade": g, "subject": b, "k": sd / growth, "naep_mean_ref": mn, "naep_sd_ref": sd, "naep_growth_per_grade": growth})
    return pd.DataFrame(rows)


def estimate_k(gcs: pd.DataFrame, cs: pd.DataFrame, years=None) -> pd.DataFrame:
    """Cross-check for k_from_naep_params: k_{g,b} = slope of GCS on CS across districts within grade x
    subject x year, averaged over years (should reproduce the documented ratio, since both scales are linear
    transformations of the same NAEP-linked means). Inputs: national long files (all-student columns) with columns
    sedaadmin, subject, grade, year, gcs_mn_all / cs_mn_all."""
    m = gcs.merge(cs, on=["sedaadmin", "subject", "grade", "year"], suffixes=("", "_cs"))
    m = m.dropna(subset=["gcs_mn_all", "cs_mn_all"])
    if years is not None:
        m = m[m.year.isin(years)]
    rows = []
    for (g, b, y), d in m.groupby(["grade", "subject", "year"]):
        x = d["cs_mn_all"].to_numpy(float); z = d["gcs_mn_all"].to_numpy(float)
        if len(d) < 30:
            continue
        slope = np.polyfit(x, z, 1)[0]
        rows.append({"grade": g, "subject": b, "year": y, "k": slope, "n_districts": len(d)})
    per = pd.DataFrame(rows)
    k = per.groupby(["grade", "subject"], as_index=False).agg(k=("k", "mean"), k_min=("k", "min"), k_max=("k", "max"), years=("year", "nunique"))
    k["flag"] = ~k["k"].between(2.5, 3.5)
    return k, per


def simulate(baseline: pd.DataFrame, shock: pd.DataFrame, k: pd.DataFrame, start_year: int,
             beta: float = CONFIG["beta"], multiplier: pd.Series | None = None) -> pd.DataFrame:
    """
    baseline: one row per (town_code, grade, subject) with gcs_baseline, n_tests.
    shock:    one row per (town_code, fiscal_year) with delta_2018 (per-pupil operating change, 2018$);
              fiscal_year >= start_year are policy years 1, 2, ...
    k:        (grade, subject, k).
    multiplier: optional Series indexed by town_code (Option A income heterogeneity).
    Returns one row per (town_code, grade, subject, fiscal_year) with exposure, delta_sd, delta_gcs, simulated gcs.
    """
    shock = shock[shock.fiscal_year >= start_year].sort_values(["town_code", "fiscal_year"])
    paths = {tc: d.sort_values("fiscal_year") for tc, d in shock.groupby("town_code")}
    kmap = {(r.grade, r.subject): r.k for r in k.itertuples()}
    out = []
    for tc, path in paths.items():
        years = path.fiscal_year.tolist(); deltas = path.delta_2018.tolist()
        b_d = beta * (multiplier.get(tc, 1.0) if multiplier is not None else 1.0)
        base = baseline[baseline.town_code == tc]
        for t_idx, fy in enumerate(years, start=1):
            for r in base.itertuples():
                e = exposure_years(t_idx, int(r.grade))
                dsd = effect_sd_path(deltas, t_idx, int(r.grade), b_d)
                kk = kmap.get((int(r.grade), r.subject), CONFIG["k_fallback"])
                out.append({"town_code": tc, "grade": int(r.grade), "subject": r.subject, "fiscal_year": fy,
                            "policy_year": t_idx, "delta_2018": deltas[t_idx - 1], "exposure": e,
                            "delta_sd": dsd, "delta_gcs": dsd * kk, "k": kk,
                            "gcs_baseline": r.gcs_baseline, "gcs_simulated": r.gcs_baseline + dsd * kk,
                            "n_tests": r.n_tests})
    return pd.DataFrame(out)


# ---------------------------------------------------------------- unit tests
def _tests():
    assert exposure_years(1, 3) == 1 and exposure_years(3, 8) == 3 and exposure_years(6, 3) == 4 and exposure_years(10, 8) == 9
    assert abs(effect_sd(1000, 4) - 0.0343) < 1e-12, "4+ years at $1,000 must equal beta"
    assert abs(effect_sd(1000, 2) - 0.01715) < 1e-12
    assert effect_sd(1000, 6) == effect_sd(1000, 4), "no growth after 4 years"
    assert abs(effect_sd_path([1000] * 6, 6, 8) - 0.0343) < 1e-12
    assert abs(effect_sd_path([1000, 1000], 2, 5) - 0.01715) < 1e-12
    cpi = {2018: 251.107, 2023: 304.702, 2025: 320.0}
    assert abs(deflate_to_base(304.702, 2023, cpi) - 251.107) < 1e-9
    assert abs(deflate_to_base(100, 2027, cpi) - 100 * 251.107 / 320.0) < 1e-9, "years past the last CPI use the last CPI"
    assert abs(income_multiplier(1.0) - 0.0312 / 0.0359) < 1e-12 and abs(income_multiplier(0.0) - 0.0161 / 0.0359) < 1e-12
    print("seda_spending_sim: all unit tests pass")


if __name__ == "__main__":
    _tests()
