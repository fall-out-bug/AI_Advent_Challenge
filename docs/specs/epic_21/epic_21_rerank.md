# Epic 21 · Reranking & Relevance Filtering (RAG++)

## Purpose
Improve the EP20 RAG agent by adding a second stage after retrieval: relevance filtering and/or cross-encoder reranking, with thresholds and ablation to compare quality with/without filtering.

## Objectives
- Add configurable relevance filter (similarity threshold) and optional reranker stage.
- Compare answers in three modes: Baseline (no RAG), RAG (no filter), RAG++ (filter/rerank).
- Tune a cutoff threshold and document impact on quality/latency.

## Dependencies
- EP19 index (Redis/FAISS + Mongo metadata) available.
- EP20 agent (RAG vs non‑RAG) runnable.
- Shared infra per `docs/specs/operations.md`.

## Stage Breakdown
| Stage | Scope | Key Deliverables | Exit Criteria |
|-------|-------|------------------|---------------|
| Stage 21_01 | Requirements & question set update | Updated queries, metrics and evaluation rubric for filtering | Approved config; queries saved |
| Stage 21_02 | Design & prototype | Filtering/rerank design; prototype producing side‑by‑side results | Prototype runs on sample queries |
| Stage 21_03 | Implementation & tests | Agent/CLI flags, threshold tuning, metrics, tests | CI green; CLI shows 3 modes |
| Stage 21_04 | Validation & report | Comparison report; recommendations; demo | Report published; demo recorded |

## Success Criteria
- Clear, reproducible improvement for a subset of queries; honest cases where RAG++ does not help.
- Configurable threshold + (optional) reranker with documented trade‑offs.
- Minimal overhead; metrics exported for inspection.

## Notes
- Use EN only for specs; epics numbered by Advent day.
