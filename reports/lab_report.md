# Lab 19 Report — Production GraphRAG vs Flat RAG

**Student:** Ngo Thanh Dat

> Run the completed notebook first, then run `python tools/generate_reports.py`.
> Empirical fields must come from actual output artefacts; do not fabricate measurements.

## 1. Pipeline Implementation

### Preprocessing & Coreference
- Articles:
- Chunks:
- Extraction chunks:
- Coreference audit:
- Real difficult/unresolved example:

### NER / Relation Extraction / Provenance
- Valid triples:
- Extraction errors:
- Invalid provenance edges:

### Entity Resolution & Neo4j
- Threshold: 0.90
- Entity-resolution audit rows:
- Real high-similarity rejected pair:
- Nodes:
- Edges:
- Bulk ingestion: `UNWIND $rows AS row`

### Retrieval
- Flat RAG: MiniLM + normalized FAISS IndexFlatIP, top-k=6
- GraphRAG: seed resolution + bounded BFS max_hops=2
- Super-node: degree >100, latest-edge cap <=50
- Global edge cap <=250
- Graph context cap <=14000 characters

## 2. Golden Evaluation

- Golden source:
- Rows:
- Factoid:
- Multi-hop:
- Cross-doc:
- Missing reference answers:

| Metric | Flat RAG | GraphRAG |
|---|---:|---:|
| Comprehensiveness | | |
| Faithfulness | | |
| Multi-hop reasoning | | |
| Latency (s) | | |
| Token usage | | |

## 3. Failure Modes

### Flat RAG weak case
- ID:
- Symptom:
- Retrieval trace:
- Root cause:
- Fix:
- Verification:

### GraphRAG difficult case
- ID:
- Symptom:
- Retrieval trace:
- Root cause:
- Fix:
- Verification:

## 4. Technical Defense

1. Real coreference challenge:
2. Why threshold 0.90:
3. High-similarity rejected entity pair:
4. Top 3 degree nodes:
5. Latest-edge trade-off:
6. Where Flat RAG wins:
7. Where GraphRAG wins:
8. Latency/token trade-off:
9. One coding-agent suggestion rejected:
10. First likely bottleneck near 350MB scale:

## 5. Reflection & Action Plan

- Lecture-to-code mapping:
- Hardest real debugging issue:
- Main lesson:
- When GraphRAG is justified:
- When Flat/Hybrid RAG is enough:
- Next production improvements:
