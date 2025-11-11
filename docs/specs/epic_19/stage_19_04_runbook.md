# Stage 19_04 · Embedding Index Runbook

## 1. Prerequisites
- Docker + Docker Compose available on host.
- Shared infrastructure running locally (MongoDB, Redis, LLM API). For default
  environment use `make day-12-up` or equivalent infra bootstrap.
- Host directories:
  - `~/work/infra/.env.infra` (readable) plus `secrets/mongo_password.txt`, `secrets/redis_password.txt`.
  - Optional: lecture repos mounted at `~/rework-branch/mlsd/lections` and `~/rework-branch/bigdata/lections`.

## 2. Container Workflow (recommended)
- Build container image:
  ```bash
  make index-container-build
  ```
- Run indexer (replaces fallback embeddings by default):
  ```bash
  make index-container-run INDEX_RUN_ARGS="--replace-fallback"
  ```
- Open interactive shell for troubleshooting:
  ```bash
  make index-container-shell
  ```
  Inside the shell, infra credentials from `/root/work/infra/.env.infra` are sourced automatically.

### Default Sources (inside container)
1. `/workspace/docs`
2. `/root/rework-branch/mlsd/lections` (bind-mounted from host)
3. `/root/rework-branch/bigdata/lections`

Override or extend sources by setting `INDEX_RUN_ARGS`:
```bash
make index-container-run INDEX_RUN_ARGS="--replace-fallback --source /extra/docs --source /mnt/data"
```

## 3. Inspecting Results
```bash
make index-container-run INDEX_RUN_ARGS="index inspect"
# Add --show-fallback to include the number of chunks stored with SHA-256 embeddings
make index-container-run INDEX_RUN_ARGS="index inspect --show-fallback"
# Example output:
# documents=293
# chunks=382
# fallback_chunks=0
# redis_index=missing  # RediSearch not loaded -> warnings logged (FAISS fallback active)
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

## 4. Local (Poetry) Workflow (optional fallback)
Only use if Docker is unavailable. Export credentials manually (mirrors container setup):
```bash
export MONGO_USER=admin
export MONGO_PASSWORD=$(cat ~/work/infra/secrets/mongo_password.txt)
export MONGODB_URL="mongodb://${MONGO_USER}:${MONGO_PASSWORD}@127.0.0.1:27017/butler?authSource=admin"
export REDIS_HOST=127.0.0.1
export REDIS_PORT=6379
export REDIS_PASSWORD=$(cat ~/work/infra/secrets/redis_password.txt)
export LLM_URL=http://127.0.0.1:8000
export LLM_MODEL=all-MiniLM-L6-v2

poetry run python -m src.presentation.cli.backoffice.main index run --replace-fallback
```

## 5. Fallback Strategy (Redis → FAISS file store)
- When RediSearch is unavailable, embeddings are persisted to `var/indices/embedding_index_v1.pkl` inside the container volume.
- MiniLM embeddings are returned by default; SHA-256 fallback now triggers only on HTTP errors/timeouts.
- To force-refresh historical fallback data:
  ```bash
  make index-container-run INDEX_RUN_ARGS="--replace-fallback"
  ```
  The command clears fallback chunks from Mongo/Redis/FAISS before re-running the pipeline.
- Inspect fallback counts with `make index-container-run INDEX_RUN_ARGS="index inspect --show-fallback"`.
- Enable RediSearch in shared infrastructure (see `docs/specs/operations.md`) to resume Redis persistence. The FAISS-compatible file (pickle format) remains as an audit trail.

## 6. Troubleshooting
| Symptom | Mitigation |
|---------|------------|
| `redis_schema_unavailable` warning | RediSearch module absent. Embeddings fall back to local file store (`var/indices/embedding_index_v1.pkl`). Enable RediSearch or migrate to FAISS for similarity queries. |
| `embedding_api_unavailable` warning | `/v1/embeddings` unreachable or returning ≥500. Gateway falls back to deterministic SHA-256 embeddings; rerun with `--replace-fallback` after fixing the endpoint. |
| `source_missing` warning | Configured source path not found. Verify path and adjust `--source` argument or `embedding_sources` setting. |
| Mongo auth errors | Ensure `MONGODB_URL` includes credentials + `authSource=admin`. |

## 7. Maintenance Guidelines
- Re-run indexer after documentation updates or new lecture drops.
- Clean Redis hashes if storage needs reset: `redis-cli -a $REDIS_PASSWORD --scan --pattern 'embedding:chunk:*' | xargs redis-cli -a $REDIS_PASSWORD del`.
- Track fallback usage via Mongo chunk metadata (`metadata.fallback == "sha256"`) or `index inspect --show-fallback`.
- Plan RediSearch enablement or FAISS upgrade for retrieval features (EP19 follow-up).
