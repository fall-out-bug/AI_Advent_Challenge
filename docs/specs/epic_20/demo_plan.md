# EP20 Demo Plan · RAG vs Non‑RAG

## Steps (2–4 minutes)
1) Run index check (EP19 ready)
2) Single compare:
```bash
poetry run python scripts/rag/compare_once.py --question "Что такое MapReduce?"
```
3) Batch compare:
```bash
poetry run cli rag:batch --queries docs/specs/epic_20/queries.jsonl --out results.jsonl
```
4) Optional judge (label better answer)
5) Show brief summary (RAG win rate, examples)

## Requirements
- Shared infra running; env from `.env.infra`
- EP19 index namespace configured in `retrieval_config.yaml`

## Outputs
- `results.jsonl` with side‑by‑side answers
- Short narration of where RAG helped vs not
