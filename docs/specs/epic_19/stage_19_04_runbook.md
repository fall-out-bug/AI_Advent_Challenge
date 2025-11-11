# Stage 19_04 · Embedding Index Runbook

## 1. Prerequisites
- Python environment with project dependencies installed (`poetry install`).
- Shared infrastructure running locally (MongoDB, Redis, LLM API). For default
  environment use `make day-12-up` or equivalent infra bootstrap.
- Access to secrets:
  - `~/work/infra/secrets/mongo_password.txt`
  - `~/work/infra/secrets/redis_password.txt`

## 2. Environment Setup
```bash
# MongoDB credentials (admin user)
export MONGO_USER=admin
export MONGO_PASSWORD=$(cat ~/work/infra/secrets/mongo_password.txt)
export MONGODB_URL="mongodb://${MONGO_USER}:${MONGO_PASSWORD}@127.0.0.1:27017/butler?authSource=admin"
export TEST_MONGODB_URL="$MONGODB_URL"

# Redis credentials
export REDIS_HOST=127.0.0.1
export REDIS_PORT=6379
export REDIS_PASSWORD=$(cat ~/work/infra/secrets/redis_password.txt)

# Embedding API (falls back to SHA-256 if /v1/embeddings unavailable)
export LLM_URL=http://127.0.0.1:8000
export LLM_MODEL=text-embedding-3-small
```

## 3. Running the Indexer
```bash
# From repository root
poetry run python -m src.presentation.cli.backoffice.main index run
```

### Default Sources
1. `<repo>/docs`
2. `~/rework-branch/mlsd/lections`
3. `~/rework-branch/bigdata/lections`

Override or extend sources:
```bash
poetry run python -m src.presentation.cli.backoffice.main \
    index run --source /path/to/extra/docs --source /another/path
```

## 4. Inspecting Results
```bash
poetry run python -m src.presentation.cli.backoffice.main index inspect
# Add --show-fallback to include the number of chunks stored with SHA-256 embeddings
poetry run python -m src.presentation.cli.backoffice.main index inspect --show-fallback
# Example output:
# documents=284
# chunks=373
# fallback_chunks=373
# redis_index=missing  # RediSearch not loaded -> warnings logged
```

### MongoDB Manual Checks
```bash
poetry run python - <<'PY'
from pymongo import MongoClient
client = MongoClient("$MONGODB_URL")
db = client["document_index"]
print("documents", db["documents"].count_documents({}))
print("chunks", db["chunks"].count_documents({}))
print("sample_document", db["documents"].find_one({}, {"document_id": 1, "source": 1, "tags": 1}))
PY
```

### Redis Manual Checks
```bash
poetry run python - <<'PY'
from redis import Redis
import os
client = Redis(host=os.environ["REDIS_HOST"], port=int(os.environ["REDIS_PORT"]), password=os.environ["REDIS_PASSWORD"])
sample_key = client.randomkey()
print("sample_key", sample_key)
if sample_key:
    print("fields", client.hgetall(sample_key))
PY
```

## 5. Fallback Strategy (Redis → FAISS file store)
- When RediSearch is unavailable, embeddings are persisted to `var/indices/embedding_index_v1.pkl`.
- Each chunk tagged with fallback embeddings carries `metadata.fallback = "sha256"` and `metadata.embedding_model = "fallback-sha256"`.
- Replacing fallback vectors with real embeddings:
  ```bash
  poetry run python -m src.presentation.cli.backoffice.main \
      index run --replace-fallback
  ```
  The command deletes existing fallback chunks from Mongo/Redis and removes the local index file before re-running the pipeline.
- Inspect fallback counts with `index inspect --show-fallback`.
- Enable RediSearch in shared infrastructure (see `docs/specs/operations.md`) to automatically resume Redis persistence. The FAISS-compatible file (pickle format) remains as an audit trail.

## 6. Troubleshooting
| Symptom | Mitigation |
|---------|------------|
| `redis_schema_unavailable` warning | RediSearch module absent. Embeddings fall back to local file store (`var/indices/embedding_index_v1.pkl`). Enable RediSearch or migrate to FAISS for similarity queries. |
| `embedding_api_unavailable` warning | `/v1/embeddings` missing. Gateway falls back to deterministic SHA-256 embeddings; rerun with `--replace-fallback` once the endpoint becomes available. |
| `source_missing` warning | Configured source path not found. Verify path and adjust `--source` argument or `embedding_sources` setting. |
| Mongo auth errors | Ensure `MONGODB_URL` includes credentials + `authSource=admin`. |

## 7. Maintenance Guidelines
- Re-run indexer after documentation updates or new lecture drops.
- Clean Redis hashes if storage needs reset: `redis-cli -a $REDIS_PASSWORD --scan --pattern 'embedding:chunk:*' | xargs redis-cli -a $REDIS_PASSWORD del`.
- Track fallback usage via Mongo chunk metadata (`metadata.fallback == "sha256"`) or `index inspect --show-fallback`.
- Plan RediSearch enablement or FAISS upgrade for retrieval features (EP19 follow-up).
