$ErrorActionPreference = "Stop"

Write-Host "=== Lab 19: dependency install ==="
python -m pip install -r requirements.txt

Write-Host "=== Lab 19: external service smoke ==="
python tools/smoke_services.py

Write-Host "=== Lab 19: clean notebook execution ==="
jupyter nbconvert `
  --to notebook `
  --execute `
  --inplace `
  --ExecutePreprocessor.timeout=-1 `
  Day19_GraphRAG_vs_FlatRAG_Production_Lab_Guide.ipynb

Write-Host "=== Lab 19: reports ==="
python tools/generate_reports.py

Write-Host "=== Lab 19: final validation ==="
python tools/validate_submission.py

Write-Host "LAB19_PIPELINE: PASS"
