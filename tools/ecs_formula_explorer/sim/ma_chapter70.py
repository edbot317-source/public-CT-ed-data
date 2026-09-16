"""
ma_chapter70.py -- a Massachusetts Chapter 70 style aid rule applied to Connecticut towns.

Pure functions; the dashboard's JavaScript engine mirrors them line for line.

foundation_budget(inputs, rates, index)   the FY2025 DESE rate schedule applied to a town's
                                          resident students by grade band, English learners,
                                          low-income concentration group, assumed special
                                          education shares, and the wage adjustment factor
target_contributions(B, eqv, inc, lam, cap) statewide solve of the uniform property and income
                                          effort rates so that the capped targets sum to lam x sum(B),
                                          with property and income each yielding half
aid(B, C, prior_aid, enrollment, min_aid) foundation aid = max(B - C, prior + min_aid x pupils)

Units: dollars of the rate year (FY2025) scaled by `index` (ratio of the chosen price index
in the year before the fiscal year to its value in calendar 2024, capped at 4.5% a year).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

LI_UPPER = [5.99, 11.99, 17.99, 23.99, 29.99, 35.99, 41.99, 47.99, 53.99, 69.99, 79.99, 100.0]
DEFAULTS = dict(sped_in=0.0393, sped_out=0.01, pk_weight=0.5, lam=0.59, cap=0.825, cey_max=1.75,
                min_aid=104.0, inflation_cap=1.045)


def li_group(pct):
    """Low-income concentration group 1-12 from the low-income share (percent)."""
    for g, hi in enumerate(LI_UPPER, start=1):
        if pct <= hi:
            return g
    return 12


def rate_table(rates: pd.DataFrame) -> dict:
    """{column: (total per pupil, wage-adjustable part)} from clean-data/ma_fy2025_foundation_rates.csv."""
    return {r.column: (float(r.total), float(r.waf_applicable)) for r in rates.itertuples()}


def foundation_from_columns(counts: dict, waf, R, index=1.0):
    """Foundation budget from DESE-style enrollment columns {column: pupils} (pk, k_half, k_full, el, ms, hs,
    voc, sped_in, sped_out, el_pk5, el_68, el_hs, li_<group>), applying the wage factor to the
    wage-adjustable part of each rate."""
    B = 0.0
    for col, n in counts.items():
        tot, w = R[col]
        B += n * (w * waf + (tot - w)) * index
    return B


def foundation_budget(res, share, ell, frpl, waf, R, index=1.0, p=DEFAULTS):
    """
    res:   resident students (ECS count); share: dict of grade-band shares pk,k,el,ms,hs;
    ell:   English learners; frpl: low-income students; waf: wage adjustment factor (>= 1);
    R:     rate table {column: (total, waf_part)}; index: price index relative to FY2025.
    Returns (foundation budget in dollars, dict of components).
    """
    def allot(col, n):
        tot, w = R[col]
        return n * (w * waf + (tot - w)) * index
    n = {b: res * share.get(b, 0.0) for b in ("pk", "k", "el", "ms", "hs")}
    comp = {"pk": allot("pk", n["pk"]), "k": allot("k_full", n["k"]), "el": allot("el", n["el"]),
            "ms": allot("ms", n["ms"]), "hs": allot("hs", n["hs"])}
    k12 = n["k"] + n["el"] + n["ms"] + n["hs"]
    comp["sped_in"] = allot("sped_in", p["sped_in"] * k12)
    comp["sped_out"] = allot("sped_out", p["sped_out"] * k12)
    # English learners split across bands in proportion to enrollment
    tot_g = max(n["pk"] + k12, 1e-9)
    comp["el_pk5"] = allot("el_pk5", ell * (n["pk"] + n["k"] + n["el"]) / tot_g)
    comp["el_68"] = allot("el_68", ell * n["ms"] / tot_g)
    comp["el_hs"] = allot("el_hs", ell * n["hs"] / tot_g)
    li_pct = 100.0 * frpl / max(res, 1e-9)
    g = li_group(li_pct)
    comp["li"] = allot(f"li_{g}", frpl)
    comp["li_group"] = g
    # foundation enrollment for per-pupil measures counts pre-K at 0.5
    comp["foundation_enrollment"] = p["pk_weight"] * n["pk"] + k12
    B = sum(v for k, v in comp.items() if k not in ("li_group", "foundation_enrollment"))
    return B, comp


def target_contributions(B, eqv, inc, lam=0.59, cap=0.825):
    """
    Uniform effort rates: property and income each yield half of the aggregate target, and the
    capped targets sum to lam x sum(B). Returns (target contribution array, rho_P, rho_Y, H).
    B, eqv, inc: aligned arrays. Towns with missing wealth get the cap.
    """
    B = np.asarray(B, float); eqv = np.asarray(eqv, float); inc = np.asarray(inc, float)
    ok = np.isfinite(eqv) & np.isfinite(inc)
    se, si = eqv[ok].sum(), inc[ok].sum()
    goal = lam * B.sum()
    def total(H):
        y = np.where(ok, H * (eqv / se + inc / si), np.inf)
        return np.minimum(y, cap * B).sum()
    lo, hi = 0.0, goal * 10
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if total(mid) < goal:
            lo = mid
        else:
            hi = mid
    H = 0.5 * (lo + hi)
    y = np.where(ok, H * (eqv / se + inc / si), np.inf)
    return np.minimum(y, cap * B), H / se, H / si, H


def required_contribution(target, B, prior=None, growth=None, cey=None, p=DEFAULTS):
    """
    Chapter 70 transition from the prior year's required contribution. With prior=None the
    steady state (contribution = target) is returned, which is what the dashboard uses.
    Otherwise: preliminary = prior x (1 + growth); above target -> reduced 100% to target;
    below target by >2.5% of B -> +1% of B, by >7.5% -> +2% of B, never above target;
    towns whose combined effort yield exceeds 175% of B are set at the 82.5% cap.
    """
    if prior is None:
        return np.asarray(target, float)
    prelim = np.asarray(prior, float) * (1 + np.asarray(growth, float))
    short = (np.asarray(target) - prelim) / np.asarray(B)
    inc = np.where(short > 0.075, 0.02, np.where(short > 0.025, 0.01, 0.0)) * np.asarray(B)
    c = np.where(prelim > target, target, np.minimum(prelim + inc, target))
    if cey is not None:
        c = np.where(np.asarray(cey) > p["cey_max"] * np.asarray(B), p["cap"] * np.asarray(B), c)
    return c


def aid(B, C, prior_aid, pupils, min_aid=104.0):
    """Foundation aid if the prior aid plus the contribution falls short of the foundation budget,
    else minimum aid of min_aid per foundation pupil; aid never falls."""
    B = np.asarray(B, float); C = np.asarray(C, float); prior = np.asarray(prior_aid, float); pupils = np.asarray(pupils, float)
    return np.maximum(B - C, prior + min_aid * pupils)


def price_index(series: dict, fy: int, base_year: int = 2024, cap: float = 1.045) -> float:
    """Chained index of the calendar year before the fiscal year relative to calendar `base_year`
    (FY2025 rates), each annual step capped at `cap` as the foundation inflation index is."""
    years = sorted(series)
    y = min(fy - 1, years[-1])
    if y == base_year:
        return 1.0
    idx = 1.0
    if y > base_year:
        for yy in range(base_year + 1, y + 1):
            idx *= min(series[yy] / series[yy - 1], cap)
    else:
        for yy in range(y + 1, base_year + 1):
            idx /= min(series[yy] / series[yy - 1], cap)
    return idx


if __name__ == "__main__":
    # unit tests against DESE's FY2025 workbook (Aid436 sheet) and the statute
    assert li_group(5.99) == 1 and li_group(6.0) == 2 and li_group(54.0) == 10 and li_group(69.99) == 10 and li_group(80.0) == 12
    # Boston FY2025: foundation 1,145,949,554; required contribution 945,408,382; FY24 aid 230,700,785; enrollment 57,369 -> aid 236,667,161
    assert abs(aid(1145949554.1, 945408382, 230700785, 57369, 104) - 236667161) < 1
    # Lexington FY2025: 91,458,918; 75,453,607; 17,609,131; 6,851 -> 18,321,635
    assert abs(aid(91458917.922, 75453607, 17609131, 6851, 104) - 18321635) < 1
    # a foundation-aid district: B - C exceeds prior + min aid
    assert aid(100.0, 40.0, 50.0, 10, 1.0) == 60.0
    # target solve: with equal wealth every town's target is lam x B when the cap does not bind
    B = np.array([100.0, 100.0]); t, rp, ry, H = target_contributions(B, np.array([1.0, 1.0]), np.array([1.0, 1.0]), 0.59, 0.825)
    assert np.allclose(t, [59.0, 59.0])
    # cap binds: the rich town is capped at 82.5% and the sum still equals lam x sum(B)
    t, *_ = target_contributions(np.array([100.0, 100.0]), np.array([9.0, 1.0]), np.array([9.0, 1.0]), 0.59, 0.825)
    assert abs(t.sum() - 118.0) < 1e-6 and abs(t[0] - 82.5) < 1e-6
    # price index: flat series -> 1; capped growth
    assert price_index({2023: 100, 2024: 100, 2025: 110}, 2026) == 1.045 and price_index({2023: 100, 2024: 100, 2025: 110}, 2025) == 1.0
    # DESE FY2025 white paper example: Plymouth, WAF 1.036, low-income group 6, total foundation budget 112,170,810
    import os
    rates_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "clean-data", "ma_fy2025_foundation_rates.csv")
    if os.path.exists(rates_csv):
        R = rate_table(pd.read_csv(rates_csv))
        plymouth = {"pk": 222, "k_half": 0, "k_full": 514, "el": 2671, "ms": 1657, "hs": 1946, "voc": 692,
                    "sped_in": 301, "sped_out": 68, "el_pk5": 240, "el_68": 55, "el_hs": 102, "li_6": 2635}
        B = foundation_from_columns(plymouth, 1.036, R)
        assert abs(B - 112170810) / 112170810 < 0.002, B
        # pre-K and half-day K use the half rates; foundation enrollment = 7,591 counts them at 0.5
        fe = 0.5 * (222 + 0) + 514 + 2671 + 1657 + 1946 + 692
        assert abs(fe - 7591) < 1
        print(f"  Plymouth FY2025 foundation budget: computed {B:,.0f} vs DESE 112,170,810 ({(B/112170810-1)*100:+.3f}%)")
    print("ma_chapter70: all unit tests pass")
