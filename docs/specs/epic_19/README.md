# Epic 19 · Document Embedding Index

## Overview
Epic 19 delivers a Clean Architecture–aligned pipeline that ingests repository
specifications and lecture notes, chunks/embeds content via the local LLM stack,
and persists metadata and vectors to shared infrastructure (MongoDB + Redis with
FAISS-compatible fallback). This README acts as the navigation hub for all Stage
19 artefacts.

## Stage Artefacts
| Stage | Description | Artefacts |
|-------|-------------|-----------|
| 19_01 – Discovery | Corpus inventory, preprocessing/storage decisions | `stage_19_01_summary.md`, `stage_19_01_backlog.md` |
| 19_02 – Design | Architecture blueprint, domain value objects, prototypes | `stage_19_02.md`, source files under `src/domain/embedding_index` |
| 19_03 – Implementation | Production pipeline, CLI, tests | Code in `src/application/embedding_index`, `src/presentation/cli/embedding_index.py`; tests under `tests/unit/...` |
| 19_04 – Validation | MVP indexing run, runbook, report | `stage_19_04_report.md`, `stage_19_04_runbook.md`, evidence in `docs/specs/epic_19/evidence/` |
| 19_05 – Reference Linkage | Spec inventory, demo plan, closure | `stage_19_05_spec_inventory.md`, `demo_plan.md`, `epic_19_worklog.md`, `epic_19_summary.md` |

## Key Commands
```bash
# Run indexer (full corpus)
poetry run python -m src.presentation.cli.backoffice.main index run

# Replace SHA-256 fallback embeddings after /v1/embeddings is available
poetry run python -m src.presentation.cli.backoffice.main index run --replace-fallback

# Inspect summary counts and fallback usage
poetry run python -m src.presentation.cli.backoffice.main index inspect --show-fallback

# Unit tests
poetry run pytest tests/unit/domain/embedding_index \
    tests/unit/infrastructure/embedding_index \
    tests/unit/application/embedding_index -q
```

## Operational References
- `stage_19_04_runbook.md` – environment setup, fallback strategy (Redis → FAISS), troubleshooting.
- `demo_plan.md` – 20-minute demo outline referencing spec inventory.
- `stage_19_05_spec_inventory.md` – consolidated list of upstream specs (EP00–EP06, core docs, EP19).

## Metrics & Evidence
- **Corpus coverage:** 284 documents / 373 chunks (`stage_19_04_report.md`).
- **Fallback tracking:** Mongo `metadata.fallback = "sha256"` and CLI `--show-fallback`.
- **Local index:** `var/indices/embedding_index_v1.pkl` if RediSearch unavailable.

## Follow-ups
- Enable RediSearch or adopt full FAISS search for vector queries.
- Replace fallback embeddings once the local `/v1/embeddings` endpoint is live.
- Epic 23 will add Prometheus metrics (`embedding_batches_total`, `embedding_latency_seconds`).
- Future work: retrieval/search API atop the stored embeddings.
