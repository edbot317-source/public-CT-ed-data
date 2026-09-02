"""
27_download_swd_outplacement.py

Download CT EdSight "Students with Disabilities Attending Out-of-District
Schools/Programs" data from the SAS Visual Analytics report.

Public landing page:
    https://public-edsight.ct.gov/students/primary-disability/out-of-district
Underlying SAS VA report:
    https://edsight-v.ct.gov/SWDOutOfDistrictReport.html
    reportUri = /reports/reports/1cae4b85-9a58-48e8-a2e8-699bee1d077b

The report is JavaScript-rendered and does not expose the older EdSight CSV
endpoint. We use Playwright to load the report, then the SAS VA component API:

    reportHandle.getObjectHandle('ve168').getData()  # State crosstab
    reportHandle.getObjectHandle('ve122').getData()  # District crosstab

The District page has a multi-select year listbox with 2024-25 selected by
default. A simple click on another year creates a mixed two-year export. This
script explicitly clears currently selected years, selects exactly one target
year, waits until ve122.getData() reports only that year, then saves and
validates the resulting district data.

Outputs:
    data/swd-outplacement/swd_state_timeseries.xlsx
    data/swd-outplacement/swd_district_YYYY-YY.xlsx
    data/swd-outplacement/swd_district_all_years.csv
    data/swd-outplacement/swd_district_all_years.xlsx
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import pandas as pd
from playwright.sync_api import Page, sync_playwright


BASE = Path(__file__).resolve().parent.parent
OUT_DIR = BASE / "data" / "swd-outplacement"
OUT_DIR.mkdir(parents=True, exist_ok=True)

REPORT_URL = "https://edsight-v.ct.gov/SWDOutOfDistrictReport.html"
YEARS = [
    "2024-25",
    "2023-24",
    "2022-23",
    "2021-22",
    "2020-21",
    "2019-20",
    "2018-19",
    "2017-18",
]

STATE_VE = "ve168"
DISTRICT_VE = "ve122"
SAS_MISSING = 1.7976931348623155e308


def render_wait(page: Page, need: int = 2, tmax: int = 90) -> int:
    """Wait until at least `need` canvas elements have non-trivial size."""
    deadline = time.time() + tmax
    while time.time() < deadline:
        n = page.evaluate(
            """() => {
              let acc=0;
              function w(r){let k=[];try{k=Array.from(r.children||[])}catch{}
                for(const c of k){
                  if(c.tagName==='CANVAS'){
                    const b=c.getBoundingClientRect();
                    if(b.width>50 && b.height>50) acc++;
                  }
                  w(c); if(c.shadowRoot) w(c.shadowRoot);
                }
              }
              w(document.body); return acc;
            }"""
        )
        if n >= need:
            return n
        time.sleep(1)
    return n


def click_stack_button(page: Page, label: str) -> bool:
    """Click a SAS VA stack button, e.g. 'State' or 'District'."""
    return page.evaluate(
        """(label) => {
          function w(root){let k=[];try{k=Array.from(root.children||[])}catch{}
            for(const c of k){
              if(c.tagName==='BUTTON' && (c.textContent||'').trim()===label){
                c.click(); return true;
              }
              if(w(c)) return true;
              if(c.shadowRoot && w(c.shadowRoot)) return true;
            }
            return false;
          }
          return w(document.body);
        }""",
        label,
    )


def open_year_listbox(page: Page) -> None:
    ok = page.evaluate(
        """() => {
          const hits=[];
          function w(root){let k=[];try{k=Array.from(root.children||[])}catch{}
            for(const c of k){
              const role=c.getAttribute&&c.getAttribute('role');
              const a=c.getAttribute&&c.getAttribute('aria-label');
              if(role==='combobox' && a==='Select Year'){
                const r=c.getBoundingClientRect();
                if(r.width>0 && r.height>0) hits.push(c);
              }
              w(c); if(c.shadowRoot) w(c.shadowRoot);
            }
          }
          w(document.body);
          if(hits[0]){ hits[0].click(); return true; }
          return false;
        }"""
    )
    if not ok:
        raise RuntimeError("Could not open District year listbox")
    time.sleep(0.4)


def visible_year_rows(page: Page) -> list[dict]:
    rows = page.evaluate(
        """() => {
          const out=[];
          function w(root){let k=[];try{k=Array.from(root.children||[])}catch{}
            for(const c of k){
              const role=c.getAttribute&&c.getAttribute('role');
              const txt=(c.textContent||'').replace(/\\s+/g,' ').trim();
              if(role==='row' && /^20\\d\\d-\\d\\d$/.test(txt)){
                const r=c.getBoundingClientRect();
                if(r.width>20 && r.height>5){
                  out.push({
                    text: txt,
                    selected: c.getAttribute('aria-selected') === 'true',
                    x: r.x + r.width/2,
                    y: r.y + r.height/2
                  });
                }
              }
              w(c); if(c.shadowRoot) w(c.shadowRoot);
            }
          }
          w(document.body);
          return out.sort((a,b)=>a.y-b.y);
        }"""
    )
    if not rows:
        raise RuntimeError("No year rows found in District listbox")
    return rows


def click_year_row(page: Page, year: str, rows: list[dict] | None = None) -> None:
    rows = visible_year_rows(page) if rows is None else rows
    match = next((r for r in rows if r["text"] == year), None)
    if not match:
        raise RuntimeError(f"Year {year} not visible in District listbox")
    page.mouse.click(match["x"], match["y"])
    time.sleep(0.45)


def current_district_years(page: Page) -> set[str]:
    result = get_visual_data(page, DISTRICT_VE)
    if result.empty:
        return set()
    return set(result["School Year"].dropna().astype(str).unique())


def set_single_year(page: Page, year: str) -> None:
    """Set the District listbox to exactly one selected school year."""
    open_year_listbox(page)
    rows = visible_year_rows(page)

    for row in rows:
        if row["selected"] and row["text"] != year:
            click_year_row(page, row["text"], rows=visible_year_rows(page))

    rows = visible_year_rows(page)
    target = next((r for r in rows if r["text"] == year), None)
    if target is None:
        raise RuntimeError(f"Year {year} is not available")
    if not target["selected"]:
        click_year_row(page, year, rows=rows)

    page.keyboard.press("Escape")

    deadline = time.time() + 45
    while time.time() < deadline:
        years = current_district_years(page)
        if years == {year}:
            return
        time.sleep(1)
    raise RuntimeError(f"District data did not settle to {year}; current years={sorted(years)}")


def get_visual_data(page: Page, visual_id: str) -> pd.DataFrame:
    payload = page.evaluate(
        """async (visualId) => {
          const sr = document.getElementById('my-report');
          const rh = await sr.getReportHandle();
          const oh = await rh.getObjectHandle(visualId);
          const got = await oh.getData();
          if(!got || !got[0]) return {columns: [], data: []};
          return {
            columns: got[0].columns.map(c => c.label || c.name),
            data: got[0].data || []
          };
        }""",
        visual_id,
    )
    df = pd.DataFrame(payload["data"], columns=payload["columns"])
    return clean_sas_missing(df)


def clean_sas_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Convert SAS VA's floating max sentinel to missing values."""
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_numeric_dtype(out[col]):
            out[col] = out[col].mask(out[col].map(is_sas_missing))
    return out


def is_sas_missing(value) -> bool:
    try:
        return math.isclose(float(value), SAS_MISSING, rel_tol=0, abs_tol=1e292)
    except (TypeError, ValueError):
        return False


def save_xlsx(df: pd.DataFrame, path: Path) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Results", index=False)


def validate_state(state_df: pd.DataFrame) -> None:
    required = {"Type", "School Year", "State Count", "State Percent"}
    missing = required - set(state_df.columns)
    if missing:
        raise RuntimeError(f"State data missing columns: {sorted(missing)}")
    years = set(state_df["School Year"].astype(str).unique())
    if years != set(YEARS):
        raise RuntimeError(f"State data has wrong years: {sorted(years)}")


def validate_district_year(district_df: pd.DataFrame, state_df: pd.DataFrame, year: str) -> None:
    required = {"School Year", "Type", "DistrictName", "Count*", "Percent*"}
    missing = required - set(district_df.columns)
    if missing:
        raise RuntimeError(f"District data for {year} missing columns: {sorted(missing)}")

    years = set(district_df["School Year"].astype(str).unique())
    if years != {year}:
        raise RuntimeError(f"District data for {year} contains years {sorted(years)}")

    totals = district_df[district_df["DistrictName"] == "State Total"].copy()
    if len(totals) != 2:
        raise RuntimeError(f"District data for {year} has {len(totals)} State Total rows")

    state_year = state_df[state_df["School Year"].astype(str) == year].copy()
    for _, row in state_year.iterrows():
        typ = row["Type"]
        total_row = totals[totals["Type"] == typ]
        if len(total_row) != 1:
            raise RuntimeError(f"District data for {year} missing State Total for {typ}")
        got_count = float(total_row.iloc[0]["Count*"])
        got_pct = float(total_row.iloc[0]["Percent*"])
        want_count = float(row["State Count"])
        want_pct = float(row["State Percent"])
        if not math.isclose(got_count, want_count, rel_tol=0, abs_tol=1e-9):
            raise RuntimeError(f"{year} {typ}: district State Total count {got_count} != state {want_count}")
        if not math.isclose(got_pct, want_pct, rel_tol=0, abs_tol=0.11):
            raise RuntimeError(f"{year} {typ}: district State Total percent {got_pct} != state {want_pct}")


def main(headless: bool = True, years: list[str] | None = None) -> None:
    years = YEARS if years is None else years

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=150 if not headless else 0)
        ctx = browser.new_context(
            viewport={"width": 1600, "height": 1000},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
        )
        page = ctx.new_page()
        print(f"[+] loading {REPORT_URL}")
        page.goto(REPORT_URL, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_selector("sas-report", timeout=30_000)
        print(f"    rendered (canvases={render_wait(page)})")

        print("[+] reading State crosstab")
        state_df = get_visual_data(page, STATE_VE)
        validate_state(state_df)
        state_path = OUT_DIR / "swd_state_timeseries.xlsx"
        save_xlsx(state_df, state_path)
        print(f"    -> {state_path.name} ({len(state_df):,} rows)")

        print("[+] activating District crosstab")
        if not click_stack_button(page, "District"):
            raise RuntimeError("Could not activate District tab")
        time.sleep(3)

        all_district = []
        for year in years:
            print(f"[+] reading District crosstab for {year}")
            set_single_year(page, year)
            district_df = get_visual_data(page, DISTRICT_VE)
            validate_district_year(district_df, state_df, year)
            out_path = OUT_DIR / f"swd_district_{year}.xlsx"
            save_xlsx(district_df, out_path)
            all_district.append(district_df)
            print(f"    -> {out_path.name} ({len(district_df):,} rows)")

        combined = pd.concat(all_district, ignore_index=True)
        csv_path = OUT_DIR / "swd_district_all_years.csv"
        xlsx_path = OUT_DIR / "swd_district_all_years.xlsx"
        combined.to_csv(csv_path, index=False)
        save_xlsx(combined, xlsx_path)
        print(f"[+] combined district file: {csv_path.name} ({len(combined):,} rows)")

        page.screenshot(path=str(OUT_DIR / "_final_district_tab.png"), full_page=True)
        browser.close()


if __name__ == "__main__":
    headless_flag = "--headed" not in sys.argv
    requested_years = [arg for arg in sys.argv[1:] if arg in YEARS]
    main(headless=headless_flag, years=requested_years or None)
