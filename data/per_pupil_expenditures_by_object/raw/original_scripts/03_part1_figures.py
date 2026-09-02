"""
10_part1_figures.py

Produce the figures requested in docs/part-1.txt for the Substack post:
  Figure 1: Histogram of "wrong" PPE (total exp / in-district enrollment), Hartford labeled
  Figure 2: Histogram of official PPE (total exp / all enrolled), Hartford labeled
  Figure 3: Histogram of classroom PPE (total - tuition - 61.4% transport / in-district), Hartford labeled
  Figure 4: Scatter of official PPE vs % high needs, with enrollment-weighted best-fit line
  Figure 5: Scatter of SBAC ELA & Math vs % high needs, with test-taker-weighted best-fit line

All figures for 2024-25.
"""

import os, re, glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import statsmodels.api as sm
from io import StringIO

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBJ_DIR = os.path.join(BASE, "data", "per-pupil-expenditures-by-object")
FIG_DIR = os.path.join(BASE, "output", "figures", "part-1")
os.makedirs(FIG_DIR, exist_ok=True)

TRANSPORT_OOD_SHARE = 0.614  # from HPS budget doc

# â”€â”€ Parse object-level data â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def parse_object_file(path):
    fname = os.path.basename(path)
    m = re.search(r"object-(\d{4})-(\d{4})\.csv", fname)
    fy = int(m.group(2))
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if '"District","District Code"' in line:
            data_start = i
            break
    df = pd.read_csv(StringIO("".join(lines[data_start:])), dtype=str)
    df.columns = df.columns.str.strip().str.strip('"')
    df["District"] = df["District"].str.strip('"').str.strip()
    obj_col = df.columns[2]
    df = df.rename(columns={obj_col: "Object"})
    df["Object"] = df["Object"].str.strip('"').str.strip()
    df["Expenditures"] = pd.to_numeric(
        df["Expenditures"].str.replace(r'[$,"]', "", regex=True).str.strip(), errors="coerce")
    df["fiscal_year"] = fy
    return df

files = sorted(glob.glob(os.path.join(OBJ_DIR, "object-*.csv")))
obj_all = pd.concat([parse_object_file(f) for f in files], ignore_index=True)

# 2024-25 only
obj25 = obj_all[obj_all["fiscal_year"] == 2025]
tuition_25 = obj25[obj25["Object"] == "Tuition"][["District", "Expenditures"]].rename(
    columns={"Expenditures": "tuition"})

# Districts that do NOT separately report tuition: EdSight folds their tuition into
# the catch-all category, relabeling it "Other - Includes Tuition" (mutually
# exclusive with the normal "Tuition"/"Other" rows). For these LEAs we cannot
# subtract tuition to build the classroom-PPE measure, so they are dropped from the
# classroom-PPE figure (Figure 3) and its summary statistics rather than being
# assigned tuition = 0 (which would overstate their classroom spending).
FOLDED_TUITION = sorted(
    obj25[obj25["Object"].str.contains("Includes Tuition", na=False)]["District"].unique()
)

# â”€â”€ District panel â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
d = pd.read_csv(os.path.join(BASE, "clean-data", "district_year_spending.csv"))
d25 = d[d["fiscal_year"] == 2025].copy()

# Merge tuition
d25 = d25.merge(tuition_25, on="District", how="left")
d25["tuition"] = d25["tuition"].fillna(0)

# Compute PPE measures
d25["ppe_wrong"] = d25["total_expenditures"] / d25["pupils_enrolled_in_district"]
d25["ppe_official"] = d25["total_expenditures"] / d25["pupils_enrolled_plus_outplaced"]
d25["ood_transport"] = TRANSPORT_OOD_SHARE * d25["exp_student_transportation_services"].fillna(0)
d25["classroom_spending"] = d25["total_expenditures"] - d25["tuition"] - d25["ood_transport"]
d25["ppe_classroom"] = d25["classroom_spending"] / d25["pupils_enrolled_in_district"]

# Filter out tiny districts (< 200 students) to avoid noise
d25_plot = d25[d25["pupils_enrolled_plus_outplaced"] >= 200].copy()

# Classroom-PPE (Figure 3) sample: drop the LEAs that do not break tuition out of
# "Other" (see FOLDED_TUITION above), since their classroom PPE cannot be computed.
d25_fig3 = d25[~d25["District"].isin(FOLDED_TUITION)].copy()

# Demographics
school = pd.read_csv(os.path.join(BASE, "clean-data", "school_year_spending.csv"))
s25 = school[school["fiscal_year"] == 2025].copy()
s25["hn_n"] = s25["enrollment"] * s25["pct_high_needs"] / 100
demo = s25.groupby("district").agg(
    enrollment=("enrollment", "sum"), hn_n=("hn_n", "sum")).reset_index()
demo["pct_high_needs"] = demo["hn_n"] / demo["enrollment"] * 100
d25_plot = d25_plot.merge(demo[["district", "pct_high_needs", "enrollment"]],
                          left_on="District", right_on="district", how="left")

# Highlight districts
HIGHLIGHT = {
    "Hartford School District": ("Hartford", "#d6604d"),
    "Westport School District": ("Westport", "#2ca02c"),
    "New Canaan School District": ("New Canaan", "#8c564b"),
    "West Hartford School District": ("West Hartford", "#ff7f0e"),
}

SOURCE_NOTE_HIST = ("Source: CT EdSight Per Pupil Expenditures, 2024-25.\n"
                    "State average is enrollment-weighted across all 194 reporting LEAs.")
SOURCE_NOTE_SCATTER = ("Source: CT EdSight Per Pupil Expenditures & school-level % High Needs, 2024-25.\n"
                       "Excludes 12 LEAs with fewer than 200 students. Best-fit line is enrollment-weighted.")


def make_histogram(data, col, title, xlabel, highlights, filename, annotate_note=None, state_avg=None, source_note=None):
    """Create a histogram with labeled vertical lines for highlighted districts."""
    fig, ax = plt.subplots(figsize=(10, 6))

    vals = data[col].dropna()
    bins = np.arange(
        np.floor(vals.min() / 1000) * 1000,
        np.ceil(vals.max() / 1000) * 1000 + 1000,
        2000
    )

    ax.hist(vals, bins=bins, color="#b0b0b0", edgecolor="white", alpha=0.8, zorder=2)

    # Sort highlights by their PPE value so labels are ordered left-to-right
    highlight_vals = []
    for dist_name, (label, color) in highlights.items():
        row = data[data["District"] == dist_name]
        if len(row) == 0:
            continue
        val = row[col].values[0]
        highlight_vals.append((val, dist_name, label, color))
    highlight_vals.sort(key=lambda x: x[0])  # left to right

    y_max = ax.get_ylim()[1]

    # Assign staggered y positions, alternating sides of line
    n = len(highlight_vals)
    for i, (val, dist_name, label, color) in enumerate(highlight_vals):
        if dist_name == "Hartford School District":
            ax.axvline(val, color=color, linewidth=2.5, linestyle="-", zorder=4)
        else:
            ax.axvline(val, color=color, linewidth=1.8, linestyle="--", zorder=3)

        # Stagger vertically
        y_pos = y_max * (0.95 - i * 0.12)
        x_range = ax.get_xlim()[1] - ax.get_xlim()[0]
        # Place label to left for leftmost points, right for rightmost
        x_offset = -x_range * 0.08 if i < n / 2 else x_range * 0.08
        ha = "right" if x_offset < 0 else "left"

        ax.annotate(f"{label}: ${val:,.0f}",
                    xy=(val, y_pos),
                    xytext=(val + x_offset, y_pos),
                    fontsize=9, fontweight="bold", color=color,
                    ha=ha, va="center",
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=color, alpha=0.9),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.2))

    # State average line
    if state_avg is not None:
        ax.axvline(state_avg, color="#333333", linewidth=2, linestyle=":", zorder=4)
        # Place label at top of chart
        y_top = ax.get_ylim()[1]
        ax.annotate(f"State avg: ${state_avg:,.0f}",
                    xy=(state_avg, y_top * 0.98),
                    xytext=(state_avg + (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.05, y_top * 0.98),
                    fontsize=9, fontweight="bold", color="#333333",
                    ha="left", va="top",
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#333333", alpha=0.9),
                    arrowprops=dict(arrowstyle="-|>", color="#333333", lw=1.2))

    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel("Number of Districts", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"${x/1000:.0f}K"))
    ax.grid(True, alpha=0.3, axis="y")

    if annotate_note:
        ax.text(0.98, 0.95, annotate_note, transform=ax.transAxes,
                fontsize=8, va="top", ha="right", style="italic", color="#555555",
                bbox=dict(boxstyle="round", fc="lightyellow", ec="#cccccc", alpha=0.9))

    fig.text(0.01, 0.01, source_note or SOURCE_NOTE_HIST, fontsize=6, color="gray", va="bottom")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(os.path.join(FIG_DIR, filename), dpi=150, bbox_inches="tight")
    print(f"Saved {filename}")
    plt.close(fig)


# â”€â”€ Compute enrollment-weighted state averages (all districts, no filter) â”€
d25_all = d25.dropna(subset=["total_expenditures", "pupils_enrolled_plus_outplaced",
                              "pupils_enrolled_in_district"])
d25_all = d25_all.merge(tuition_25, on="District", how="left", suffixes=("", "_dup"))
# Use existing tuition column if already merged, otherwise use new one
if "tuition_dup" in d25_all.columns:
    d25_all.drop(columns=["tuition_dup"], inplace=True)
state_total_exp = d25_all["total_expenditures"].sum()
state_total_students_all = d25_all["pupils_enrolled_plus_outplaced"].sum()
state_total_students_indistrict = d25_all["pupils_enrolled_in_district"].sum()
state_total_tuition = d25_all["tuition"].sum()
state_total_ood_transport = TRANSPORT_OOD_SHARE * d25_all["exp_student_transportation_services"].fillna(0).sum()

STATE_AVG_WRONG = state_total_exp / state_total_students_indistrict
STATE_AVG_OFFICIAL = state_total_exp / state_total_students_all
STATE_AVG_CLASSROOM = (state_total_exp - state_total_tuition - state_total_ood_transport) / state_total_students_indistrict

# Classroom state-average line for Figure 3 is computed on the SAME sample that is
# plotted, i.e. excluding the folded-tuition LEAs, so the dotted line matches the bars.
d25_all_fig3 = d25_all[~d25_all["District"].isin(FOLDED_TUITION)]
state_total_exp_f3 = d25_all_fig3["total_expenditures"].sum()
state_total_tuition_f3 = d25_all_fig3["tuition"].sum()
state_total_ood_transport_f3 = TRANSPORT_OOD_SHARE * d25_all_fig3["exp_student_transportation_services"].fillna(0).sum()
state_total_students_indistrict_f3 = d25_all_fig3["pupils_enrolled_in_district"].sum()
STATE_AVG_CLASSROOM_FIG3 = (
    state_total_exp_f3 - state_total_tuition_f3 - state_total_ood_transport_f3
) / state_total_students_indistrict_f3

print(f"Enrollment-weighted state averages:")
print(f"  Wrong PPE: ${STATE_AVG_WRONG:,.0f}")
print(f"  Official PPE: ${STATE_AVG_OFFICIAL:,.0f}")
print(f"  Classroom PPE (all LEAs): ${STATE_AVG_CLASSROOM:,.0f}")
print(f"  Classroom PPE (excl. {len(FOLDED_TUITION)} folded-tuition LEAs, Fig 3 line): ${STATE_AVG_CLASSROOM_FIG3:,.0f}")

# â”€â”€ Figure 3 summary statistics (unweighted across the plotted sample) â”€â”€â”€â”€â”€â”€â”€â”€
# These are the numbers quoted in the Part 1 prose. Recomputed on the sample that
# DROPS the folded-tuition LEAs so code and text stay in sync.
_f3 = d25_fig3["ppe_classroom"].dropna()
_hart = d25.loc[d25["District"] == "Hartford School District", "ppe_classroom"].values[0]
_pct = (_f3 < _hart).mean() * 100
print(f"\nFigure 3 classroom-PPE summary (N={len(_f3)}, folded-tuition LEAs dropped):")
print(f"  mean   = ${_f3.mean():,.0f}")
print(f"  median = ${_f3.median():,.0f}")
print(f"  Hartford = ${_hart:,.0f}  ->  {_pct:.1f}th percentile")
print(f"  dropped LEAs ({len(FOLDED_TUITION)}): {', '.join(FOLDED_TUITION)}")


# â”€â”€ Figure 1: Wrong PPE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
make_histogram(
    d25, "ppe_wrong",
    "The wrong way to compute per-pupil expenditures",
    "Per-Pupil Expenditure (Total Budget / In-District Enrollment)",
    HIGHLIGHT,
    "part1_fig1_wrong_ppe.png",
    annotate_note="Divides total budget by in-district enrollment only.\nInflates PPE for districts with many outplaced students.",
    state_avg=STATE_AVG_WRONG,
)

# â”€â”€ Figure 2: Official PPE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
make_histogram(
    d25, "ppe_official",
    "One right way: Per-pupil expenditures by district of residence",
    "Per-Pupil Expenditure (Total Budget / All Students)",
    HIGHLIGHT,
    "part1_fig2_official_ppe.png",
    state_avg=STATE_AVG_OFFICIAL,
)

# â”€â”€ Figure 3: Classroom PPE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
make_histogram(
    d25_fig3, "ppe_classroom",
    "Another right way: Per-pupil expenditures for in-district students",
    "Per-Pupil Expenditure (Excl. Tuition & 61.4% Transport / In-District Enrollment)",
    HIGHLIGHT,
    "part1_fig3_classroom_ppe.png",
    annotate_note=("Subtracts tuition to other providers and\n"
                   "61.4% of transportation (out-of-district share).\n"
                   f"Excludes {len(FOLDED_TUITION)} districts that do not\n"
                   "separately report tuition (EdSight folds it\n"
                   'into "Other").'),
    state_avg=STATE_AVG_CLASSROOM_FIG3,
    source_note=("Source: CT EdSight Per Pupil Expenditures, 2024-25.\n"
                 f"Excludes {len(FOLDED_TUITION)} LEAs that do not separately report tuition; "
                 f"state average is enrollment-weighted across the remaining {194 - len(FOLDED_TUITION)} LEAs."),
)


# â”€â”€ Figure 4: Spending vs Need scatter â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
plot_data = d25_plot.dropna(subset=["ppe_official", "pct_high_needs", "enrollment"]).copy()

# Enrollment-weighted OLS
X = sm.add_constant(plot_data["pct_high_needs"].values)
wls = sm.WLS(plot_data["ppe_official"].values, X,
             weights=plot_data["enrollment"].values).fit()

fig, ax = plt.subplots(figsize=(10, 6))

# All districts as gray dots
other = plot_data[~plot_data["District"].isin(HIGHLIGHT) &
                  (plot_data["District"] != "Capitol Region Education Council")]
ax.scatter(other["pct_high_needs"], other["ppe_official"] / 1000,
           s=other["enrollment"] / 80, alpha=0.3, color="#c0c0c0",
           edgecolors="none", zorder=1, label="Other CT districts")

# Best-fit line (enrollment-weighted)
x_line = np.linspace(plot_data["pct_high_needs"].min(), plot_data["pct_high_needs"].max(), 100)
y_line = (wls.params[0] + wls.params[1] * x_line) / 1000
ax.plot(x_line, y_line, color="black", linewidth=1.5, linestyle="--", zorder=3,
        label=f"Best fit (slope = ${wls.params[1]:.0f}/pp, enrollment-weighted)")

HIGHLIGHT_SCATTER = dict(HIGHLIGHT)
HIGHLIGHT_SCATTER["Capitol Region Education Council"] = ("CREC", "#9467bd")

markers = {"Hartford School District": "o", "Westport School District": "^",
           "New Canaan School District": "s", "West Hartford School District": "D",
           "Capitol Region Education Council": "p"}

# Manual label offsets (tuned to avoid overlap and match left-right ordering)
label_offsets_fig4 = {
    "New Canaan":     (15, -30),   # right, well below
    "Westport":       (15, 30),    # right, well above
    "West Hartford":  (15, -18),   # right of point
    "CREC":           (15, 18),    # right of point
    "Hartford":       (-15, -18),  # left of point
}

for dist_name, (label, color) in HIGHLIGHT_SCATTER.items():
    row = plot_data[plot_data["District"] == dist_name]
    if len(row) == 0:
        continue
    r = row.iloc[0]
    marker = markers.get(dist_name, "o")
    ax.scatter(r["pct_high_needs"], r["ppe_official"] / 1000,
               s=250, color=color, marker=marker,
               edgecolors="black", linewidths=1.5, zorder=5)
    ox, oy = label_offsets_fig4[label]
    ha = "left" if ox > 0 else "right"
    ax.annotate(f"{label}\n${r['ppe_official']/1000:.1f}K",
                (r["pct_high_needs"], r["ppe_official"] / 1000),
                textcoords="offset points", xytext=(ox, oy),
                ha=ha, va="center", fontsize=9, fontweight="bold", color=color,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=color, alpha=0.9),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.0,
                               connectionstyle="arc3,rad=0.15"))

# Cap y-axis to reduce empty space (keep outliers visible but trim excess)
ax.set_ylim(8, 48)
ax.set_xlabel("% High-Needs Students", fontsize=12)
ax.set_ylabel("Per-Pupil Expenditure ($1,000s)", fontsize=12)
ax.set_title("Spending per student vs. student need by district (2024-25)", fontsize=14)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{x:.0f}%"))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"${x:.0f}K"))
ax.grid(True, alpha=0.3)
ax.legend(loc="upper right", fontsize=9)
fig.text(0.01, 0.01, SOURCE_NOTE_SCATTER + "\nBubble size ~ enrollment.",
         fontsize=6, color="gray", va="bottom")
fig.tight_layout(rect=[0, 0.06, 1, 1])
fig.savefig(os.path.join(FIG_DIR, "part1_fig4_spending_vs_need.png"), dpi=150, bbox_inches="tight")
print("Saved part1_fig4_spending_vs_need.png")
print(f"  WLS slope: ${wls.params[1]:.0f} per percentage point high needs")
plt.close(fig)


# â”€â”€ Figure 5: Achievement vs Need scatter (ELA + Math panels) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
sbac_path = os.path.join(BASE, "data", "sbac_all_districts_trend.csv")
with open(sbac_path, "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if '"District","District Code","Subject"' in line:
        header_idx = i
        break
sbac = pd.read_csv(StringIO("".join(lines[header_idx:])), dtype=str)
sbac.columns = sbac.columns.str.strip().str.strip('"')
sbac["District"] = sbac["District"].str.strip('"').str.strip().replace("", None).ffill()
sbac["Subject"] = sbac["Subject"].str.strip('"').str.strip()
sbac["pct_prof"] = pd.to_numeric(
    sbac.iloc[:, -1].str.replace(r'["%,]', "", regex=True).str.strip(), errors="coerce")
sbac["n_scored"] = pd.to_numeric(
    sbac.iloc[:, -2].str.replace(r'[",]', "", regex=True).str.strip(), errors="coerce")

HIGHLIGHT_ACH = dict(HIGHLIGHT)
HIGHLIGHT_ACH["Capitol Region Education Council"] = ("CREC", "#9467bd")
HIGHLIGHT_ACH["Meriden School District"] = ("Meriden", "#ff7f0e")

markers_ach = {"Hartford School District": "o", "Westport School District": "^",
               "New Canaan School District": "s", "West Hartford School District": "D",
               "Capitol Region Education Council": "p", "Meriden School District": "*"}

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

for idx, subj in enumerate(["ELA", "Math"]):
    ax = axes[idx]
    subdf = sbac[sbac["Subject"] == subj][["District", "pct_prof", "n_scored"]].copy()
    subdf = subdf.merge(demo[["district", "pct_high_needs", "enrollment"]],
                        left_on="District", right_on="district", how="inner")
    subdf = subdf.dropna(subset=["pct_prof", "pct_high_needs", "enrollment", "n_scored"])

    # All districts gray
    other = subdf[~subdf["District"].isin(HIGHLIGHT_ACH)]
    ax.scatter(other["pct_high_needs"], other["pct_prof"],
               s=other["enrollment"] / 80, alpha=0.25, color="#c0c0c0",
               edgecolors="none", zorder=1)

    # Test-taker-weighted OLS
    X = sm.add_constant(subdf["pct_high_needs"].values)
    wls = sm.WLS(subdf["pct_prof"].values, X,
                 weights=subdf["n_scored"].values).fit()
    x_line = np.linspace(subdf["pct_high_needs"].min(), subdf["pct_high_needs"].max(), 100)
    y_line = wls.params[0] + wls.params[1] * x_line
    ax.plot(x_line, y_line, color="black", linewidth=1.5, linestyle="--", zorder=3,
            label=f"Best fit (weighted by test takers)")

    # Manual label offsets per subject (tuned to avoid overlap)
    # New Canaan and Westport always cluster â€” give them large vertical separation
    if subj == "ELA":
        label_offsets_ach = {
            "New Canaan":     (15, -30),
            "Westport":       (15, 30),
            "West Hartford":  (15, -18),
            "Meriden":        (-15, 18),
            "CREC":           (15, 18),
            "Hartford":       (-15, -18),
        }
    else:  # Math
        label_offsets_ach = {
            "New Canaan":     (15, -30),
            "Westport":       (15, 30),
            "West Hartford":  (-15, 18),
            "Meriden":        (-15, 18),
            "CREC":           (-15, 18),
            "Hartford":       (-15, -18),
        }

    for dist_name, (label, color) in HIGHLIGHT_ACH.items():
        row = subdf[subdf["District"] == dist_name]
        if len(row) == 0:
            continue
        r = row.iloc[0]
        pred = wls.params[0] + wls.params[1] * r["pct_high_needs"]
        resid = r["pct_prof"] - pred
        marker = markers_ach.get(dist_name, "o")
        ax.scatter(r["pct_high_needs"], r["pct_prof"], s=250, color=color, marker=marker,
                   edgecolors="black", linewidths=1.5, zorder=5)
        sign = "+" if resid >= 0 else ""
        ox, oy = label_offsets_ach[label]
        ha = "left" if ox > 0 else "right"
        ax.annotate(f"{label}\n{r['pct_prof']:.1f}% ({sign}{resid:.1f}pp)",
                    (r["pct_high_needs"], r["pct_prof"]),
                    textcoords="offset points", xytext=(ox, oy),
                    ha=ha, va="center", fontsize=8, fontweight="bold", color=color,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=color, alpha=0.9),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=0.8,
                                   connectionstyle="arc3,rad=0.15"))

    ax.set_xlabel("% High-Needs Students", fontsize=11)
    ax.set_ylabel(f"% {subj} Proficient", fontsize=11)
    ax.set_title(f"SBAC {subj} Proficiency vs. Student Need (2024-25)", fontsize=12, fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{x:.0f}%"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{x:.0f}%"))
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", fontsize=8)

fig.text(0.01, 0.01,
         "Source: CT EdSight SBAC 2024-25 & school-level % High Needs.\n"
         "Bubble size ~ enrollment.\n"
         "Best-fit line is weighted by test takers. Values in parentheses = distance from best-fit line.",
         fontsize=6, color="gray", va="bottom")
fig.tight_layout(rect=[0, 0.04, 1, 1])
fig.savefig(os.path.join(FIG_DIR, "part1_fig5_achievement_vs_need.png"), dpi=150, bbox_inches="tight")
print("Saved part1_fig5_achievement_vs_need.png")

# Print residuals for the text
for subj in ["ELA", "Math"]:
    subdf = sbac[sbac["Subject"] == subj][["District", "pct_prof", "n_scored"]].copy()
    subdf = subdf.merge(demo[["district", "pct_high_needs", "enrollment"]],
                        left_on="District", right_on="district", how="inner")
    subdf = subdf.dropna(subset=["pct_prof", "pct_high_needs", "enrollment", "n_scored"])
    X = sm.add_constant(subdf["pct_high_needs"].values)
    wls = sm.WLS(subdf["pct_prof"].values, X,
                 weights=subdf["n_scored"].values).fit()
    for dist in ["Hartford School District", "Capitol Region Education Council", "Meriden School District"]:
        row = subdf[subdf["District"] == dist]
        if len(row) > 0:
            r = row.iloc[0]
            pred = wls.params[0] + wls.params[1] * r["pct_high_needs"]
            resid = r["pct_prof"] - pred
            lbl = dist.split(" School")[0].split(" Education")[0]
            print(f"  {lbl} {subj}: actual={r['pct_prof']:.1f}%, predicted={pred:.1f}%, resid={resid:+.1f}pp")

plt.close("all")
print("\nDone â€” all Part 1 figures saved.")
