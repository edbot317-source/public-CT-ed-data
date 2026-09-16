"""Summary tables for the Chapter 70 rule applied to Connecticut (writes output/ecs/ma_chapter70_results.md)."""
import os, sys, json
import numpy as np, pandas as pd
sys.argv = ["x"]; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_sim as R
import ma_chapter70 as M
D = R.D; towns = D["towns"]; YEARS = R.YEARS
lines = []
def say(s=""): print(s); lines.append(s)
say("# Massachusetts Chapter 70 rule applied to Connecticut towns: results\n")
say("Engine: sim/ma_chapter70.py (validated against DESE's FY2025 workbook: Plymouth foundation budget exact; statewide contribution solve reproduces DESE's uniform rates and all 351 municipal targets within $1). Scenario: 'ma' from FY2019, lambda = 0.59, minimum aid $104, CPI-U index, steady-state contributions.\n")
en = {fy: 0 for fy in YEARS}; ma = {fy: 0 for fy in YEARS}
series_en = {t["code"]: R.series(t, R.enacted_params) for t in towns}
series_ma = {t["code"]: R.series(t, lambda fy: R.scenario_params(fy, {"ma"}, 2019, {})) for t in towns}
say("## Statewide, nominal dollars\n")
say("| FY | foundation budgets | required local | state share of foundation | aid under rule | enacted ECS | difference | towns gaining | towns losing | towns at 82.5% cap | mills on EQV | % of income |")
say("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
rows = []
for fy in YEARS:
    c = R.MA_CACHE[fy]; sumB = sum(v["B"] for v in c.values()); sumT = sum(v["T"] for v in c.values())
    B = np.array([v["B"] for v in c.values()]); T = np.array([v["T"] for v in c.values()]); capped = int((T >= 0.825 * B - 1e-6).sum())
    eqv = sum(t["ma"][str(fy)]["eqv"] for t in towns if t["ma"].get(str(fy)) and t["ma"][str(fy)]["eqv"]); inc = sum(t["ma"][str(fy)]["inc"] for t in towns if t["ma"].get(str(fy)) and t["ma"][str(fy)]["inc"])
    Tsum, rp, ry, H = M.target_contributions(B, np.array([t["ma"][str(fy)]["eqv"] for t in towns]), np.array([t["ma"][str(fy)]["inc"] for t in towns]), 0.59, 0.825)
    a = sum(series_ma[t["code"]][fy] for t in towns); e = sum(series_en[t["code"]][fy] for t in towns)
    gain = sum(1 for t in towns if series_ma[t["code"]][fy] > series_en[t["code"]][fy] + 1); lose = sum(1 for t in towns if series_ma[t["code"]][fy] < series_en[t["code"]][fy] - 1)
    say(f"| {fy} | ${sumB/1e9:.2f}B | ${sumT/1e9:.2f}B | {100*(1-sumT/sumB):.0f}% | ${a/1e9:.2f}B | ${e/1e9:.2f}B | {'+' if a>=e else '-'}${abs(a-e)/1e9:.2f}B | {gain} | {lose} | {capped} | {rp*1000:.2f} | {ry*100:.2f}% |")
    rows.append(dict(fy=fy, sumB=sumB, sumT=sumT, aid=a, ecs=e))
# per-town FY2025
fy = 2025; c = R.MA_CACHE[fy]
rec = []
for t in towns:
    v = c.get(t["code"]); y = t["yr"][str(fy)]
    if not v: continue
    rec.append(dict(town=t["name"], res=y["res"], frpl_share=y["frpl"]/max(y["res"],1), alliance=y["hh"], B=v["B"], B_pp=v["B"]/max(v["fe"],1), T=v["T"], T_share=v["T"]/v["B"], group=v["group"],
                    aid_ma=series_ma[t["code"]][fy], ecs=series_en[t["code"]][fy], nce=y["nce"], adm=y["adm"], waf=t["ma"][str(fy)]["waf"]))
df = pd.DataFrame(rec); df["diff"] = df.aid_ma - df.ecs; df["diff_pp"] = df["diff"] / df.res
say(f"\n## FY2025 by town (nominal)\n")
say(f"- Foundation budget per foundation pupil: median ${df.B_pp.median():,.0f}, min ${df.B_pp.min():,.0f} ({df.loc[df.B_pp.idxmin(),'town']}), max ${df.B_pp.max():,.0f} ({df.loc[df.B_pp.idxmax(),'town']}). Massachusetts' FY2025 average is $16,051.")
say(f"- Required local share of foundation: median {100*df.T_share.median():.0f}%; {int((df.T_share>=0.8249).sum())} towns at the 82.5% cap; lowest {100*df.T_share.min():.0f}% ({df.loc[df.T_share.idxmin(),'town']}).")
say(f"- Low-income groups (FRPL basis): " + ", ".join(f"group {g}: {n}" for g, n in df.group.value_counts().sort_index().items()) + ".")
say(f"- Aid vs enacted ECS FY2025: {int((df['diff']>1).sum())} towns gain, {int((df['diff']<-1).sum())} lose (losers are held at prior aid + $104/pupil, so 'lose' here means below enacted ECS growth); total {'+' if df['diff'].sum()>=0 else '-'}${abs(df['diff'].sum())/1e6:,.0f}M.")
top = df.sort_values("diff", ascending=False).head(10)[["town","frpl_share","group","B_pp","T_share","ecs","aid_ma","diff","diff_pp"]]
bot = df.sort_values("diff").head(10)[["town","frpl_share","group","B_pp","T_share","ecs","aid_ma","diff","diff_pp"]]
def tbl(x, title):
    say(f"\n### {title}\n"); say("| town | FRPL share | LI group | foundation $/pupil | local share | enacted ECS | Chapter 70 aid | difference | per resident student |"); say("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in x.itertuples(): say(f"| {r.town} | {100*r.frpl_share:.0f}% | {r.group} | ${r.B_pp:,.0f} | {100*r.T_share:.0f}% | ${r.ecs/1e6:,.1f}M | ${r.aid_ma/1e6:,.1f}M | {'+' if r.diff>=0 else '-'}${abs(r.diff)/1e6:,.1f}M | {'+' if r.diff_pp>=0 else '-'}${abs(r.diff_pp):,.0f} |")
tbl(top, "Largest gains, FY2025"); tbl(bot, "Largest shortfalls vs enacted, FY2025")
cities = df[df.town.isin(["Hartford","New Haven","Bridgeport","Waterbury","Stamford","Greenwich","Danbury","Norwalk","New Britain","Windham"])].sort_values("diff", ascending=False)[["town","frpl_share","group","B_pp","T_share","ecs","aid_ma","diff","diff_pp"]]
tbl(cities, "Selected towns, FY2025")
# adequacy: NCE vs foundation budget (towns with local boards, FY2025)
d2 = df[df.nce.notna()].copy(); d2["nce_pp"] = d2.nce / d2.adm; d2["gap"] = d2.B - d2.nce
say(f"\n## Adequacy check, FY2025: current net current expenditures vs the Chapter 70 foundation budget ({len(d2)} towns with a local board)\n")
say(f"- Towns spending below their foundation budget: {int((d2.gap>0).sum())} of {len(d2)}; total shortfall ${d2.gap.clip(lower=0).sum()/1e9:.2f}B; median NCE per pupil ${d2.nce_pp.median():,.0f} vs median foundation per pupil ${d2.B_pp.median():,.0f}.")
say(f"- Below-foundation towns by FRPL share: " + "; ".join(f"{lab}: {int(((d2.gap>0)&m).sum())}/{int(m.sum())}" for lab, m in [("FRPL<25%", d2.frpl_share<.25), ("25-50%", (d2.frpl_share>=.25)&(d2.frpl_share<.5)), ("50%+", d2.frpl_share>=.5)]) + ".")
say("- Caveat: NCE covers the town's own schools and tuition payments while the foundation budget covers all resident students, and NCE includes federal and other revenue; treat as indicative.")
say(f"\n## Test-score simulation, Chapter 70 rule from FY2019 (pooled beta, 100% pass-through, plateau)\n")
say("See the logged run under output/ecs/sim/runs/*_ma_from2019 (statewide FY2025 +0.164 grade levels, test-weighted).")
open(os.path.join(R.OUTROOT if not R.PUBLIC else os.path.dirname(R.OUTROOT), "..", "ma_chapter70_results.md") if False else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ma_chapter70_results.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
df.to_csv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ma_chapter70_fy2025_by_town.csv"), index=False)
print("\n[write] output/ecs/ma_chapter70_results.md, ma_chapter70_fy2025_by_town.csv")
