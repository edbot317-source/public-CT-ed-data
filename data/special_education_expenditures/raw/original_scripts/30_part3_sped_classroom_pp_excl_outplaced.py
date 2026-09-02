"""
30_part3_sped_classroom_pp_excl_outplaced.py

Part 3 special education figure: classroom special education spending per
NON-OUTPLACED special education student.

  Numerator   = total SpEd spending - SpEd tuition - SpEd transportation
                (the in-house "classroom" component), inflation-adjusted to
                2024-25 dollars.
  Denominator = enrolled SpEd students - SpEd students outplaced to
                PRIVATE/other settings (APSEPs, nonpublic, hospital/homebound,
                residential, out-of-state). This is the count of SpEd students
                educated in the district's OWN public schools.

This is the companion to 26_part3_sped_classroom_pp.py (enrolled denominator).
The point: EdSight's district-level SpEd enrollment count (PSIS Reporting
District, X1) INCLUDES students the district outplaces to private/nonpublic
settings (X3), but the classroom numerator strips out the tuition and
transportation spent on those same students. Dividing classroom spending by
(X1 - X3) removes that mismatch.

CRITICAL (verified against EdSight methodology, 2026-08-14): X1 does NOT include
SpEd students who attend charter schools, RESC/interdistrict magnet schools, or
public schools/programs in OTHER districts (the "Public Schools in Other
Districts" outplacement bucket, X2) -- those students are reported to CSDE by
the receiving entity, not by the resident district. Because X2 was never in X1,
subtracting it double-removes and understates the denominator. We therefore
subtract ONLY X3. See docs/sped_classroom_pp_construction.md for sources/quotes.

NO BACKCAST. District-level outplacement counts only exist in EdSight from
2017-18 (FY2018) on, so this figure runs FY2018-FY2025 only. No assumptions are
made about earlier years.

Comparison groups (per Seth's request):
    Sheff Region, HPS (Hartford), CREC, Peer Cities (Waterbury, New Haven, Bridgeport).

CREC reports SpEd expenditures only from 2017-18 on and, as a receiving entity,
does not appear in the outplacement export, so its outplaced count is zero
(non-outplaced = enrolled SpEd).

Input:
    data/special-education-expenditures/sped-exp-new-*.csv   (FY2018-FY2025)
    data/swd-outplacement/swd_district_all_years.csv         (FY2018-FY2025)
    clean-data/district_year_enrollment.csv
    data/cpi-u-annual-avg-fred.csv
Output:
    output/figures/part-3/part3_sped_classroom_pp_excl_outplaced.png
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

# EdSight small-cell suppression: outplacement counts of 1-5 students are masked
# (blank Count*). EdSight emits an explicit 0 for a genuine zero, so a blank is
# NOT zero -- it is a hidden count in [1, 5]. Impute the midpoint (3) for point
# estimates, consistent with the enrollment imputation in scripts 07/11/17/37-39.
# (Hartford has no suppressed outplacement cells, so the HPS non-outplaced
# denominator and the $16,478 per-pupil figure are unaffected by this choice.)
SUPPRESSION_IMPUTE_MID = 3  # midpoint of CT's 1-5 suppressed range (threshold = 6)

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
    ("Hartford", HARTFORD),
    ("CREC", CREC),
    ("Peer Cities", PEER_CITIES),
]
# Shared district-group palette (consistent across all Part 3 figures).
COLORS = {
    "Hartford": "#d6604d",
    "Peer Cities": "#ff7f0e",
    "Sheff Region": "#4393c3",
    "CREC": "#1b7837",
    "State": "#878787",
}
LABEL_OFFSET = {
    "Sheff Region": 10,
    "Hartford": 10,
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
    # Same-year merge: fiscal_year 2025 (2024-25 school year) uses calendar-2025
    # CPI, matching the cleaning scripts (e.g. 01_clean_district.py). The base
    # year must therefore have a deflator of exactly 1.0.
    return {int(row["year"]): row["CPIAUCSL"] for _, row in cpi_raw.iterrows()}


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
    """Line-item files only (FY2018-FY2025) -- the window with outplacement data."""
    frames = []
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
    # Blank Count* = suppressed 1-5 (not zero); impute the midpoint of the range.
    df["count"] = pd.to_numeric(df["Count*"], errors="coerce").fillna(SUPPRESSION_IMPUTE_MID)
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
    subset = df if districts is None else df[df["District"].isin(districts)]
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

# Restrict to the outplacement window (FY2018-FY2025): the only years with
# observed district-level outplacement counts. No backcast.
OUTPL_YEARS = sorted(outpl["fiscal_year"].unique())
cpi_map = read_cpi_map()
assert abs(BASE_CPI / cpi_map[2025] - 1) < 1e-9, "CPI base-year factor must be 1.0"

merged = sped.merge(enroll, on=["District", "fiscal_year"], how="inner")
merged = merged[merged["fiscal_year"].isin(OUTPL_YEARS)].copy()
# Left-merge observed outplacement; districts/years absent from the outplacement
# export genuinely have zero outplaced SpEd students that year.
merged = merged.merge(outpl, on=["District", "fiscal_year"], how="left")
merged[["private_outplaced", "public_outplaced"]] = (
    merged[["private_outplaced", "public_outplaced"]].fillna(0)
)
# EdSight SpEd enrollment (X1, PSIS Reporting District) already EXCLUDES students
# outplaced to charter/magnet/other-district public schools (X2 = public_outplaced),
# since those are reported by the receiving entity. X1 DOES include students
# outplaced to private/nonpublic settings (X3 = private_outplaced). So the count
# educated in the district's own public schools is X1 - X3. Do NOT subtract X2.
merged["n_outplaced"] = merged["private_outplaced"]
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
fig, ax = plt.subplots(figsize=(10, 6))
plot_lines(
    ax,
    aggs,
    "sped_classroom_pp",
    "Classroom special education spending /\nnon-outplaced special education student (2024-25 $)",
    "Classroom Special Education Spending per Non-Outplaced Special Education Student",
)
ax.legend(frameon=False, fontsize=10, loc="best")
SRC = (
    "Source: CT EdSight Special Education Expenditures, Students with Disabilities Attending "
    "Out-of-District Schools/Programs, and Enrollment. Classroom spending = total special "
    "education spending minus tuition and transportation (constant 2024-25 dollars). Denominator = "
    "enrolled special education students minus those outplaced to private/nonpublic settings "
    "(APSEPs, nonpublic schools, hospital/homebound, residential, out-of-state); students who "
    "attend charter, magnet, or other-district public schools are already excluded from EdSight's "
    "district-level enrollment count. District-level outplacement counts are available from 2017-18 on, "
    "so the figure begins in 2017-18. Outplacement counts of five or fewer students are suppressed by "
    "EdSight and imputed at three (the midpoint of the suppressed range); Hartford has no suppressed "
    "counts, so its per-student figure is unaffected. Peer Cities = Waterbury, New Haven, Bridgeport. "
    "Sheff Region = Hartford, CREC, and 21 surrounding districts (pooled)."
)
fig.text(0.5, 0.005, textwrap.fill(SRC, width=110),
         ha="center", va="bottom", fontsize=7, color="gray")
fig.tight_layout(rect=[0, 0.17, 1, 1])
out = os.path.join(FIG_DIR, "part3_sped_classroom_pp_excl_outplaced.png")
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {out}")
