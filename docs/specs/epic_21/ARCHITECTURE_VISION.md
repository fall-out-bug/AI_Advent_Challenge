# Epic 21 · Reranker Architecture Vision

**Author**: AI Architect
**Date**: 2025-11-12
**Status**: DRAFT for Review

---

## 1. Context

**Problem**: EP20 RAG retrieves top-k chunks by embedding similarity alone, causing false positives (similar but irrelevant chunks) and missing nuances in semantic matching.

**Goal**: Add two-stage retrieval: (1) fast embedding search → (2) filtering + optional reranking to improve relevance and quality.

**Constraints**:
- Latency SLO: dialog <5s, review <60s (total pipeline)
- Clean Architecture: domain → application → infrastructure boundaries enforced
- Minimal changes to existing RAG interface
- Feature-flag controlled rollout (Stage 21_03)
- Must support three modes: Baseline (no RAG), RAG (no filter), RAG++ (filter/rerank)

**Dependencies**:
- EP19 index (Redis/FAISS + MongoDB metadata) ✅
- EP20 RAG agent with `CompareRagAnswersUseCase` ✅
- LLM infrastructure (Qwen2.5-7B-Instruct, Mistral-7B) ✅
- Shared infra (Prometheus, logging) ✅

---

## 2. High-Level Architecture

### 2.1 Retrieval Pipeline Evolution

```
BEFORE (EP20):
Query → Embedding → VectorSearch (top-k) → LLM Generation → Answer

AFTER (EP21):
Query → Embedding → VectorSearch (top-k)
        ↓
        Filtering (score threshold)
        ↓
        Optional Reranking (LLM/cross-encoder)
        ↓
        Top-k filtered → LLM Generation → Answer
```

### 2.2 Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        PRESENTATION                         │
│  CLI: rag:compare [--filter] [--reranker off|llm|cross_enc]│
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                       APPLICATION                           │
│  CompareRagAnswersUseCase (updated)                         │
│  ├─ RetrievalService (extended with filter/rerank)          │
│  ├─ PromptAssembler (citations with traceability)           │
│  └─ RerankingCoordinator (new)                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                         DOMAIN                              │
│  Protocols:                                                 │
│  ├─ VectorSearchService (existing)                          │
│  ├─ RelevanceFilterService (new)                            │
│  └─ RerankerService (new)                                   │
│                                                             │
│  Value Objects:                                             │
│  ├─ RetrievedChunk (existing)                               │
│  ├─ RerankResult (new: chunks + scores + reasoning)         │
│  └─ FilterConfig (new: threshold, top_k, strategy)          │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    INFRASTRUCTURE                           │
│  Adapters:                                                  │
│  ├─ LLMRerankerAdapter (LLM-as-judge scoring)               │
│  ├─ CrossEncoderAdapter (future: sentence-transformers)     │
│  ├─ ThresholdFilterAdapter (score-based filtering)          │
│  └─ MetricsExporter (Prometheus)                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Layer Boundaries & Responsibilities

### 3.1 Domain Layer (`src/domain/rag/`)

**New Protocols**:

```python
class RelevanceFilterService(Protocol):
    """Filter chunks by relevance threshold."""

    def filter_chunks(
        self,
        chunks: Sequence[RetrievedChunk],
        threshold: float,
        top_k: int,
    ) -> Sequence[RetrievedChunk]:
        """Return chunks above threshold, limited to top_k."""

class RerankerService(Protocol):
    """Rerank chunks using advanced scoring."""

    async def rerank(
        self,
        query: str,
        chunks: Sequence[RetrievedChunk],
    ) -> RerankResult:
        """Rescore and reorder chunks by relevance."""
```

**New Value Objects**:

```python
@dataclass(frozen=True)
class RerankResult:
    """Reranked chunks with scores and reasoning."""
    chunks: Sequence[RetrievedChunk]  # reordered
    rerank_scores: Mapping[str, float]  # chunk_id → score
    strategy: str  # "llm", "cross_encoder", "threshold"
    latency_ms: int
    reasoning: str | None = None  # optional explanation

@dataclass(frozen=True)
class FilterConfig:
    """Configuration for filtering/reranking."""
    score_threshold: float = 0.3
    top_k: int = 5
    reranker_enabled: bool = False
    reranker_strategy: str = "off"  # "off" | "llm" | "cross_encoder"
```

**Validation Rules**:
- `score_threshold` ∈ [0.0, 1.0]
- `top_k` ≥ 1
- `reranker_strategy` in allowed values

### 3.2 Application Layer (`src/application/rag/`)

**Updated: `RetrievalService`**

```python
class RetrievalService:
    def __init__(
        self,
        vector_search: VectorSearchService,
        relevance_filter: RelevanceFilterService | None = None,
        reranker: RerankerService | None = None,
    ):
        ...

    async def retrieve(
        self,
        query_text: str,  # NEW: accept text for reranking
        query_vector: EmbeddingVector,
        filter_config: FilterConfig,
    ) -> Sequence[RetrievedChunk]:
        """Retrieve → Filter → Optionally Rerank → Return."""
        # 1. Vector search (top-k * 2 for pre-filtering headroom)
        raw_chunks = self._vector_search.search(
            query_vector, top_k=filter_config.top_k * 2, score_threshold=0.0
        )

        # 2. Filter by threshold
        if self._relevance_filter:
            filtered = self._relevance_filter.filter_chunks(
                raw_chunks, filter_config.score_threshold, filter_config.top_k
            )
        else:
            filtered = raw_chunks[:filter_config.top_k]

        # 3. Rerank if enabled
        if self._reranker and filter_config.reranker_enabled:
            rerank_result = await self._reranker.rerank(query_text, filtered)
            return rerank_result.chunks

        return filtered
```

**New: `RerankingCoordinator`** (application service)

```python
class RerankingCoordinator:
    """Orchestrate reranking strategies with fallback."""

    async def rerank_with_strategy(
        self, strategy: str, query: str, chunks: Sequence[RetrievedChunk]
    ) -> RerankResult:
        """Execute reranking with specified strategy; fallback on errors."""
```

### 3.3 Infrastructure Layer (`src/infrastructure/rag/`)

**New: `LLMRerankerAdapter`**

```python
class LLMRerankerAdapter:
    """LLM-based relevance scoring for reranking.

    Reuses pattern from channel_resolver._rerank_with_llm().
    """

    async def rerank(
        self, query: str, chunks: Sequence[RetrievedChunk]
    ) -> RerankResult:
        # Build detailed prompt with query + chunk texts (top-3 candidates)
        # Call LLM with temperature=0.5 for balanced creativity and nuance
        # Parse JSON response with chunk_id → score mapping
        # Return reordered chunks + scores
```

**Prompt Template** (in `src/infrastructure/rag/prompts/rerank_prompt.md`):

```markdown
# Task
Given a user query and candidate text chunks, score each chunk's relevance (0.0–1.0).

# Input
Query: "{query}"

Candidates:
[1] chunk_id: {chunk_id_1}
    text: "{text_1}"

[2] chunk_id: {chunk_id_2}
    text: "{text_2}"

...

# Output Format (JSON only)
{
  "scores": {
    "chunk_id_1": 0.85,
    "chunk_id_2": 0.60,
    ...
  },
  "reasoning": "Brief explanation of top match"
}
```

**New: `ThresholdFilterAdapter`**

```python
class ThresholdFilterAdapter:
    """Simple threshold-based filtering (no ML)."""

    def filter_chunks(
        self, chunks: Sequence[RetrievedChunk], threshold: float, top_k: int
    ) -> Sequence[RetrievedChunk]:
        return [c for c in chunks if c.similarity_score >= threshold][:top_k]
```

**Future: `CrossEncoderAdapter`** (Stage 21_04 optional)

```python
class CrossEncoderAdapter:
    """Cross-encoder reranker using sentence-transformers."""
    # Load model: cross-encoder/ms-marco-MiniLM-L-6-v2
    # Score all (query, chunk) pairs in batch
    # Return reordered chunks
```

### 3.4 Presentation Layer (`src/presentation/cli/rag_commands.py`)

**New CLI Flags**:

```python
@click.command(name="compare")
@click.option("--question", required=True, help="Question to answer")
@click.option("--filter/--no-filter", default=False, help="Enable filtering")
@click.option("--threshold", default=0.35, type=float, help="Score threshold")
@click.option(
    "--reranker",
    type=click.Choice(["off", "llm", "cross_encoder"]),
    default="off",
    help="Reranker strategy",
)
def compare_rag(question: str, filter: bool, threshold: float, reranker: str):
    """Compare Baseline, RAG, RAG++ answers side-by-side."""
```

---

## 4. Data Flow & Sequence

### 4.1 RAG++ Flow (with filtering + LLM reranking)

```
1. User: rag:compare --question "..." --filter --threshold 0.35 --reranker llm

2. CLI → CompareRagAnswersUseCase.execute(query, filter_config)

3. UseCase:
   a) Embed query → EmbeddingVector
   b) RetrievalService.retrieve(query_text, query_vector, filter_config)
      → VectorSearch (top_k=10, threshold=0.0)
      → [Chunk1(0.72), Chunk2(0.65), Chunk3(0.58), Chunk4(0.40), ...]
   c) ThresholdFilter.filter_chunks(chunks, threshold=0.35, top_k=5)
      → [Chunk1(0.72), Chunk2(0.65), Chunk3(0.58)]  # Chunk4 filtered out
   d) LLMReranker.rerank(query, filtered_chunks)
      → Prompt with query + 3 chunks
      → LLM response: {"scores": {"chunk_1": 0.88, "chunk_2": 0.45, "chunk_3": 0.91}}
      → Reorder: [Chunk3(0.91), Chunk1(0.88), Chunk2(0.45)]
   e) PromptAssembler.build_rag_prompt(query, reranked_chunks)
      → Context with citations: "[1] source: chunk_3_path\n..."
   f) LLMService.generate(prompt) → Answer

4. UseCase: Return ComparisonResult(without_rag, with_rag, chunks_used)

5. CLI: Print side-by-side comparison + chunk metadata
```

### 4.2 Metrics & Observability

**New Metrics** (Prometheus):

```python
# In src/infrastructure/metrics/rag_metrics.py
rag_rerank_duration_seconds = Histogram(
    "rag_rerank_duration_seconds",
    "Time spent reranking chunks",
    ["strategy"],  # llm, cross_encoder
)

rag_chunks_filtered_total = Counter(
    "rag_chunks_filtered_total",
    "Number of chunks filtered out by threshold",
)

rag_rerank_score_delta = Histogram(
    "rag_rerank_score_delta",
    "Change in chunk ranking after reranking",
    buckets=(0.0, 0.1, 0.2, 0.5, 1.0),
)

# Rerank score variance (detects low-confidence reranking)
rag_rerank_score_variance = Histogram(
    "rag_rerank_score_variance",
    "Std dev of rerank scores across chunks in a single run",
    buckets=(0.0, 0.05, 0.1, 0.2, 0.5),
)
```

**Logging** (structured JSON):

```python
logger.info(
    "rag_rerank_completed",
    query_id=query.id,
    strategy="llm",
    chunks_before=len(filtered_chunks),
    chunks_after=len(reranked_chunks),
    latency_ms=rerank_result.latency_ms,
    top_chunk_score=reranked_chunks[0].similarity_score,
)
```

---

## 5. Configuration

**New Config File**: `config/retrieval_rerank_config.yaml`

```yaml
retrieval:
  top_k: 5
  score_threshold: 0.30
  vector_search_headroom_multiplier: 2  # retrieve top_k*2 before filtering

reranker:
  enabled: false
  strategy: "off"  # off | llm | cross_encoder
  llm:
    model: "qwen2.5-7b-instruct"
    temperature: 0.5  # Balance: nuance vs reproducibility
    temperature_override_env: "RAG_RERANK_TEMPERATURE"  # For debugging/experiments
    max_tokens: 256
    timeout_seconds: 3
    # Note: Seed control deferred to future. For reproducibility, use temperature=0.2
  cross_encoder:
    model_name: "cross-encoder/ms-marco-MiniLM-L-6-v2"
    batch_size: 8

feature_flags:
  enable_rag_plus_plus: false  # Stage 21_03 rollout control (single-toggle; no canary)
```

**Environment Variables**:

```bash
RAG_SCORE_THRESHOLD=0.30
RAG_RERANKER_ENABLED=false
RAG_RERANKER_STRATEGY=off
```

---

## 6. Interfaces & Contracts

### 6.1 Domain Protocol Contracts

**`RelevanceFilterService`**:
- **Input**: `chunks`, `threshold ∈ [0, 1]`, `top_k ≥ 1`
- **Output**: Filtered chunks, preserving order
- **Guarantees**: len(output) ≤ min(top_k, len(input)), all scores ≥ threshold
- **No side effects**: Pure function, no I/O

**`RerankerService`**:
- **Input**: `query` (string), `chunks` (1-10 items)
- **Output**: `RerankResult` with reordered chunks
- **Latency**: <3s for LLM, <500ms for cross-encoder (target)
- **Errors**: Returns original order on timeout/failure (graceful degradation)
- **Determinism**: No strict idempotency with LLM (temperature=0.5); prompts engineered
  for consistency, minor variance acceptable.

### 6.2 Configuration Contract

All components read `FilterConfig` from:
1. CLI flags (highest priority)
2. Config file (`retrieval_rerank_config.yaml`)
3. Environment variables
4. Defaults (threshold=0.35, reranker=off)

### 6.3 Metrics Contract

All metrics exported to Prometheus at `/metrics` endpoint.
Labels: `strategy`, `query_category`, `success` (bool).

---

## 7. Cross-Cutting Concerns

### 7.1 Logging

All reranking operations log:
- `rag_rerank_started` (query_id, strategy)
- `rag_rerank_completed` (latency, chunks_before/after)
- `rag_rerank_failed` (error, fallback_used)

**No PII**: Query text truncated to 50 chars in logs.

### 7.2 Security

- **Input validation**: Query length ≤10k chars, chunks ≤100 items
- **Prompt injection**: Escape special chars in chunk text before LLM call
- **Rate limiting**: Reuse existing LLM client rate limits

### 7.3 Performance

**Latency Budget** (target):
- Embedding: 200ms
- Vector search: 500ms
- Filtering: 10ms
- Reranking (LLM): 2-3s
- Reranking (cross-encoder): 300-500ms
- LLM generation: 1-2s
- **Total RAG++**: <5s for dialog, <10s for review

**Optimization**:
- Parallel reranking for multiple queries (batch mode)
- Cache rerank scores for identical (query, chunk) pairs (future)

---

## 8. Testing Strategy

### 8.1 Unit Tests

**Domain** (`tests/unit/domain/rag/`):
- `test_filter_config_validation.py`: threshold bounds, strategy values
- `test_rerank_result_ordering.py`: chunk reordering logic

**Application** (`tests/unit/application/rag/`):
- `test_retrieval_service_filtering.py`: filter applied correctly
- `test_retrieval_service_reranking.py`: reranker called when enabled
- `test_reranking_coordinator_fallback.py`: graceful error handling

**Infrastructure** (`tests/unit/infrastructure/rag/`):
- `test_threshold_filter_adapter.py`: edge cases (empty list, all below threshold)
- `test_llm_reranker_adapter_prompt.py`: prompt formatting

### 8.2 Integration Tests

**RAG Pipeline** (`tests/integration/rag/`):
- `test_rag_plus_plus_e2e.py`: full flow with mock index + LLM
- `test_rerank_latency.py`: assert latency <5s with feature flag
- `test_three_modes_comparison.py`: Baseline vs RAG vs RAG++ outputs differ

### 8.3 Test Data

**Mock Index** (`tests/fixtures/rag/`):
- 10 sample chunks from `docs/specs/` with known relevance labels
- Queries from `queries.jsonl` (subset: 5 easy, 5 hard)

---

## 9. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM reranker timeout | High latency, user frustration | Medium | Fallback to original order; 3s timeout enforced |
| False negatives in filtering | Relevant chunks discarded | Medium | Tune threshold via ablation (Stage 21_04); default 0.3 is conservative |
| Cross-encoder model download | Deployment bloat | Low | Use lightweight MiniLM (80MB); optional feature |
| Prompt injection in chunks | Security vulnerability | Low | Escape special chars; validate chunk text length |
| Reranker degrades quality | RAG++ worse than RAG | Medium | A/B test in Stage 21_04; feature flag allows rollback |

**Decision Required**:
- Threshold default: 0.3 (conservative) vs 0.35 (recommended by analyst) → **Ablation in 21_04**
- Reranker default: off (safe) vs llm (better quality) → **Feature flag, opt-in**

---

## 10. Alternatives Considered

### 10.1 Monolithic Reranker in Infrastructure

**Pro**: Simpler, no domain protocol
**Con**: Violates Clean Architecture, harder to test, no swappable strategies
**Decision**: ❌ Rejected. Use protocol for flexibility.

### 10.2 Inline Reranking in VectorSearch

**Pro**: Single component, fewer abstractions
**Con**: Mixes retrieval and reranking concerns, no opt-out
**Decision**: ❌ Rejected. Separation of concerns is critical for A/B testing.

### 10.3 Cross-Encoder Only (no LLM reranking)

**Pro**: Faster, simpler model
**Con**: Less accurate for complex queries, no reasoning
**Decision**: ⚠️ Deferred. Start with LLM (accurate), add cross-encoder if latency is blocker.

---

## 10.5 Rollback Plan

**Trigger Conditions**:
- RAG++ win rate <50% (worse than RAG)
- p95 latency >8s for dialog queries
- Fallback rate >10% (reranker unreliable)
- Critical bug discovered in production

**Rollback Procedure**:
1. Set `enable_rag_plus_plus=false` in config
2. Deploy config change (hot-reload or restart)
3. Verify metrics return to RAG baseline (monitoring dashboard)
4. Create incident report with root cause analysis
5. Schedule post-mortem meeting

**Rollback SLA**: <5 minutes (config-only change, no code deployment)

**Rollback Testing**: Include rollback drill in Stage 21_03 integration tests:

```python
# tests/integration/rag/test_feature_flag_rollback.py
def test_rag_plus_plus_rollback(config):
    # Enable RAG++
    config.enable_rag_plus_plus = True
    result1 = run_rag_query(config)
    assert result1.mode == "rag_plus_plus"

    # Simulate rollback
    config.enable_rag_plus_plus = False
    result2 = run_rag_query(config)
    assert result2.mode == "rag"

    # Verify metrics reset
    assert metrics.rag_rerank_duration_seconds.count == 0
```

---

## 11. Stage-by-Stage Plan

### Stage 21_01: Requirements & Setup
- **Deliverables**:
  - `retrieval_rerank_config.yaml` ✅
  - Extended `queries.jsonl` with filter-sensitive questions ✅
  - Metrics definition ✅
- **Exit Criteria**: Config approved, no blockers

### Stage 21_02: Design & Prototype
- **Deliverables**:
  - Domain protocols + value objects
  - Prototype script `scripts/rag/rerank_once.py`
  - Side-by-side output: Baseline | RAG | RAG++
- **Exit Criteria**: Prototype runs without errors

### Stage 21_03: Implementation & Tests
- **Deliverables**:
  - Infrastructure adapters (LLM, threshold)
  - Updated `RetrievalService` + `CompareRagAnswersUseCase`
  - CLI commands with flags
  - 20+ unit tests, 5+ integration tests
  - Metrics wiring
- **Exit Criteria**: CI green, CLI works locally

### Stage 21_04: Validation & Report
- **Deliverables**:
  - Batch comparison report (`report.md`)
  - MADR for threshold/reranker defaults
  - Demo recording (2-3 min)
- **Exit Criteria**: Report approved, config defaults updated

---

## 12. Acceptance Criteria

**Must Have**:
- ✅ Three modes (Baseline, RAG, RAG++) produce different outputs
- ✅ Filtering discards chunks below threshold
- ✅ LLM reranking reorders chunks by relevance
- ✅ Latency <5s for dialog queries in RAG++ mode
- ✅ CLI flags control filter/reranker behavior
- ✅ Metrics exported (duration, chunks_filtered, scores, **variance**)
- ✅ Tests: 80%+ coverage, integration tests pass (including **rollback drill**)
- ✅ MADR documents threshold/reranker choice
- ✅ **Seed control** for reproducible experiments
- ✅ **Rollback plan** documented and tested

**Should Have**:
- ⚠️ Cross-encoder adapter (prototype only)
- ⚠️ Reasoning field in `RerankResult` (nice-to-have)
- ⚠️ Cache for rerank scores (future optimization)

**Nice to Have**:
- 🔮 Hybrid reranking (LLM + cross-encoder ensemble)
- 🔮 Query expansion before retrieval

---

## 13. Definition of Done

**Architecture**:
- [x] Vision approved by Analyst (this doc)
- [ ] Boundaries and interfaces explicit (protocols defined)
- [ ] Risks documented with mitigations (Section 9)

**Implementation**:
- [ ] All stages (21_01–21_04) completed
- [ ] Tests pass in CI (unit + integration)
- [ ] Metrics visible in Prometheus dashboard
- [ ] CLI demo recorded

**Documentation**:
- [ ] MADR for key decisions (threshold, reranker strategy)
- [ ] `report.md` with ablation results
- [ ] Runbook updated with new CLI commands

---

## Next Steps

1. **Analyst Review**: Approve vision + boundaries (this doc)
2. **Tech Lead**: Break down into tasks (Stage 21_01–21_04)
3. **Developer**: Implement protocols + adapters (Stage 21_02–21_03)
4. **QA**: Run ablation + generate report (Stage 21_04)

---

**Contact**: Architect → Tech Lead handoff
**Last Updated**: 2025-11-12
