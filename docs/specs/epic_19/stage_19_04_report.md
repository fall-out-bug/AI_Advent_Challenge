# Stage 19_04 · Validation & Documentation Report

## 1. Overview
- Executed the document embedding index pipeline across project documentation and
  external lecture corpora.
- Stored canonical metadata in MongoDB (`documents`, `chunks` collections) and
  embedding vectors via Redis/FAISS adapters (RediSearch still unavailable, so FAISS
  fallback file remains the primary store).
- Captured benchmark statistics, CLI evidence, and highlighted residual gaps for
  retrieval readiness.

## 2. Execution Summary
| Item | Value | Notes |
|------|-------|-------|
| Command | `make index-container-run INDEX_RUN_ARGS="--replace-fallback"` | Executes Docker Compose service (`docker-compose.indexer.yml`) with infra secrets mounted from host. |
| Documents processed | 293 | Sources: `docs/`, `~/rework-branch/mlsd/lections`, `~/rework-branch/bigdata/lections`. |
| Chunks generated | 382 | Sliding window chunker (`size=1200`, `overlap=200`, `min=200`). |
| Embeddings stored | 382 | Real vectors from `all-MiniLM-L6-v2` (dim=384); SHA-256 fallbacks cleared. |
| Evidence | `docs/specs/epic_19/evidence/stage_19_04_index_run.txt` | Raw CLI output. |
| Test evidence | `docs/specs/epic_19/evidence/stage_19_03_tests.txt` | Unit test execution log. |

## 3. Runtime Observations
- **Embedding API**: Local endpoint (`http://host.docker.internal:8000/v1/embeddings`)
  responded with `200 OK` after capping `max_length=512` inside the LLM container.
  Gateway logs confirm Dockerised batches executed without fallback; chunk metadata
  now omits `fallback` flags.
- **Redis RediSearch**: Host instance still lacks the RediSearch module (`FT.CREATE`
  rejected with "Index already exists"/module missing). Embeddings persist to
  `var/indices/embedding_index_v1.pkl` via the FAISS-compatible fallback store until
  RediSearch is enabled.
- **Telemetry**: Logging captures source skips and batch timings. Metrics hooks
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
- Add Prometheus metrics (`embedding_batches_total`, `embedding_latency_seconds`)
  and structured logging for chunk/embedding throughput.
- Automate periodic verification of LLM API limits (batch size, latency) to catch
  regressions early.

## 7. Next Steps
- Document runbook for operations (see `stage_19_04_runbook.md`).
- Integrate retrieval API or CLI commands (`index search`) leveraging stored vectors.
- Schedule periodic re-indexing when documentation changes; leverage document hash
  to short-circuit unchanged files.
