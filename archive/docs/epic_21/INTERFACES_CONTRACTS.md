# Epic 21 · Reranker Interfaces & Contracts

**Author**: AI Architect
**Date**: 2025-11-12
**Status**: DRAFT

---

## 1. Overview

This document defines **explicit interfaces and contracts** for the Epic 21 reranking system. All components MUST adhere to these contracts to ensure correctness, testability, and maintainability.

---

## 2. Domain Layer Protocols

### 2.1 RelevanceFilterService

**Purpose**: Filter retrieved chunks by similarity threshold.

**Location**: `src/domain/rag/interfaces.py`

**Protocol Definition**:

```python
from typing import Protocol, Sequence
from src.domain.rag import RetrievedChunk

class RelevanceFilterService(Protocol):
    """Filter chunks by relevance threshold."""

    def filter_chunks(
        self,
        chunks: Sequence[RetrievedChunk],
        threshold: float,
        top_k: int,
    ) -> Sequence[RetrievedChunk]:
        """Return chunks above threshold, limited to top_k.

        Purpose:
            Remove irrelevant chunks based on similarity score cutoff.

        Args:
            chunks: Input chunks with similarity_score field (0.0-1.0).
            threshold: Minimum similarity score to keep (0.0-1.0).
            top_k: Maximum number of chunks to return (≥1).

        Returns:
            Filtered chunks, preserving original order, limited to top_k.

        Raises:
            ValueError: If threshold not in [0.0, 1.0] or top_k < 1.

        Guarantees:
            - len(output) ≤ min(top_k, len(input))
            - all(c.similarity_score ≥ threshold for c in output)
            - order preserved from input

        Example:
            >>> filter = ThresholdFilterAdapter()
            >>> chunks = [Chunk(score=0.8), Chunk(score=0.4), Chunk(score=0.6)]
            >>> result = filter.filter_chunks(chunks, threshold=0.5, top_k=2)
            >>> result  # [Chunk(0.8), Chunk(0.6)]
        """
```

**Contract**:

| Aspect | Requirement |
|--------|-------------|
| **Input Validation** | threshold ∈ [0.0, 1.0], top_k ≥ 1, chunks non-null |
| **Output Guarantee** | All output chunks have score ≥ threshold |
| **Order Preservation** | Output order matches input order (no reordering) |
| **Limit Enforcement** | len(output) ≤ top_k |
| **Performance** | O(n) time complexity, no I/O |
| **Side Effects** | None (pure function) |

**Error Handling**:
- `ValueError` for invalid threshold or top_k
- Empty list returned if no chunks pass threshold

---

### 2.2 RerankerService

**Purpose**: Rerank chunks using advanced scoring (LLM or cross-encoder).

**Location**: `src/domain/rag/interfaces.py`

**Protocol Definition**:

```python
from typing import Protocol
from src.domain.rag import RetrievedChunk, RerankResult

class RerankerService(Protocol):
    """Rerank chunks using advanced scoring."""

    async def rerank(
        self,
        query: str,
        chunks: Sequence[RetrievedChunk],
    ) -> RerankResult:
        """Rescore and reorder chunks by relevance.

        Purpose:
            Compute relevance scores for each chunk relative to query,
            then reorder chunks by descending score.

        Args:
            query: User query text (1-10k characters).
            chunks: Input chunks to rerank (1-100 items).

        Returns:
            RerankResult with reordered chunks and scores.

        Raises:
            ValueError: If query empty or chunks list invalid.
            RuntimeError: If reranker model unavailable (graceful fallback).

        Guarantees:
            - Output chunks are same objects as input (no copies)
            - Reordered by descending rerank_score
            - len(output) == len(input)
            - latency_ms field populated

        Graceful Degradation:
            On timeout/error, returns input chunks in original order with
            warning in reasoning field.

        Example:
            >>> reranker = LLMRerankerAdapter(llm_client)
            >>> result = await reranker.rerank(
            ...     query="What is MapReduce?",
            ...     chunks=[chunk1, chunk2, chunk3],
            ... )
            >>> result.chunks[0]  # highest scored chunk
        """
```

**Contract**:

| Aspect | Requirement |
|--------|-------------|
| **Input Validation** | query non-empty, len(query) ≤10k, 1 ≤ len(chunks) ≤100 |
| **Output Guarantee** | Chunks reordered by score (descending) |
| **Latency SLO** | <3s for LLM, <500ms for cross-encoder (target) |
| **Timeout Behavior** | Fallback to original order, no exception raised |
| **Determinism** | No strict idempotency with LLM (temperature=0.5); minor variance acceptable |
| **Concurrency** | Safe for parallel calls (thread-safe) |

**Error Handling**:
- `ValueError` for invalid inputs (fail fast)
- `RuntimeError` → graceful fallback to original order
- Timeout (3s) → fallback with warning in `reasoning`

---

## 3. Value Objects

### 3.1 FilterConfig

**Purpose**: Configuration for filtering and reranking.

**Location**: `src/domain/rag/value_objects.py`

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class FilterConfig:
    """Configuration for filtering/reranking.

    Attributes:
        score_threshold: Minimum similarity score (0.0-1.0).
        top_k: Maximum number of chunks to return (≥1).
        reranker_enabled: Whether to apply reranking.
        reranker_strategy: "off" | "llm" | "cross_encoder".
    """

    score_threshold: float = 0.35
    top_k: int = 5
    reranker_enabled: bool = False
    reranker_strategy: str = "off"

    def __post_init__(self) -> None:
        """Validate FilterConfig fields."""
        if not 0.0 <= self.score_threshold <= 1.0:
            raise ValueError(
                f"score_threshold must be [0.0, 1.0], got {self.score_threshold}"
            )
        if self.top_k < 1:
            raise ValueError(f"top_k must be ≥1, got {self.top_k}")
        if self.reranker_strategy not in ("off", "llm", "cross_encoder"):
            raise ValueError(
                f"reranker_strategy must be off|llm|cross_encoder, "
                f"got {self.reranker_strategy}"
            )
        if self.reranker_strategy != "off" and not self.reranker_enabled:
            raise ValueError(
                "reranker_strategy != 'off' requires reranker_enabled=True"
            )
```

**Contract**:

| Field | Type | Constraints | Default |
|-------|------|-------------|---------|
| `score_threshold` | float | [0.0, 1.0] | 0.35 |
| `top_k` | int | ≥1 | 5 |
| `reranker_enabled` | bool | - | False |
| `reranker_strategy` | str | "off" \| "llm" \| "cross_encoder" | "off" |

**Validation Rules**:
1. If `reranker_strategy != "off"`, then `reranker_enabled` MUST be `True`
2. `score_threshold` MUST be ∈ [0.0, 1.0]
3. `top_k` MUST be ≥1

---

### 3.2 RerankResult

**Purpose**: Result of reranking operation with metadata.

**Location**: `src/domain/rag/value_objects.py`

```python
from dataclasses import dataclass
from typing import Mapping, Sequence
from src.domain.rag import RetrievedChunk

@dataclass(frozen=True)
class RerankResult:
    """Reranked chunks with scores and reasoning.

    Attributes:
        chunks: Reordered chunks (descending by rerank_score).
        rerank_scores: Mapping of chunk_id → rerank_score (0.0-1.0).
        strategy: Reranker strategy used ("llm", "cross_encoder").
        latency_ms: Time spent reranking (milliseconds).
        reasoning: Optional explanation of ranking (LLM only).
    """

    chunks: Sequence[RetrievedChunk]
    rerank_scores: Mapping[str, float]
    strategy: str
    latency_ms: int
    reasoning: str | None = None

    def __post_init__(self) -> None:
        """Validate RerankResult fields."""
        if not self.chunks:
            raise ValueError("chunks cannot be empty")
        if len(self.rerank_scores) != len(self.chunks):
            raise ValueError(
                f"rerank_scores count ({len(self.rerank_scores)}) "
                f"must match chunks count ({len(self.chunks)})"
            )
        if self.strategy not in ("llm", "cross_encoder", "threshold"):
            raise ValueError(
                f"strategy must be llm|cross_encoder|threshold, got {self.strategy}"
            )
        if self.latency_ms < 0:
            raise ValueError(f"latency_ms must be ≥0, got {self.latency_ms}")

        # Verify all chunks have corresponding scores
        for chunk in self.chunks:
            if chunk.chunk_id not in self.rerank_scores:
                raise ValueError(
                    f"Missing rerank_score for chunk_id={chunk.chunk_id}"
                )
```

**Contract**:

| Field | Type | Constraints |
|-------|------|-------------|
| `chunks` | Sequence[RetrievedChunk] | Non-empty, reordered by score |
| `rerank_scores` | Mapping[str, float] | Keys = all chunk_ids, values ∈ [0.0, 1.0] |
| `strategy` | str | "llm" \| "cross_encoder" \| "threshold" |
| `latency_ms` | int | ≥0 |
| `reasoning` | str \| None | Optional (LLM only) |

**Validation Rules**:
1. `len(rerank_scores) == len(chunks)`
2. All `chunk.chunk_id` present in `rerank_scores.keys()`
3. Chunks ordered by `rerank_scores[chunk.chunk_id]` (descending)

---

## 4. Application Layer Interfaces

### 4.1 RetrievalService (Extended)

**Purpose**: Orchestrate retrieval, filtering, and reranking.

**Location**: `src/application/rag/retrieval_service.py`

**Method Signature**:

```python
class RetrievalService:
    async def retrieve(
        self,
        query_text: str,
        query_vector: EmbeddingVector,
        filter_config: FilterConfig,
    ) -> Sequence[RetrievedChunk]:
        """Retrieve, filter, and optionally rerank chunks.

        Purpose:
            Coordinate full retrieval pipeline: vector search → filter → rerank.

        Args:
            query_text: User query (needed for reranking).
            query_vector: Embedding of query (for vector search).
            filter_config: Filtering/reranking configuration.

        Returns:
            Filtered and optionally reranked chunks.

        Raises:
            RuntimeError: If vector search fails.

        Workflow:
            1. VectorSearch(query_vector, top_k * 2) → raw_chunks
            2. Filter(raw_chunks, threshold) → filtered_chunks
            3. If reranker_enabled: Rerank(filtered_chunks) → final_chunks
            4. Return final_chunks[:top_k]
        """
```

**Contract**:

| Aspect | Requirement |
|--------|-------------|
| **Retrieval Headroom** | Fetch `top_k * 2` from vector search for filtering |
| **Filtering Applied** | If `filter_config.score_threshold > 0`, filter chunks |
| **Reranking Applied** | If `filter_config.reranker_enabled`, call reranker |
| **Output Limit** | Return at most `filter_config.top_k` chunks |
| **Graceful Degradation** | On reranker failure, use filtered (non-reranked) chunks |

---

## 5. Infrastructure Adapters

### 5.1 ThresholdFilterAdapter

**Purpose**: Implement RelevanceFilterService with simple threshold check.

**Location**: `src/infrastructure/rag/threshold_filter_adapter.py`

**Implementation Contract**:

```python
class ThresholdFilterAdapter:
    """Threshold-based filtering (no ML inference)."""

    def filter_chunks(
        self,
        chunks: Sequence[RetrievedChunk],
        threshold: float,
        top_k: int,
    ) -> Sequence[RetrievedChunk]:
        """Filter by similarity_score ≥ threshold."""
        # Input validation
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Invalid threshold: {threshold}")
        if top_k < 1:
            raise ValueError(f"Invalid top_k: {top_k}")

        # Filter and limit
        filtered = [c for c in chunks if c.similarity_score >= threshold]
        return filtered[:top_k]
```

**Performance Requirements**:
- Time complexity: O(n)
- No I/O operations
- No external dependencies

---

### 5.2 LLMRerankerAdapter

**Purpose**: Implement RerankerService using LLM for scoring.

**Location**: `src/infrastructure/rag/llm_reranker_adapter.py`

**Implementation Contract**:

```python
class LLMRerankerAdapter:
    """LLM-based reranking with prompt-based scoring."""

    def __init__(
        self,
        llm_client: LLMClient,
        timeout_seconds: int = 3,
        temperature: float = 0.5,
        max_tokens: int = 256,
    ):
        """Initialize with LLM client and config."""
        self._llm_client = llm_client
        self._timeout_seconds = timeout_seconds
        self._temperature = temperature
        self._max_tokens = max_tokens

    async def rerank(
        self,
        query: str,
        chunks: Sequence[RetrievedChunk],
    ) -> RerankResult:
        """Rerank using LLM scoring.

        Workflow:
            1. Build a detailed prompt with query + chunk texts (top-3 only), include
               explicit evaluation criteria and tie-breakers
            2. Call LLM with temperature=0.5, timeout=3s
            3. Parse JSON response: {"scores": {"chunk_id": float}}
            4. Reorder chunks by scores (descending)
            5. Return RerankResult with latency

        Graceful Degradation:
            On timeout/parse error, return original order with warning.
        """
```

**Prompt Template** (JSON-structured):

```json
{
  "role": "system",
  "content": "You are a relevance scorer. Given a query and text chunks, score each chunk's relevance (0.0-1.0)."
},
{
  "role": "user",
  "content": "Query: {query}\n\nChunks:\n[1] {chunk_id_1}: {text_1}\n[2] {chunk_id_2}: {text_2}\n...\n\nOutput JSON only: {\"scores\": {\"chunk_id\": float}, \"reasoning\": str}"
}
```

**Performance Requirements**:
- Latency target: <3s (p95)
- Timeout: 3s hard limit
- Max chunks: 10 (truncate if more)
- Fallback: Original order on error

---

## 6. Configuration Interface

### 6.1 Config File Structure

**File**: `config/retrieval_rerank_config.yaml`

```yaml
retrieval:
  top_k: 5                          # int, ≥1
  score_threshold: 0.35             # float, [0.0, 1.0]
  vector_search_headroom_multiplier: 2  # int, ≥1

reranker:
  enabled: false                    # bool
  strategy: "off"                   # "off" | "llm" | "cross_encoder"
  llm:
    model: "qwen2.5-7b-instruct"    # str, model name
    temperature: 0.2                # float, [0.0, 1.0]
    max_tokens: 256                 # int, ≥1
    timeout_seconds: 3              # int, ≥1
  cross_encoder:
    model_name: "cross-encoder/ms-marco-MiniLM-L-6-v2"
    batch_size: 8                   # int, ≥1

feature_flags:
  enable_rag_plus_plus: false       # bool
```

**Validation Rules**:
1. All numeric fields MUST be within specified ranges
2. `reranker.strategy` MUST match `reranker.enabled` (strategy != "off" ⇒ enabled = true)
3. Model names MUST be non-empty strings

---

## 7. Metrics Interface

### 7.1 Prometheus Metrics

**Location**: `src/infrastructure/metrics/rag_metrics.py`

**Metrics Definitions**:

```python
from prometheus_client import Counter, Histogram

# Reranking duration
rag_rerank_duration_seconds = Histogram(
    "rag_rerank_duration_seconds",
    "Time spent reranking chunks",
    ["strategy"],  # llm, cross_encoder
    buckets=(0.1, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0),
)

# Chunks filtered
rag_chunks_filtered_total = Counter(
    "rag_chunks_filtered_total",
    "Number of chunks filtered out by threshold",
    ["category"],  # below_threshold, above_top_k
)

# Rerank score deltas
rag_rerank_score_delta = Histogram(
    "rag_rerank_score_delta",
    "Change in top chunk score after reranking",
    buckets=(-1.0, -0.5, -0.1, 0.0, 0.1, 0.5, 1.0),
)

# Reranker fallback count
rag_reranker_fallback_total = Counter(
    "rag_reranker_fallback_total",
    "Number of times reranker fell back to original order",
    ["reason"],  # timeout, parse_error, exception
)
```

**Usage Contract**:
- All metrics MUST be exported at `/metrics` endpoint
- Labels MUST be lowercase, underscore-separated
- Counters MUST be monotonically increasing
- Histograms MUST use specified buckets

---

## 8. CLI Interface

### 8.1 Command Signatures

**Command**: `rag:compare`

```bash
rag compare \
  --question "What is MapReduce?" \
  [--filter / --no-filter] \
  [--threshold FLOAT] \
  [--reranker {off,llm,cross_encoder}]
```

**Arguments**:

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--question` | str | Required | Question to answer |
| `--filter` | bool | False | Enable threshold filtering |
| `--threshold` | float | 0.35 | Similarity score threshold |
| `--reranker` | choice | "off" | Reranker strategy |

**Output Format**:

```
=== RAG Comparison Results ===

MODE: Baseline (No RAG)
Answer: [generated text]
Latency: 1234ms

MODE: RAG (No Filter)
Answer: [generated text]
Chunks: 5 retrieved
Latency: 2345ms

MODE: RAG++ (Filter + Rerank)
Answer: [generated text]
Chunks: 3 filtered, 3 reranked
Top chunk: docs/architecture.md (score: 0.88)
Latency: 4567ms
```

---

## 9. Testing Contracts

### 9.1 Unit Test Requirements

**Domain Layer**:
- `test_filter_config_validation()`: All validation rules covered
- `test_rerank_result_ordering()`: Chunks ordered correctly

**Application Layer**:
- `test_retrieval_service_filtering()`: Filter applied when enabled
- `test_retrieval_service_reranking()`: Reranker called when enabled
- `test_reranking_fallback()`: Graceful degradation on errors

**Infrastructure Layer**:
- `test_threshold_filter_edge_cases()`: Empty list, all below threshold
- `test_llm_reranker_timeout()`: Fallback on timeout
- `test_llm_reranker_prompt_format()`: Prompt matches template

### 9.2 Integration Test Requirements

**End-to-End**:
- `test_rag_plus_plus_pipeline()`: Full flow with mock index + LLM
- `test_three_modes_comparison()`: Baseline ≠ RAG ≠ RAG++
- `test_latency_slo()`: p95 latency <5s with feature flag

---

## 10. Backward Compatibility

### 10.1 Existing Code

**Guarantee**: All changes MUST be backward compatible with EP20 RAG.

**Compatibility Matrix**:

| Component | Change | Backward Compatible? |
|-----------|--------|---------------------|
| `RetrievalService.retrieve()` | Added `query_text`, `filter_config` params | ❌ Breaking (signature change) |
| `CompareRagAnswersUseCase` | Uses new `retrieve()` signature | ✅ Internal change only |
| `RetrievedChunk` | No changes | ✅ Fully compatible |
| `VectorSearchService` | No changes | ✅ Fully compatible |

**Migration Path**:
1. Old code uses `retrieve(query_vector, top_k, score_threshold)`
2. New code uses `retrieve(query_text, query_vector, filter_config)`
3. Provide adapter wrapper for old signature (deprecate in Stage 21_04)

---

## 11. Acceptance Checklist

- [ ] All protocols defined with explicit contracts
- [ ] Value objects have validation rules
- [ ] Application services specify workflow steps
- [ ] Infrastructure adapters implement protocols
- [ ] Configuration schema documented
- [ ] Metrics definitions exported
- [ ] CLI interface specified
- [ ] Testing contracts defined
- [ ] Backward compatibility addressed

---

## Next Steps

1. **Tech Lead**: Review contracts for completeness
2. **Developer**: Implement protocols and adapters per contracts
3. **QA**: Write tests based on testing contracts

---

**Last Updated**: 2025-11-12
