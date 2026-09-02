"""
22_part3_sped_enrollment_spending.py

Two sets of stacked bar charts:
  1. Student counts: special ed vs non-special-ed
  2. Total expenditures: special ed vs all other

For: State, Sheff Region, HPS, CREC (enrollment-weighted aggregates).

Input:
    clean-data/district_year_enrollment.csv  (n_sped)
    clean-data/district_year_spending.csv    (total_expenditures, pupils, CPI)
    data/special-education-expenditures/     (sped expenditure totals)
Output:
    output/figures/part-3/part3_sped_enrollment.png
    output/figures/part-3/part3_sped_spending.png
"""

import os
import re
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = os.path.join(BASE, "output", "figures", "part-3")
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

BASE_CPI = 321.962


def fy_label(fy):
    return f"{int(fy)-1}-{str(int(fy))[-2:]}"


# ── Load enrollment (sped counts) ─────────────────────────────────────────────
enroll = pd.read_csv(os.path.join(BASE, "clean-data", "district_year_enrollment.csv"))

# ── Load spending (total expenditures, pupils, CPI) ──────────────────────────
spend = pd.read_csv(os.path.join(BASE, "clean-data", "district_year_spending.csv"))
spend_slim = spend[["District", "fiscal_year", "total_expenditures",
                     "pupils_enrolled_plus_outplaced", "cpi_u"]].dropna()

# ── Parse special ed expenditures ─────────────────────────────────────────────
SPED_DIR = os.path.join(BASE, "data", "special-education-expenditures")


def parse_archived_sped(fpath):
    """Parse archived sped expenditure CSV (2006-07 to 2016-17)."""
    m = re.search(r"archived-(\d{4})-(\d{2})\.csv$", os.path.basename(fpath))
    fy = int(m.group(1)[:2] + m.group(2))
    df = pd.read_csv(fpath, skiprows=4, dtype=str)
    df.columns = df.columns.str.strip().str.strip('"')
    # First column is Organization (district name)
    df = df.rename(columns={df.columns[0]: "District"})
    df["District"] = df["District"].str.lstrip("=").str.strip('"').str.strip()
    df = df[df["District"].str.len() > 0]
    # Total Expenditures column
    total_col = "Total Expenditures"
    df["sped_total"] = pd.to_numeric(
        df[total_col].astype(str).str.replace(r'[$,"]', "", regex=True),
        errors="coerce"
    )
    df["fiscal_year"] = fy
    return df[["District", "fiscal_year", "sped_total"]]


def parse_current_sped(fpath):
    """Parse current sped expenditure CSV (2017-18+)."""
    m = re.search(r"sped-exp-(\d{4})-(\d{2})\.csv$", os.path.basename(fpath))
    fy = int(m.group(1)[:2] + m.group(2))
    df = pd.read_csv(fpath, skiprows=3, dtype=str)
    df.columns = df.columns.str.strip().str.strip('"')
    df["District"] = df["District"].str.strip('"').str.strip()
    df["Description"] = df["Description"].str.strip('"').str.strip()
    df["Amount"] = pd.to_numeric(
        df["Amount"].astype(str).str.replace(r'[$,"]', "", regex=True),
        errors="coerce"
    )
    # Keep only Total rows
    totals = df[df["Description"] == "Total"].copy()
    totals = totals.rename(columns={"Amount": "sped_total"})
    totals["fiscal_year"] = fy
    return totals[["District", "fiscal_year", "sped_total"]]


# Parse all files
sped_frames = []
for f in sorted(glob.glob(os.path.join(SPED_DIR, "sped-exp-archived-*.csv"))):
    sped_frames.append(parse_archived_sped(f))
for f in sorted(glob.glob(os.path.join(SPED_DIR, "sped-exp-[0-9]*.csv"))):
    # Skip archived-format files (pre-2017)
    bn = os.path.basename(f)
    m = re.search(r"sped-exp-(\d{4})", bn)
    if m and int(m.group(1)) < 2017:
        continue
    sped_frames.append(parse_current_sped(f))

sped = pd.concat(sped_frames, ignore_index=True)
print(f"Sped expenditures: {len(sped):,} rows, years {sorted(sped['fiscal_year'].unique())}")

# ── Merge datasets ────────────────────────────────────────────────────────────
# We need: enrollment (total + sped), total expenditures, sped expenditures
# Limit to years where we have all three
# Enrollment has n_sped; spending has total_expenditures

# Merge enrollment + spending
merged = enroll[["District", "fiscal_year", "enrollment_total", "n_sped"]].merge(
    spend_slim, on=["District", "fiscal_year"], how="inner"
)
# Merge sped expenditures
merged = merged.merge(sped, on=["District", "fiscal_year"], how="inner")

merged["n_non_sped"] = merged["enrollment_total"] - merged["n_sped"].fillna(0)
merged["non_sped_exp"] = merged["total_expenditures"] - merged["sped_total"].fillna(0)
merged["cpi_factor"] = BASE_CPI / merged["cpi_u"]
merged["sped_total_real"] = merged["sped_total"] * merged["cpi_factor"]
merged["non_sped_exp_real"] = merged["non_sped_exp"] * merged["cpi_factor"]
merged["total_exp_real"] = merged["total_expenditures"] * merged["cpi_factor"]

print(f"Merged: {len(merged):,} rows")
print(f"Years: {sorted(merged['fiscal_year'].unique())}")

# Only keep years where spending data exists (2018+)
# Enrollment sped data may go back further but spending doesn't
available_years = sorted(merged["fiscal_year"].unique())
print(f"Available years: {available_years}")


# ── Aggregation functions ──────────────────────────────────────────────────────
def aggregate(group_df, label):
    rows = []
    for fy in available_years:
        g = group_df[group_df["fiscal_year"] == fy]
        if len(g) == 0:
            continue
        rows.append({
            "fiscal_year": fy,
            "group": label,
            "enrollment_total": g["enrollment_total"].sum(),
            "n_sped": g["n_sped"].sum(),
            "n_non_sped": g["n_non_sped"].sum(),
            "sped_total_real": g["sped_total_real"].sum(),
            "non_sped_exp_real": g["non_sped_exp_real"].sum(),
            "total_exp_real": g["total_exp_real"].sum(),
            "pupils": g["pupils_enrolled_plus_outplaced"].sum(),
        })
    return pd.DataFrame(rows)


hps_df = merged[merged["District"] == "Hartford School District"]
crec_df = merged[merged["District"] == "Capitol Region Education Council"]
sheff_df = merged[merged["District"].isin(SHEFF_DISTRICTS)]
state_df = merged

hps_agg = aggregate(hps_df, "HPS")
crec_agg = aggregate(crec_df, "CREC")
sheff_agg = aggregate(sheff_df, "Sheff Region")
state_agg = aggregate(state_df, "State")

GROUPS = [("State", state_agg), ("Sheff Region", sheff_agg),
          ("HPS", hps_agg), ("CREC", crec_agg)]

# Print summary
for label, agg in GROUPS:
    print(f"\n{label}:")
    for _, r in agg.iterrows():
        yr = fy_label(r["fiscal_year"])
        pct_sped = r["n_sped"] / r["enrollment_total"] * 100 if r["enrollment_total"] > 0 else 0
        sped_pp = r["sped_total_real"] / r["pupils"] if r["pupils"] > 0 else 0
        total_pp = r["total_exp_real"] / r["pupils"] if r["pupils"] > 0 else 0
        pct_sped_exp = r["sped_total_real"] / r["total_exp_real"] * 100 if r["total_exp_real"] > 0 else 0
        print(f"  {yr}: enroll={r['enrollment_total']:,.0f}, sped={r['n_sped']:,.0f} ({pct_sped:.1f}%), "
              f"sped_exp=${sped_pp:,.0f}/pp ({pct_sped_exp:.1f}%), total=${total_pp:,.0f}/pp")


# ── Plot 1: Student counts ────────────────────────────────────────────────────
# Compute global y-max for enrollment
enr_max = max(agg["enrollment_total"].max() for _, agg in GROUPS) * 1.12

fig, axes = plt.subplots(2, 2, figsize=(16, 11))
for idx, (label, agg) in enumerate(GROUPS):
    ax = axes[idx // 2, idx % 2]
    years = agg["fiscal_year"].values
    x = np.arange(len(years))
    width = 0.6

    non_sped = agg["n_non_sped"].values
    sped = agg["n_sped"].values

    ax.bar(x, non_sped, width, label="Non-Special Ed", color="#67a9cf", edgecolor="white", linewidth=0.5)
    ax.bar(x, sped, width, bottom=non_sped, label="Special Ed", color="#d6604d", edgecolor="white", linewidth=0.5)

    # Label sped count inside bar
    for i in range(len(years)):
        mid = non_sped[i] + sped[i] / 2
        if sped[i] > 0:
            ax.text(x[i], mid, f"{sped[i]:,.0f}", ha="center", va="center",
                    fontsize=6, fontweight="bold", color="white")
        # Total on top
        total = non_sped[i] + sped[i]
        ax.text(x[i], total + enr_max * 0.01, f"{total:,.0f}",
                ha="center", va="bottom", fontsize=6.5, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([fy_label(y) for y in years], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Students", fontsize=10)
    ax.set_title(label, fontsize=13, fontweight="bold")
    ax.set_ylim(0, enr_max)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: f"{v:,.0f}"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if idx == 0:
        ax.legend(loc="upper right", fontsize=9)

fig.text(0.5, 0.01,
         "Source: CT EdSight Enrollment (Special Education subgroup) and Per Pupil Expenditures by Function.\n"
         "State and Sheff aggregates are enrollment-weighted.",
         ha="center", fontsize=8, color="gray")
fig.tight_layout(rect=[0, 0.04, 1, 1])
out1 = os.path.join(FIG_DIR, "part3_sped_enrollment.png")
fig.savefig(out1, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nSaved: {out1}")


# ── Plot 2: Total expenditures (real $) ───────────────────────────────────────
# Compute global y-max for spending
exp_max = max(agg["total_exp_real"].max() for _, agg in GROUPS) * 1.12

fig, axes = plt.subplots(2, 2, figsize=(16, 11))
for idx, (label, agg) in enumerate(GROUPS):
    ax = axes[idx // 2, idx % 2]
    years = agg["fiscal_year"].values
    x = np.arange(len(years))
    width = 0.6

    non_sped = (agg["non_sped_exp_real"].values) / 1e6
    sped = (agg["sped_total_real"].values) / 1e6
    total = (agg["total_exp_real"].values) / 1e6
    exp_max_m = max(agg["total_exp_real"].max() for _, agg in GROUPS) / 1e6 * 1.12

    ax.bar(x, non_sped, width, label="Non-Special Ed", color="#67a9cf", edgecolor="white", linewidth=0.5)
    ax.bar(x, sped, width, bottom=non_sped, label="Special Ed", color="#d6604d", edgecolor="white", linewidth=0.5)

    # Label sped $ inside bar
    for i in range(len(years)):
        mid = non_sped[i] + sped[i] / 2
        if sped[i] > 5:  # only if big enough (>$5M)
            ax.text(x[i], mid, f"${sped[i]:,.0f}M", ha="center", va="center",
                    fontsize=6, fontweight="bold", color="white")
        # Total on top
        ax.text(x[i], total[i] + exp_max_m * 0.01, f"${total[i]:,.0f}M",
                ha="center", va="bottom", fontsize=6.5, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([fy_label(y) for y in years], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Total Expenditures ($ millions)", fontsize=10)
    ax.set_title(label, fontsize=13, fontweight="bold")
    ax.set_ylim(0, exp_max_m)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: f"${v:,.0f}M"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if idx == 0:
        ax.legend(loc="upper right", fontsize=9)

fig.text(0.5, 0.01,
         "Source: CT EdSight Special Education Expenditures and Per Pupil Expenditures by Function.\n"
         "Constant 2024-25 dollars (CPI-U adjusted). State and Sheff aggregates are sums across districts.",
         ha="center", fontsize=8, color="gray")
fig.tight_layout(rect=[0, 0.04, 1, 1])
out2 = os.path.join(FIG_DIR, "part3_sped_spending.png")
fig.savefig(out2, dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {out2}")
