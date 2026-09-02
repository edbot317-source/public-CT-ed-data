"""
SBAC High Needs proficiency trends: HPS, CREC, and Sheff Region.
Parses year-by-year SBAC exports for High Needs subgroup.
"""
import os, re, glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from io import StringIO

BASE = r'C:\Users\seth\Dropbox\CT-school-finance\ct-school-finance-post'
SBAC_DIR = os.path.join(BASE, "data", "sbac-by-year-high-needs")
FIG_DIR = os.path.join(BASE, "output", "figures", "part-2")
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

# Shared district-group palette, consistent with 11_part2_figures.py:
# HPS red, CREC purple, Sheff Region blue.
COLORS = {"HPS": "#d6604d", "CREC": "#9467bd", "Sheff Region": "#4393c3"}
SOURCE = "Source: CT EdSight Smarter Balanced Assessments, High Needs subgroup, 2014-15 through 2024-25."


def fy_label(fy):
    return f"{fy-1}-{str(fy)[-2:]}"


# Parse all year files
sbac_long = []
for f in sorted(glob.glob(os.path.join(SBAC_DIR, "sbac-high-needs-*.csv"))):
    fname = os.path.basename(f)
    m = re.search(r"sbac-high-needs-(\d{4})-(\d{2})\.csv$", fname)
    if not m:
        continue
    fy = int(m.group(1)[:2] + m.group(2))

    with open(f, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    # Find header row
    header_idx = None
    for i, line in enumerate(lines):
        if '"District","District Code","Subject"' in line:
            header_idx = i
            break
    if header_idx is None:
        print(f"  {fname}: no header found, skipping")
        continue

    df = pd.read_csv(StringIO("".join(lines[header_idx:])), dtype=str)
    df.columns = df.columns.str.strip().str.strip('"')
    df["District"] = df["District"].str.strip('"').str.strip().replace("", None).ffill()
    df["Subject"] = df["Subject"].str.strip('"').str.strip().ffill()

    # Identify the high needs column (4th column)
    hn_col = df.columns[3]

    # Keep both High Needs = Y and N
    df = df[df[hn_col].isin(["Y", "N"])].copy()

    # Proficiency % is the last column of the original CSV (before we add new cols)
    # It's column index 17 (0-indexed) = "%.4" in the 18-column layout
    prof_col_idx = len(df.columns) - 1  # last original column
    df["pct_prof"] = pd.to_numeric(df.iloc[:, prof_col_idx], errors="coerce")

    df["needs_group"] = df[hn_col].map({"Y": "High Needs", "N": "Non-High Needs"})

    # Also get count of scored tests for weighting
    scored_col = "Total Number with Scored Tests"
    df["n_scored"] = pd.to_numeric(
        df[scored_col].str.replace(r'[",]', "", regex=True).str.strip(),
        errors="coerce"
    )

    df["fiscal_year"] = fy
    sbac_long.append(df[["District", "Subject", "fiscal_year", "pct_prof", "n_scored", "needs_group"]])

sbac_long = pd.concat(sbac_long, ignore_index=True)
print(f"SBAC High Needs years: {sorted(sbac_long['fiscal_year'].unique())}")
print(f"Total rows: {len(sbac_long)}")

# Check Hartford
hps_check = sbac_long[(sbac_long["District"] == "Hartford School District")]
print(f"\nHartford rows: {len(hps_check)}")
print(hps_check[["fiscal_year", "Subject", "pct_prof", "n_scored"]].to_string())

# CREC
crec_check = sbac_long[(sbac_long["District"] == "Capitol Region Education Council")]
print(f"\nCREC rows: {len(crec_check)}")
print(crec_check[["fiscal_year", "Subject", "pct_prof", "n_scored"]].to_string())

# Sheff region: scored-test-weighted average proficiency by needs group
sheff = sbac_long[sbac_long["District"].isin(SHEFF_DISTRICTS)].copy()
sheff = sheff.dropna(subset=["pct_prof", "n_scored"])
sheff_agg = sheff.groupby(["fiscal_year", "Subject", "needs_group"]).apply(
    lambda g: pd.Series({"pct_prof": np.average(g["pct_prof"], weights=g["n_scored"])})
).reset_index()

# Plot: 2x2 grid (rows = needs group, cols = subject)
NEEDS_GROUPS = ["High Needs", "Non-High Needs"]
YLIMS = {"High Needs": (0, 45), "Non-High Needs": (0, 80)}

fig, axes = plt.subplots(2, 2, figsize=(16, 11))

for row_idx, needs in enumerate(NEEDS_GROUPS):
    for col_idx, subj in enumerate(["ELA", "Math"]):
        ax = axes[row_idx, col_idx]

        # HPS
        hps_s = sbac_long[(sbac_long["District"] == "Hartford School District") &
                           (sbac_long["Subject"] == subj) &
                           (sbac_long["needs_group"] == needs)].sort_values("fiscal_year")
        ax.plot(hps_s["fiscal_year"], hps_s["pct_prof"], "o-", color=COLORS["HPS"],
                linewidth=2, markersize=6, label="Hartford")

        # CREC
        crec_s = sbac_long[(sbac_long["District"] == "Capitol Region Education Council") &
                            (sbac_long["Subject"] == subj) &
                            (sbac_long["needs_group"] == needs)].sort_values("fiscal_year")
        ax.plot(crec_s["fiscal_year"], crec_s["pct_prof"], "s-", color=COLORS["CREC"],
                linewidth=2, markersize=6, label="CREC")

        # Sheff region
        sheff_s = sheff_agg[(sheff_agg["Subject"] == subj) &
                             (sheff_agg["needs_group"] == needs)].sort_values("fiscal_year")
        ax.plot(sheff_s["fiscal_year"], sheff_s["pct_prof"], "D-.", color=COLORS["Sheff Region"],
                linewidth=1.5, markersize=5, label="Sheff Region")

        # Label endpoints
        offsets = {"HPS": (8, -8), "CREC": (8, 8), "Sheff": (8, 0)}
        for d, label, color in [(hps_s, "HPS", COLORS["HPS"]),
                                 (crec_s, "CREC", COLORS["CREC"]),
                                 (sheff_s, "Sheff", COLORS["Sheff Region"])]:
            if len(d) > 0:
                last = d.iloc[-1]
                ofs = offsets[label]
                ax.annotate(f"{last['pct_prof']:.1f}%",
                            (last["fiscal_year"], last["pct_prof"]),
                            textcoords="offset points", xytext=ofs,
                            fontsize=9, fontweight="bold", color=color, va="center")

        # Mark COVID gap
        ylo, yhi = YLIMS[needs]
        ax.axvspan(2019.5, 2021.5, color="#f0f0f0", zorder=0)
        ax.text(2020.5, ylo + 2, "No testing\n(COVID-19)", ha="center", va="bottom",
                fontsize=7, color="#999999", style="italic")

        ax.set_xlabel("School Year", fontsize=10)
        ax.set_ylabel(f"% Proficient ({subj})", fontsize=10)
        ax.set_title(f"SBAC {subj}: {needs} Students", fontsize=12, fontweight="bold")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{x:.0f}%"))
        ax.set_ylim(ylo, yhi)
        all_fy = sorted(set(hps_s["fiscal_year"]) | set(crec_s["fiscal_year"]))
        ax.set_xticks(all_fy)
        ax.set_xticklabels([fy_label(y) for y in all_fy], rotation=45, ha="right")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="upper right", fontsize=8)

fig.text(0.01, 0.01,
         SOURCE + "\n"
         "Sheff Region: average of Sheff districts + CREC, weighted by number of test takers.",
         fontsize=7, color="gray", va="bottom")
fig.tight_layout(rect=[0, 0.03, 1, 1])
outpath = os.path.join(FIG_DIR, "part2_fig8_sbac_high_needs_trends.png")
fig.savefig(outpath, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"\nSaved: {outpath}")
