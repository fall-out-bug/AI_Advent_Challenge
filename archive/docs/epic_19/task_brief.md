# Task Brief · Day 19

## Problem Statement
- Gather a set of documents (README, articles, code, PDF → text).
- Implement a pipeline: text ingestion → chunking → embedding generation.
- Persist the index locally (FAISS, SQLite with vectors, or JSON).
- Deliverable: local document index with embeddings for semantic retrieval.

## Integration with Epic 19
Epic 19 reframes the task to fit within our Clean Architecture project:
- Corpus targets: `docs/` + external lecture directories `~/rework-branch/mlsd/lections` and `~/rework-branch/bigdata/lections`.
- Pipeline stages map to Stage 19_01–19_04 (discovery, design, implementation, validation).
- Storage leverages shared infra (MongoDB metadata, Redis/FAISS vector store).
- Embeddings generated via the local OpenAI-compatible API (backed by existing model).

## MVP Expectations
- One-time indexing run for demonstration (no incremental update required yet).
- Chunk size/overlap defined during Stage 19_01; ensure metadata records document hashes for future delta support.
- Documentation (EN/RU) updated to explain how to rerun the indexer.

## Follow-up Ideas (beyond MVP)
- Incremental updates based on file hashes or timestamps.
- Search API / CLI to query the index.
- Benchmarking retrieval quality with semantic QA tasks.
