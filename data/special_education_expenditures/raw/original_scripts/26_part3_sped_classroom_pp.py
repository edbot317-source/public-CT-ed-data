"""
26_part3_sped_classroom_pp.py

Part 3 special education spending figures:
  1. Classroom special education spending per special education student.

All figures use the Part 3 comparison groups:
  Hartford, Peer Cities, Sheff Region, and State.

Input:
    data/special-education-expenditures/
    clean-data/district_year_enrollment.csv
    clean-data/district_year_spending.csv
    data/cpi-u-annual-avg-fred.csv
Output:
    output/figures/part-3/part3_sped_classroom_pp.png
"""

import glob
import os
import re

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPED_DIR = os.path.join(BASE, "data", "special-education-expenditures")
FIG_DIR = os.path.join(BASE, "output", "figures", "part-3")
os.makedirs(FIG_DIR, exist_ok=True)

BASE_CPI = 321.962  # 2024-25 base year

HARTFORD = ["Hartford School District"]
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
GROUPS = [
    ("Hartford", HARTFORD),
    ("Peer Cities", PEER_CITIES),
    ("Sheff Region", SHEFF_DISTRICTS),
    ("State", None),
]
COLORS = {
    "Hartford": "#d6604d",
    "Peer Cities": "#ff7f0e",
    "Sheff Region": "#4393c3",
    "State": "#878787",
}


def fiscal_year_from_filename(path):
    m = re.search(r"(\d{4})-(\d{2})\.csv$", os.path.basename(path))
    if not m:
        raise ValueError(f"Could not parse fiscal year from {path}")
    return int(m.group(1)[:2] + m.group(2))


def fy_label(fy):
    return f"'{str(int(fy))[-2:]}"


def currency(value, decimals=0):
    return f"${value:,.{decimals}f}"


def read_cpi_map():
    cpi_raw = pd.read_csv(os.path.join(BASE, "data", "cpi-u-annual-avg-fred.csv"))
    cpi_raw["year"] = pd.to_datetime(cpi_raw["observation_date"]).dt.year
    return {int(row["year"]) + 1: row["CPIAUCSL"] for _, row in cpi_raw.iterrows()}


def parse_archived_sped(path):
    df = pd.read_csv(path, skiprows=4, dtype=str)
    df.columns = df.columns.str.strip().str.strip('"')
    df = df.rename(columns={df.columns[0]: "District"})
    df["District"] = df["District"].str.lstrip("=").str.strip('"').str.strip()
    df = df[df["District"].str.len() > 0].copy()

    def to_num(col):
        return pd.to_numeric(
            df[col].astype(str).str.replace(r'[$,"]', "", regex=True),
            errors="coerce",
        ).fillna(0)

    df["fiscal_year"] = fiscal_year_from_filename(path)
    df["sped_total"] = to_num("Total Expenditures")
    df["sped_tuition"] = to_num("Tuition to Other Schools")
    df["sped_transport"] = to_num("Transportation")
    return df[["District", "fiscal_year", "sped_total", "sped_tuition", "sped_transport"]]


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


def load_sped_expenditures():
    frames = []
    for year in range(2006, 2017):
        school_year = f"{year}-{str(year + 1)[-2:]}"
        path = os.path.join(SPED_DIR, f"sped-exp-{school_year}.csv")
        if os.path.exists(path):
            frames.append(parse_archived_sped(path))
    for path in sorted(glob.glob(os.path.join(SPED_DIR, "sped-exp-new-*.csv"))):
        frames.append(parse_current_sped(path))
    sped = pd.concat(frames, ignore_index=True)
    sped["sped_classroom"] = (
        sped["sped_total"] - sped["sped_tuition"] - sped["sped_transport"]
    )
    return sped


def aggregate_group(df, label, districts):
    subset = df if districts is None else df[df["District"].isin(districts)]
    if label == "Sheff Region":
        hartford_years = set(
            df.loc[df["District"] == "Hartford School District", "fiscal_year"]
        )
        subset = subset[subset["fiscal_year"].isin(hartford_years)]
    rows = []
    for fy, g in subset.groupby("fiscal_year"):
        n_sped = g["n_sped"].sum()
        if n_sped <= 0:
            continue
        rows.append({
            "fiscal_year": fy,
            "group": label,
            "n_sped": n_sped,
            "sped_classroom_pp": g["sped_classroom_real"].sum() / n_sped,
        })
    return pd.DataFrame(rows)


def plot_lines(ax, data, y_col, ylabel, title, label_values=True):
    years = sorted(data["fiscal_year"].unique())
    for label, _ in GROUPS:
        d = data[data["group"] == label].sort_values("fiscal_year")
        d_plot = d if label == "Hartford" else d.set_index("fiscal_year").reindex(years).reset_index()
        ax.plot(
            d_plot["fiscal_year"],
            d_plot[y_col],
            marker="o",
            markersize=5,
            color=COLORS[label],
            linewidth=2.2,
            label=label,
        )
        if label_values and not d.empty:
            row = d.iloc[-1]
            yoff = 10 if label in ["Hartford", "Peer Cities"] else -16
            ax.annotate(
                currency(row[y_col]),
                (row["fiscal_year"], row[y_col]),
                textcoords="offset points",
                xytext=(0, yoff),
                ha="center",
                fontsize=8,
                fontweight="bold",
                color=COLORS[label],
            )

    ax.set_xticks(years)
    ax.set_xticklabels([fy_label(y) for y in years], fontsize=9)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: f"${v:,.0f}"))
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


sped = load_sped_expenditures()
enroll = pd.read_csv(os.path.join(BASE, "clean-data", "district_year_enrollment.csv"))
enroll = enroll[["District", "fiscal_year", "n_sped"]].dropna(subset=["n_sped"])

cpi_map = read_cpi_map()
merged = sped.merge(enroll, on=["District", "fiscal_year"], how="inner")
merged["cpi_u"] = merged["fiscal_year"].map(cpi_map)
merged = merged.dropna(subset=["cpi_u"])
merged = merged[merged["n_sped"] > 0].copy()
merged["cpi_factor"] = BASE_CPI / merged["cpi_u"]
for col in ["sped_total", "sped_tuition", "sped_transport", "sped_classroom"]:
    merged[f"{col}_real"] = merged[col] * merged["cpi_factor"]

aggs = pd.concat(
    [aggregate_group(merged, label, districts) for label, districts in GROUPS],
    ignore_index=True,
)

print(f"Merged rows: {len(merged):,}")
print(f"Years: {sorted(aggs['fiscal_year'].unique())}")
for label, _ in GROUPS:
    d = aggs[aggs["group"] == label].sort_values("fiscal_year")
    first, last = d.iloc[0], d.iloc[-1]
    print(
        f"{label}: classroom {currency(first['sped_classroom_pp'])} "
        f"({int(first['fiscal_year'])}) -> {currency(last['sped_classroom_pp'])} "
        f"({int(last['fiscal_year'])})"
    )

# Figure 1: classroom special education spending per special education student.
fig, ax = plt.subplots(figsize=(12, 7))
plot_lines(
    ax,
    aggs,
    "sped_classroom_pp",
    "Classroom special education spending / enrolled special education student (2024-25 $)",
    "Classroom Special Education Spending per Enrolled Special Education Student",
)
ax.legend(frameon=False, fontsize=10, loc="best")
fig.text(
    0.5,
    0.01,
    "Source: CT EdSight Special Education Expenditures and Enrollment. "
    "Classroom spending = total special education spending minus tuition and transportation. "
    "Denominator is enrolled special education students. "
    "Hartford and Sheff Region series omit years when Hartford spending data are unavailable. "
    "Peer Cities = Waterbury, New Haven, Bridgeport.",
    ha="center",
    fontsize=8,
    color="gray",
)
fig.tight_layout(rect=[0, 0.04, 1, 1])
out1 = os.path.join(FIG_DIR, "part3_sped_classroom_pp.png")
fig.savefig(out1, dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {out1}")
