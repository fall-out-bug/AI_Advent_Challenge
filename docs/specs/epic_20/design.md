# Epic 20 Design Document · RAG vs Non-RAG Answering Agent

## 1. Architecture Overview

### 1.1 High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Query                               │
│                  (from CLI or queries.jsonl)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              CompareRagAnswersUseCase                            │
│              (Application Layer)                                 │
└─────────┬─────────────────────────────────┬─────────────────────┘
          │                                 │
          │ Non-RAG Path                    │ RAG Path
          │                                 │
          ▼                                 ▼
┌──────────────────────┐        ┌──────────────────────────────────┐
│  LLM Gateway         │        │  RetrievalService                │
│  (direct prompt)     │        │  (search → retrieve chunks)      │
└──────────────────────┘        └─────────┬────────────────────────┘
          │                               │
          │                               ▼
          │                     ┌──────────────────────────────────┐
          │                     │  EmbeddingGateway                │
          │                     │  (embed query)                   │
          │                     └─────────┬────────────────────────┘
          │                               │
          │                               ▼
          │                     ┌──────────────────────────────────┐
          │                     │  VectorSearchAdapter             │
          │                     │  (Redis/FAISS search)            │
          │                     └─────────┬────────────────────────┘
          │                               │
          │                               ▼
          │                     ┌──────────────────────────────────┐
          │                     │  ChunkRepository                 │
          │                     │  (fetch metadata)                │
          │                     └─────────┬────────────────────────┘
          │                               │
          │                               ▼
          │                     ┌──────────────────────────────────┐
          │                     │  PromptAssembler                 │
          │                     │  (format context + question)     │
          │                     └─────────┬────────────────────────┘
          │                               │
          │                               ▼
          │                     ┌──────────────────────────────────┐
          │                     │  LLM Gateway                     │
          │                     │  (RAG prompt)                    │
          │                     └─────────┬────────────────────────┘
          │                               │
          └───────────────┬───────────────┘
                          ▼
                ┌──────────────────────────────────────┐
                │  ComparisonResult                    │
                │  (both answers + metadata)           │
                └──────────────────────────────────────┘
```

### 1.2 Layer Responsibilities

| Layer | Components | Responsibilities |
|-------|-----------|------------------|
| **Domain** | `Query`, `Answer`, `RetrievedChunk`, `ComparisonResult` | Value objects; pure business logic |
| **Application** | `CompareRagAnswersUseCase`, `RetrievalService` | Orchestration; no infrastructure coupling |
| **Infrastructure** | `VectorSearchAdapter`, `MongoChunkRepository`, `LocalEmbeddingGateway`, `LLMClient` | External integrations (DB, API, file I/O) |
| **Presentation** | CLI commands: `rag:compare`, `rag:batch` | User interface; parse args, format output |

---

## 2. Domain Layer

### 2.1 Value Objects

#### 2.1.1 `Query`

```python
@dataclass(frozen=True)
class Query:
    """User query for Q&A system."""

    id: str
    question: str
    category: str | None = None
    language: str = "ru"
    expectation: str | None = None  # Optional ground truth for evaluation
```

#### 2.1.2 `Answer`

```python
@dataclass(frozen=True)
class Answer:
    """LLM-generated answer."""

    text: str
    model: str
    latency_ms: int
    tokens_generated: int
    metadata: Mapping[str, str] | None = None
```

#### 2.1.3 `RetrievedChunk`

```python
@dataclass(frozen=True)
class RetrievedChunk:
    """Retrieved document chunk with similarity score."""

    chunk_id: str
    document_id: str
    text: str
    similarity_score: float
    source_path: str
    metadata: Mapping[str, str]
```

#### 2.1.4 `ComparisonResult`

```python
@dataclass(frozen=True)
class ComparisonResult:
    """Side-by-side comparison of RAG vs non-RAG answers."""

    query: Query
    without_rag: Answer
    with_rag: Answer
    chunks_used: Sequence[RetrievedChunk]
    timestamp: str
```

---

### 2.2 Domain Interfaces

#### 2.2.1 `VectorSearchService` (Protocol)

```python
class VectorSearchService(Protocol):
    """Search for similar vectors in the index."""

    def search(
        self,
        query_vector: EmbeddingVector,
        top_k: int,
        score_threshold: float,
    ) -> Sequence[RetrievedChunk]:
        """Return top-k chunks above similarity threshold."""
```

#### 2.2.2 `LLMService` (Protocol)

```python
class LLMService(Protocol):
    """Generate text completions from prompts."""

    def generate(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> Answer:
        """Generate completion and return answer with metadata."""
```

---

## 3. Application Layer

### 3.1 `CompareRagAnswersUseCase`

**Purpose**: Orchestrate side-by-side comparison of RAG vs non-RAG answers.

**Dependencies**:
- `RetrievalService`: Retrieve and rank chunks
- `PromptAssembler`: Format prompts for both modes
- `LLMService`: Generate answers
- `EmbeddingGateway`: Embed query text

**Workflow**:

```python
class CompareRagAnswersUseCase:
    def execute(self, query: Query) -> ComparisonResult:
        # 1. Non-RAG path (baseline)
        non_rag_prompt = self._prompt_assembler.build_non_rag_prompt(query.question)
        without_rag = self._llm_service.generate(non_rag_prompt, ...)

        # 2. RAG path
        query_vector = self._embedding_gateway.embed_query(query.question)
        chunks = self._retrieval_service.retrieve(query_vector, top_k=5, ...)
        rag_prompt = self._prompt_assembler.build_rag_prompt(query.question, chunks)
        with_rag = self._llm_service.generate(rag_prompt, ...)

        # 3. Assemble result
        return ComparisonResult(
            query=query,
            without_rag=without_rag,
            with_rag=with_rag,
            chunks_used=chunks,
            timestamp=...,
        )
```

---

### 3.2 `RetrievalService`

**Purpose**: Encapsulate retrieval logic (search + fetch metadata).

**Dependencies**:
- `VectorSearchService`: Perform similarity search
- `ChunkRepository`: Fetch full chunk metadata

**Workflow**:

```python
class RetrievalService:
    def retrieve(
        self,
        query_vector: EmbeddingVector,
        top_k: int,
        score_threshold: float,
    ) -> Sequence[RetrievedChunk]:
        # 1. Search for similar vectors
        chunk_ids_with_scores = self._vector_search.search(
            query_vector, top_k, score_threshold
        )

        # 2. Fetch full chunk metadata from repository
        chunks = []
        for chunk_id, score in chunk_ids_with_scores:
            chunk_data = self._chunk_repository.get_by_id(chunk_id)
            chunks.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    similarity_score=score,
                    text=chunk_data.text,
                    ...
                )
            )

        return chunks
```

---

### 3.3 `PromptAssembler`

**Purpose**: Format prompts according to templates (non-RAG and RAG).

**Methods**:

```python
class PromptAssembler:
    def build_non_rag_prompt(self, question: str) -> str:
        """Return baseline prompt (no context)."""
        return SYSTEM_PROMPT_NON_RAG.format(question=question)

    def build_rag_prompt(
        self,
        question: str,
        chunks: Sequence[RetrievedChunk],
        max_context_tokens: int = 3000,
    ) -> str:
        """Return RAG prompt with context from retrieved chunks."""
        context = self._format_chunks(chunks, max_context_tokens)
        return SYSTEM_PROMPT_RAG.format(context=context, question=question)

    def _format_chunks(
        self,
        chunks: Sequence[RetrievedChunk],
        max_tokens: int,
    ) -> str:
        """Format chunks with budget control."""
        # Truncate chunks if total exceeds max_tokens
        ...
```

---

## 4. Infrastructure Layer

### 4.1 `VectorSearchAdapter`

**Purpose**: Perform similarity search in Redis/FAISS.

**Implementation Options**:

#### Option A: Redis RediSearch (preferred)

```python
class RedisVectorSearchAdapter:
    def search(
        self,
        query_vector: EmbeddingVector,
        top_k: int,
        score_threshold: float,
    ) -> Sequence[Tuple[str, float]]:
        """Use Redis FT.SEARCH with KNN query."""
        # Build RediSearch KNN query
        query = (
            f"*=>[KNN {top_k} @embedding $query_vec AS score]"
        )
        query_params = {
            "query_vec": self._encode_vector(query_vector),
        }

        # Execute search
        results = self._client.ft(self._index_name).search(
            Query(query).return_fields("chunk_id", "score").dialect(2),
            query_params,
        )

        # Filter by threshold
        return [
            (doc.chunk_id, float(doc.score))
            for doc in results.docs
            if float(doc.score) >= score_threshold
        ]
```

#### Option B: FAISS File Store (fallback)

```python
class FaissVectorSearchAdapter:
    def search(
        self,
        query_vector: EmbeddingVector,
        top_k: int,
        score_threshold: float,
    ) -> Sequence[Tuple[str, float]]:
        """Use FAISS for local similarity search."""
        # Load FAISS index from pickle
        index = self._load_faiss_index()

        # Search
        distances, indices = index.search(
            np.array([query_vector.values], dtype=np.float32),
            k=top_k,
        )

        # Map indices to chunk_ids and filter by threshold
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if dist >= score_threshold:
                chunk_id = self._index_to_chunk_id[idx]
                results.append((chunk_id, float(dist)))

        return results
```

---

### 4.2 `MongoChunkRepository` (Extended)

**Purpose**: Fetch chunk metadata by ID.

**New Method**:

```python
class MongoChunkRepository:
    def get_by_id(self, chunk_id: str) -> DocumentChunk | None:
        """Fetch chunk by ID from MongoDB."""
        doc = self._collection.find_one({"chunk_id": chunk_id})
        if not doc:
            return None

        return DocumentChunk(
            chunk_id=doc["chunk_id"],
            document_id=doc["document_id"],
            ordinal=doc["ordinal"],
            text=doc["text"],
            token_count=doc["token_count"],
            metadata=doc.get("metadata"),
        )

    def get_by_ids(self, chunk_ids: Sequence[str]) -> Sequence[DocumentChunk]:
        """Batch fetch chunks by IDs."""
        cursor = self._collection.find({"chunk_id": {"$in": list(chunk_ids)}})
        return [self._parse_document(doc) for doc in cursor]
```

---

### 4.3 `LocalEmbeddingGateway` (Extended)

**Purpose**: Embed query text (single-text embedding, not batch).

**New Method**:

```python
class LocalEmbeddingGateway:
    def embed_query(self, text: str) -> EmbeddingVector:
        """Embed a single query string."""
        response = self._client.post(
            f"{self._base_url}/v1/embeddings",
            json={"input": text, "model": self._model},
            timeout=self._timeout,
        )
        response.raise_for_status()
        data = response.json()

        return EmbeddingVector(
            values=tuple(data["data"][0]["embedding"]),
            model=self._model,
            dimension=len(data["data"][0]["embedding"]),
        )
```

---

### 4.4 `LLMClient` (Reuse Existing)

**Purpose**: Generate completions from prompts.

**Integration**: Reuse existing `src/infrastructure/llm/llm_client.py` or create thin wrapper:

```python
class LLMServiceAdapter:
    def __init__(self, llm_client: LLMClient):
        self._client = llm_client

    def generate(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> Answer:
        """Generate completion and wrap in Answer value object."""
        start_time = time.time()

        response = self._client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )

        latency_ms = int((time.time() - start_time) * 1000)

        return Answer(
            text=response["choices"][0]["message"]["content"],
            model=response["model"],
            latency_ms=latency_ms,
            tokens_generated=response["usage"]["completion_tokens"],
        )
```

---

## 5. Presentation Layer

### 5.1 CLI Commands

#### 5.1.1 `rag:compare` (Single Query)

```bash
poetry run cli rag:compare --question "Что такое MapReduce?"
```

**Output** (JSON):

```json
{
  "query": {"id": "cli-query-1", "question": "Что такое MapReduce?"},
  "without_rag": {...},
  "with_rag": {...},
  "chunks_used": [...]
}
```

#### 5.1.2 `rag:batch` (Batch from JSONL)

```bash
poetry run cli rag:batch \
  --queries docs/specs/epic_20/queries.jsonl \
  --out results.jsonl
```

**Output**: JSONL file with one `ComparisonResult` per line.

---

### 5.2 CLI Implementation Sketch

```python
@click.group(name="rag")
def rag_commands():
    """RAG comparison commands."""

@rag_commands.command(name="compare")
@click.option("--question", required=True, help="Question to answer")
def compare_command(question: str):
    """Compare RAG vs non-RAG for a single question."""
    settings = get_settings()
    use_case = _build_use_case(settings)

    query = Query(id="cli-query-1", question=question)
    result = use_case.execute(query)

    click.echo(json.dumps(dataclasses.asdict(result), ensure_ascii=False, indent=2))

@rag_commands.command(name="batch")
@click.option("--queries", required=True, type=click.Path(exists=True))
@click.option("--out", required=True, type=click.Path())
def batch_command(queries: str, out: str):
    """Run batch comparison on queries.jsonl."""
    settings = get_settings()
    use_case = _build_use_case(settings)

    with open(queries, "r") as infile, open(out, "w") as outfile:
        for line in infile:
            query_data = json.loads(line)
            query = Query(**query_data)
            result = use_case.execute(query)
            outfile.write(json.dumps(dataclasses.asdict(result), ensure_ascii=False))
            outfile.write("\n")

    click.echo(f"Results written to {out}")
```

---

## 6. Prototype Plan (Stage 20_02)

### 6.1 Minimal Prototype Scope

**Goal**: Validate retrieval + prompting + answer generation for a single query.

**Script**: `scripts/rag/compare_once.py`

**Steps**:

1. Hardcode a sample query (e.g., "Что такое MapReduce?")
2. Connect to EP19 index (Redis/FAISS + Mongo)
3. Embed query text
4. Search for top-5 chunks
5. Fetch chunk metadata
6. Assemble RAG prompt
7. Generate both answers (non-RAG and RAG)
8. Print side-by-side comparison

**Dependencies**:
- Shared infra running (Mongo, Redis, LLM API)
- EP19 index available (minimal demo index)

**Output**:

```json
{
  "query": "Что такое MapReduce?",
  "without_rag": "MapReduce — это модель программирования...",
  "with_rag": "Согласно лекции...",
  "chunks_used": [...]
}
```

---

### 6.2 Prototype Implementation (Minimal)

```python
#!/usr/bin/env python3
"""Prototype: Single RAG vs non-RAG comparison."""

import json
from pathlib import Path

from pymongo import MongoClient
from redis import Redis

from src.infrastructure.config.settings import get_settings
from src.infrastructure.embeddings import LocalEmbeddingClient
from src.infrastructure.llm import LLMClient

def main():
    settings = get_settings()

    # 1. Sample query
    question = "Что такое MapReduce?"

    # 2. Embed query
    embedding_client = LocalEmbeddingClient(
        api_url=settings.embedding_api_url,
        model=settings.embedding_model,
    )
    query_vector = embedding_client.embed_text(question)

    # 3. Search Redis (simplified, assume RediSearch available)
    redis_client = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
    )
    # TODO: RediSearch KNN query (see design section)
    chunk_ids = ["chunk-1", "chunk-2", "chunk-3"]  # Placeholder

    # 4. Fetch chunks from Mongo
    mongo_client = MongoClient(settings.mongodb_url)
    db = mongo_client[settings.embedding_mongo_database]
    chunks_collection = db[settings.embedding_mongo_chunks_collection]
    chunks = list(chunks_collection.find({"chunk_id": {"$in": chunk_ids}}))

    # 5. Assemble prompts
    non_rag_prompt = f"Вопрос: {question}"
    context = "\n\n".join([c["text"] for c in chunks])
    rag_prompt = f"Контекст:\n{context}\n\nВопрос: {question}"

    # 6. Generate answers
    llm_client = LLMClient(
        base_url=settings.llm_url,
        model=settings.llm_model,
    )

    without_rag = llm_client.chat_completion(
        messages=[{"role": "user", "content": non_rag_prompt}],
        max_tokens=1000,
    )

    with_rag = llm_client.chat_completion(
        messages=[{"role": "user", "content": rag_prompt}],
        max_tokens=1000,
    )

    # 7. Print result
    result = {
        "query": question,
        "without_rag": without_rag["choices"][0]["message"]["content"],
        "with_rag": with_rag["choices"][0]["message"]["content"],
        "chunks_used": len(chunks),
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))

    # Cleanup
    redis_client.close()
    mongo_client.close()

if __name__ == "__main__":
    main()
```

---

## 7. Testing Strategy

### 7.1 Unit Tests

| Component | Test Cases |
|-----------|-----------|
| `Query` | Validation (empty question, missing ID) |
| `Answer` | Validation (negative latency, empty text) |
| `RetrievedChunk` | Validation (similarity score bounds) |
| `ComparisonResult` | Immutability, serialization |
| `PromptAssembler` | Template formatting, token budget truncation |
| `RetrievalService` | Mock vector search, chunk repository |
| `CompareRagAnswersUseCase` | Mock all dependencies, verify orchestration |

### 7.2 Integration Tests

| Scope | Setup | Assertions |
|-------|-------|-----------|
| Retrieval | EP19 index + fixtures | Top-k results returned, scores descending |
| LLM | Mock LLM API | Prompt correctly formatted, response parsed |
| End-to-end | Full pipeline with test index | ComparisonResult contains both answers |

---

## 8. Metrics & Observability

### 8.1 Prometheus Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `rag_retrieval_duration_seconds` | Histogram | Time to retrieve chunks |
| `rag_llm_duration_seconds` | Histogram | Time for LLM generation (by mode) |
| `rag_chunks_retrieved_total` | Counter | Total chunks retrieved |
| `rag_compare_duration_seconds` | Histogram | Total comparison duration |
| `rag_comparison_errors_total` | Counter | Errors during comparison |

### 8.2 Structured Logging

Log events:
- `rag_comparison_started`: Query ID, question
- `rag_retrieval_completed`: Chunk count, latency
- `rag_llm_completed`: Mode (with_rag/without_rag), latency, tokens
- `rag_comparison_completed`: Total latency, result ID
- `rag_error`: Error type, query ID, stack trace

---

## 9. Configuration Management

### 9.1 Environment Variables

```bash
# Retrieval settings
RAG_TOP_K=5
RAG_SCORE_THRESHOLD=0.3
RAG_MAX_CONTEXT_TOKENS=3000

# LLM settings (reuse existing)
LLM_URL=http://127.0.0.1:8000
LLM_MODEL=qwen
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1000

# Index settings (from EP19)
EMBEDDING_API_URL=http://127.0.0.1:8000
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_MONGO_DATABASE=document_index
EMBEDDING_MONGO_CHUNKS_COLLECTION=chunks
EMBEDDING_REDIS_INDEX_NAME=embedding:index:v1
```

### 9.2 Config Loading

Use `pydantic-settings` to extend existing `Settings` class:

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # RAG retrieval settings
    rag_top_k: int = Field(default=5, description="Number of chunks to retrieve")
    rag_score_threshold: float = Field(default=0.3, description="Min similarity")
    rag_max_context_tokens: int = Field(default=3000, description="Token budget")
```

---

## 10. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Redis RediSearch unavailable | High | Use FAISS fallback (file store) |
| LLM API timeout | Medium | Retry with exponential backoff |
| Chunk metadata missing | Low | Log warning, skip chunk |
| Token budget overflow | Medium | Truncate chunks, log warning |
| Empty retrieval results | Low | Fallback to non-RAG mode automatically |

---

## 11. References

- `docs/specs/epic_19/epic_19.md` — EP19 index architecture
- `docs/specs/epic_20/retrieval_config.yaml` — Retrieval parameters
- `docs/specs/epic_20/prompt_templates.md` — Prompt templates
- `src/application/embedding_index/use_case.py` — Indexing use case
- `src/infrastructure/vector_store/` — Vector store implementations

---

## Next Steps → Prototype Implementation

1. Create `scripts/rag/compare_once.py` (minimal prototype)
2. Implement vector search adapter (Redis + FAISS fallback)
3. Extend `MongoChunkRepository` with `get_by_id()` method
4. Implement `PromptAssembler` service
5. Test prototype with sample query
6. Validate output format matches spec

**Exit Criteria**:
- Prototype returns both answers for a single query
- Retrieval works (Redis or FAISS fallback)
- Prompts formatted correctly
- Output matches JSON schema

---

**Design Review Status**: ✅ Approved for prototyping
**Last Updated**: 2025-11-11
**Reviewers**: Tech Lead (self)
