# Epic 21 · Analyst Review & Recommendations

**Date**: 2025-11-12
**Role**: Analyst
**Status**: ✅ APPROVED with Minor Recommendations

---

## Executive Summary

**Verdict**: Epic 21 (Reranker & Relevance Filtering) is **READY FOR IMPLEMENTATION**.

Architect and Tech Lead have delivered comprehensive, well-structured documentation with clear architecture boundaries, explicit contracts, and realistic staging plan. All key decisions are documented with rationale and trade-offs.

**Recommendation**: Proceed with Stage 21_02 immediately. No blocking issues identified.

---

## ✅ What Works Well

### 1. **Architecture & Clean Boundaries**
- ✅ Domain layer protocols (`RelevanceFilterService`, `RerankerService`) are isolated from infrastructure
- ✅ Clear separation: Domain → Application → Infrastructure layers
- ✅ Protocol-based design enables testability and swappable implementations
- ✅ No circular dependencies or layer violations

**Impact**: Maintainability 🟢, Testability 🟢, Extensibility 🟢

---

### 2. **Comprehensive Interface Contracts**
- ✅ `RelevanceFilterService`: Input/output guarantees, error handling explicit
- ✅ `RerankerService`: Graceful degradation (timeout → original order) is well-designed
- ✅ Value objects (`FilterConfig`, `RerankResult`) have built-in validation in `__post_init__`
- ✅ Configuration schema is explicit (YAML + environment variables)

**Impact**: Clarity 🟢, Type Safety 🟢, Reliability 🟢

---

### 3. **Risk Awareness & Mitigations**
- ✅ LLM timeout risk mitigated with 3s hard limit + fallback
- ✅ False negatives in filtering addressed via ablation in Stage 21_04
- ✅ Feature flag (`enable_rag_plus_plus`) enables safe rollout
- ✅ Cross-encoder deferred explicitly (not blocking MVP)

**Impact**: Safety 🟢, Rollout Control 🟢, Reversibility 🟢

---

### 4. **Realistic Staging Plan**
- ✅ Stage 21_01 (Requirements): Config + metrics defined
- ✅ Stage 21_02 (Design): Prototype script validates approach
- ✅ Stage 21_03 (Implementation): Phased layer-by-layer development
- ✅ Stage 21_04 (Validation): Ablation study + report generation

**Impact**: Manageability 🟢, Visibility 🟢, Quality Gates 🟢

---

### 5. **Metrics & Observability**
- ✅ Prometheus metrics defined: duration, chunks filtered, fallback count
- ✅ Structured logging specified (query_id, strategy, latency)
- ✅ Latency SLOs explicit: dialog <5s, review <60s (total pipeline)
- ✅ No PII in logs (query truncated to 50 chars)

**Impact**: Observability 🟢, Performance Tracking 🟢, Security 🟢

---

## ⚠️ Minor Recommendations

### 1. **SHOULD: Clarify FilterConfig Validation Logic**

**Issue**: `FilterConfig.__post_init__()` has strict coupling between `reranker_strategy` and `reranker_enabled`:

```python
if self.reranker_strategy != "off" and not self.reranker_enabled:
    raise ValueError(...)
```

**Recommendation**:
- Keep validation strict ✅ (prevents accidental misconfig)
- **Add explicit comment** explaining the invariant:
  ```python
  # Invariant: reranker_strategy="off" ⟺ reranker_enabled=False
  ```
- **Provide factory method** for common configs:
  ```python
  @classmethod
  def with_reranking(cls, strategy: str, ...) -> FilterConfig:
      """Create config with reranker enabled."""
      return cls(..., reranker_enabled=True, reranker_strategy=strategy)
  ```

**Impact**: Reduced config errors 🟢, Better discoverability 🟢

---

### 2. **SHOULD: Add Backward Compatibility Wrapper Early**

**Issue**: `RetrievalService.retrieve()` signature changes breaking old callers:
- Old: `retrieve(query_vector, top_k, score_threshold)`
- New: `retrieve(query_text, query_vector, filter_config)`

**Recommendation**:
- **Create `RetrievalServiceCompat` wrapper** in Stage 21_03 (not 21_04)
  ```python
  class RetrievalServiceCompat:
      """Adapter for backward compatibility with EP20."""
      def retrieve_legacy(self, query_vector, top_k, score_threshold):
          filter_config = FilterConfig(score_threshold=score_threshold, top_k=top_k)
          return await self._new_service.retrieve("", query_vector, filter_config)
  ```
- Deprecate old signature immediately
- Update all callers before Stage 21_04

**Impact**: Smooth migration 🟢, Zero breaking changes 🟢

---

### 3. **SHOULD: Default Threshold Conservative → Ablate in 21_04**

**Current Config**:
```yaml
score_threshold: 0.35  # Recommended by architect
```

**Issue**: Default threshold of 0.35 is not conservative enough for safety. Concerns:
- May silently filter out relevant chunks (false negatives)
- Difficult to debug in production

**Recommendation**:
- **Start with 0.30** (conservative default in Stage 21_03)
- **Document the choice** in ARCHITECTURE_VISION.md:
  > "Default 0.30 is conservative to avoid silent false negatives. Ablation in Stage 21_04 will determine optimal threshold."
- **Run ablation in 21_04**: Compare 0.25, 0.30, 0.35, 0.40
- **Record winner** in config and MADR

**Impact**: Safety-first approach 🟢, Data-driven tuning 🟢

---

### 4. **SHOULD: Expand CLI Help Text**

**Current**:
```bash
rag:compare --question "..." [--filter] [--threshold FLOAT] [--reranker off|llm|cross_encoder]
```

**Recommendation**:
- Add help examples:
  ```bash
  rag compare \
    --question "What is MapReduce?" \
    --filter \
    --threshold 0.35 \
    --reranker llm
  ```
- Add explicit note: "Without `--filter`, all retrieved chunks used. `--reranker off` is default (safe)."
- Add link to runbook: `See docs/runbooks/rag.md for tuning guide`

**Impact**: Reduced user confusion 🟢, Better discoverability 🟢

---

### 5. **NICE-TO-HAVE: Document Reranker Prompt Tuning Strategy**

**Current**: Prompt template in ARCHITECTURE_VISION.md is generic.

**Recommendation**:
- Add section `5.1.1 Prompt Engineering Strategy` in ARCHITECTURE_VISION.md:
  ```markdown
  ## Prompt Engineering Strategy

  **Goal**: Achieve consistent, accurate relevance scores.

  **Initial Prompt**:
  - Few-shot examples: Include 2-3 labeled (query, chunk, expected_score) pairs
  - Tie-breaker rules: Explicit criteria for similar scores (e.g., "prefer longer context")
  - Temperature 0.5: Balance between consistency (0.0) and flexibility (1.0)

  **Tuning Process** (Stage 21_04):
  1. Run 20 queries with baseline prompt
  2. Identify disagreements between LLM and human raters
  3. Refine prompt based on patterns
  4. Re-test and record improvement
  ```
- Add `scripts/rag/tune_rerank_prompt.py` to assist tuning

**Impact**: Better reranking quality 🟢, Systematic improvements 🟢

---

## ✅ Acceptance Criteria Check

| Criteria | Status | Notes |
|----------|--------|-------|
| **Requirements doc approved** | ✅ | Clear Must/Should/Out-of-Scope |
| **Acceptance criteria measurable** | ✅ | Mapped to Prometheus metrics & tests |
| **Cross-links to architecture exist** | ✅ | ARCHITECTURE_VISION.md complete |
| **Traceable to tests** | ✅ | 20+ unit + 5+ integration tests planned |
| **File paths referenced** | ✅ | All concrete (`src/domain/rag/`, `config/retrieval_rerank_config.yaml`) |

---

## 📋 Definition of Done Checklist

**Before Stage 21_02 Kickoff**:
- [x] Vision doc approved (ARCHITECTURE_VISION.md)
- [x] Contracts explicit (INTERFACES_CONTRACTS.md)
- [x] Risks documented with mitigations
- [x] Staging plan realistic (4 stages, ~1 day total)
- [x] Metrics & observability designed
- [x] No architectural blockers

**For Tech Lead**:
- [ ] Acknowledge handoff receipt
- [ ] Break Stage 21_02 into tasks (2-3 hours)
- [ ] Setup feature flag in DI container
- [ ] Create developer tasks with links to ARCHITECTURE_VISION.md

**For Developers**:
- [ ] Review ARCHITECTURE_VISION.md + INTERFACES_CONTRACTS.md (1 hour)
- [ ] Understand protocol contracts + value object validation
- [ ] Write tests first (TDD): FilterConfig validation → ThresholdFilterAdapter → LLMRerankerAdapter
- [ ] Implement with type hints 100%

---

## 🎯 Key Success Factors

1. **Strict Adherence to Layer Boundaries**
   - Domain must remain pure Python (no I/O, no framework code)
   - All adapters in infrastructure layer only
   - ✅ Risk: **LOW** (architecture explicitly defined)

2. **Protocol Contracts Must Be Honored**
   - Implementations MUST satisfy protocol specs
   - Graceful degradation (timeout → fallback) is mandatory
   - ✅ Risk: **LOW** (tests will validate)

3. **Feature Flag Activation**
   - Single-toggle `enable_rag_plus_plus` controls entire feature
   - Default: `false` (safe, non-breaking)
   - ✅ Risk: **LOW** (explicitly designed)

4. **Latency SLO Compliance**
   - p95 dialog latency <5s including reranking
   - p95 review latency <60s (total pipeline)
   - ✅ Risk: **MEDIUM** (LLM timeout is key; mitigated with 3s limit)

5. **Test Coverage ≥80%**
   - Domain: 100% (simple validation logic)
   - Infrastructure: 80%+ (mocked LLM calls)
   - Integration: 5+ E2E tests
   - ✅ Risk: **LOW** (straightforward to test)

---

## 📊 Metrics Summary

**Estimated Effort**:
- Stage 21_01 (Requirements): ✅ Complete (config + metrics)
- Stage 21_02 (Design): 3-4 hours
- Stage 21_03 (Implementation): 4-6 hours
- Stage 21_04 (Validation): 2-3 hours
- **Total**: ~10-13 hours (feasible in 1 day with parallel work)

**Test Coverage Expected**:
- Unit tests: 20+ (domain + adapter unit tests)
- Integration tests: 5+ (pipeline E2E)
- Coverage: 85-90% (realistic for this scope)

**Success Metrics** (from Tech Lead handoff):
- RAG++ win rate ≥60% vs RAG ✅ (measurable in Stage 21_04)
- Precision@3 +10% improvement ✅ (traceable via ablation)
- p95 latency <5s dialog ✅ (Prometheus SLO)
- Fallback rate <5% ✅ (monitoring metric)

---

## 🚀 Final Recommendation

**APPROVED** ✅ for implementation start.

**Next Steps**:
1. **Tech Lead**: Acknowledge receipt, break Stage 21_02 into Jira tasks
2. **Developers**: Read ARCHITECTURE_VISION.md (1 hour), start with domain layer (protocols + value objects)
3. **All**: Daily sync on Stage 21_02 progress (prototype script validation)
4. **QA**: Prepare test environment for Stage 21_03 integration tests

---

## 📝 Remarks

### Strengths
- Architect delivered **production-ready design** with explicit contracts
- Tech Lead provided **realistic staging plan** with clear exit criteria
- **Zero architectural concerns** identified
- Risks are **well-understood and mitigated**

### Opportunities for Improvement (Post-MVP)
- Implement **hybrid reranking** (LLM + cross-encoder ensemble) in Epic 22
- Add **query expansion** before retrieval (advanced RAG)
- Build **prompt tuning dashboard** for continuous optimization

### No Blockers
- All dependencies already available (EP19 index, EP20 RAG agent, LLM infra)
- No external approvals needed
- Backward compatibility plan is sound

---

## Sign-Off

**Analyst Review**: ✅ **COMPLETE**

| Role | Approval | Notes |
|------|----------|-------|
| Analyst | ✅ | Vision approved, recommendations logged |
| Ready for Tech Lead | ✅ | Handoff complete |
| Ready for Developers | ✅ | ARCHITECTURE_VISION.md is developer-ready |

---

**Analyst**: AI Assistant
**Date**: 2025-11-12
**Status**: ✅ APPROVED — Proceed to Stage 21_02

---

## Appendix: Recommended Edits to ARCHITECTURE_VISION.md

### A1: Section 3.1 Add FilterConfig Factory Method

**Location**: After line 137 (after FilterConfig definition)

**Add**:
```python
    @classmethod
    def with_reranking(
        cls, strategy: str = "llm", threshold: float = 0.35, top_k: int = 5
    ) -> FilterConfig:
        """Create config with reranking enabled.

        Purpose:
            Convenience factory for common reranking configurations.

        Args:
            strategy: "llm" (default) or "cross_encoder".
            threshold: Similarity score threshold [0.0, 1.0].
            top_k: Maximum chunks to return.

        Returns:
            FilterConfig with reranker_enabled=True.

        Example:
            >>> config = FilterConfig.with_reranking("llm", threshold=0.35)
            >>> config.reranker_enabled
            True
        """
        return cls(
            score_threshold=threshold,
            top_k=top_k,
            reranker_enabled=True,
            reranker_strategy=strategy,
        )
```

---

### A2: Section 5 Add Prompt Engineering Strategy

**Location**: After section 4.2 (after Metrics & Observability)

**Add**:
```markdown
### 4.3 Prompt Engineering & Tuning

**Goal**: Achieve consistent, accurate relevance scoring from LLM reranker.

**Initial Prompt Design**:
- **Few-shot examples** (2-3 labeled pairs): Help LLM understand score distribution
- **Explicit evaluation criteria**: "Score based on: semantic relevance, answer completeness, factual accuracy"
- **Tie-breaker rules**: "If scores are within 0.1, prefer chunks with more context"
- **Temperature 0.5**: Balance consistency (cold) with flexibility (warm)

**Tuning Process** (Stage 21_04):
1. Run baseline prompt on 20 diverse queries
2. Collect human relevance judgments (optional: manual labels or click-through data)
3. Identify LLM disagreements (e.g., "LLM scored 0.9 but human said irrelevant")
4. Refine prompt based on patterns (e.g., add tie-breaker, adjust examples)
5. Re-test and measure improvement (e.g., "LLM agreement increased from 75% to 85%")

**Optimization Toolkit** (`scripts/rag/`):
- `tune_rerank_prompt.py`: Interactive prompt refinement script
- `eval_rerank_quality.py`: Compare prompt versions on test set
- `benchmark_latency.py`: Measure latency impact of prompt changes
```

---

### A3: Update Risk Table (Section 9)

**Location**: Row for "False negatives in filtering"

**Update**:
```
| False negatives in filtering | Relevant chunks discarded | Medium | Tune threshold via ablation (Stage 21_04); **start conservative at 0.30** → ablate to find optimal |
```

---

### A4: Section 11 Update Stage-by-Stage Plan

**Location**: Stage 21_03 Implementation section, add bullet:

**Add**:
```
- **Backward Compatibility Wrapper** (not deferred to 21_04)
  - `RetrievalServiceCompat` adapter for old `retrieve(query_vector, top_k, threshold)` signature
  - Mark old signature `@deprecated` with migration note
  - Update all EP20 callers before Stage 21_04 merge
```

---

## Appendix B: Questions for Tech Lead

1. **Should we start with threshold 0.30 (conservative) or 0.35 (recommended)**?
   - Analyst recommendation: Start 0.30, ablate in Stage 21_04 → Recommend 0.35 only if data supports

2. **Backward compatibility: wrapper now vs later**?
   - Analyst recommendation: Implement wrapper in Stage 21_03 (easier to debug earlier)

3. **LLM prompt tuning: baseline or iterate**?
   - Analyst recommendation: Use baseline prompt (ARCHITECTURE_VISION.md template) in 21_03, optimize in 21_04

---

**End of Analyst Review**
