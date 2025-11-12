# ADR 0001: Reranker Architecture and Integration Strategy

**Status**: Proposed
**Date**: 2025-11-12
**Context**: Epic 21 Reranking & Relevance Filtering (RAG++)
**Deciders**: Architect, Analyst, Tech Lead

---

## Context

EP20 RAG retrieves chunks using only embedding similarity (cosine distance), which causes:
1. **False positives**: Chunks with similar words but wrong semantic intent
2. **No nuance**: Cannot distinguish between "defining X" vs "using X"
3. **Ranking noise**: Small embedding score differences (0.65 vs 0.63) are unreliable

We need a second-stage reranking mechanism to improve relevance precision while staying within latency SLO (<5s dialog, <60s review).

---

## Decision

We will implement a **two-stage retrieval pipeline** with:

1. **Filtering Stage**: Threshold-based filtering (simple, fast, deterministic)
2. **Reranking Stage**: Optional LLM-based reranking (accurate, interpretable, slower)

Both stages are:
- **Opt-in** via feature flags and CLI arguments
- **Swappable** through domain protocols (Clean Architecture)
- **Observable** via Prometheus metrics

### Key Architectural Choices

#### 1. Domain Protocol for Reranker

**Decision**: Define `RerankerService` protocol in `src/domain/rag/interfaces.py`

**Rationale**:
- Keeps domain layer pure (no infra dependencies)
- Allows multiple implementations (LLM, cross-encoder, hybrid)
- Simplifies testing (mock protocol in unit tests)

**Trade-offs**:
- ✅ Flexibility: Easy to swap strategies
- ✅ Testability: Mock reranker in tests
- ❌ Indirection: One extra abstraction layer

**Alternatives Rejected**:
- ❌ Monolithic reranker in infrastructure: Violates Clean Architecture
- ❌ Inline in VectorSearch: Mixes concerns, no opt-out

#### 2. LLM-Based Reranking (Primary Strategy)

**Decision**: Use `Qwen2.5-7B-Instruct` with structured prompt for chunk scoring

**Rationale**:
- **Accuracy**: LLMs understand semantic intent better than embedding similarity
- **Interpretability**: Can provide reasoning ("Chunk X matches because...")
- **Available**: Already deployed in infra, no new model downloads
- **Proven**: Pattern exists in `channel_resolver._rerank_with_llm()`

**Trade-offs**:
- ✅ High quality: Reduces false positives significantly
- ✅ Reasoning: Can explain why chunk was ranked higher
- ❌ Latency: 2-3s per rerank call (vs 50ms for embeddings)
- ❌ Cost: LLM inference is more expensive than vector search

**Alternatives Considered**:
- **Cross-encoder** (e.g., `ms-marco-MiniLM-L-6-v2`):
  - ✅ Faster: 300-500ms for 5 chunks
  - ❌ Less accurate for complex queries
  - ❌ No reasoning/explanation
  - 🔮 **Decision**: Add in Stage 21_04 if LLM latency is blocker

- **Hybrid (LLM + cross-encoder)**:
  - ✅ Best of both worlds
  - ❌ Complex orchestration
  - 🔮 **Decision**: Future optimization, not MVP

#### 3. Threshold-Based Filtering (Always On)

**Decision**: Filter chunks below `score_threshold` before reranking

**Rationale**:
- **Fast**: O(n) filtering, no ML inference
- **Deterministic**: Same threshold = same output
- **Reduces noise**: Eliminates obviously irrelevant chunks before expensive reranking

**Default Threshold**: `0.35`
- Based on EP20 experiments (to be validated in Stage 21_04 ablation)
- Conservative: Keeps false positives to avoid discarding relevant chunks

**Trade-offs**:
- ✅ Simple: No model loading, instant filtering
- ✅ Predictable: Easy to tune and explain
- ❌ Rigid: Cannot learn from data (vs learned threshold)

#### 4. Integration Point: RetrievalService (Application Layer)

**Decision**: Extend `RetrievalService` to orchestrate filter + rerank

**Rationale**:
- **Single Responsibility**: RetrievalService owns retrieval workflow
- **Backward Compatible**: Inject `None` for filter/reranker = original behavior
- **Testable**: Mock dependencies in unit tests

**Alternatives Rejected**:
- ❌ New `RagPlusPlusService`: Duplicate logic, harder to maintain
- ❌ Extend `VectorSearchService`: Wrong layer (infra, not application)

---

## Consequences

### Positive

1. **Quality Improvement**: LLM reranking reduces false positives by 20-40% (estimated)
2. **Flexibility**: Protocol-based design allows strategy swapping without code changes
3. **Observability**: Metrics show rerank latency, score deltas, filter counts
4. **Graceful Degradation**: Reranker timeout → fallback to original order
5. **Clean Architecture**: Domain remains pure, all infra isolated

### Negative

1. **Latency Impact**: RAG++ adds 2-3s to query time (still within <5s SLO for dialog)
2. **Complexity**: New abstractions (protocols, value objects, adapters)
3. **Testing Overhead**: More integration tests needed (3 modes × 2 strategies)
4. **Configuration Complexity**: More flags and config options for users

### Neutral

1. **Cross-Encoder Deferred**: Added to backlog, not blocking MVP
2. **Cache Deferred**: Rerank result caching is future optimization
3. **Hybrid Reranking**: Interesting but not urgent (low ROI for complexity)

---

## Implementation Plan

### Stage 21_01: Requirements
- [x] Define `retrieval_rerank_config.yaml` schema
- [x] Extend `queries.jsonl` with filter-sensitive questions
- [x] Metrics definition (Prometheus)

### Stage 21_02: Design & Prototype
- [ ] Domain protocols: `RerankerService`, `RelevanceFilterService`
- [ ] Value objects: `RerankResult`, `FilterConfig`
- [ ] Prototype script: `scripts/rag/rerank_once.py`

### Stage 21_03: Implementation
- [ ] Infrastructure adapters: `LLMRerankerAdapter`, `ThresholdFilterAdapter`
- [ ] Update `RetrievalService` with filter/rerank logic
- [ ] CLI commands: `rag:compare --filter --reranker llm`
- [ ] Metrics: `rag_rerank_duration_seconds`, `rag_chunks_filtered_total`
- [ ] Tests: 20+ unit, 5+ integration

### Stage 21_04: Validation
- [ ] Batch ablation: Baseline vs RAG vs RAG++
- [ ] Tune threshold (0.3 vs 0.35 vs 0.4)
- [ ] Report: win rate, latency analysis, recommendations
- [ ] Demo recording

---

## Validation Criteria

### Success Metrics (Stage 21_04)

1. **Quality**:
   - RAG++ win rate ≥60% vs RAG (manual eval on 20 queries)
   - Precision@3 improvement ≥10% (relevant chunks in top-3)

2. **Latency**:
   - p95 latency ≤5s for dialog queries with reranking
   - p95 latency ≤60s for review queries with reranking

3. **Robustness**:
   - Fallback triggered ≤5% of rerank calls (timeout/errors)
   - No crashes or 500 errors in CLI

### Rejection Criteria (Rollback Trigger)

- RAG++ win rate <50% (worse than RAG)
- p95 latency >8s for dialog
- >10% fallback rate (unreliable reranker)

---

## References

- [Architecture Vision](../ARCHITECTURE_VISION.md)
- [Epic 21 Summary](../epic_21_rerank.md)
- [EP20 RAG Implementation](../../epic_20/epic_20.md)
- [Channel Resolver Reranking Pattern](../../../../src/domain/services/channel_resolver.py#L167-L237)

---

## Revision History

- **2025-11-12**: Initial draft (Architect)
- **2025-11-12**: Implementation complete, reviewed by Tech Lead
- **2025-11-12**: Architect final sign-off (APPROVED FOR PRODUCTION)
- **TBD**: Updated after Stage 21_04 ablation results

---

## Post-Implementation Notes (2025-11-12)

### Adjustments Made

1. **Threshold**: 0.30 (conservative, high recall) instead of 0.35
2. **Prompt**: Simplified to 18 lines (production-ready)
3. **Seed**: Deferred to future (use temperature=0.2 for experiments)
4. **Variance**: Measures chunk spread per run (detects low-confidence)

### Status

✅ Stage 21_03 COMPLETE — Ready for Stage 21_04 validation
See: ARCHITECT_FINAL_SIGNOFF.md, STAGE_21_03_COMPLETE.md
