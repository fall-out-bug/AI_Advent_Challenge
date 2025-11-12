# Day 19 · Document Embedding Index

## Scope
- Ingest corpus (project docs + lectures), chunk text, generate embeddings via local LLM API.
- Persist vectors/metadata using shared infra (Redis/FAISS + Mongo).

## Where to Look
- Epic: `docs/specs/epic_19/`
- Key files: `epic_19.md`, `stage_19_01.md`, `stage_19_02.md`, `stage_19_03.md`, `stage_19_04.md`
- Demo/links: `stage_19_05_spec_inventory.md`

## Outcomes
- MVP index for `docs/`, `~/rework-branch/mlsd/lections`, `~/rework-branch/bigdata/lections`.
- CLI/scripts for indexing/inspection; fallback to FAISS if Redis unavailable.

## Next
- Wire retrieval to RAG agent (Day 20).*** End Patch```  }```  ***!
