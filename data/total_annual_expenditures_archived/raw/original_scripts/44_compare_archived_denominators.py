"""
44_compare_archived_denominators.py

DECISION AID for FIX 7 (audit P1-3): the archived-years denominator of the
Part 3 "Share of Total Spending on Special Education" figure
(24_part3_sped_share_lines.py, right panel).

For archived years (<=FY2017) that figure builds total district expenditures
TWO different ways depending on what we choose. This script plots BOTH nominal
denominators over time so we can decide:

  (1) RECONSTRUCTED (what 24 currently uses):
        total_expenditures = ppe_total (archived per-pupil, EdSight PerPupilExport)
                             x enrollment_total (in-district enrollment)
      Source files: clean-data/district_year_ppe_archived.csv
                    clean-data/district_year_enrollment.csv

  (2) REPORTED (newly scraped, script 43):
        total_expenditures = EdSight "Total Annual Expenditures by Type"
                             (FinanceReport_SiteCore), reported nominal dollars
      Source files: data/total-annual-expenditures-archived/total-exp-archived-*.csv

Both are aggregated to the SAME four groups the spending-share figure uses
(Hartford, Peer Cities, Sheff Region, State) by summing member districts per
year, so the comparison is apples-to-apples with the figure's denominator.

Output:
    output/figures/part-3/part3_archived_denominator_comparison.png
    plus a printed Hartford year-by-year table.

NOTE: nominal dollars (NOT inflation-adjusted) per the request -- we are
comparing the raw denominator construction, not real trends.
"""

import glob
import os

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = os.path.join(BASE, "output", "figures", "part-3")
ARCH_DIR = os.path.join(BASE, "data", "total-annual-expenditures-archived")
os.makedirs(FIG_DIR, exist_ok=True)

SHEFF_DISTRICTS = [
    "Avon School District", "Bloomfield School District", "Canton School District",
    "East Granby School District", "East Hartford School District",
    "East Windsor School District", "Ellington School District",
    "Farmington School District", "Glastonbury School District",
    "Granby School District", "Hartford School District",
    "Manchester School District", "Newington School District",
    "Rocky Hill School District", "Simsbury School District",
    "South Windsor School District", "Suffield School District",
    "Vernon School District", "West Hartford School District",
    "Wethersfield School District", "Windsor School District",
    "Windsor Locks School District",
    "Capitol Region Education Council",
]
PEER_CITIES = [
    "Waterbury School District", "New Haven School District", "Bridgeport School District",
]
GROUPS = [
    ("Hartford", ["Hartford School District"]),
    ("Peer Cities", PEER_CITIES),
    ("Sheff Region", SHEFF_DISTRICTS),
    ("State", None),  # all districts
]

# ---- (1) reconstructed denominator (exactly as 24 builds it) ---------------
arch_ppe = pd.read_csv(os.path.join(BASE, "clean-data", "district_year_ppe_archived.csv"))
enroll = pd.read_csv(os.path.join(BASE, "clean-data", "district_year_enrollment.csv"))
enroll = enroll.dropna(subset=["enrollment_total"])

recon = arch_ppe[["District", "fiscal_year", "ppe_total"]].merge(
    enroll[["District", "fiscal_year", "enrollment_total"]],
    on=["District", "fiscal_year"], how="inner",
)
recon["total_expenditures"] = recon["ppe_total"] * recon["enrollment_total"]

# ---- (2) reported denominator (scraped, script 43) -------------------------
rep_frames = [pd.read_csv(f) for f in sorted(glob.glob(
    os.path.join(ARCH_DIR, "total-exp-archived-*.csv")))]
reported = pd.concat(rep_frames, ignore_index=True)[
    ["District", "fiscal_year", "total_expenditures"]]


def group_series(df, districts):
    sub = df if districts is None else df[df["District"].isin(districts)]
    g = sub.groupby("fiscal_year")["total_expenditures"].sum().reset_index()
    return g


# ---- plot ------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(12, 9))
axes = axes.ravel()

hartford_table = []
for ax, (label, districts) in zip(axes, GROUPS):
    r = group_series(recon, districts)
    p = group_series(reported, districts)
    # Compare on the overlapping archived window only.
    yrs = sorted(set(r["fiscal_year"]) | set(p["fiscal_year"]))
    yrs = [y for y in yrs if y <= 2017]
    r = r[r["fiscal_year"].isin(yrs)]
    p = p[p["fiscal_year"].isin(yrs)]

    ax.plot(r["fiscal_year"], r["total_expenditures"] / 1e6, marker="o", markersize=5,
            color="#d6604d", linewidth=2.2, label="Reconstructed (ppe x enrollment) - current")
    ax.plot(p["fiscal_year"], p["total_expenditures"] / 1e6, marker="s", markersize=5,
            color="#2166ac", linewidth=2.2, label="Reported (scraped) - proposed")
    ax.set_title(label, fontsize=13, fontweight="bold")
    ax.set_ylabel("Total expenditures ($M, nominal)", fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p_: f"${v:,.0f}M"))
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xticks(yrs)
    ax.set_xticklabels([f"'{str(y)[-2:]}" for y in yrs], fontsize=8)
    ax.legend(frameon=False, fontsize=8, loc="upper left")

    if label == "Hartford":
        merged = r.merge(p, on="fiscal_year", how="outer", suffixes=("_recon", "_rep")).sort_values("fiscal_year")
        for _, row in merged.iterrows():
            rec = row["total_expenditures_recon"]
            rep = row["total_expenditures_rep"]
            ratio = (rec / rep) if pd.notna(rec) and pd.notna(rep) and rep else float("nan")
            hartford_table.append((int(row["fiscal_year"]), rec, rep, ratio))

fig.suptitle(
    "Archived-Years Total-Expenditure Denominator: Reconstructed vs Reported (nominal)",
    fontsize=15, fontweight="bold",
)
fig.tight_layout(rect=[0, 0.02, 1, 0.97])
out = os.path.join(FIG_DIR, "part3_archived_denominator_comparison.png")
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close()

print("Hartford year-by-year total expenditures (nominal):")
print(f"{'FY':>5} {'reconstructed':>16} {'reported':>16} {'recon/reported':>16}")
for fy, rec, rep, ratio in hartford_table:
    rec_s = f"${rec:,.0f}" if pd.notna(rec) else "n/a"
    rep_s = f"${rep:,.0f}" if pd.notna(rep) else "n/a"
    ratio_s = f"{ratio:.3f}" if pd.notna(ratio) else "n/a"
    print(f"{fy:>5} {rec_s:>16} {rep_s:>16} {ratio_s:>16}")
print(f"\nSaved: {out}")
