# Stage 19 · Document Embedding Index Demo Plan

## 1. Goal
Demonstrate how the Stage 19 pipeline ingests repository documentation and lecture
notes, generates embeddings, and exposes operational tooling for maintainers.

## 2. Prerequisites
- Shared infrastructure running (`make day-12-up` or manual bootstrap).
- Credentials exported (Mongo, Redis, LLM) as described in `stage_19_04_runbook.md`.
- Optional: clean fallback state by running `poetry run python -m src.presentation.cli.backoffice.main index run --replace-fallback`.
- Updated spec inventory (`stage_19_05_spec_inventory.md`) available as reference.

## 3. Agenda (≈20 minutes)
1. **Context (3 min)**  
   - Walk through spec inventory: highlight EP00–EP06 inputs, architecture boundaries, and EP19 objectives.
2. **Pipeline Architecture (4 min)**  
   - Review Clean Architecture diagram (Stage 19_02) and mention gateway fallback logic.
3. **Live Indexing Run (6 min)**  
   - Execute `index run` command, narrate fallback behaviour if `/v1/embeddings` is unavailable.
4. **Inspect Results (4 min)**  
   - Show `index inspect --show-fallback`, Mongo queries, and Redis/FAISS artefacts.
5. **Q&A / Next Steps (3 min)**  
   - Discuss Epic 23 Prometheus work, retrieval API roadmap, and demo hand-off.

## 4. Demo Script

### Step 1: Reference Specs
```bash
bat docs/specs/epic_19/stage_19_05_spec_inventory.md
```
Call out key rows (EP00 scope, EP03 metrics, operations/architecture cross-cutting).

### Step 2: Run Indexer
```bash
poetry run python -m src.presentation.cli.backoffice.main index run
# Optional re-run after embedding endpoint switches live:
poetry run python -m src.presentation.cli.backoffice.main index run --replace-fallback
```
While running, highlight:
- Chunking parameters (`chunk_size_tokens`, `chunk_overlap_tokens`).
- SHA-256 fallback warnings if `/v1/embeddings` returns 404.
- Local fallback persistence (`var/indices/embedding_index_v1.pkl`).

### Step 3: Inspect Counts & Metadata
```bash
poetry run python -m src.presentation.cli.backoffice.main index inspect --show-fallback
poetry run python - <<'PY'
from pymongo import MongoClient
import os
client = MongoClient(os.environ["MONGODB_URL"])
collection = client["document_index"]["chunks"]
print("Sample chunk:", collection.find_one({}, {"chunk_id": 1, "metadata": 1}))
PY
```
Point out `metadata.fallback` flag and `embedding_model` entries.

### Step 4: Discuss Retrieval Roadmap
- Emphasise RediSearch enablement path from `stage_19_04_runbook.md`.
- Note FAISS-compatible file for offline demos.

## 5. Talking Points
- Clean Architecture enforcement (no cross-layer imports).
- Deterministic fallback strategy ensures demo reliability even without embedding endpoint.
- Mongo metadata enables downstream analytics (language, stage tags, fallback indicators).
- Future Epic 23 work will add Prometheus metrics; retrieval API planned post-fallback replacement.

## 6. Anticipated Questions
| Question | Suggested Answer |
|----------|------------------|
| How do we regenerate real embeddings once the API is exposed? | Run `index run --replace-fallback` after enabling `/v1/embeddings`; fallback chunks are automatically purged prior to re-index. |
| Can we query the embeddings today? | Redis RediSearch must be enabled; otherwise use the FAISS-compatible file as interim storage. Retrieval API is on the roadmap. |
| What happens if new docs are added? | Re-run the indexer; chunk hashes and metadata upserts make the operation idempotent. |

## 7. Follow-up Artefacts
- `stage_19_04_runbook.md` — operational guide with fallback details.
- `stage_19_04_report.md` — validation metrics and open items.
- `stage_19_05_spec_inventory.md` — canonical reference list for maintainers.

