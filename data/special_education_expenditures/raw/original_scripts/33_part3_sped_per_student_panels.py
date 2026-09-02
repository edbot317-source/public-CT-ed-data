"""
33_part3_sped_per_student_panels.py

Consolidated per-student special education FUNDING figure (two panels in one),
to match the text in part-3.html, which describes:

  "special education tuition per outplaced student (in the left panel) and
   special education classroom expenditures per in-district special education
   student (right panel)"

  LEFT  panel: special education tuition per outplaced student with disabilities
               (constant 2024-25 dollars).
               Groups: Hartford, Peer Cities, Sheff Region.
               (CREC is a receiving entity and does not outplace, so it is
               omitted from the tuition-per-outplaced panel.)

  RIGHT panel: classroom special education spending per in-district (non-
               outplaced) special education student (constant 2024-25 dollars).
               Groups: Sheff Region, Hartford, CREC, Peer Cities.

Both panels share the FY2018-FY2025 (2017-18 .. 2024-25) window, the only years
with observed district-level outplacement counts. A single consolidated source
note sits beneath the figure.

This supersedes the two separate figures previously emitted by
  25_part3_outplacement_tuition.py  (part3_tuition_per_outplaced.png)
  30_part3_sped_classroom_pp_excl_outplaced.py  (part3_sped_classroom_pp_excl_outplaced.png)
for the combined exhibit. Those scripts are retained for their other outputs.

Input:
    data/special-education-expenditures/sped-exp-new-*.csv   (FY2018-FY2025)
    data/swd-outplacement/swd_district_all_years.csv         (FY2018-FY2025)
    clean-data/district_year_enrollment.csv
    data/cpi-u-annual-avg-fred.csv
Output:
    output/figures/part-3/part3_sped_per_student_panels.png
"""

import glob
import os
import re
import textwrap

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPED_DIR = os.path.join(BASE, "data", "special-education-expenditures")
FIG_DIR = os.path.join(BASE, "output", "figures", "part-3")
os.makedirs(FIG_DIR, exist_ok=True)

BASE_CPI = 321.962  # 2024-25 base year
PRIVATE = "Private Schools or Other Settings"
PUBLIC_OTHER = "Public Schools in Other Districts"

HARTFORD = ["Hartford School District"]
CREC = ["Capitol Region Education Council"]
PEER_CITIES = [
    "Waterbury School District",
    "New Haven School District",
    "Bridgeport School District",
]
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

# Shared district-group palette (consistent across all Part 3 figures).
COLORS = {
    "Hartford": "#d6604d",
    "Peer Cities": "#ff7f0e",
    "Sheff Region": "#4393c3",
    "CREC": "#9467bd",
    "State": "#878787",
}

# Left panel: tuition per outplaced (CREC excluded -- receiving entity).
TUITION_GROUPS = [
    ("Hartford", HARTFORD),
    ("Peer Cities", PEER_CITIES),
    ("Sheff Region", SHEFF_DISTRICTS),
]
# Right panel: classroom spending per non-outplaced sped student.
CLASSROOM_GROUPS = [
    ("Sheff Region", SHEFF_DISTRICTS),
    ("Hartford", HARTFORD),
    ("CREC", CREC),
    ("Peer Cities", PEER_CITIES),
]
# Per-panel vertical label offsets to keep endpoint labels legible.
TUITION_OFFSET = {"Hartford": 10, "Peer Cities": -16, "Sheff Region": 10}
CLASSROOM_OFFSET = {"Sheff Region": 10, "Hartford": -16, "CREC": 10, "Peer Cities": -16}


def fiscal_year_from_filename(path):
    m = re.search(r"(\d{4})-(\d{2})\.csv$", os.path.basename(path))
    if not m:
        raise ValueError(f"Could not parse fiscal year from {path}")
    return int(m.group(1)[:2] + m.group(2))


def fiscal_year_from_school_year(school_year):
    return int("20" + str(school_year).split("-")[1])


def fy_label(fy):
    return f"'{str(int(fy))[-2:]}"


def read_cpi_map():
    cpi_raw = pd.read_csv(os.path.join(BASE, "data", "cpi-u-annual-avg-fred.csv"))
    cpi_raw["year"] = pd.to_datetime(cpi_raw["observation_date"]).dt.year
    return {int(row["year"]) + 1: row["CPIAUCSL"] for _, row in cpi_raw.iterrows()}


def parse_current_sped(path):
    df = pd.read_csv(path, skiprows=2, dtype=str)
    df.columns = df.columns.str.strip().str.strip('"')
    df["District"] = df["District"].str.strip('"').str.strip().replace("", pd.NA).ffill()
    df["Description"] = df["Description"].str.strip('"').str.strip()
    df["value"] = pd.to_numeric(
        df["Amount"].astype(str).str.replace(r'[$,"]', "", regex=True),
        errors="coerce",
    ).fillna(0)
    pivot = df.pivot_table(
        index="District", columns="Description", values="value", aggfunc="sum"
    ).reset_index()
    pivot["fiscal_year"] = fiscal_year_from_filename(path)
    pivot["sped_total"] = pivot.get("Total", 0)
    pivot["sped_tuition"] = pivot.get("Special Education Tuition", 0)
    pivot["sped_transport"] = pivot.get("Purchased Services For Transportation", 0)
    return pivot[["District", "fiscal_year", "sped_total", "sped_tuition", "sped_transport"]]


def load_sped():
    frames = [parse_current_sped(p)
              for p in sorted(glob.glob(os.path.join(SPED_DIR, "sped-exp-new-*.csv")))]
    sped = pd.concat(frames, ignore_index=True)
    sped["sped_classroom"] = sped["sped_total"] - sped["sped_tuition"] - sped["sped_transport"]
    return sped


def load_outplacement():
    path = os.path.join(BASE, "data", "swd-outplacement", "swd_district_all_years.csv")
    df = pd.read_csv(path)
    df["fiscal_year"] = df["School Year"].map(fiscal_year_from_school_year)
    df["count"] = pd.to_numeric(df["Count*"], errors="coerce").fillna(0)
    wide = df.pivot_table(
        index=["DistrictName", "fiscal_year"], columns="Type", values="count",
        aggfunc="sum",
    ).reset_index().fillna(0)
    wide = wide.rename(columns={
        "DistrictName": "District",
        PRIVATE: "private_outplaced",
        PUBLIC_OTHER: "public_outplaced",
    })
    for col in ["private_outplaced", "public_outplaced"]:
        if col not in wide.columns:
            wide[col] = 0.0
    wide["n_outplaced"] = wide["private_outplaced"] + wide["public_outplaced"]
    return wide[["District", "fiscal_year", "n_outplaced"]]


# ---- build dataset ---------------------------------------------------------
sped = load_sped()
outpl = load_outplacement()
enroll = pd.read_csv(os.path.join(BASE, "clean-data", "district_year_enrollment.csv"))
enroll = enroll[["District", "fiscal_year", "n_sped"]].dropna(subset=["n_sped"])
cpi_map = read_cpi_map()

OUTPL_YEARS = sorted(outpl["fiscal_year"].unique())

merged = sped.merge(enroll, on=["District", "fiscal_year"], how="inner")
merged = merged[merged["fiscal_year"].isin(OUTPL_YEARS)].copy()
merged = merged.merge(outpl, on=["District", "fiscal_year"], how="left")
merged["n_outplaced"] = merged["n_outplaced"].fillna(0)
merged["n_nonoutplaced"] = (merged["n_sped"] - merged["n_outplaced"]).clip(lower=0)
merged["cpi_u"] = merged["fiscal_year"].map(cpi_map)
merged = merged.dropna(subset=["cpi_u"])
merged["cpi_factor"] = BASE_CPI / merged["cpi_u"]
merged["sped_tuition_real"] = merged["sped_tuition"] * merged["cpi_factor"]
merged["sped_classroom_real"] = merged["sped_classroom"] * merged["cpi_factor"]


def agg_tuition(label, districts):
    sub = merged[merged["District"].isin(districts)]
    rows = []
    for fy, g in sub.groupby("fiscal_year"):
        n_out = g["n_outplaced"].sum()
        if n_out <= 0:
            continue
        rows.append({"fiscal_year": fy, "group": label,
                     "value": g["sped_tuition_real"].sum() / n_out})
    return pd.DataFrame(rows)


def agg_classroom(label, districts):
    sub = merged[merged["District"].isin(districts)]
    rows = []
    for fy, g in sub.groupby("fiscal_year"):
        n_non = g["n_nonoutplaced"].sum()
        if n_non <= 0:
            continue
        rows.append({"fiscal_year": fy, "group": label,
                     "value": g["sped_classroom_real"].sum() / n_non})
    return pd.DataFrame(rows)


tuition_data = pd.concat([agg_tuition(l, d) for l, d in TUITION_GROUPS], ignore_index=True)
classroom_data = pd.concat([agg_classroom(l, d) for l, d in CLASSROOM_GROUPS], ignore_index=True)
years = sorted(set(tuition_data["fiscal_year"]) | set(classroom_data["fiscal_year"]))


def plot_panel(ax, data, groups, offsets, title, ylabel):
    for label, _ in groups:
        d = data[data["group"] == label].sort_values("fiscal_year")
        if d.empty:
            continue
        ax.plot(d["fiscal_year"], d["value"], marker="o", markersize=5,
                color=COLORS[label], linewidth=2.2, label=label)
        row = d.iloc[-1]
        ax.annotate(f"${row['value']:,.0f}",
                    (row["fiscal_year"], row["value"]),
                    textcoords="offset points", xytext=(0, offsets[label]),
                    ha="center", fontsize=8, fontweight="bold", color=COLORS[label])
    ax.set_xticks(years)
    ax.set_xticklabels([fy_label(y) for y in years], fontsize=9)
    ax.set_title(title, fontsize=12.5, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: f"${v:,.0f}"))
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, fontsize=9, loc="best")
    # Add vertical headroom so endpoint labels (incl. below-line offsets) clear
    # the axis and the legend.
    ymin, ymax = ax.get_ylim()
    pad = (ymax - ymin) * 0.10
    ax.set_ylim(ymin - pad, ymax + pad)


fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(13, 5.8))

plot_panel(
    ax_l, tuition_data, TUITION_GROUPS, TUITION_OFFSET,
    "Special Education Tuition per Outplaced Student",
    "Tuition per outplaced student\nwith disabilities (2024-25 $)",
)
plot_panel(
    ax_r, classroom_data, CLASSROOM_GROUPS, CLASSROOM_OFFSET,
    "Classroom Spending per In-District Special Education Student",
    "Classroom spending per non-outplaced\nspecial education student (2024-25 $)",
)

SRC = (
    "Source: CT EdSight Special Education Expenditures, Students with Disabilities Attending "
    "Out-of-District Schools/Programs, and Enrollment; constant 2024-25 dollars. "
    "Left: special education tuition divided by outplaced students with disabilities. "
    "Right: classroom special education spending (total special education spending minus tuition "
    "and transportation) divided by in-district special education students (enrolled minus outplaced). "
    "Outplaced students attend private schools/other settings or public schools in other districts. "
    "District-level outplacement counts are available from 2017-18 on, so both panels begin in 2017-18. "
    "CREC is a receiving entity and does not outplace, so it is omitted from the tuition panel. "
    "Peer Cities = Waterbury, New Haven, Bridgeport. Sheff Region = Hartford, CREC, and 21 surrounding "
    "districts (pooled)."
)
fig.text(0.5, 0.005, textwrap.fill(SRC, width=135),
         ha="center", va="bottom", fontsize=7.5, color="gray")
fig.tight_layout(rect=[0, 0.16, 1, 1])

out = os.path.join(FIG_DIR, "part3_sped_per_student_panels.png")
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {out}")

print("\n-- Tuition per outplaced student --")
for label, _ in TUITION_GROUPS:
    d = tuition_data[tuition_data["group"] == label].sort_values("fiscal_year")
    first, last = d.iloc[0], d.iloc[-1]
    print(f"  {label}: ${first['value']:,.0f} ({int(first['fiscal_year'])}) -> "
          f"${last['value']:,.0f} ({int(last['fiscal_year'])})")
print("\n-- Classroom spending per non-outplaced sped student --")
for label, _ in CLASSROOM_GROUPS:
    d = classroom_data[classroom_data["group"] == label].sort_values("fiscal_year")
    first, last = d.iloc[0], d.iloc[-1]
    print(f"  {label}: ${first['value']:,.0f} ({int(first['fiscal_year'])}) -> "
          f"${last['value']:,.0f} ({int(last['fiscal_year'])})")
