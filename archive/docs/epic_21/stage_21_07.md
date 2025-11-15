# Stage 21_04 · Validation & Report

## Goal
Compare quality/latency for Baseline, RAG, and RAG++ on the query set; publish a short report with threshold recommendations.

## Checklist
- [ ] Run `rag:batch` with/without `--filter` (and optional reranker).
- [ ] Aggregate: RAG++ win rate, examples of improvements and failures.
- [ ] Tune threshold; record recommended default values.
- [ ] Write `report.md`; record MADR for chosen defaults (threshold, reranker).
- [ ] Record short demo (IDE/console).

## Deliverables
- `report.md` with summary tables and recommendations.
- MADR decision(s) under `docs/specs/epic_21/decisions/`.

## Exit Criteria
- Report and MADR approved; defaults updated in config.
