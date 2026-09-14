"""
71_clean_seda_ct.py

Builds a tidy Connecticut panel of SEDA 2025.2 administrative-district achievement
(GCS scale, grades 3-8 pooled) and maps each estimate to the ECS town it serves.

    clean-data/district_year_seda_gcs.csv
        sedaadmin (NCES LEA id), district (SEDA name), fiscal_year (spring test year),
        subgroup (all / ecd / nec / race groups ...), tot_asmts,
        gcs_mn_avg_eb, gcs_mn_avg_eb_se, gcs_mn_avg_ol, gcs_mn_avg_ol_se,
        grade_levels_vs_national (= gcs_mn_avg_eb - gradecenter, i.e. grade-level units
        above (+) or below (-) the national average for the same grades),
        math / rla versions of the same from the by-subject file,
        town_code, town, town_match ("local district" | "regional district" | "")

Town mapping. Town boards of education are matched by name ("<Town> School
District"). Towns whose grades 3-8 are educated in a K-12 regional district are
mapped to that region's estimate (Regions 10, 12, 13, 14, 15, 16, 17, 18, 20).
Towns whose small K-6/K-8 district has no SEDA estimate in a year (SEDA suppresses
small cells) stay unmatched for that year; secondary-only regions (grades 7-12 or
9-12) are left as districts without a town. Charter, magnet and RESC districts are
kept as rows with no town.

Scale. GCS ("grade cohort standardized"): the national average for grade g equals
g, so a district score minus the file's gradecenter (5.5 for grades 3-8 pooled) is
its distance from the national average in grade levels. SEDA recommends the
empirical-Bayes (_eb) estimates; the OLS (_ol) values are kept alongside.
"""

import os

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "seda")
OUT = os.path.join(BASE, "clean-data")

# K-12 regional school districts (grades 3-8 are tested in the region) -> member towns
REGIONAL_K12 = {
    "Regional School District 10": ["Burlington", "Harwinton"],
    "Regional School District 12": ["Bridgewater", "Roxbury", "Washington"],
    "Regional School District 13": ["Durham", "Middlefield"],
    "Regional School District 14": ["Bethlehem", "Woodbury"],
    "Regional School District 15": ["Middlebury", "Southbury"],
    "Regional School District 16": ["Beacon Falls", "Prospect"],
    "Regional School District 17": ["Haddam", "Killingworth"],
    "Regional School District 18": ["Lyme", "Old Lyme"],
    "Regional School District 20": ["Goshen", "Litchfield", "Morris", "Warren"],   # Litchfield + former Region 6, from 2024-25
    "Regional School District 06": ["Goshen", "Morris", "Warren"],               # through 2023-24
}


def main():
    towns = pd.read_csv(os.path.join(BASE, "clean-data", "town_year_ecs_inputs.csv"))[["town_code", "town"]].drop_duplicates()
    name_to_code = dict(zip(towns.town, towns.town_code))

    a = pd.read_csv(os.path.join(RAW, "seda_admindist_annual_gcs_2025.2_CT.csv"))
    a = a[a.subcat.isin(["all", "ecd", "race"])].copy()
    a["grade_levels_vs_national"] = a["gcs_mn_avg_eb"] - a["gradecenter"]
    a["grade_levels_vs_national_ol"] = a["gcs_mn_avg_ol"] - a["gradecenter"]
    keep = ["sedaadmin", "sedaadminname", "year", "subcat", "subgroup", "gradecenter", "tot_asmts",
            "gcs_mn_avg_eb", "gcs_mn_avg_eb_se", "gcs_mn_avg_ol", "gcs_mn_avg_ol_se",
            "grade_levels_vs_national", "grade_levels_vs_national_ol"]
    a = a[keep]

    s = pd.read_csv(os.path.join(RAW, "seda_admindist_annualsub_gcs_2025.2_CT.csv"))
    s = s[s.subcat.isin(["all", "ecd", "race"])].copy()
    for subj in ("mth", "rla"):
        s[f"grade_levels_vs_national_{subj}"] = s[f"gcs_mn_avg_{subj}_eb"] - s["gradecenter"]
    s = s[["sedaadmin", "year", "subgroup", "gcs_mn_avg_mth_eb", "gcs_mn_avg_mth_eb_se",
           "gcs_mn_avg_rla_eb", "gcs_mn_avg_rla_eb_se", "grade_levels_vs_national_mth", "grade_levels_vs_national_rla"]]
    df = a.merge(s, on=["sedaadmin", "year", "subgroup"], how="left")
    df = df.rename(columns={"sedaadminname": "district", "year": "fiscal_year"})

    # town mapping
    rows = []
    for _, r in df.drop_duplicates(["sedaadmin", "district"]).iterrows():
        name = r["district"]
        local = name.replace(" School District", "") if name.endswith(" School District") else None
        if local in name_to_code:
            rows.append((r["sedaadmin"], name_to_code[local], local, "local district", None, None))
        elif name in REGIONAL_K12:
            for t in REGIONAL_K12[name]:
                lo, hi = (None, 2024) if name.endswith("06") else ((2025, None) if name.endswith("20") else (None, None))
                rows.append((r["sedaadmin"], name_to_code[t], t, "regional district", lo, hi))
    m = pd.DataFrame(rows, columns=["sedaadmin", "town_code", "town", "town_match", "yr_from", "yr_to"])
    out = df.merge(m, on="sedaadmin", how="left")
    for c in ("yr_from", "yr_to"):
        out[c] = pd.to_numeric(out[c], errors="coerce")
    ok = ((out["yr_from"].isna()) | (out["fiscal_year"] >= out["yr_from"])) & ((out["yr_to"].isna()) | (out["fiscal_year"] <= out["yr_to"]))
    out.loc[~ok, ["town_code", "town", "town_match"]] = [None, None, None]
    out = out.drop(columns=["yr_from", "yr_to"]).drop_duplicates(["sedaadmin", "fiscal_year", "subgroup", "town_code"])
    # a town gets at most one estimate per year: local board first, else region
    out["town_match"] = out["town_match"].fillna("")
    out = out.sort_values(["fiscal_year", "subgroup", "town_code", "town_match"]).reset_index(drop=True)
    dup = out[out.town_code.notna()].duplicated(["fiscal_year", "subgroup", "town_code"], keep="first")
    if dup.any():
        out = out[~(out.town_code.notna() & dup)]
    out["town_code"] = out["town_code"].astype("Int64")
    out.to_csv(os.path.join(OUT, "district_year_seda_gcs.csv"), index=False)
    allst = out[(out.subgroup == "all")]
    print(f"[write] district_year_seda_gcs.csv: {len(out)} rows; districts {out.sedaadmin.nunique()}; years {sorted(out.fiscal_year.unique())}")
    for fy in (2019, 2022, 2023, 2024, 2025):
        d = allst[allst.fiscal_year == fy]
        print(f"  FY{fy}: {len(d)} districts, towns matched {d.town_code.notna().sum()} "
              f"({(d.town_match=='local district').sum()} local, {(d.town_match=='regional district').sum()} via region)")
    d25 = allst[allst.fiscal_year == 2025]
    missing = sorted(set(towns.town) - set(d25.town.dropna()))
    print(f"  FY2025 towns without an estimate ({len(missing)}): {missing}")


if __name__ == "__main__":
    main()
