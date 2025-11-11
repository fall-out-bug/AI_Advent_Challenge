# Stage 19_02 · Design and Prototyping

## 1. Goals
- Translate Stage 19_01 requirements into a Clean Architecture blueprint.
- Establish domain value objects for documents, chunks, and embeddings.
- Deliver infrastructure prototypes that validate LLM embedding calls and
  Redis vector index creation.
- Capture testing strategy and open issues ahead of Stage 19_03 implementation.

## 2. Architecture Overview
```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Presentation Layer (CLI/API)                     │
│  - `embedding_index.py` CLI commands (`index run`, `index inspect`)      │
│  - Future API adapters (gRPC/HTTP) for retrieval                         │
├──────────────────────────────────────────────────────────────────────────┤
│                         Application Layer                                │
│  - `EmbeddingIndexOrchestrator` (batch ingestion + DI)                   │
│  - `ChunkingService` (windowed chunking, overlap management)             │
│  - `EmbeddingService` (batch to local API with rate limiting)            │
│  - `PersistenceService` (writes metadata + vectors via repositories)     │
├──────────────────────────────────────────────────────────────────────────┤
│                         Domain Layer                                     │
│  - Value objects (`DocumentRecord`, `DocumentChunk`, `EmbeddingVector`)  │
│  - Repository interfaces (`DocumentRepository`, `VectorStore`)           │
│  - Policies (chunk sizing, metadata tagging)                             │
├──────────────────────────────────────────────────────────────────────────┤
│                         Infrastructure Layer                             │
│  - Filesystem ingestion adapter                                          │
│  - Markdown/PDF preprocessors                                            │
│  - `LocalEmbeddingClient` (HTTPX client for local LLM API)               │
│  - Redis schema manager + persistence adapter                            │
│  - MongoDB repositories (metadata/chunk storage)                         │
└──────────────────────────────────────────────────────────────────────────┘
```

Dependency boundaries:
- Domain layer remains pure; application services depend on domain interfaces.
- Infrastructure adapters implement domain interfaces and are injected via the
  application service constructors.
- Presentation layer (CLI/API) only references application services.

## 3. Domain Modelling
- Added package `src/domain/embedding_index/value_objects.py` containing:
  - `DocumentRecord`: metadata (id, source path, source tag, language, SHA-256,
    optional tags). Validation enforces non-empty fields and hex digest length.
  - `DocumentChunk`: chunk identifier, parent document id, ordinal, text,
    token count, optional metadata.
  - `EmbeddingVector`: tuple of floats, model id, dimension, optional metadata,
    with helper `as_list()` for mutable copies.
- Tests: `tests/unit/domain/embedding_index/test_value_objects.py` exercises
  mandatory field validation and vector dimensionality guarantees.
- Repository interfaces (for Stage 19_03):
  - `DocumentRepository`: add/find `DocumentRecord`.
  - `ChunkRepository`: persist/retrieve `DocumentChunk`.
  - `VectorStore`: upsert embeddings, similarity search.

## 4. Application Design
- `EmbeddingIndexOrchestrator` (to be implemented): orchestrates pipeline:
  1. Enumerate documents -> build `DocumentRecord`.
  2. Execute preprocessing + chunking -> produce `DocumentChunk`.
  3. Batch chunk texts -> `EmbeddingService`.
  4. Persist metadata + vectors using repositories.
- Chunking strategy: sliding window on token estimates with 1,200-token target
  and 200-token overlap (configurable).
- Error handling: orchestrator raises `EmbeddingIndexError` on irrecoverable
  failures; partial progress recorded in Mongo for resumption.
- Metrics hooks: decorators capture processing duration, chunk counts, and
  embedding latency for Prometheus (implement in Stage 19_03).

## 5. Infrastructure Prototypes
- `LocalEmbeddingClient` (`src/infrastructure/embeddings/local_embedding_client.py`)
  - Uses `httpx.post` against `/v1/embeddings`.
  - Returns domain `EmbeddingVector` objects; validates response schema.
  - Raises `EmbeddingClientError` for HTTP/JSON issues.
  - Tests: `tests/unit/infrastructure/embedding_index/test_local_embedding_client.py`
    mock HTTP responses to verify happy-path, error handling, and validation.
- `RedisSchemaManager` (`src/infrastructure/vector_store/redis_schema_manager.py`)
  - Builds `FT.CREATE` command for RediSearch index creation.
  - Accepts any client implementing `execute_command`; surfaces failures as
    `RedisSchemaError`.
  - Tests: `tests/unit/infrastructure/embedding_index/test_redis_schema_manager.py`
    assert command structure and error wrapping via fake clients.
- Evidence generated:
  - Domain prototypes align with Stage 19_01 metadata/tagging rules.
  - Unit tests run locally (see Stage 19_02 validation step).

## 6. Testing Strategy
- Unit tests cover domain validation and infrastructure prototypes (already
  implemented).
- Stage 19_03 will add:
  - Application-layer tests using in-memory repositories.
  - Integration tests with mocked Mongo/Redis (using dockerised fixtures or
    local services from operations guide).
  - CLI smoke tests to verify wiring and logging.
- Coverage targets: domain ≥85%, infrastructure ≥80%.

## 7. Open Issues & Next Steps
- Add Redis client dependency (`redis` or `redis[hiredis]`) in Stage 19_03 to
  replace the protocol-based fake.
- Finalise chunking/token estimation utility (consider `tiktoken` vs. heuristic
  splitter).
- Define MongoDB schema migrations (indexes on `document_id`, `sha256`).
- Design Prometheus metrics (processing durations, chunk counts, error totals)
  and integrate with Stage 19_03 application services.
- Decide on retry/backoff policy for Redis writes (Stage 19_03).
- Prepare CLI UX (flags for dry-run, chunk preview, index inspection).
