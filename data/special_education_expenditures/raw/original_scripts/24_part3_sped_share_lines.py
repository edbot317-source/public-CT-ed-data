"""
24_part3_sped_share_lines.py

Two-panel line graph:
  Left:  Share of students classified as special education
  Right: Share of total expenditures going to special education

Four series: HPS, Peer Cities (Waterbury, New Haven, Bridgeport), Sheff Region, State.

Input:
    clean-data/district_year_enrollment.csv
    clean-data/district_year_spending.csv
    clean-data/district_year_ppe_archived.csv
    data/special-education-expenditures/sped-exp-archived-*.csv
    data/special-education-expenditures/sped-exp-new-*.csv
Output:
    output/figures/part-3/part3_sped_shares.png
"""

import os, re, glob, textwrap
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = os.path.join(BASE, "output", "figures", "part-3")
os.makedirs(FIG_DIR, exist_ok=True)

# ── District definitions ──────────────────────────────────────────────────────
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
    "Waterbury School District",
    "New Haven School District",
    "Bridgeport School District",
]

# ── 1. Enrollment share (left panel) ─────────────────────────────────────────
enroll = pd.read_csv(os.path.join(BASE, "clean-data", "district_year_enrollment.csv"))
enroll = enroll.dropna(subset=["enrollment_total", "n_sped"])


def enrollment_share(df, label):
    """Compute enrollment-weighted sped share by year."""
    g = df.groupby("fiscal_year").agg(
        n_sped=("n_sped", "sum"),
        enrollment_total=("enrollment_total", "sum"),
    ).reset_index()
    g["pct_sped"] = g["n_sped"] / g["enrollment_total"] * 100
    g["group"] = label
    return g


def keep_hartford_comparable_years(series, hartford_series):
    hartford_years = set(hartford_series["fiscal_year"])
    return series[series["fiscal_year"].isin(hartford_years)].copy()


enroll_hps = enrollment_share(
    enroll[enroll["District"] == "Hartford School District"], "Hartford")
enroll_peers = enrollment_share(
    enroll[enroll["District"].isin(PEER_CITIES)], "Peer Cities")
enroll_sheff = enrollment_share(
    enroll[enroll["District"].isin(SHEFF_DISTRICTS)], "Sheff Region")
enroll_sheff = keep_hartford_comparable_years(enroll_sheff, enroll_hps)
enroll_state = enrollment_share(enroll, "State")

enroll_all = pd.concat([enroll_hps, enroll_peers, enroll_sheff, enroll_state], ignore_index=True)

# ── 2. Spending share (right panel) ──────────────────────────────────────────
# Parse sped expenditure files
SPED_DIR = os.path.join(BASE, "data", "special-education-expenditures")


def parse_archived_sped(fpath):
    """Parse archived sped expenditure CSV (wide format)."""
    m = re.search(r"sped-exp-archived-(\d{4})-(\d{2})\.csv$", os.path.basename(fpath))
    fy = int(m.group(1)[:2] + m.group(2))
    df = pd.read_csv(fpath, skiprows=4, dtype=str)
    df.columns = df.columns.str.strip().str.strip('"')
    df = df.rename(columns={df.columns[0]: "District"})
    df["District"] = df["District"].str.lstrip("=").str.strip('"').str.strip()
    df = df[df["District"].str.len() > 0]
    # Total column
    total_col = "Total Expenditures" if "Total Expenditures" in df.columns else df.columns[-1]
    df["sped_total"] = pd.to_numeric(
        df[total_col].astype(str).str.replace(r'[$,"]', "", regex=True), errors="coerce"
    )
    df["fiscal_year"] = fy
    return df[["District", "fiscal_year", "sped_total"]]


def parse_current_sped(fpath):
    """Parse current sped expenditure CSV (long format)."""
    m = re.search(r"sped-exp-new-(\d{4})-(\d{2})\.csv$", os.path.basename(fpath))
    fy = int(m.group(1)[:2] + m.group(2))
    df = pd.read_csv(fpath, skiprows=2, dtype=str)
    df.columns = df.columns.str.strip().str.strip('"')
    df["District"] = df["District"].str.strip('"').str.strip().replace("", pd.NA).ffill()
    df["Description"] = df["Description"].str.strip('"').str.strip()
    totals = df[df["Description"] == "Total"].copy()
    totals["sped_total"] = pd.to_numeric(
        totals["Amount"].str.replace(r'[$,"]', "", regex=True), errors="coerce"
    )
    totals["fiscal_year"] = fy
    return totals[["District", "fiscal_year", "sped_total"]]


sped_frames = []
for f in sorted(glob.glob(os.path.join(SPED_DIR, "sped-exp-archived-*.csv"))):
    sped_frames.append(parse_archived_sped(f))
for f in sorted(glob.glob(os.path.join(SPED_DIR, "sped-exp-new-*.csv"))):
    sped_frames.append(parse_current_sped(f))

sped = pd.concat(sped_frames, ignore_index=True)
sped = sped.dropna(subset=["sped_total"])
print(f"Sped expenditures: {len(sped):,} rows, years {sorted(sped['fiscal_year'].unique())}")

# Total expenditures denominator:
#   Current years (FY2018+): EdSight reported total_expenditures (district_year_spending.csv).
#   Archived years (<=FY2017): REPORTED total expenditures scraped from EdSight
#     "Total Annual Expenditures by Type (2016-17 and earlier)" via the
#     FinanceReport_SiteCore stored process (see code/43_download_archived_total_expenditures.py).
#
# FIX 7 / audit P1-3 (2026-08-17): archived years previously reconstructed the
# denominator as ppe_total (archived per-pupil) x enrollment_total (in-district
# enrollment). That reconstruction is unsupported -- EdSight's per-pupil base is
# pupils_enrolled_plus_outplaced, not in-district enrollment -- and it understated
# Hartford's total by a share that GREW from ~4% (FY2008) to ~13% (FY2017),
# artificially inflating Hartford's pre-2018 sped spending share and manufacturing
# a level/trend break at the FY2018 numerator/denominator seam. We now use the
# actual reported nominal totals, which are constructed the same way as FY2018+.
spend = pd.read_csv(os.path.join(BASE, "clean-data", "district_year_spending.csv"))
spend_current = spend[["District", "fiscal_year", "total_expenditures"]].dropna()

ARCH_EXP_DIR = os.path.join(BASE, "data", "total-annual-expenditures-archived")
arch_frames = [pd.read_csv(f) for f in sorted(glob.glob(
    os.path.join(ARCH_EXP_DIR, "total-exp-archived-*.csv")))]
spend_archived = pd.concat(arch_frames, ignore_index=True)[
    ["District", "fiscal_year", "total_expenditures"]].dropna()

# Combine, preferring current where overlap
all_spend = pd.concat([
    spend_archived[~spend_archived["fiscal_year"].isin(spend_current["fiscal_year"].unique())],
    spend_current,
], ignore_index=True)

# Merge sped with total spending
merged = sped.merge(all_spend, on=["District", "fiscal_year"], how="inner")
merged["sped_share"] = merged["sped_total"] / merged["total_expenditures"] * 100


def spending_share(df, label):
    """Compute aggregate sped spending share by year."""
    g = df.groupby("fiscal_year").agg(
        sped_total=("sped_total", "sum"),
        total_expenditures=("total_expenditures", "sum"),
    ).reset_index()
    g["sped_share"] = g["sped_total"] / g["total_expenditures"] * 100
    g["group"] = label
    return g


spend_hps = spending_share(
    merged[merged["District"] == "Hartford School District"], "Hartford")
spend_peers = spending_share(
    merged[merged["District"].isin(PEER_CITIES)], "Peer Cities")
spend_sheff = spending_share(
    merged[merged["District"].isin(SHEFF_DISTRICTS)], "Sheff Region")
spend_sheff = keep_hartford_comparable_years(spend_sheff, spend_hps)
spend_state = spending_share(merged, "State")

spend_all = pd.concat([spend_hps, spend_peers, spend_sheff, spend_state], ignore_index=True)

# ── 3. Plot ───────────────────────────────────────────────────────────────────
# Shared district-group palette (consistent across all Part 3 figures).
COLORS = {
    "Hartford": "#d6604d",
    "Peer Cities": "#ff7f0e",
    "Sheff Region": "#4393c3",
    "State": "#878787",
}

# Stack the two panels vertically so each spans the full text-column width
# (the post displays figures at text width, ~740px), keeping labels legible.
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 9.5))

# Left panel: enrollment share
years_e = sorted(enroll_all["fiscal_year"].unique())
for label, color in COLORS.items():
    d = enroll_all[enroll_all["group"] == label].sort_values("fiscal_year")
    d_plot = d if label == "Hartford" else d.set_index("fiscal_year").reindex(years_e).reset_index()
    ax1.plot(d_plot["fiscal_year"], d_plot["pct_sped"], marker="o", markersize=4,
             color=color, linewidth=2, label=label)

ax1.set_title("Share of Students in Special Education", fontsize=13, fontweight="bold")
ax1.set_ylabel("Percent of enrollment", fontsize=11)
ax1.set_xlabel("")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: f"{v:.0f}%"))
ax1.legend(loc="upper left", fontsize=10)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
ax1.grid(axis="y", alpha=0.3)
# X-axis: show every other year label
ax1.set_xticks(years_e)
ax1.set_xticklabels(
    [f"'{str(y)[-2:]}" if y % 2 == 0 else "" for y in years_e],
    fontsize=9,
)

# Right panel: spending share
years_s = sorted(spend_all["fiscal_year"].unique())
for label, color in COLORS.items():
    d = spend_all[spend_all["group"] == label].sort_values("fiscal_year")
    if label == "Sheff Region":
        # Sheff spending share is only defined in years when Hartford spending
        # data exist. Draw it as a single connected line over those years
        # (no markers), rather than as disconnected points across NaN gaps.
        d = d.dropna(subset=["sped_share"])
        ax2.plot(d["fiscal_year"], d["sped_share"],
                 color=color, linewidth=2, label=label)
    else:
        d_plot = d if label == "Hartford" else d.set_index("fiscal_year").reindex(years_s).reset_index()
        ax2.plot(d_plot["fiscal_year"], d_plot["sped_share"], marker="o", markersize=4,
                 color=color, linewidth=2, label=label)

ax2.set_title("Share of Total Spending on Special Education", fontsize=13, fontweight="bold")
ax2.set_ylabel("Percent of total expenditures", fontsize=11)
ax2.set_xlabel("")
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: f"{v:.0f}%"))
ax2.legend(loc="upper left", fontsize=10)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.grid(axis="y", alpha=0.3)
ax2.set_xticks(years_s)
ax2.set_xticklabels(
    [f"'{str(y)[-2:]}" if y % 2 == 0 else "" for y in years_s],
    fontsize=9,
)

# Sync y-axes across panels
ymin = min(ax1.get_ylim()[0], ax2.get_ylim()[0])
ymax = max(ax1.get_ylim()[1], ax2.get_ylim()[1])
ax1.set_ylim(ymin, ymax)
ax2.set_ylim(ymin, ymax)

SRC = (
    "Source: CT EdSight Enrollment (special education subgroup), Special Education Expenditures, "
    "and Total Expenditures (reported; archived years from Total Annual Expenditures by Type). "
    "Sheff Region = Hartford, CREC, and 21 surrounding districts. Peer Cities = Waterbury, New Haven, "
    "Bridgeport. Hartford special education spending data are unavailable in some years; "
    "those years are omitted from both the Hartford and Sheff Region series."
)
fig.tight_layout(rect=[0, 0.08, 1, 1])
fig.text(0.5, 0.01, textwrap.fill(SRC, width=95),
         ha="center", va="bottom", fontsize=9, color="gray")

out = os.path.join(FIG_DIR, "part3_sped_shares.png")
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nSaved: {out}")

# Print summary table
print("\n-- Enrollment share (%) --")
for label in ["Hartford", "Peer Cities", "Sheff Region", "State"]:
    d = enroll_all[enroll_all["group"] == label].sort_values("fiscal_year")
    first, last = d.iloc[0], d.iloc[-1]
    print(f"  {label}: {first['pct_sped']:.1f}% ({int(first['fiscal_year'])}) -> "
          f"{last['pct_sped']:.1f}% ({int(last['fiscal_year'])})")

print("\n-- Spending share (%) --")
for label in ["Hartford", "Peer Cities", "Sheff Region", "State"]:
    d = spend_all[spend_all["group"] == label].sort_values("fiscal_year")
    first, last = d.iloc[0], d.iloc[-1]
    print(f"  {label}: {first['sped_share']:.1f}% ({int(first['fiscal_year'])}) -> "
          f"{last['sped_share']:.1f}% ({int(last['fiscal_year'])})")
