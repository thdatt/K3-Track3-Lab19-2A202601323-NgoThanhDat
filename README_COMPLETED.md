# Lab 19 — Production GraphRAG vs Flat RAG

Student: **Ngo Thanh Dat**

This folder is the completed submission overlay for the existing Lab 19 repository.

## Completed implementation

The notebook implements:

- Hugging Face streaming of HackerNoon tech-company news
- deterministic Golden-aware preprocessing
- exact SHA-1 deduplication
- optional MinHash-LSH near deduplication
- 220-word chunks / 40-word overlap
- conservative coreference resolution
- strict Company / Person / Technology extraction
- allow-listed graph relations
- edge provenance hard gate
- auditable entity resolution
- Neo4j schema + `UNWIND $rows AS row` batch writes
- MiniLM + normalized FAISS `IndexFlatIP` Flat RAG
- graph seed extraction and exact/alias/vector matching
- bounded 2-hop graph traversal
- super-node mitigation
- hybrid graph + vector context
- Groq generation
- Groq/OpenAI judge abstraction
- resumable 50-case Golden evaluation
- benchmark CSV export
- failure-mode evidence collection
- final submission audit
- optional Near-Dedup / Community / Self-Correction scaffolds

## Important: preserve instructor files

When merging this ZIP into the original GitHub repository, keep the original:

- `README.md`
- `ASSIGNMENT.md`
- `RUBRIC.md`
- instructor-provided Golden files under `data/`

This package does **not** replace instructor handout/rubric content.

## Golden files expected in the original repository

The completed notebook prefers:

- `data/graphrag_golden_50_first5000.csv`
- `data/graphrag_golden_50_first5000_detailed.csv`

It refuses to call the final benchmark complete when reference answers or required groups are missing.

## Local run

```powershell
# keep your existing gitignored .env
python -m pip install -r requirements.txt

python tools/smoke_services.py

jupyter nbconvert `
  --to notebook `
  --execute `
  --inplace `
  --ExecutePreprocessor.timeout=-1 `
  Day19_GraphRAG_vs_FlatRAG_Production_Lab_Guide.ipynb

python tools/generate_reports.py
python tools/validate_submission.py
```

Or use:

```powershell
powershell -ExecutionPolicy Bypass -File .\RUN_LAB19.ps1
```

## Secret safety

`.env` is deliberately excluded from this package.
Do not add `.env`, API keys, Neo4j passwords, or Hugging Face tokens to Git.
