from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)

def present(name: str) -> bool:
    return bool(os.getenv(name, "").strip())

def status(label: str, ok: bool) -> None:
    print(f"{label}: {'PASS' if ok else 'FAIL'}")

# Presence only. Never echo values.
neo_user_present = present("NEO4J_USER") or present("NEO4J_USERNAME")
required = {
    "NEO4J_URI": present("NEO4J_URI"),
    "NEO4J_USER_OR_USERNAME": neo_user_present,
    "NEO4J_PASSWORD": present("NEO4J_PASSWORD"),
    "GROQ_API_KEY": present("GROQ_API_KEY"),
    "GROQ_MODEL": present("GROQ_MODEL"),
    "JUDGE_PROVIDER": present("JUDGE_PROVIDER"),
    "JUDGE_MODEL": present("JUDGE_MODEL"),
    "HF_TOKEN": present("HF_TOKEN"),
}
for k, v in required.items():
    print(f"{k}: {'PRESENT' if v else 'EMPTY'}")

if not all(required.values()):
    raise SystemExit("BLOCKED: fill missing non-secret/secret settings in .env.")

# Neo4j
try:
    from neo4j import GraphDatabase
    user = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME") or "neo4j"
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(user, os.environ["NEO4J_PASSWORD"]),
    )
    driver.verify_connectivity()
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    with driver.session(database=database) as s:
        ok = s.run("RETURN 1 AS ok").single()["ok"] == 1
    driver.close()
    status("NEO4J", ok)
except Exception as exc:
    print(f"NEO4J: FAIL ({type(exc).__name__})")
    raise

# Hugging Face: tiny streaming probe only.
try:
    from datasets import load_dataset
    ds = load_dataset(
        "HackerNoon/tech-company-news-data-dump",
        split="train",
        streaming=True,
        token=os.environ["HF_TOKEN"],
    )
    row = next(iter(ds))
    status("HUGGING_FACE_STREAM", isinstance(row, dict) and bool(row))
except Exception as exc:
    print(f"HUGGING_FACE_STREAM: FAIL ({type(exc).__name__})")
    raise

# Groq generation + judge. No key or response body printed.
try:
    from groq import Groq
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    gen = client.chat.completions.create(
        model=os.environ["GROQ_MODEL"],
        messages=[{"role":"user","content":"Reply with exactly LAB19_OK"}],
        temperature=0,
    )
    status("GROQ_GENERATION", "LAB19_OK" in (gen.choices[0].message.content or ""))
except Exception as exc:
    print(f"GROQ_GENERATION: FAIL ({type(exc).__name__})")
    raise

try:
    provider = os.environ.get("JUDGE_PROVIDER", "groq").strip().lower()
    if provider == "groq":
        judge = client.chat.completions.create(
            model=os.environ["JUDGE_MODEL"],
            messages=[{"role":"user","content":'Return JSON only: {"score":5,"reason":"ok"}'}],
            temperature=0,
        )
        text = judge.choices[0].message.content or ""
        status("GROQ_JUDGE", '"score"' in text and "5" in text)
    elif provider == "openai":
        status("OPENAI_JUDGE_CONFIG", present("OPENAI_API_KEY"))
    else:
        raise ValueError("JUDGE_PROVIDER must be groq or openai")
except Exception as exc:
    print(f"JUDGE: FAIL ({type(exc).__name__})")
    raise

print("SERVICE_SMOKE: PASS")
