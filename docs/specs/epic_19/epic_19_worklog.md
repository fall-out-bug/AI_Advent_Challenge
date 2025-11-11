# Epic 19 · Worklog

## Overview
Epic 19 delivered a document embedding pipeline that ingests core repository
specifications and lecture notes, generates `all-MiniLM-L6-v2` embeddings via the
local LLM stack, and persists metadata/embeddings in shared infrastructure with a
FAISS contingency when RediSearch is absent.

## Timeline
- **Stage 19_01 – Discovery (2025-11-10):** Corpus inventory, preprocessing
  rules, storage layout, connectivity checks.
- **Stage 19_02 – Design & Prototyping (2025-11-10):** Clean Architecture
  blueprint, domain value objects, infrastructure spikes (HTTP embedding client,
  RediSearch schema manager).
- **Stage 19_03 – Implementation (2025-11-10/11):** Production pipeline,
  CLI commands (`index run`, `index inspect`), Mongo/Redis adapters, unit tests.
- **Stage 19_04 – Validation (2025-11-11):** MVP run (293 documents / 382 chunks),
  runbook and validation report, fallback strategy exercised then replaced with
  live embeddings.
- **Stage 19_05 – Reference Linkage (2025-11-11):** Spec inventory, demo plan,
  closure artefacts.

## Key Decisions
- **Embedding model & limits:** Switched default encoder to `all-MiniLM-L6-v2` with
  `max_length=512`, ensuring local LLM handles Stage 19 payloads without errors.
- **Fallback strategy:** SHA-256 deterministic vectors remain as contingency; metadata
  flag retained for future auditing, but current corpus stores real embeddings.
- **Vector persistence:** Redis RediSearch preferred; FAISS-compatible file fallback
  (`var/indices/embedding_index_v1.pkl`) activated automatically if schema creation
  fails.
- **Chunk metadata:** `embedding_model`, optional `fallback`, and source/stage tags
  recorded in Mongo for observability and downstream filtering.
- **CLI UX:** `index run --replace-fallback` cleans up historical fallback vectors,
  `index inspect --show-fallback` surfaces contingency usage.
- **Container packaging:** `docker/Dockerfile.indexer`, `docker-compose.indexer.yml`,
  and Make targets (`index-container-*`) provide reproducible execution with mounted
  infra secrets.

## Risks & Mitigations
- **Embedding endpoint regressions:** Deterministic fallback remains available; runbook
  prescribes health checks and `--replace-fallback` replay once fixed.
- **RediSearch module absent:** FAISS-compatible file fallback keeps embeddings
  persisted; runbook documents module enablement steps.
- **Metric coverage deferred:** Prometheus integration postponed to Epic 23;
  metric naming reserved in design docs to avoid churn.

## Metrics & Evidence
- **Indexed corpus:** 293 documents, 382 chunks (`stage_19_04_report.md`).
- **Tests:** `poetry run pytest tests/unit/domain/embedding_index tests/unit/infrastructure/embedding_index tests/unit/application/embedding_index -q` (25 tests passing).
- **Runbook:** `stage_19_04_runbook.md` updated with container workflow, fallback strategy,
  and maintenance guidelines.
- **Spec inventory:** `stage_19_05_spec_inventory.md` summarises upstream inputs.
- **Demo artefact:** `demo_plan.md` outlines 20-minute walkthrough referencing inventory.

## Outstanding Follow-ups
- Enable RediSearch or adopt full FAISS search pipeline for query support.
- Epic 23: add Prometheus metrics (`embedding_batches_total`, `embedding_latency_seconds`).
- Build retrieval/query tooling atop the indexed embeddings (CLI/API).

## Sign-off
- Tech Lead review: _pending_ (record signature in `epic_19_summary.md`).
