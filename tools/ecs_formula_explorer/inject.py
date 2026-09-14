from pathlib import Path
import os; os.chdir(os.path.dirname(os.path.abspath(__file__)))
s=Path("ecs_dashboard_template.html").read_text(encoding="utf-8")
out=s.replace("/*__DATA__*/",Path("ecs_dash_data.json").read_text(encoding="utf-8")).replace("/*__GEO__*/",Path("ct_towns.geojson").read_text(encoding="utf-8"))
for f in ("ecs_dashboard.html","ecs_formula_explorer.html"): Path(f).write_text(out,encoding="utf-8")
print("injected", len(out)//1024, "KB")
