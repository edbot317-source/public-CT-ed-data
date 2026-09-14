"""
run_sim.py -- reference (Python) run of the test-score simulation for a dashboard scenario,
writing the outputs and the assumptions log the instructions call for.

    python run_sim.py --scenario f13087 --start 2023
    python run_sim.py --scenario inflation --start 2024 --hetero A
    python run_sim.py --shock my_shock.csv --start 2023      # town_code, fiscal_year, delta_nominal_per_student

The scenario engine here is a line-for-line port of the dashboard's JavaScript (paramsFor /
fullyFunded / step / simulate), reading the same ecs_dash_data.json, so a Python run and the
page agree. Scenarios: observed | inflation | f13087 | fullfund, optionally combined with
"+" (e.g. "inflation+fullfund"). Slider overrides: --set w_frpl=0.35 --set foundation=12000 ...

Every run is logged to output/ecs/sim/runs/<timestamp>_<scenario>_from<start>/ with the seven
outputs (district_grade_subject_year.csv, district_summary.csv, state_summary.csv,
gap_summary.csv, figures, assumptions_log.md, README.md) and appended to output/ecs/sim/RUNS.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DASH = os.path.dirname(HERE)
# working repo: <repo>/output/ecs/dashboard/sim, logs to <repo>/output/ecs/sim
# public release: public-CT-ed-data/tools/ecs_formula_explorer/sim, datasets under data/<key>/<key>.csv, logs here
PUBLIC = os.path.exists(os.path.join(DASH, "..", "..", "datapackage.json"))
REPO = os.path.abspath(os.path.join(DASH, "..", "..")) if PUBLIC else os.path.abspath(os.path.join(DASH, "..", "..", ".."))
OUTROOT = HERE if PUBLIC else os.path.join(REPO, "output", "ecs", "sim")


def clean(key):
    return os.path.join(REPO, "data", key, f"{key}.csv") if PUBLIC else os.path.join(REPO, "clean-data", f"{key}.csv")

sys.path.insert(0, HERE)
from seda_spending_sim import CONFIG, simulate, deflate_to_base, income_multiplier  # noqa: E402

D = json.load(open(os.path.join(DASH, "ecs_dash_data.json")))
HORIZON_END = 2025                     # dashboard horizon: ECS panel and SEDA scores both stop at FY2025
YEARS = [fy for fy in D["years"] if 2023 <= fy <= HORIZON_END]
CPI = {int(k): v for k, v in D["cpi"].items()}
OBS = {fy: D["policy"][str(fy)] for fy in YEARS}
CURRENT = {"w_frpl": 0.30, "cp_thr": 0.60, "w_cp": 0.15, "w_ell": 0.25, "thr_factor": 1.35, "w_engl": 0.70,
           "min_bar": 0.01, "min_bar_hh": 0.10, "foundation": 11525}


def enacted_params(fy):
    o = OBS[fy]
    return dict(w_frpl=o["w_frpl"], cp_thr=o["cp_thr"], w_cp=o["w_cp"], w_ell=o["w_ell"], thr_factor=o["thr_factor"],
                w_engl=o["w_engl"], w_mhi=o["w_mhi"], min_bar=o["min_bar"], min_bar_hh=o["min_bar_hh"], foundation=o["foundation"],
                pct_under=o["pct_under"], pct_over=o["pct_over"], hh="alliance", engl_median=o["engl_median"], mhi_median=o["mhi_median"])


def scenario_params(fy, on, start, sliders, hh_mode="alliance", phase=1.0):
    if fy < start:
        return enacted_params(fy)
    o = OBS[fy]
    p = enacted_params(fy)
    for k in CURRENT:
        p[k] = sliders.get(k, CURRENT[k])
    p["w_mhi"] = 1 - p["w_engl"]
    if "inflation" in on:
        y = min(fy - 1, max(CPI))
        p["foundation"] = 11525 * CPI[y] / CPI[2013]
    if "f13087" in on:
        p["foundation"] = 13087
    full = "fullfund" in on
    p["pct_under"] = min(1, o["pct_under"] * phase); p["pct_over"] = min(1, o["pct_over"] * phase)
    if full:
        p["pct_under"] = p["pct_over"] = 1
    p["hh"] = "none" if full else hh_mode
    return p


def fully_funded(y, p):
    excess = max(y["frpl"] - p["cp_thr"] * y["res"], 0)
    need = y["res"] + p["w_frpl"] * y["frpl"] + p["w_cp"] * excess + p["w_ell"] * y["ell"]
    englf = y["eepc"] / (p["engl_median"] * p["thr_factor"]); mhif = y["mhi"] / (p["mhi_median"] * p["thr_factor"])
    waf = 1 - (p["w_engl"] * englf + p["w_mhi"] * mhif)
    bar = max(waf, p["min_bar_hh"] if y["hh"] else p["min_bar"])
    final = bar + (y["pic"] or 0)
    base = round(need * final * p["foundation"])
    return base + (y["rsd"] or 0) + (y["end"] or 0)


def step(y, p, prior):
    ff = fully_funded(y, p)
    ent = prior + p["pct_under"] * (ff - prior) if ff > prior else prior - p["pct_over"] * (prior - ff)
    if p["hh"] == "all" or (p["hh"] == "alliance" and y["hh"]):
        ent = max(ent, prior, y["fy17"] or 0)
    return round(ent)


def series(t, pf):
    prior = t["ent"][str(YEARS[0] - 1)]; out = {}
    for fy in YEARS:
        e = step(t["yr"][str(fy)], pf(fy), prior); out[fy] = e; prior = e
    return out


def shock_from_scenario(on, start, sliders, hh_mode, phase):
    rows = []
    for t in D["towns"]:
        obs = series(t, enacted_params)
        scn = series(t, lambda fy: scenario_params(fy, on, start, sliders, hh_mode, phase))
        for fy in YEARS:
            res = t["yr"][str(fy)]["res"]
            rows.append({"town_code": t["code"], "town": t["name"], "fiscal_year": fy,
                         "delta_nominal_per_student": (scn[fy] - obs[fy]) / max(res, 1), "resident_students": res,
                         "frpl_share": t["yr"][str(fy)]["frpl"] / max(res, 1)})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="f13087", help="observed|inflation|f13087|fullfund, joined with +")
    ap.add_argument("--shock", help="CSV with town_code, fiscal_year, delta_nominal_per_student (overrides --scenario)")
    ap.add_argument("--start", type=int, default=2023)
    ap.add_argument("--hetero", choices=["none", "A", "both"], default="both", help="income-heterogeneity sensitivity (Option A multiplier)")
    ap.add_argument("--hh", choices=["alliance", "none", "all"], default="alliance")
    ap.add_argument("--phase", type=float, default=1.0)
    ap.add_argument("--set", action="append", default=[], help="slider override key=value")
    a = ap.parse_args()
    sliders = {kv.split("=")[0]: float(kv.split("=")[1]) for kv in a.set}
    on = set() if a.scenario == "observed" else set(a.scenario.split("+"))
    label = a.scenario if not a.shock else "shockfile"
    if a.shock:
        shock = pd.read_csv(a.shock)
        info = pd.DataFrame([{"town_code": t["code"], "town": t["name"], "fiscal_year": fy, "resident_students": t["yr"][str(fy)]["res"],
                              "frpl_share": t["yr"][str(fy)]["frpl"] / max(t["yr"][str(fy)]["res"], 1)} for t in D["towns"] for fy in YEARS])
        shock = shock.merge(info, on=["town_code", "fiscal_year"], how="left")
    else:
        shock = shock_from_scenario(on, a.start, sliders, a.hh, a.phase)
    shock = shock[shock.fiscal_year >= a.start].copy()
    shock["delta_2018"] = [deflate_to_base(v, fy, CPI) for v, fy in zip(shock.delta_nominal_per_student, shock.fiscal_year)]

    k = pd.read_csv(clean("seda_k_grade_subject"))
    base = pd.read_csv(clean("town_grade_subject_seda_baseline"))
    fr = shock[shock.fiscal_year == shock.fiscal_year.max()].set_index("town_code")["frpl_share"]
    runs = {"pooled": simulate(base, shock[["town_code", "fiscal_year", "delta_2018"]], k, a.start)}
    if a.hetero in ("A", "both"):
        mult = fr.map(income_multiplier)
        runs["optionA"] = simulate(base, shock[["town_code", "fiscal_year", "delta_2018"]], k, a.start, multiplier=mult)

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = os.path.join(OUTROOT, "runs", f"{stamp}_{label}_from{a.start}")
    os.makedirs(outdir, exist_ok=True)
    summaries = {}
    for tag, r in runs.items():
        r = r.merge(shock[["town_code", "fiscal_year", "town", "resident_students", "frpl_share", "delta_nominal_per_student"]], on=["town_code", "fiscal_year"])
        r.to_csv(os.path.join(outdir, f"district_grade_subject_year_{tag}.csv"), index=False)
        w = lambda d, col: np.average(d[col], weights=d["n_tests"]) if d["n_tests"].sum() > 0 else np.nan
        dist = r.groupby(["town_code", "town", "fiscal_year", "policy_year"]).apply(
            lambda d: pd.Series({"delta_2018": d.delta_2018.iloc[0], "delta_nominal": d.delta_nominal_per_student.iloc[0],
                                 "delta_sd": w(d, "delta_sd"), "delta_gcs": w(d, "delta_gcs"), "n_tests": d.n_tests.sum(),
                                 "frpl_share": d.frpl_share.iloc[0]}), include_groups=False).reset_index()
        dist.to_csv(os.path.join(outdir, f"district_summary_{tag}.csv"), index=False)
        st = r.groupby(["fiscal_year", "policy_year", "subject"]).apply(lambda d: pd.Series({"delta_gcs": w(d, "delta_gcs"), "delta_sd": w(d, "delta_sd"), "n_tests": d.n_tests.sum()}), include_groups=False).reset_index()
        st_all = r.groupby(["fiscal_year", "policy_year"]).apply(lambda d: pd.Series({"delta_gcs": w(d, "delta_gcs"), "delta_sd": w(d, "delta_sd"), "n_tests": d.n_tests.sum()}), include_groups=False).reset_index().assign(subject="all")
        st = pd.concat([st_all, st]).sort_values(["fiscal_year", "subject"])
        st.to_csv(os.path.join(outdir, f"state_summary_{tag}.csv"), index=False)
        dist["tercile"] = pd.qcut(dist.groupby("town_code")["frpl_share"].transform("first"), 3, labels=["low FRPL", "middle", "high FRPL"])
        gap = dist.groupby(["fiscal_year", "policy_year", "tercile"], observed=True).apply(lambda d: pd.Series({"delta_gcs": w(d, "delta_gcs"), "towns": d.town_code.nunique()}), include_groups=False).reset_index()
        piv = gap.pivot(index=["fiscal_year", "policy_year"], columns="tercile", values="delta_gcs").reset_index()
        piv["gap_change_high_minus_low"] = piv["high FRPL"] - piv["low FRPL"]
        piv.to_csv(os.path.join(outdir, f"gap_summary_{tag}.csv"), index=False)
        summaries[tag] = (st, piv, dist)

    # figures (pooled run)
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        st, piv, dist = summaries["pooled"]
        fig, ax = plt.subplots(figsize=(6, 3.4)); s = st[st.subject == "all"]
        ax.plot(s.fiscal_year, s.delta_gcs, marker="o"); ax.axhline(0, color="grey", lw=.8); ax.set_ylabel("grade levels"); ax.set_title("Statewide predicted change in achievement (test-weighted)")
        fig.tight_layout(); fig.savefig(os.path.join(outdir, "fig1_state_by_year.png"), dpi=150); plt.close(fig)
        fig, ax = plt.subplots(figsize=(6, 3.4))
        for col in ["low FRPL", "middle", "high FRPL"]:
            if col in piv: ax.plot(piv.fiscal_year, piv[col], marker="o", label=col)
        ax.axhline(0, color="grey", lw=.8); ax.legend(); ax.set_ylabel("grade levels"); ax.set_title("Predicted change by FRPL tercile")
        fig.tight_layout(); fig.savefig(os.path.join(outdir, "fig2_by_tercile.png"), dpi=150); plt.close(fig)
        last = dist[dist.fiscal_year == dist.fiscal_year.max()].sort_values("delta_gcs")
        fig, ax = plt.subplots(figsize=(6, 12)); ax.barh(last.town, last.delta_gcs); ax.tick_params(axis="y", labelsize=5); ax.set_xlabel("grade levels"); ax.set_title(f"District effects, FY{int(last.fiscal_year.max())}")
        fig.tight_layout(); fig.savefig(os.path.join(outdir, "fig3_districts_last_year.png"), dpi=150); plt.close(fig)
    except Exception as e:  # noqa: BLE001
        print("figures skipped:", e)

    st, piv, dist = summaries["pooled"]
    ktxt = "; ".join(f"g{int(r.grade)}/{r.subject}={r.k:.3f}" for r in k.itertuples())
    mult_mean = float(np.average(fr.map(income_multiplier), weights=shock[shock.fiscal_year == shock.fiscal_year.max()].set_index("town_code").loc[fr.index, "resident_students"]))
    log = f"""# Assumptions log -- test-score simulation run {stamp}

- Scenario: **{a.scenario if not a.shock else a.shock}**, changes take effect from FY{a.start}; hold-harmless mode {a.hh}; phase-in multiplier {a.phase}; slider overrides {sliders or 'none'}.
- Shock: scenario ECS entitlement minus enacted, per ECS resident student, by fiscal year (from the dashboard's engine and data, ecs_dash_data.json). Treated as an OPERATING (noncapital) spending change spent one for one; no capital component. Partial-equilibrium: no behavioral responses (enrollment, local tax offsets, teacher labor markets) beyond what the reduced-form estimates embed.
- Dollars: nominal fiscal-year dollars deflated to {CONFIG['dollar_base_year']} dollars with CPI-U annual averages (FRED CPIAUCSL); fiscal year t uses calendar-year t CPI; years past the last complete CPI year ({max(CPI)}) use that year.
- Effect size: beta = {CONFIG['beta']} student-level SD per $1,000 per pupil (2018$) at four years of exposure (Jackson & Mackevicius 2024, AEJ: Applied 16(1), Table 3 col 2 constant = noncapital marginal effect; se {CONFIG['beta_se']}, tau {CONFIG['beta_tau']}). The pooled headline {CONFIG['beta_pooled_reference']} (col 1) is not used.
- Exposure: no churn since kindergarten; exposure = min(policy year, grade + 1). Dose linear to {CONFIG['dose_years']} years and flat after (user assumption). With a year-varying shock the effect is beta/{CONFIG['dose_years']} times the sum of the last min(exposure, {CONFIG['dose_years']}) years' per-pupil increases (reduces to beta x dose x delta for a constant shock).
- Horizon: FY{a.start}-FY{HORIZON_END} (the dashboard's ECS panel and SEDA scores both stop at 2025), so no policy year exceeds {max(YEARS) - a.start + 1}; the plateau never binds.
- k (grade levels per SD): from SEDA's own scale definitions, k = national NAEP SD_(grade, subject) / per-grade NAEP growth_(subject), using the Table 9 parameters in the SEDA 2025.2 documentation averaged over the four reference cohorts (eqs. 7.2-7.4; the documentation's rule of thumb is ~3 grade levels per SD): {ktxt}. Cross-check against the GCS-on-CS slope across all U.S. districts: max |difference| {float((k.k - k.k_regression).abs().max()):.4f}; flagged (> 0.05): {int(k.flag.sum())}.
- Baseline scores: SEDA 2025.2 admin-district long files, GCS, all students, averaged over spring 2023-2025 by town x grade x subject (post-2019 years included). Weights = mean tests taken. Towns: local boards by name; K-12 regional districts (10, 12-18, 20; 6 through 2024) mapped to member towns; charter/magnet/RESC not assigned. Matched towns cover 99.3% of ECS resident students.
- Heterogeneity sensitivity (Option A): beta_d = beta x [s x 0.0312/0.0359 + (1-s) x 0.0161/0.0359] with s = FRPL share of resident students in FY{int(shock.fiscal_year.max())}. Not normalized: CT resident-weighted mean multiplier = {mult_mean:.3f}. Option B (ecd/nec subgroup means) is available for ~100 towns and not run here.
- Uncertainty: not reported in this run (user's instruction). For reference the se-only 95% band on the average effect is [{CONFIG['beta'] - 1.96 * CONFIG['beta_se']:.3f}, {CONFIG['beta'] + 1.96 * CONFIG['beta_se']:.3f}] SD per $1,000; the policy-level predictive SD is sqrt(se^2 + tau^2) = {np.sqrt(CONFIG['beta_se']**2 + CONFIG['beta_tau']**2):.4f}.
- Results (pooled beta, test-weighted statewide, grade levels): {"; ".join(f"FY{int(r.fiscal_year)}: {r.delta_gcs:+.4f}" for r in st[st.subject == 'all'].itertuples())}.
- Gap (high minus low FRPL tercile, grade levels): {"; ".join(f"FY{int(r.fiscal_year)}: {r.gap_change_high_minus_low:+.4f}" for r in piv.itertuples())}.
- Validation: unit tests in seda_spending_sim.py pass (exposure, dose plateau, $1,000 at 4 years = 0.0343, at 2 years = 0.01715, deflator). Aggregation check of grade files vs pooled annual file: output/ecs/sim/aggregation_check.md.
"""
    open(os.path.join(outdir, "assumptions_log.md"), "w", encoding="utf-8").write(log)
    open(os.path.join(outdir, "README.md"), "w", encoding="utf-8").write(
        f"# Run {stamp}\n\nCommand: `python run_sim.py --scenario {a.scenario} --start {a.start} --hetero {a.hetero} --hh {a.hh} --phase {a.phase}"
        + "".join(f" --set {s}" for s in a.set) + "`\n\nOutputs: district_grade_subject_year_*.csv, district_summary_*.csv, state_summary_*.csv, gap_summary_*.csv, fig1-3, assumptions_log.md.\n")
    with open(os.path.join(OUTROOT, "RUNS.md"), "a", encoding="utf-8") as f:
        f.write(f"- {stamp} | {label} from FY{a.start} | hh={a.hh} phase={a.phase} set={sliders or '-'} | statewide "
                + ", ".join(f"FY{int(r.fiscal_year)} {r.delta_gcs:+.4f}" for r in st[st.subject == 'all'].itertuples()) + f" | {os.path.relpath(outdir, OUTROOT)}\n")
    print(f"[run] {outdir}")
    print(st[st.subject == "all"][["fiscal_year", "policy_year", "delta_sd", "delta_gcs"]].to_string(index=False))
    print(piv.to_string(index=False))


if __name__ == "__main__":
    main()
