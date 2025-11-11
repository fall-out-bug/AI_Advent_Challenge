# Epic 19 · Worklog

## Overview
Epic 19 delivered a document embedding pipeline that ingests core repository
specifications and lecture notes, generates embeddings via the local LLM stack,
and persists metadata/embeddings in shared infrastructure with deterministic
fallbacks.

## Timeline
- **Stage 19_01 – Discovery (2025-11-10):** Corpus inventory, preprocessing
  rules, storage layout, connectivity checks.
- **Stage 19_02 – Design & Prototyping (2025-11-10):** Clean Architecture
  blueprint, domain value objects, infrastructure spikes (HTTP embedding client,
  RediSearch schema manager).
- **Stage 19_03 – Implementation (2025-11-10/11):** Production pipeline,
  CLI commands (`index run`, `index inspect`), Mongo/Redis adapters, unit tests.
- **Stage 19_04 – Validation (2025-11-11):** MVP run (284 documents / 373 chunks),
  runbook and validation report, fallback strategy documented.
- **Stage 19_05 – Reference Linkage (2025-11-11):** Spec inventory, demo plan,
  closure artefacts.

## Key Decisions
- **Fallback embeddings:** SHA-256 deterministic vectors recorded when `/v1/embeddings`
  returns 404. Metadata `fallback=sha256` stored for quick inspection/replacement.
- **Vector persistence:** Redis RediSearch preferred; FAISS-compatible file fallback
  (`var/indices/embedding_index_v1.pkl`) activated automatically if schema creation
  fails.
- **Chunk metadata:** `embedding_model`, `fallback`, and source/stage tags recorded
  in Mongo for observability and downstream filtering.
- **CLI UX:** `index run --replace-fallback` cleans up historical SHA-256 vectors,
  `index inspect --show-fallback` surfaces fallback counts.

## Risks & Mitigations
- **Missing embedding endpoint:** Deterministic fallback ensures demo readiness;
  `--replace-fallback` flag prepared for migration to real embeddings.
- **RediSearch module absent:** FAISS-compatible file fallback keeps embeddings
  persisted; runbook documents module enablement steps.
- **Metric coverage deferred:** Prometheus integration postponed to Epic 23;
  metric naming reserved in design docs to avoid churn.

## Metrics & Evidence
- **Indexed corpus:** 284 documents, 373 chunks (`stage_19_04_report.md`).
- **Tests:** `poetry run pytest tests/unit/domain/embedding_index tests/unit/infrastructure/embedding_index tests/unit/application/embedding_index -q` (25 tests passing).
- **Runbook:** `stage_19_04_runbook.md` updated with fallback strategy, CLI options,
  and maintenance guidelines.
- **Spec inventory:** `stage_19_05_spec_inventory.md` summarises upstream inputs.
- **Demo artefact:** `demo_plan.md` outlines 20-minute walkthrough referencing inventory.

## Outstanding Follow-ups
- Enable RediSearch or adopt full FAISS search pipeline for query support.
- Replace SHA-256 fallback embeddings once `/v1/embeddings` endpoint is available.
- Epic 23: add Prometheus metrics (`embedding_batches_total`, `embedding_latency_seconds`).

## Sign-off
- Tech Lead review: _pending_ (record signature in `epic_19_summary.md`).

