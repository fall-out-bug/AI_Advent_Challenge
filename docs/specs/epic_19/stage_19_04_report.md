# Stage 19_04 · Validation & Documentation Report

## 1. Overview
- Executed the document embedding index pipeline across project documentation and
  external lecture corpora.
- Stored canonical metadata in MongoDB (`documents`, `chunks` collections) and
  embedding vectors in Redis hashes (fallback mode without RediSearch module).
- Captured benchmark statistics, CLI evidence, and highlighted residual gaps for
  search/readiness.

## 2. Execution Summary
| Item | Value | Notes |
|------|-------|-------|
| Command | `poetry run python -m src.presentation.cli.backoffice.main index run` | Environment variables sourced from shared infra secrets. |
| Documents processed | 284 | Sources: `docs/`, `~/rework-branch/mlsd/lections`, `~/rework-branch/bigdata/lections`. |
| Chunks generated | 373 | Sliding window chunker (`size=1200`, `overlap=200`, `min=200`). |
| Embeddings stored | 373 | Fallback SHA-256 embeddings due to missing `/v1/embeddings` endpoint support. |
| Evidence | `docs/specs/epic_19/evidence/stage_19_04_index_run.txt` | Raw CLI output. |
| Test evidence | `docs/specs/epic_19/evidence/stage_19_03_tests.txt` | Unit test execution log. |

## 3. Runtime Observations
- **Embedding API**: Local LLM endpoint (`http://127.0.0.1:8000/v1/embeddings`) returned
  `404`. Gateway now logs a warning and falls back to deterministic SHA-256
  embeddings (`model=fallback-sha256`) with dimension `1536`. Fallback chunks
  are tagged via `metadata.fallback = "sha256"` to simplify future replacement.
- **Redis RediSearch**: Host instance lacks the RediSearch module (`FT.CREATE` unknown).
  Schema creation is skipped with warning; embeddings are persisted to
  `var/indices/embedding_index_v1.pkl` via the FAISS-compatible fallback store
  until RediSearch is enabled.
- **Telemetry**: Logging captures skipped sources and fallback usage. Metrics hooks
  remain TODO for Stage 19_04 follow-up.

## 4. MongoDB Collections
- `document_index.documents`
  - Keys: `document_id`, `source_path`, `source`, `language`, `sha256`, `tags`.
  - Example metadata tags: `{"stage": "19", "language": "ru", "source": "docs"}`.
- `document_index.chunks`
  - Contains chunk-level payloads with metadata (source, language, stage).
  - Embedding references stored implicitly via Redis key prefix
    `embedding:chunk:{chunk_id}`.

## 5. Validation Commands
```bash
# Inspect summary counts
poetry run python -m src.presentation.cli.backoffice.main index inspect

# Mongo verification (example)
poetry run python - <<'PY'
from pymongo import MongoClient
client = MongoClient("$MONGODB_URL")
db = client["document_index"]
print("documents", db["documents"].count_documents({}))
print("chunks", db["chunks"].count_documents({}))
PY
```

## 6. Open Risks & Follow-ups
- Enable RediSearch on shared Redis or continue using the FAISS-compatible fallback
  to allow vector similarity queries and audit trails.
- Replace fallback embeddings with true model embeddings once `/v1/embeddings`
  is available (run `index run --replace-fallback` after enabling the endpoint).
- Add Prometheus metrics (`embedding_batches_total`, `embedding_latency_seconds`)
  and structured logging for chunk/embedding throughput.
- Consider persisting fallback indicator in Mongo for visibility (`metadata.fallback`).

## 7. Next Steps
- Document runbook for operations (see `stage_19_04_runbook.md`).
- Integrate retrieval API or CLI commands (`index search`) leveraging stored vectors.
- Schedule periodic re-indexing when documentation changes; leverage document hash
  to short-circuit unchanged files.

