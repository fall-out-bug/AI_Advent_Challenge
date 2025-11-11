# Stage 20_04 · Validation & Report

## Goal
Run the comparison on the query set, summarise where RAG helped and where it did
not, and publish a short report + demo.

## Checklist
- [ ] Execute `rag:batch` on `queries.jsonl`.
- [ ] Produce `results_with_labels.jsonl` (optional judge labels).
- [ ] Aggregate metrics: win/loss rate for RAG, examples of failure modes.
- [ ] Write `report.md` with highlights and recommendations (prompt fixes, top_k
  tuning, chunk size adjustments).
- [ ] Record a short demo (IDE/console) per `demo_plan.md`.

## Deliverables
- `report.md` and `results_with_labels.jsonl`.
- Demo recording or script for reproducible demo.

## Exit Criteria
- Report approved; next steps (if any) filed as backlog items.
