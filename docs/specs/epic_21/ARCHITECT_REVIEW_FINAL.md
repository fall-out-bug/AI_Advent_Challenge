# Epic 21 Reranker · Architect Final Review

**Date**: 2025-11-12
**Reviewer**: AI Architect
**Reviewed**: Tech Lead amendments to Architecture Vision, Interfaces, and Handoff
**Status**: ✅ APPROVED WITH AMENDMENTS

---

## 📋 Review Summary

Tech Lead's changes reviewed. **3 amendments proposed** before final approval.

### Changes Reviewed

| Change | Location | Status |
|--------|----------|--------|
| Temperature 0.2→0.5 | Multiple files | ⚠️ **APPROVED with risk documentation** |
| Determinism relaxed | Interfaces, contracts | ✅ **APPROVED** (realistic for LLM) |
| Feature flag (no canary) | Config, handoff | ⚠️ **APPROVED with rollback plan** |
| Detailed prompts emphasis | Multiple | ✅ **APPROVED** (essential) |

---

## 🔍 Detailed Review

### 1. Temperature Change (0.2 → 0.5)

**Tech Lead Rationale**: "Balanced creativity and nuance" for better semantic understanding.

**Architect Assessment**: ⚠️ **APPROVED with caveats**

**Trade-offs**:
- ✅ **Pro**: More nuanced scoring, better handles ambiguous queries
- ✅ **Pro**: Reduces over-confident wrong answers (temperature too low can be brittle)
- ❌ **Con**: Less reproducibility for A/B tests (same query → different scores)
- ❌ **Con**: Harder to debug (variance in outputs)
- ❌ **Con**: Potentially slower convergence in ablation studies

**Risk Level**: **MEDIUM**

**Mitigations Required**:
1. **Seed control**: Add `random_seed` parameter for reproducible experiments
2. **Variance monitoring**: Track score variance across runs (new metric)
3. **Fallback**: Allow override to `temperature=0.2` via CLI flag for debugging
4. **Documentation**: Explicitly warn about non-determinism in user docs

**Amendment #1**: Add to config:

```yaml
reranker:
  llm:
    temperature: 0.5  # Balance: nuance vs reproducibility
    seed: null        # Set for reproducible experiments (e.g., 42)
    temperature_override_env: "RAG_RERANK_TEMPERATURE"  # For debugging
```

**Amendment #2**: Add metric to track variance:

```python
rag_rerank_score_variance = Histogram(
    "rag_rerank_score_variance",
    "Variance in rerank scores across repeated runs (same query)",
    buckets=(0.0, 0.05, 0.1, 0.2, 0.5),
)
```

**Decision**: ✅ Accept 0.5 as default, but provide escape hatches.

---

### 2. Determinism Relaxed

**Tech Lead Change**: Removed "Same (query, chunks) → same output (deterministic)" from contract.

**Architect Assessment**: ✅ **APPROVED**

**Rationale**:
- Realistic: LLMs with temperature > 0 are inherently non-deterministic
- Honest: Better to document actual behavior than promise false guarantees
- Correct contract: "Minor variance acceptable" is accurate

**No amendments needed**. This is good engineering honesty.

**Recommendation**: Add to testing strategy:

```python
# In tests, use low temperature or seed for reproducibility
@pytest.fixture
def deterministic_reranker():
    return LLMRerankerAdapter(
        llm_client=mock_llm,
        temperature=0.0,  # Deterministic for tests
        seed=42,
    )
```

---

### 3. Feature Flag: Single-Toggle (No Canary)

**Tech Lead Change**: Clarified "single-toggle; no canary rollout".

**Architect Assessment**: ⚠️ **APPROVED with rollback plan**

**Trade-offs**:
- ✅ **Pro**: Simpler implementation (MVP-friendly)
- ✅ **Pro**: Faster deployment (no gradual rollout infrastructure)
- ❌ **Con**: All-or-nothing risk (cannot test on 10% traffic)
- ❌ **Con**: Harder to isolate issues in production

**Risk Level**: **MEDIUM-HIGH** (for production deployment)

**Acceptable for MVP** (Stage 21_03–21_04) because:
1. CLI-first deployment (no production traffic initially)
2. Manual testing in Stage 21_04 before enabling
3. Feature flag allows instant rollback

**Amendment #3**: Add explicit rollback procedure to operations docs:

**New Section in `ARCHITECTURE_VISION.md`**:

```markdown
### Rollback Plan (Feature Flag)

**Trigger**: RAG++ win rate <50% OR p95 latency >8s OR >10% fallback rate

**Procedure**:
1. Set `enable_rag_plus_plus=false` in config
2. Restart services (or hot-reload if supported)
3. Verify metrics return to baseline (RAG mode)
4. Post-mortem: Analyze logs, identify root cause
5. Fix or defer to next epic

**Rollback Time**: <5 minutes (config change + restart)

**Testing**: Include rollback drill in Stage 21_03 integration tests
```

**Decision**: ✅ Accept single-toggle for MVP, but document rollback clearly.

**Future Enhancement** (Epic 22+): Add canary support via percentage-based flag:

```yaml
feature_flags:
  rag_plus_plus_enabled: false
  rag_plus_plus_canary_percentage: 0  # 0-100, gradual rollout
```

---

### 4. Detailed Prompts Emphasis

**Tech Lead Change**: "Include explicit evaluation criteria and tie-breakers" in prompt.

**Architect Assessment**: ✅ **STRONGLY APPROVED**

**Rationale**:
- **Essential** for temperature=0.5 to work well
- Reduces variance by guiding LLM reasoning
- Improves interpretability (reasoning field in output)

**Recommendation**: Provide prompt template in handoff.

**Amendment #4**: Add concrete prompt template to `INTERFACES_CONTRACTS.md`:

```markdown
### Prompt Template (LLM Reranker)

**File**: `src/infrastructure/rag/prompts/rerank_prompt.md`

```markdown
# Task: Relevance Scoring for RAG Retrieval

You are a relevance scorer for a retrieval system. Given a user query and text chunks, score each chunk's relevance to the query (0.0–1.0 scale).

## Evaluation Criteria (in priority order)

1. **Semantic Match** (40%): Does the chunk directly answer the query?
2. **Completeness** (30%): Does it provide sufficient detail?
3. **Recency** (15%): Is the information up-to-date? (if applicable)
4. **Source Quality** (15%): Is it from official docs vs user comments?

## Tie-Breaker Rules

- If scores are within 0.1, prefer shorter chunks (higher information density)
- If same source type, prefer chunks with examples over pure definitions

## Input

**Query**: "{query}"

**Chunks**:
[1] chunk_id: {chunk_id_1}
    source: {source_path_1}
    text: "{text_1}"

[2] chunk_id: {chunk_id_2}
    source: {source_path_2}
    text: "{text_2}"

[3] chunk_id: {chunk_id_3}
    source: {source_path_3}
    text: "{text_3}"

## Output Format (JSON only, no markdown)

{{
  "scores": {{
    "{chunk_id_1}": 0.85,
    "{chunk_id_2}": 0.60,
    "{chunk_id_3}": 0.42
  }},
  "reasoning": "Chunk 1 scores highest because it directly defines MapReduce with examples (semantic match + completeness). Chunk 2 mentions MapReduce but focuses on Hadoop (partial match). Chunk 3 is tangential (low relevance)."
}}

**Important**: Output ONLY valid JSON. No explanations outside the JSON structure.
```
```

---

## 📊 Risk Assessment Update

| Risk | Original | After Tech Lead Changes | Mitigation Status |
|------|----------|-------------------------|-------------------|
| **Temperature variance** | Low (temp=0.2) | **MEDIUM** (temp=0.5) | ✅ Seed control added |
| **Non-determinism** | Low | **MEDIUM** | ✅ Documented + test fixtures |
| **Feature flag risk** | Low (canary) | **MEDIUM-HIGH** (no canary) | ✅ Rollback plan added |
| **Prompt quality** | Medium | **LOW** (detailed template) | ✅ Template provided |

**Overall Risk**: **MEDIUM** (acceptable for MVP with mitigations)

---

## ✅ Amendments Summary

### Amendment #1: Config - Add Seed Control
**File**: `config/retrieval_rerank_config.yaml`

```yaml
reranker:
  llm:
    model: "qwen2.5-7b-instruct"
    temperature: 0.5
    seed: null  # Set to integer for reproducible experiments
    temperature_override_env: "RAG_RERANK_TEMPERATURE"
    max_tokens: 256
    timeout_seconds: 3
```

### Amendment #2: Metrics - Track Variance
**File**: `src/infrastructure/metrics/rag_metrics.py`

```python
rag_rerank_score_variance = Histogram(
    "rag_rerank_score_variance",
    "Std dev of rerank scores across repeated runs (same query)",
    buckets=(0.0, 0.05, 0.1, 0.2, 0.5),
)

# Usage: measure variance when running same query N times in Stage 21_04
```

### Amendment #3: Rollback Plan
**File**: `docs/specs/epic_21/ARCHITECTURE_VISION.md`

Add new section (after Section 11):

```markdown
## 11.5 Rollback Plan

**Trigger Conditions**:
- RAG++ win rate <50% (worse than RAG)
- p95 latency >8s for dialog queries
- Fallback rate >10% (reranker unreliable)
- Critical bug discovered in production

**Rollback Procedure**:
1. Set `enable_rag_plus_plus=false` in config
2. Deploy config change (hot-reload or restart)
3. Verify metrics return to RAG baseline
4. Create incident report
5. Schedule post-mortem

**Rollback SLA**: <5 minutes (config-only change)

**Test Rollback**: Include rollback drill in Stage 21_03 integration tests
```

### Amendment #4: Prompt Template
**File**: `src/infrastructure/rag/prompts/rerank_prompt.md`

Create file with detailed evaluation criteria (see full template above in Section 4).

---

## 🎯 Updated Success Criteria

| Metric | Target | Notes |
|--------|--------|-------|
| **RAG++ win rate** | ≥60% vs RAG | Despite temperature variance |
| **Rerank score variance** | <0.15 std dev | Acceptable variance with temp=0.5 |
| **Determinism (repeated runs)** | ≥80% same top-1 chunk | Relaxed from 100% |
| **p95 latency (dialog)** | <5s | Unchanged |
| **Rollback drill success** | 100% | Must pass in Stage 21_03 |

---

## 📝 Documentation Updates Required

### 1. User-Facing Docs
**File**: `docs/specs/epic_21/stage_21_03.md`

Add warning:

```markdown
## Non-Determinism Notice

⚠️ **Important**: LLM reranker (temperature=0.5) produces non-deterministic results. Same query may yield slightly different rankings across runs. This is expected behavior for nuanced semantic scoring.

**For reproducible experiments**:
- Set `RAG_RERANK_TEMPERATURE=0.2` (more deterministic)
- Or set `seed=42` in config (exact reproducibility)
```

### 2. Developer Docs
**File**: `INTERFACES_CONTRACTS.md`

Update Section 5.2 (LLMRerankerAdapter) with:

```markdown
**Variance Handling**:
- Temperature=0.5 produces minor variance (±0.1 score difference typical)
- For tests, use `temperature=0.0` or `seed=42` for determinism
- For production, accept variance as feature (more nuanced scoring)
```

### 3. Operations Runbook
**New File**: `docs/specs/epic_21/OPERATIONS_RUNBOOK.md`

Create with sections:
- Feature flag management
- Rollback procedures
- Monitoring dashboards
- Troubleshooting guide

---

## ✅ Final Approval Checklist

- [x] **Temperature change reviewed**: Approved with seed control
- [x] **Determinism relaxed**: Approved (realistic for LLM)
- [x] **Feature flag strategy**: Approved with rollback plan
- [x] **Prompt template**: Approved and detailed template provided
- [x] **Risk assessment updated**: Medium risk, acceptable for MVP
- [x] **Amendments proposed**: 4 amendments documented
- [x] **Documentation updates specified**: User, dev, ops docs

---

## 🚀 Final Verdict

**Status**: ✅ **APPROVED FOR IMPLEMENTATION**

**Conditions**:
1. Apply 4 amendments (seed control, variance metric, rollback plan, prompt template)
2. Update documentation (3 files)
3. Include rollback drill in Stage 21_03 integration tests
4. Monitor variance metric in Stage 21_04 ablation

**Next Steps**:
1. **Tech Lead**: Review amendments, acknowledge acceptance
2. **Developer**: Implement amendments alongside Stage 21_02
3. **Architect**: Available for prompt engineering review (Amendment #4)

---

## 📞 Open for Discussion

**Architect willing to reconsider**:
- Temperature value (0.5 vs 0.3 vs 0.2) based on Stage 21_04 ablation
- Canary rollout (if time/resources allow in Stage 21_04)
- Cross-encoder priority (if LLM variance too high)

**Architect firm on**:
- Seed control must be added (non-negotiable for experiments)
- Rollback plan must be documented (production safety)
- Prompt template must include explicit criteria (quality baseline)

---

## 📚 References

- Original Architecture Vision (pre-amendments)
- Tech Lead changes in: ARCHITECTURE_VISION.md, INTERFACES_CONTRACTS.md, HANDOFF_TO_TECH_LEAD.md
- MADR 0001 (reranker architecture decision)

---

**Architect**: AI Assistant
**Review Date**: 2025-11-12
**Approval**: ✅ CONDITIONAL (apply amendments)
**Next Review**: After Stage 21_04 ablation (temperature validation)

---

*Awaiting Tech Lead acknowledgment and Developer kickoff for Stage 21_02.*
