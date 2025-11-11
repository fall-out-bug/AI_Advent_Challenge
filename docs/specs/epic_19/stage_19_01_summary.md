# Stage 19_01 Summary · Document Embedding Index

## 1. Overview
- Confirmed discovery scope for the document embedding index (project docs plus
  MLSD/BigData lecture folders).
- Established preprocessing, embedding, and storage strategies in line with
  Clean Architecture and shared infrastructure constraints.
- Recorded evidence of data access, connectivity checks, and sample text
  conversion.

## 2. Corpus Inventory
| Corpus | Total Files | Size (MB) | Markdown | Text | JSON | YAML | Code | Other | Notes |
|--------|-------------|-----------|----------|------|------|------|------|-------|-------|
| docs | 246 | 1.31 | 220 | 21 | 4 | 0 | 0 | 1 | Covers specs, ops guides, architecture docs. |
| mlsd_lections | 36 | 0.71 | 25 | 7 | 0 | 1 | 1 | 2 | Includes homework statements and configs. |
| bigdata_lections | 7 | 0.17 | 0 | 7 | 0 | 0 | 0 | 0 | Plain-text lecture summaries. |

Large file policy:
- Skip binaries ≥ 20 MB (none detected in the initial scan).
- Record skipped filenames in the run report for auditability.

## 3. Preprocessing Decisions
- Markdown: strip YAML front matter, keep headings as text, retain fenced code
  blocks with ```` ```lang```` delimiters so downstream consumers can decide
  whether to include them. Initial implementation will use a lightweight parser
  with markdown token stripping; Stage 19_02 will evaluate `markdown-it-py` for
  richer structure.
- Plain text: normalise line endings and collapse excess blank lines while
  preserving paragraphs.
- PDFs: extract text with `pypdf` (fallback to `pdfminer.six` if tables/images
  require additional handling). No PDFs present in the initial corpus, but the
  pipeline will keep optional dependencies behind feature flags.
- Encoding: enforce UTF-8 input; files failing to decode will be logged and
  excluded until manual remediation.
- Language tagging: default `language=ru` for metadata; optionally add
  `language_detected` field once fasttext/fastlang integration is available.

## 4. Embedding Configuration
- Provider: local OpenAI-compatible API (`http://127.0.0.1:8000`) using model
  `text-embedding-3-small`.
- Chunking: target ~1,200 tokens (~4,800 characters) with 200-token overlap;
  smaller documents remain whole when below half the target size.
- Hashing: compute SHA-256 of source file plus preprocessing configuration to
  support idempotent re-runs and future incremental updates.
- Rate limiting: batch requests to ≤64 chunks per minute until empirical limits
  are confirmed; exponential backoff on HTTP 429/5xx.

## 5. Storage Layout
- MongoDB (metadata):
  - Database: `document_index`
  - Collections:
    - `documents`: `{document_id, source_path, sha256, language, tags, created_at}`
    - `chunks`: `{chunk_id, document_id, ordinal, text, token_count, embedding_ref}`
- Redis (vector store via RediSearch module):
  - Index name: `embedding:index:v1`
  - Key pattern: `embedding:chunk:{chunk_id}`
  - Schema: `{embedding VECTOR, document_id TAG, source TAG, stage TAG}`
- FAISS fallback: local file-backed index stored under
  `var/indices/embedding_index_v1.faiss` for offline development.
- Naming conventions: collections and keys are prefixed with `embedding` to
  avoid clashes with existing review pipeline artefacts.

## 6. Metadata & Tagging
- Required tags per chunk:
  - `source`: directory identifier (`docs`, `mlsd_lections`, `bigdata_lections`).
  - `stage`: fixed value `19`.
  - `language`: fixed value `ru`.
- Optional metadata captured in Mongo (not indexed in Redis):
  - `content_type`: `markdown`, `pdf`, `text`, `code`, `json`, `yaml`, etc.
  - `chunk_strategy`: descriptor of the chunker configuration.
  - `embedding_model_version`: e.g., `text-embedding-3-small@2025-11-10`.

## 7. Connectivity Verification
- MongoDB: `poetry run python` script executed with credentials from
  `/home/fall_out_bug/work/infra/.env.infra`; `admin.command("ping")`
  succeeded (`mongo=ok`).
- Redis: TCP handshake to `127.0.0.1:6379` returned `-NOAUTH` as expected,
  confirming port reachability and the need to issue `AUTH {password}` before
  RediSearch commands. Redis Python client (`redis-py`) is not yet installed;
  add dependency during Stage 19_03.

## 8. Security & Retention
- Secrets are sourced exclusively from `/home/fall_out_bug/work/infra/.env.infra`
  and never persisted in repository files.
- Embedding payloads include document hashes to support auditing and eventual
  TTL policies.
- Index artefacts stored locally under `var/indices/` respect `.gitignore`.
- Manual review required before indexing any document outside the approved
  directories.

## 9. Evidence
- Inventory script: ad-hoc Python walker generating file counts and sizes
  (command captured in session log on 2025-11-10).
- Sample text conversion:
  `docs/specs/epic_19/evidence/stage_19_01_sample_conversion.txt` generated from
  `docs/specs/specs.md` via prototype Markdown flattener.
- Connectivity check: see `poetry run python` command with Mongo ping and Redis
  socket probe (2025-11-10).

## 10. Open Items for Stage 19_02
- Finalise Markdown parsing approach (evaluate `markdown-it-py` vs. existing
  prototype; determine if code blocks need separate chunking).
- Add Redis client dependency and authenticate before running RediSearch
  commands.
- Produce architecture outline/diagram covering domain entities, application
  orchestration, and infrastructure adapters.
- Define Prometheus metrics schema (processing duration, chunk counts, HTTP
  error rates) and logging structure for ingestion jobs.
