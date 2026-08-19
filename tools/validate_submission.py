from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
REP = ROOT / "reports"

def check(label, ok, failures):
    print(f"{label}: {'PASS' if ok else 'FAIL'}")
    if not ok:
        failures.append(label)

failures = []

# Secret safety
check(".env excluded from Git package", not (ROOT / ".env").exists(), failures)
check(".git directory excluded", not (ROOT / ".git").exists(), failures)

nb = ROOT / "Day19_GraphRAG_vs_FlatRAG_Production_Lab_Guide.ipynb"
check("Notebook exists", nb.exists() and nb.stat().st_size > 0, failures)

# Golden
gold = DATA / "graphrag_golden_50_first5000.csv"
check("Golden 50 source exists", gold.exists() and gold.stat().st_size > 0, failures)
if gold.exists():
    g = pd.read_csv(gold)
    check("Golden rows == 50", len(g) == 50, failures)
    check("Golden unique IDs", "id" in g and g["id"].is_unique, failures)
    check(
        "Golden reference answers complete",
        "reference_answer" in g and g["reference_answer"].fillna("").astype(str).str.strip().ne("").all(),
        failures,
    )
    if "group" in g:
        groups = set(
            g["group"].astype(str).str.lower()
             .str.replace("_","-", regex=False)
             .str.replace("multihop","multi-hop", regex=False)
             .str.replace("crossdoc","cross-doc", regex=False)
        )
        check("Golden groups present", {"factoid","multi-hop","cross-doc"}.issubset(groups), failures)

# Runtime outputs
required_outputs = [
    "graphrag_eval_results.csv",
    "graphrag_vs_flatrag_summary.csv",
    "coreference_audit.csv",
    "entity_resolution_audit.csv",
    "top_degree_entities.csv",
    "lab19_run_summary.json",
]
for name in required_outputs:
    p = OUT / name
    check(f"Output {name}", p.exists() and p.stat().st_size > 0, failures)

summary_path = OUT / "lab19_run_summary.json"
if summary_path.exists():
    s = json.loads(summary_path.read_text(encoding="utf-8"))
    check("Nodes > 0", int(s.get("nodes",0)) > 0, failures)
    check("Edges > 0", int(s.get("edges",0)) > 0, failures)
    check("Invalid provenance == 0", int(s.get("invalid_provenance_edges",-1)) == 0, failures)
    check("Entity audit rows >= 10", int(s.get("entity_resolution_audit_rows",0)) >= 10, failures)
    check("Golden evaluated rows == 50", int(s.get("evaluation_rows",0)) == 50, failures)

evp = OUT / "graphrag_eval_results.csv"
if evp.exists():
    e = pd.read_csv(evp)
    check("Evaluation rows == 50", len(e) == 50, failures)
    if "error" in e:
        check("Evaluation failed rows == 0", e["error"].fillna("").astype(str).str.strip().eq("").all(), failures)

# Reports
for name in [
    "lab_report.md",
    "technical_defense.md",
    "failure_analysis.md",
    "reflection_NgoThanhDat.md",
]:
    p = REP / name
    check(f"Report {name}", p.exists() and p.stat().st_size > 100, failures)

if failures:
    print("\nSUBMISSION_STATUS: FAIL")
    print("Failed gates:", ", ".join(failures))
    raise SystemExit(1)

print("\nSUBMISSION_STATUS: PASS")
