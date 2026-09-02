"""
23_sped_pp_by_type.py

Per-student spending for special ed students vs non-special ed students.
  - Sped $/student = sped expenditures / sped enrollment
  - Non-sped $/student = non-sped expenditures / non-sped enrollment

For: State, Sheff Region, HPS, Cities (Hartford, New Haven, Bridgeport,
     Waterbury, Stamford).

All figures in constant 2024-25 dollars (CPI-U adjusted).

Input:
    data/special-education-expenditures/ (archived + current)
    clean-data/district_year_enrollment.csv
    clean-data/district_year_spending.csv
    clean-data/district_year_ppe_archived.csv
Output:
    output/figures/part-3/part3_sped_pp_by_type.png
"""

import os, re, glob
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

CITIES = [
    "Hartford School District", "New Haven School District",
    "Bridgeport School District", "Waterbury School District",
    "Stamford School District",
]

# ── CPI ────────────────────────────────────────────────────────────────────────
spend = pd.read_csv(os.path.join(BASE, "clean-data", "district_year_spending.csv"))
cpi_map = spend[["fiscal_year", "cpi_u"]].drop_duplicates().set_index("fiscal_year")["cpi_u"].to_dict()
BASE_CPI = 321.962
CPI_ARCHIVE = {
    2007: 207.342, 2008: 215.303, 2009: 214.537, 2010: 218.056,
    2011: 224.939, 2012: 229.594, 2013: 232.957, 2014: 236.736,
    2015: 240.007, 2016: 241.428, 2017: 245.120,
}
for k, v in CPI_ARCHIVE.items():
    if k not in cpi_map:
        cpi_map[k] = v

# ── Parse sped expenditures ───────────────────────────────────────────────────
SPED_DIR = os.path.join(BASE, "data", "special-education-expenditures")


def parse_archived(fpath):
    m = re.search(r"sped-exp-(\d{4})-(\d{2})\.csv$", os.path.basename(fpath))
    fy = int(m.group(1)[:2] + m.group(2))
    df = pd.read_csv(fpath, skiprows=4, dtype=str)
    df.columns = df.columns.str.strip().str.strip('"')
    df = df.rename(columns={df.columns[0]: "District"})
    df["District"] = df["District"].str.lstrip("=").str.strip('"').str.strip()
    df = df[df["District"].str.len() > 0]
    total_col = "Total Expenditures"
    df["sped_total"] = pd.to_numeric(df[total_col].astype(str).str.replace(r'[$,"]', "", regex=True), errors="coerce")
    df["fiscal_year"] = fy
    return df[["District", "fiscal_year", "sped_total"]]


def parse_current(fpath):
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
for y in range(2006, 2017):
    yr = f"{y}-{str(y+1)[-2:]}"
    f = os.path.join(SPED_DIR, f"sped-exp-{yr}.csv")
    if os.path.exists(f):
        sped_frames.append(parse_archived(f))
for f in sorted(glob.glob(os.path.join(SPED_DIR, "sped-exp-new-*.csv"))):
    sped_frames.append(parse_current(f))

sped = pd.concat(sped_frames, ignore_index=True)

# ── Load enrollment ───────────────────────────────────────────────────────────
enroll = pd.read_csv(os.path.join(BASE, "clean-data", "district_year_enrollment.csv"))
enroll_slim = enroll[["District", "fiscal_year", "enrollment_total", "n_sped"]].dropna(subset=["enrollment_total"])
enroll_slim["n_non_sped"] = enroll_slim["enrollment_total"] - enroll_slim["n_sped"].fillna(0)

# ── Build total expenditures ──────────────────────────────────────────────────
spend_current = spend[["District", "fiscal_year", "total_expenditures",
                        "pupils_enrolled_plus_outplaced", "cpi_u"]].dropna().copy()

arch_ppe = pd.read_csv(os.path.join(BASE, "clean-data", "district_year_ppe_archived.csv"))
arch_ppe = arch_ppe[["District", "fiscal_year", "ppe_total"]].copy()
arch_merged = arch_ppe.merge(
    enroll[["District", "fiscal_year", "enrollment_total"]],
    on=["District", "fiscal_year"], how="inner"
)
arch_merged["total_expenditures"] = arch_merged["ppe_total"] * arch_merged["enrollment_total"]
arch_merged["pupils_enrolled_plus_outplaced"] = arch_merged["enrollment_total"]
arch_merged["cpi_u"] = arch_merged["fiscal_year"].map(cpi_map)
arch_merged = arch_merged.dropna(subset=["cpi_u"])
spend_archived = arch_merged[["District", "fiscal_year", "total_expenditures",
                                "pupils_enrolled_plus_outplaced", "cpi_u"]]

all_spend = pd.concat([spend_archived[~spend_archived["fiscal_year"].isin(spend_current["fiscal_year"].unique())],
                        spend_current], ignore_index=True)

# ── Merge everything ──────────────────────────────────────────────────────────
merged = sped.merge(all_spend, on=["District", "fiscal_year"], how="inner")
merged = merged.merge(enroll_slim[["District", "fiscal_year", "n_sped", "n_non_sped"]],
                       on=["District", "fiscal_year"], how="inner")
merged["non_sped_exp"] = merged["total_expenditures"] - merged["sped_total"]
merged["cpi_factor"] = BASE_CPI / merged["cpi_u"]
merged["sped_total_real"] = merged["sped_total"] * merged["cpi_factor"]
merged["non_sped_exp_real"] = merged["non_sped_exp"] * merged["cpi_factor"]

print(f"Merged: {len(merged):,} rows, years {sorted(merged['fiscal_year'].unique())}")


# ── Aggregate ─────────────────────────────────────────────────────────────────
def aggregate(df, label):
    rows = []
    for fy in sorted(df["fiscal_year"].unique()):
        g = df[df["fiscal_year"] == fy]
        total_sped_students = g["n_sped"].sum()
        total_non_sped_students = g["n_non_sped"].sum()
        total_sped_exp = g["sped_total_real"].sum()
        total_non_sped_exp = g["non_sped_exp_real"].sum()
        rows.append({
            "fiscal_year": fy,
            "group": label,
            "sped_pp": total_sped_exp / total_sped_students if total_sped_students > 0 else np.nan,
            "non_sped_pp": total_non_sped_exp / total_non_sped_students if total_non_sped_students > 0 else np.nan,
        })
    return pd.DataFrame(rows)


def keep_hartford_comparable_years(series, hartford_series):
    hartford_years = set(hartford_series["fiscal_year"])
    return series[series["fiscal_year"].isin(hartford_years)].copy()


GROUPS_DEF = [
    ("State", None),
    ("Sheff Region", SHEFF_DISTRICTS),
    ("HPS", ["Hartford School District"]),
    ("Cities", CITIES),
]

aggs = []
for label, districts in GROUPS_DEF:
    df_g = merged if districts is None else merged[merged["District"].isin(districts)]
    aggs.append(aggregate(df_g, label))

hps_years = aggs[2]
aggs[1] = keep_hartford_comparable_years(aggs[1], hps_years)

for a in aggs:
    label = a["group"].iloc[0]
    print(f"\n{label}:")
    for _, r in a.iterrows():
        fy = int(r["fiscal_year"])
        yr = f"{fy-1}-{str(fy)[-2:]}"
        print(f"  {yr}: sped=${r['sped_pp']:,.0f}  non-sped=${r['non_sped_pp']:,.0f}")


def fy_label(fy):
    return f"{int(fy)-1}-{str(int(fy))[-2:]}"


# ── Plot ──────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(16, 11))
plot_years = sorted(set().union(*[set(a["fiscal_year"]) for a in aggs]))

# Global y-axis
global_ymax = 0
for a in aggs:
    global_ymax = max(global_ymax, a["sped_pp"].max(), a["non_sped_pp"].max())
global_ymax *= 1.12

for idx, a in enumerate(aggs):
    ax = axes[idx // 2, idx % 2]
    label = a["group"].iloc[0]

    a_plot = a.set_index("fiscal_year").reindex(plot_years).reset_index()
    years = a_plot["fiscal_year"].values
    xlabels = [fy_label(y) for y in years]

    ax.plot(xlabels, a_plot["sped_pp"].values, "o-", color="#d6604d",
            linewidth=2, markersize=5, label="Special Ed $/student")
    ax.plot(xlabels, a_plot["non_sped_pp"].values, "s-", color="#2166ac",
            linewidth=2, markersize=5, label="Non-Special Ed $/student")

    # Label first and last
    for series, col in [(a_plot["sped_pp"], "#d6604d"), (a_plot["non_sped_pp"], "#2166ac")]:
        valid = series.dropna()
        for i in [valid.index[0], valid.index[-1]]:
            v = series.iloc[i]
            if not np.isnan(v):
                ax.annotate(f"${v:,.0f}",
                            (xlabels[i], v),
                            textcoords="offset points",
                            xytext=(0, 10 if col == "#d6604d" else -14),
                            ha="center", fontsize=8, fontweight="bold", color=col)

    ax.set_xlabel("School Year", fontsize=10)
    ax.set_ylabel("Expenditure per Student ($)", fontsize=10)
    ax.set_title(label, fontsize=13, fontweight="bold")
    ax.set_ylim(0, global_ymax)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: f"${v:,.0f}"))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=7)
    ax.grid(True, alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if idx == 0:
        ax.legend(loc="upper left", fontsize=9)

fig.suptitle("Per-Student Spending: Special Ed vs. Non-Special Ed Students",
             fontsize=15, fontweight="bold", y=0.98)
fig.text(0.5, 0.01,
         "Source: CT EdSight Special Education Expenditures, Enrollment, Per-Pupil Expenditures.\n"
         "Constant 2024-25 dollars (CPI-U adjusted). Sped $/student = sped spending / sped students. "
         "Sheff Region omits years when Hartford spending data are unavailable. "
         "Cities = Hartford, New Haven, Bridgeport, Waterbury, Stamford.",
         ha="center", fontsize=8, color="gray")
fig.tight_layout(rect=[0, 0.05, 1, 0.96])

outpath = os.path.join(FIG_DIR, "part3_sped_pp_by_type.png")
fig.savefig(outpath, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nSaved: {outpath}")
