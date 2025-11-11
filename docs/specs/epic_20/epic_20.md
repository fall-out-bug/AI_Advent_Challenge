# Epic 20 · RAG vs Non‑RAG Answering Agent

## Purpose
Implement a question‑answering agent with two modes: (1) plain LLM (no context)
and (2) RAG (retrieve relevant chunks from the EP19 index and augment the
prompt). Compare answers and produce a short report: where RAG helps and where
it does not.

## Objectives
- Reuse EP19 index (Mongo metadata + Redis/FAISS vectors) for retrieval.
- Provide an agent/CLI with two modes (with RAG / without RAG) and side‑by‑side
  comparison output.
- Define a lightweight evaluation rubric (LLM‑as‑judge from EP05) to label
  improvements or regressions.
- Deliver a demo flow runnable from IDE/console.

## Dependencies
- EP19 index available (or minimal index built from configured folders).
- Shared infra per `docs/specs/operations.md` (LLM API, Mongo, Redis).
- EP05 scoring templates optionally reused for quick LLM‑as‑judge.

## Stage Breakdown
| Stage | Scope | Key Deliverables | Exit Criteria |
|-------|-------|------------------|---------------|
| Stage 20_01 | Requirements & dataset of questions | Query set, retrieval config, evaluation rubric | Approved scope; queries saved |
| Stage 20_02 | Design & prototype | Retrieval + prompting design, side‑by‑side prototype | Prototype returns comparable outputs |
| Stage 20_03 | Implementation & tests | Agent + CLI, metrics/logging, basic tests | CLI works in both modes; tests pass |
| Stage 20_04 | Validation & report | Runs on query set; report (where RAG helped/failed) | Report published; demo recorded |

## Success Criteria
- CLI produces comparable answers in both modes for a small curated query set.
- Report summarises cases where RAG improves coverage/accuracy/coherence and
  where it does not (hallucinations, wrong retrieval, prompt overflow).
- Minimal integration with EP19 index; no ad‑hoc stores.

## References
- `docs/specs/epic_19/epic_19.md` (indexing)
- `docs/specs/epic_05/stage_05_02_runbook.md` (LLM‑as‑judge automation)
- `docs/specs/operations.md` (shared infra)
