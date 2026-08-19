#!/usr/bin/env bash
set -euo pipefail

python -m pip install -r requirements.txt
python tools/smoke_services.py
jupyter nbconvert \
  --to notebook \
  --execute \
  --inplace \
  --ExecutePreprocessor.timeout=-1 \
  Day19_GraphRAG_vs_FlatRAG_Production_Lab_Guide.ipynb
python tools/generate_reports.py
python tools/validate_submission.py
echo "LAB19_PIPELINE: PASS"
