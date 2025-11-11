# Epic 19 · Document Embedding Index

## Purpose
Build a pipeline that ingests project documentation and lecture notes, chunks text, generates embeddings with the local LLM API, and stores the resulting vector index using existing shared infrastructure (MongoDB/Redis/Postgres).

## Objectives
- Catalogue target corpora (`docs/`, selected lecture folders) and normalise them into a common ingestion format (plain text + metadata).
- Design and implement a modular pipeline (ingestion → chunking → embeddings → persistence) compliant with Clean Architecture.
- Persist embeddings and metadata in shared infra (MongoDB for metadata + Redis/FAISS for vector similarity) and expose CLI commands for indexing and inspection.
- Produce initial index covering `/home/fall_out_bug/rework-branch/mlsd/lections` and `/home/fall_out_bug/rework-branch/bigdata/lections` as an MVP demo run.

## Dependencies
- Shared infrastructure: MongoDB, Redis, Postgres (availability assumed per `docs/specs/operations.md`).
- EP06 repository reorganisation (ensure ingestion paths align with final docs tree).
- LLM API (OpenAI-compatible endpoint backed by local model, per operations guide).

## Stage Breakdown
| Stage | Scope | Key Deliverables | Exit Criteria |
|-------|-------|------------------|---------------|
| Stage 19_01 | Discovery & requirements alignment | Corpus inventory, ingestion requirements, storage decision, backlog | Requirements document approved; backlog prioritised |
| Stage 19_02 | Pipeline design & prototyping | Architecture diagram, ingestion/chunking prototypes, storage adapters | Prototype processes sample docs, design validated |
| Stage 19_03 | Implementation & integration | Production-ready pipeline, CLI commands, tests, shared infra config | Index built for target corpora, tests passing |
| Stage 19_04 | Validation & documentation | Benchmark report, maintainer guide, index artefact, future roadmap | Demo index delivered, docs updated, sign-off recorded |
| Stage 19_05 | Reference linkage & knowledge hand-off | Consolidated index of legacy specs (EP00–EP06) integrated into documentation | Spec inventory available alongside index demo, stakeholders sign off |

## Success Criteria
- Pipeline modular and testable; domain/application layers independent of infrastructure details.
- Embeddings generated via local LLM API; metadata and vectors persisted in shared infra without ad-hoc stores.
- MVP index covering the specified lecture directories produced and stored with reproducible commands.
- Documentation (EN/RU) and CLI instructions available for rerunning the indexer.

## Stakeholders
- Tech Lead Agent: TBD (planning, approvals).
- Developer Agents: implement ingestion, embeddings, storage.
- Operations/Infra: ensure shared services accessible and monitored.

## Risks & Mitigations
- **Risk:** Large corpora cause memory/time issues.
  **Mitigation:** Configurable chunk size/overlap; incremental processing per directory.
- **Risk:** Shared infra quotas (Redis/Mongo) exceeded.
  **Mitigation:** Establish namespace/collection naming and retention policy; monitor usage.
- **Risk:** LLM embedding API variability.
  **Mitigation:** Cache embeddings per document hash; log version/model metadata.

## References
- `docs/specs/operations.md` — shared infra access.
- `docs/specs/epic_05/stage_05_01_starter_kit.md` — dataset/benchmark templates (reuse for metadata).
- `docs/specs/epic_06/repo_cleanup_rfc.md` — ensure doc locations remain stable.
