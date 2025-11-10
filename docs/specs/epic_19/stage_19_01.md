# Stage 19_01 · Discovery & Requirements Alignment

## Goal
Define the scope for the document embedding index, catalogue target sources, and choose storage/embedding strategies compatible with shared infrastructure.

## Checklist
- [ ] Inventory target corpora:
  - `docs/` (project documentation, specs)
  - `/home/fall_out_bug/rework-branch/mlsd/lections`
  - `/home/fall_out_bug/rework-branch/bigdata/lections`
- [ ] Decide on preprocessing requirements (Markdown → plain text, PDF → text, code blocks handling).
- [ ] Confirm embedding strategy (local OpenAI-compatible endpoint backed by existing model) and chunking parameters (size, overlap).
- [ ] Select storage layout:
  - Metadata in MongoDB collection (`document_index.metadata`)
  - Vector store leveraging Redis (Redisearch) with FAISS-compatible export.
- [ ] Draft backlog (`stage_19_01_backlog.md`) and architecture outline (`stage_19_01_architecture.md`).
- [ ] Capture security and retention policies (local storage path vs external).

## Deliverables
- Requirements summary (`stage_19_01_summary.md`) capturing decisions and open questions.
- Backlog covering ingestion, chunking, embeddings, storage, CLI integration.
- Architecture outline / data flow diagram for pipeline components.

## Metrics & Evidence
- Document inventory table with counts and formats.
- Sample conversion log (e.g., PDF → text run) demonstrating feasibility.
- Confirmation that MongoDB/Redis collections are reachable (connection check).

## Dependencies
- Shared infra credentials sourced per `docs/specs/operations.md`.
- Access to lecture directories on host filesystem.
- Alignment with EP06 repository cleanup plan to avoid conflicting moves.

## Exit Criteria
- Stakeholder (you) signs off on requirements document and backlog.
- Storage and embedding choices finalised; no open blockers for Stage 19_02.
- Data access confirmed for all target directories.

## Open Questions
- Need to confirm any exclusions (e.g., skip large binary attachments?).
- Are there naming conventions or tags required for metadata (e.g., `source=mlsd`)?
