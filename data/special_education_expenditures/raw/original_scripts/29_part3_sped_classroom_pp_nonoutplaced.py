"""
29_part3_sped_classroom_pp_nonoutplaced.py

Part 3 special education figure (v2):
  Classroom special education spending per NON-OUTPLACED special education
  student.

  Numerator  = total SpEd spending - SpEd tuition - SpEd transportation
               (the in-house "classroom" component), inflation-adjusted.
  Denominator = enrolled SpEd students - outplaced SpEd students
               (private/other settings + public schools in other districts).

Comparison groups (per Seth's request):
  Sheff Region, HPS (Hartford), CREC, Peer Cities.

Window: non-CREC groups run FY2008-FY2025 (school years 2007-08 .. 2024-25);
CREC runs FY2018-FY2025 (CREC reports SpEd expenditures only from 2017-18 on).

Denominator detail: district-level outplacement counts only exist from FY2018
(2017-18) on -- that is the earliest year CT EdSight's outplacement report
exposes. For FY2008-FY2017 we backcast each district's outplaced count by
holding its earliest observed (FY2018) outplaced SHARE of SpEd enrollment
constant. This keeps the series continuous at the FY2018 data boundary and
stays district-specific. CREC does not appear in the outplacement export -- as
a receiving entity it does not outplace students -- so its outplaced count is 0
(non-outplaced = enrolled SpEd).

Input:
    data/special-education-expenditures/sped-exp-*.csv
    data/swd-outplacement/swd_district_all_years.csv
    clean-data/district_year_enrollment.csv
    data/cpi-u-annual-avg-fred.csv
Output:
    output/figures/part-3/part3_sped_classroom_pp_nonoutplaced.png
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
GROUPS = [
    ("Sheff Region", SHEFF_DISTRICTS),
    ("HPS", HARTFORD),
    ("CREC", CREC),
    ("Peer Cities", PEER_CITIES),
]
COLORS = {
    "Sheff Region": "#4393c3",
    "HPS": "#d6604d",
    "CREC": "#1b7837",
    "Peer Cities": "#ff7f0e",
}
# vertical offset for end-of-line value labels (avoid overlap)
LABEL_OFFSET = {
    "Sheff Region": -16,
    "HPS": 10,
    "CREC": 10,
    "Peer Cities": -16,
}


def fiscal_year_from_filename(path):
    m = re.search(r"(\d{4})-(\d{2})\.csv$", os.path.basename(path))
    if not m:
        raise ValueError(f"Could not parse fiscal year from {path}")
    return int(m.group(1)[:2] + m.group(2))


def fiscal_year_from_school_year(school_year):
    return int("20" + str(school_year).split("-")[1])


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
    """Archived wide files (FY2007-FY2017) + line-item files (FY2018-FY2025).
    Archived years carry the non-CREC history back to 2007-08; the line-item
    files carry CREC and align with the outplacement window."""
    frames = []
    for year in range(2006, 2017):  # archived files: 2006-07 .. 2016-17
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


def load_outplacement():
    path = os.path.join(BASE, "data", "swd-outplacement", "swd_district_all_years.csv")
    df = pd.read_csv(path)
    df["fiscal_year"] = df["School Year"].map(fiscal_year_from_school_year)
    df["count"] = pd.to_numeric(df["Count*"], errors="coerce").fillna(0)
    counts = df.pivot_table(
        index=["DistrictName", "fiscal_year"],
        columns="Type",
        values="count",
        aggfunc="sum",
    ).reset_index().fillna(0)
    counts = counts.rename(columns={
        "DistrictName": "District",
        PRIVATE: "private_outplaced",
        PUBLIC_OTHER: "public_outplaced",
    })
    for col in ["private_outplaced", "public_outplaced"]:
        if col not in counts.columns:
            counts[col] = 0.0
    return counts[["District", "fiscal_year", "private_outplaced", "public_outplaced"]]


def aggregate_group(df, label, districts):
    subset = df[df["District"].isin(districts)].copy()
    rows = []
    for fy, g in subset.groupby("fiscal_year"):
        n_nonout = g["n_nonoutplaced"].sum()
        if n_nonout <= 0:
            continue
        rows.append({
            "fiscal_year": fy,
            "group": label,
            "n_nonoutplaced": n_nonout,
            "sped_classroom_pp": g["sped_classroom_real"].sum() / n_nonout,
        })
    return pd.DataFrame(rows)


def plot_lines(ax, data, y_col, ylabel, title):
    years = sorted(data["fiscal_year"].unique())
    for label, _ in GROUPS:
        d = data[data["group"] == label].sort_values("fiscal_year")
        if d.empty:
            continue
        ax.plot(
            d["fiscal_year"], d[y_col], marker="o", markersize=5,
            color=COLORS[label], linewidth=2.2, label=label,
        )
        row = d.iloc[-1]
        ax.annotate(
            currency(row[y_col]),
            (row["fiscal_year"], row[y_col]),
            textcoords="offset points",
            xytext=(0, LABEL_OFFSET[label]),
            ha="center", fontsize=8, fontweight="bold", color=COLORS[label],
        )
    ax.set_xticks(years)
    ax.set_xticklabels([fy_label(y) for y in years], fontsize=9)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: f"${v:,.0f}"))
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# ---- build dataset ---------------------------------------------------------
sped = load_sped_expenditures()
enroll = pd.read_csv(os.path.join(BASE, "clean-data", "district_year_enrollment.csv"))
enroll = enroll[["District", "fiscal_year", "n_sped"]].dropna(subset=["n_sped"])
outpl = load_outplacement()

cpi_map = read_cpi_map()

merged = sped.merge(enroll, on=["District", "fiscal_year"], how="inner")
# left-merge observed outplacement (FY2018+); districts/years with no outplaced
# rows (incl. CREC) legitimately have zero outplaced students for that year.
merged = merged.merge(outpl, on=["District", "fiscal_year"], how="left")
merged[["private_outplaced", "public_outplaced"]] = (
    merged[["private_outplaced", "public_outplaced"]].fillna(0)
)
merged["n_outplaced_obs"] = merged["private_outplaced"] + merged["public_outplaced"]

# Backcast pre-FY2018 outplacement: hold each district's earliest observed
# (FY2018) outplaced SHARE of SpEd enrollment constant for FY2008-FY2017.
FIRST_OBS_FY = int(outpl["fiscal_year"].min())  # 2018
base = merged[merged["fiscal_year"] == FIRST_OBS_FY].copy()
base["outplaced_share"] = (base["n_outplaced_obs"] / base["n_sped"]).clip(0, 1)
share_map = dict(zip(base["District"], base["outplaced_share"]))

merged["outplaced_share_base"] = merged["District"].map(share_map).fillna(0.0)
merged["n_outplaced"] = merged["n_outplaced_obs"].where(
    merged["fiscal_year"] >= FIRST_OBS_FY,
    merged["n_sped"] * merged["outplaced_share_base"],
)
merged["n_nonoutplaced"] = (merged["n_sped"] - merged["n_outplaced"]).clip(lower=0)

merged["cpi_u"] = merged["fiscal_year"].map(cpi_map)
merged = merged.dropna(subset=["cpi_u"])
merged = merged[merged["n_nonoutplaced"] > 0].copy()
merged["cpi_factor"] = BASE_CPI / merged["cpi_u"]
merged["sped_classroom_real"] = merged["sped_classroom"] * merged["cpi_factor"]

aggs = pd.concat(
    [aggregate_group(merged, label, districts) for label, districts in GROUPS],
    ignore_index=True,
)

print(f"Merged district-year rows: {len(merged):,}")
print(f"Years: {sorted(aggs['fiscal_year'].unique())}")
for label, _ in GROUPS:
    d = aggs[aggs["group"] == label].sort_values("fiscal_year")
    if d.empty:
        print(f"{label}: NO DATA")
        continue
    first, last = d.iloc[0], d.iloc[-1]
    print(
        f"{label}: {currency(first['sped_classroom_pp'])} ({int(first['fiscal_year'])})"
        f" -> {currency(last['sped_classroom_pp'])} ({int(last['fiscal_year'])})"
    )

# ---- figure ----------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 7))
plot_lines(
    ax,
    aggs,
    "sped_classroom_pp",
    "Classroom special education spending / non-outplaced special education student (2024-25 $)",
    "Classroom Special Education Spending per Non-Outplaced Special Education Student",
)
ax.legend(frameon=False, fontsize=10, loc="best")
fig.text(
    0.5,
    0.01,
    "Source: CT EdSight Special Education Expenditures, Students with Disabilities Attending "
    "Out-of-District Schools/Programs, and Enrollment. Classroom spending = total special "
    "education spending minus tuition and transportation (2024-25 dollars). Denominator = enrolled "
    "special education students minus outplaced students (private/other settings + public schools in "
    "other districts). District outplacement counts exist from 2017-18 on; for earlier years each "
    "district's outplaced share of SpEd enrollment is held at its 2017-18 value. CREC does not "
    "outplace and is absent from the outplacement export, so its outplaced count is zero; CREC "
    "reports SpEd expenditures only from 2017-18 on. Peer Cities = Waterbury, New Haven, Bridgeport. "
    "Sheff Region = Hartford, CREC, and 21 surrounding districts (pooled).",
    ha="center",
    fontsize=7,
    color="gray",
)
fig.tight_layout(rect=[0, 0.05, 1, 1])
out = os.path.join(FIG_DIR, "part3_sped_classroom_pp_nonoutplaced.png")
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {out}")
