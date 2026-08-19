from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
REP = ROOT / "reports"
REP.mkdir(exist_ok=True)

def need(path: Path) -> Path:
    if not path.exists() or path.stat().st_size == 0:
        raise FileNotFoundError(f"Required real artefact missing: {path}")
    return path

run_summary = json.loads(need(OUT / "lab19_run_summary.json").read_text(encoding="utf-8"))
eval_df = pd.read_csv(need(OUT / "graphrag_eval_results.csv"))
summary_df = pd.read_csv(need(OUT / "graphrag_vs_flatrag_summary.csv"))
top_df = pd.read_csv(need(OUT / "top_degree_entities.csv"))
audit_df = pd.read_csv(need(OUT / "entity_resolution_audit.csv"))
coref_df = pd.read_csv(need(OUT / "coreference_audit.csv"))

if "error" in eval_df.columns:
    bad = eval_df["error"].fillna("").astype(str).str.strip().ne("")
    if bad.any():
        raise RuntimeError(f"Evaluation still has {int(bad.sum())} failed rows.")

# Score delta for empirical case selection.
for c in [
    "flat_comprehensiveness","graph_comprehensiveness",
    "flat_faithfulness","graph_faithfulness"
]:
    eval_df[c] = pd.to_numeric(eval_df[c], errors="coerce")

eval_df["graph_minus_flat"] = (
    eval_df["graph_comprehensiveness"] - eval_df["flat_comprehensiveness"]
)
flat_weak = eval_df.sort_values("graph_minus_flat", ascending=False).iloc[0]
graph_hard = eval_df.sort_values(
    ["graph_faithfulness","graph_comprehensiveness"], ascending=[True, True]
).iloc[0]

rejects = audit_df[audit_df.get("decision", "").eq("REJECT_GUARD")].copy()
if len(rejects) and "similarity" in rejects:
    rejects["similarity"] = pd.to_numeric(rejects["similarity"], errors="coerce")
    rejected = rejects.sort_values("similarity", ascending=False).iloc[0]
else:
    rejected = None

# Find a real unresolved/coref issue if available.
coref_case = None
if "unresolved_mentions" in coref_df.columns:
    mask = coref_df["unresolved_mentions"].fillna("").astype(str).str.len().gt(2)
    if mask.any():
        coref_case = coref_df[mask].iloc[0]

def overall(metric: str, system: str):
    row = summary_df[
        summary_df["Loại câu hỏi"].astype(str).eq("ALL")
        & summary_df["Metric"].astype(str).eq(metric)
    ]
    if row.empty:
        return "N/A"
    col = "Flat RAG" if system == "flat" else "GraphRAG"
    return row.iloc[0][col]

top3 = top_df.head(3)
top_lines = "\n".join(
    f"{i+1}. {r.get('name','?')} — degree={r.get('degree','?')}"
    for i, (_, r) in enumerate(top3.iterrows())
) or "No real degree rows."

reject_line = (
    f"{rejected.get('left')} ↔ {rejected.get('right')}, "
    f"similarity={rejected.get('similarity')}"
    if rejected is not None else
    "No real REJECT_GUARD row was produced; do not fabricate one."
)

coref_line = (
    f"chunk_id={coref_case.get('chunk_id')}; unresolved={coref_case.get('unresolved_mentions')}"
    if coref_case is not None else
    "No non-empty unresolved mention was recorded in this run."
)

lab_report = f"""# Lab 19 Report — Production GraphRAG vs Flat RAG

**Student:** Ngo Thanh Dat

## 1. Pipeline Implementation

- Articles: {run_summary.get('articles')}
- Chunks: {run_summary.get('chunks')}
- Extraction chunks: {run_summary.get('extraction_chunks')}
- Valid triples: {run_summary.get('valid_triples')}
- Extraction errors: {run_summary.get('extraction_errors')}
- Nodes: {run_summary.get('nodes')}
- Edges: {run_summary.get('edges')}
- Invalid provenance edges: {run_summary.get('invalid_provenance_edges')}
- Entity-resolution audit rows: {run_summary.get('entity_resolution_audit_rows')}
- Coreference difficult/unresolved evidence: {coref_line}
- High-similarity guard rejection: {reject_line}

The graph is bulk-ingested with `UNWIND $rows AS row`. Every accepted edge is
required to preserve `source_chunk_id`, `published_date`, `evidence`, and
`confidence`; the final pipeline audit requires zero invalid provenance edges.

## 2. Golden Evaluation

- Source: {run_summary.get('golden_source')}
- Rows: {run_summary.get('golden_rows')}
- Groups: {run_summary.get('golden_groups')}

| Metric | Flat RAG | GraphRAG |
|---|---:|---:|
| Comprehensiveness | {overall('Comprehensiveness','flat')} | {overall('Comprehensiveness','graph')} |
| Faithfulness | {overall('Faithfulness','flat')} | {overall('Faithfulness','graph')} |
| Multi-hop reasoning | {overall('Multi-hop reasoning','flat')} | {overall('Multi-hop reasoning','graph')} |
| Latency (s) | {overall('Latency (s)','flat')} | {overall('Latency (s)','graph')} |
| Token usage | {overall('Token usage','flat')} | {overall('Token usage','graph')} |

## 3. Failure Modes

### Flat RAG weak case where GraphRAG helps

- ID: {flat_weak.get('id')}
- Group: {flat_weak.get('group')}
- Question: {flat_weak.get('question')}
- Flat comprehensiveness: {flat_weak.get('flat_comprehensiveness')}
- Graph comprehensiveness: {flat_weak.get('graph_comprehensiveness')}
- Root cause should be verified against the saved retrieval trace before making a stronger claim.

### GraphRAG difficult case

- ID: {graph_hard.get('id')}
- Group: {graph_hard.get('group')}
- Question: {graph_hard.get('question')}
- Graph comprehensiveness: {graph_hard.get('graph_comprehensiveness')}
- Graph faithfulness: {graph_hard.get('graph_faithfulness')}
- Root cause should be verified against matched seeds, collected edges, vector fallback, and judge rationale.

## 4. Top Degree Nodes

{top_lines}

The implemented super-node policy treats degree >100 as a super-node, caps each
such expansion to <=50 latest edges, applies a global edge cap <=250, and bounds
graph context to <=14000 characters.

## 5. Reflection

Flat RAG is the cheaper baseline for direct semantic matches, while GraphRAG is
intended to add explicit relational paths and provenance for multi-hop/cross-document
questions. The measured benchmark above must decide whether that extra graph work is
worth the latency/token cost on this dataset; the report does not assume GraphRAG wins.
"""
(REP / "lab_report.md").write_text(lab_report, encoding="utf-8")

technical = f"""# Technical Defense — Ngo Thanh Dat

1. **Coreference challenge:** {coref_line}
2. **Entity threshold:** 0.90 is deliberately conservative; embedding similarity is additionally gated by lexical/type checks to avoid false merges.
3. **High-similarity rejected pair:** {reject_line}
4. **Top 3 high-degree nodes:**  
{top_lines}
5. **Latest-edge trade-off:** latest-first controls super-node explosion and preserves recency, but may hide older evidence when historical chronology matters.
6. **Flat RAG strongest group:** determine from `outputs/graphrag_vs_flatrag_summary.csv`; do not infer without measured group means.
7. **GraphRAG strongest group:** determine from the same real group means.
8. **Latency/token trade-off:** overall Flat latency={overall('Latency (s)','flat')}, GraphRAG latency={overall('Latency (s)','graph')}; Flat tokens={overall('Token usage','flat')}, GraphRAG tokens={overall('Token usage','graph')}.
9. **Coding-agent suggestion rejected:** do not use unlimited context or embedding-only entity merges; both hide the production failure modes this lab is meant to control.
10. **First likely scale bottleneck near 350MB:** LLM coreference/NER-RE calls, because call count grows with extracted chunks; batching, caching, bounded extraction, and checkpoints are therefore explicit design choices.
"""
(REP / "technical_defense.md").write_text(technical, encoding="utf-8")

failure = f"""# Failure Analysis — Ngo Thanh Dat

## Case A — Flat RAG weakness / GraphRAG advantage

**ID:** {flat_weak.get('id')}  
**Symptom:** GraphRAG receives a higher measured comprehensiveness score than Flat RAG.  
**Question:** {flat_weak.get('question')}  
**Flat answer:** {flat_weak.get('flat_answer')}  
**Graph answer:** {flat_weak.get('graph_answer')}  

**Root-cause method:** inspect Flat top-k chunk IDs versus Graph matched seeds / collected edges.
A likely retrieval-stage explanation must only be accepted if the saved trace confirms it.

**Verification:** compare the two judge rationales and retrieval metadata in
`outputs/graphrag_eval_results.csv`.

## Case B — GraphRAG difficult case

**ID:** {graph_hard.get('id')}  
**Symptom:** low measured GraphRAG faithfulness/comprehensiveness.  
**Question:** {graph_hard.get('question')}  
**Graph answer:** {graph_hard.get('graph_answer')}  

**Root-cause method:** inspect seed extraction, entity matching, BFS coverage, super-node
truncation, provenance lines, and vector fallback before blaming generation.

**Verification:** rerun the case after the smallest justified retrieval/extraction fix and
compare the same judge dimensions.
"""
(REP / "failure_analysis.md").write_text(failure, encoding="utf-8")

reflection_path = REP / "reflection_NgoThanhDat.md"
reflection = reflection_path.read_text(encoding="utf-8") if reflection_path.exists() else "# Reflection — Ngo Thanh Dat\n"
reflection += f"""

## Measured run addendum

- Articles: {run_summary.get('articles')}
- Chunks: {run_summary.get('chunks')}
- Valid triples: {run_summary.get('valid_triples')}
- Graph nodes/edges: {run_summary.get('nodes')}/{run_summary.get('edges')}
- Golden rows: {run_summary.get('golden_rows')}
- Overall Flat comprehensiveness: {overall('Comprehensiveness','flat')}
- Overall GraphRAG comprehensiveness: {overall('Comprehensiveness','graph')}

The main engineering lesson is to optimize evidence quality under explicit scope and
provenance constraints rather than simply increasing retrieval volume.
"""
reflection_path.write_text(reflection, encoding="utf-8")

# Mirror canonical benchmark outputs under reports for rubric variants.
for name in ["graphrag_eval_results.csv", "graphrag_vs_flatrag_summary.csv"]:
    src = OUT / name
    if src.exists():
        (REP / name).write_bytes(src.read_bytes())

print("REPORT_GENERATION: PASS")
