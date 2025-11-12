# Epic 21 Reranker · Architect → Tech Lead Handoff

**Date**: 2025-11-12
**From**: AI Architect
**To**: Tech Lead
**Epic**: Epic 21 Reranking & Relevance Filtering (RAG++)

---

## 📋 Summary

Architecture for two-stage RAG retrieval (filter + rerank) is ready for implementation. All boundaries, interfaces, and contracts are defined. Target: complete all 4 stages today.

---

## 📦 Deliverables

### ✅ Architecture Documents

1. **[ARCHITECTURE_VISION.md](./ARCHITECTURE_VISION.md)** (1500 lines)
   - Component diagram and data flows
   - Layer boundaries (domain/application/infrastructure)
   - Configuration schema
   - Metrics definitions
   - Testing strategy
   - Risks & mitigations

2. **[decisions/0001-reranker-architecture.md](./decisions/0001-reranker-architecture.md)** (MADR)
   - Decision: LLM-based reranking (primary), cross-encoder (future)
   - Rationale: Accuracy > latency for MVP
   - Trade-offs documented
   - Validation criteria defined

3. **[INTERFACES_CONTRACTS.md](./INTERFACES_CONTRACTS.md)** (900 lines)
   - Domain protocols: `RerankerService`, `RelevanceFilterService`
   - Value objects: `RerankResult`, `FilterConfig`
   - Application interface: Extended `RetrievalService`
   - Infrastructure adapters: `LLMRerankerAdapter`, `ThresholdFilterAdapter`
   - Metrics interface (Prometheus)
   - CLI interface specification
   - Testing contracts

---

## 🎯 Key Decisions

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| **LLM-based reranking** | Higher accuracy, interpretable | +2-3s latency (within SLO) |
| **Protocol-based design** | Swappable strategies, testable | +1 abstraction layer |
| **Threshold filtering first** | Fast, deterministic, reduces noise | Cannot learn from data |
| **Feature flag toggle (no canary)** | Safe enable/disable via single flag | Limited gradual control |
| **Cross-encoder deferred** | Focus on MVP, add if needed | May need later optimization |

---

## 🏗️ Architecture Overview

### Component Layers

```
┌─────────────────────────────────────────┐
│  PRESENTATION (CLI)                     │
│  rag:compare --filter --reranker llm    │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│  APPLICATION                            │
│  CompareRagAnswersUseCase (updated)     │
│  RetrievalService (extended)            │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│  DOMAIN (Protocols)                     │
│  RerankerService                        │
│  RelevanceFilterService                 │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│  INFRASTRUCTURE (Adapters)              │
│  LLMRerankerAdapter                     │
│  ThresholdFilterAdapter                 │
└─────────────────────────────────────────┘
```

### Data Flow (RAG++ Mode)

```
Query → Embed → VectorSearch (top_k*2)
        ↓
        Filter (threshold) → [5 chunks]
        ↓
        Rerank (LLM) → [3 chunks reordered]
        ↓
        PromptAssembler → LLM Generation → Answer
```

---

## 🛠️ Implementation Tasks

### Stage 21_01: Requirements & Setup ✅
- [x] Config schema (`retrieval_rerank_config.yaml`)
- [x] Extended `queries.jsonl` (already exists)
- [x] Metrics definitions

### Stage 21_02: Design & Prototype (3-4 hours)
- [ ] **Domain Layer** (`src/domain/rag/`)
  - [ ] Add `RerankerService` protocol to `interfaces.py`
  - [ ] Add `RelevanceFilterService` protocol to `interfaces.py`
  - [ ] Add `RerankResult` value object to `value_objects.py`
  - [ ] Add `FilterConfig` value object to `value_objects.py`
  - [ ] Unit tests for value objects (validation rules)

- [ ] **Prototype Script** (`scripts/rag/rerank_once.py`)
  - [ ] Load single query from `queries.jsonl`
  - [ ] Run 3 modes: Baseline | RAG | RAG++
  - [ ] Print side-by-side comparison
  - [ ] Example usage: `python scripts/rag/rerank_once.py --query-id arch_001`

**Exit Criteria**: Prototype runs without errors, outputs 3 different answers

### Stage 21_03: Implementation & Tests (4-6 hours)
- [ ] **Infrastructure Layer** (`src/infrastructure/rag/`)
  - [ ] `threshold_filter_adapter.py` (simple filtering)
  - [ ] `llm_reranker_adapter.py` (LLM-based reranking)
  - [ ] Prompt template in `prompts/rerank_prompt.md`
  - [ ] Unit tests for adapters

- [ ] **Application Layer** (`src/application/rag/`)
  - [ ] Extend `RetrievalService.retrieve()` with filter/rerank logic
  - [ ] Update `CompareRagAnswersUseCase` to use new signature
  - [ ] Unit tests for updated services

- [ ] **Presentation Layer** (`src/presentation/cli/rag_commands.py`)
  - [ ] Add `--filter`, `--threshold`, `--reranker` flags to `compare` command
  - [ ] Update CLI help text
  - [ ] CLI smoke test

- [ ] **Metrics** (`src/infrastructure/metrics/rag_metrics.py`)
  - [ ] `rag_rerank_duration_seconds` (Histogram)
  - [ ] `rag_chunks_filtered_total` (Counter)
  - [ ] `rag_reranker_fallback_total` (Counter)
  - [ ] Wire metrics into adapters

- [ ] **Configuration**
  - [ ] Create `config/retrieval_rerank_config.yaml`
  - [ ] Environment variable support
  - [ ] Feature flag: `enable_rag_plus_plus` (single-toggle; no canary)
  - [ ] Default LLM reranker temperature: `0.5`; encourage detailed prompts

- [ ] **Integration Tests**
  - [ ] `test_rag_plus_plus_e2e.py` (mock index + LLM)
  - [ ] `test_three_modes_comparison.py` (outputs differ)
  - [ ] `test_rerank_latency.py` (p95 <5s)

**Exit Criteria**: CI green, CLI works locally, all tests pass

### Stage 21_04: Validation & Report (2-3 hours)
- [ ] **Batch Comparison**
  - [ ] Run `rag:batch` on full `queries.jsonl` (3 modes)
  - [ ] Aggregate results: win rate, latency, precision@3

- [ ] **Ablation Study**
  - [ ] Test thresholds: 0.3, 0.35, 0.4
  - [ ] Test strategies: off, llm
  - [ ] Record best configuration

- [ ] **Report** (`docs/specs/epic_21/stage_21_04_report.md`)
  - [ ] Summary tables (win rate, latency)
  - [ ] Examples: improvements and failures
  - [ ] Recommendations: threshold = 0.35, reranker = llm (opt-in)

- [ ] **MADR Update**
  - [ ] Update `0001-reranker-architecture.md` with ablation results
  - [ ] Document chosen defaults

- [ ] **Demo**
  - [ ] Record 2-3 min video: CLI usage, side-by-side comparison
  - [ ] Show metrics in Prometheus

**Exit Criteria**: Report approved, defaults updated in config

---

## 📊 Success Metrics

| Metric | Target | Validation |
|--------|--------|------------|
| **RAG++ win rate** | ≥60% vs RAG | Manual eval on 20 queries |
| **Precision@3** | +10% improvement | Relevant chunks in top-3 |
| **p95 latency (dialog)** | <5s | Prometheus histogram |
| **p95 latency (review)** | <60s | Prometheus histogram |
| **Fallback rate** | <5% | Prometheus counter |
| **Test coverage** | ≥80% | pytest-cov report |

---

## ⚠️ Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **LLM reranker timeout** | 3s timeout + fallback to original order |
| **False negatives in filtering** | Conservative threshold (0.35), tune in 21_04 |
| **Cross-encoder not ready** | Deferred to future, not blocking MVP |
| **RAG++ degrades quality** | Feature flag allows rollback, A/B test |

---

## 🔗 Dependencies

### External
- ✅ EP19 index (Redis/FAISS + MongoDB)
- ✅ EP20 RAG agent (`CompareRagAnswersUseCase`)
- ✅ LLM infra (Qwen2.5-7B-Instruct, Mistral-7B)
- ✅ Prometheus metrics endpoint

### Internal
- ⚠️ Need to refactor `RetrievalService.retrieve()` signature (breaking change)
- ⚠️ Provide backward-compatible wrapper for old signature

---

## 📂 File Structure

```
docs/specs/epic_21/
├── ARCHITECTURE_VISION.md          # High-level design
├── INTERFACES_CONTRACTS.md         # Detailed contracts
├── decisions/
│   └── 0001-reranker-architecture.md  # MADR
├── stage_21_01.md                  # Requirements (existing)
├── stage_21_02.md                  # Design & prototype (existing)
├── stage_21_03.md                  # Implementation (existing)
├── stage_21_04.md                  # Validation (existing)
└── stage_21_04_report.md           # Final report (to be created)

src/
├── domain/rag/
│   ├── interfaces.py               # Add protocols
│   └── value_objects.py            # Add FilterConfig, RerankResult
├── application/rag/
│   ├── retrieval_service.py        # Extend with filter/rerank
│   └── use_case.py                 # Update signature
├── infrastructure/rag/
│   ├── threshold_filter_adapter.py # New
│   ├── llm_reranker_adapter.py     # New
│   └── prompts/
│       └── rerank_prompt.md        # New
└── presentation/cli/
    └── rag_commands.py             # Add flags

config/
└── retrieval_rerank_config.yaml    # New

scripts/rag/
└── rerank_once.py                  # Prototype (new)
```

---

## 🚀 Next Actions

### For Tech Lead
1. **Review architecture docs** (30 min)
   - Verify boundaries make sense
   - Check for missing edge cases
   - Approve or request changes

2. **Break down Stage 21_02** (1 hour)
   - Create developer tasks (Jira/GitHub issues)
   - Assign priorities (critical path: domain → application → infra)
   - Estimate hours per task

3. **Setup feature flag** (15 min)
   - Add `enable_rag_plus_plus` to settings
   - Wire into DI container

4. **Kickoff with developer** (30 min)
   - Walk through architecture vision
   - Clarify protocol contracts
   - Agree on testing strategy

5. **Developer Handoff Spec (FINAL)**
   - See: `DEVELOPER_IMPLEMENTATION_SPEC.md` (authoritative tasks, tests, CI gates)

### For Developer
1. **Read architecture docs** (1 hour)
   - Understand component boundaries
   - Review protocol contracts
   - Note edge cases

2. **Start Stage 21_02** (3-4 hours)
   - Implement domain protocols + value objects
   - Write prototype script
   - Run smoke test

3. **Parallel work**: Infrastructure can start while domain is finalized
   - Domain (protocols) → Application (service) → Infrastructure (adapters)
   - Tests written alongside code (TDD)

---

## 📞 Questions & Clarifications

### Open Questions for Tech Lead
1. **Backward compatibility**: Provide wrapper for old `retrieve()` signature or force migration?
   - **Architect recommendation**: Wrapper in 21_03, deprecate in 21_04

2. **Cross-encoder timing**: Add in 21_04 or defer to Epic 22?
   - **Architect recommendation**: Prototype in 21_04, ship if time allows

3. **Judge prompts**: Reuse EP05 judge or create new ones?
   - **Architect recommendation**: Reuse EP05, adjust if needed

### Ready to Answer
- Protocol design rationale
- Layer boundary enforcement
- Metrics granularity
- Testing strategy details

---

## 📚 References

- [Architecture Vision](./ARCHITECTURE_VISION.md) — Full design (1500 lines)
- [Interfaces & Contracts](./INTERFACES_CONTRACTS.md) — Detailed specs (900 lines)
- [MADR 0001](./decisions/0001-reranker-architecture.md) — Key decisions
- [Epic 21 Summary](./epic_21_rerank.md) — Original scope
- [EP20 RAG](../epic_20/epic_20.md) — Existing implementation
- [Channel Resolver Pattern](../../../../src/domain/services/channel_resolver.py#L167) — Reranking reference

---

## ✅ Architect Sign-Off

**Architecture Complete**: ✅
**Boundaries Defined**: ✅
**Contracts Explicit**: ✅
**Risks Documented**: ✅
**Ready for Implementation**: ✅

---

**Architect**: AI Assistant
**Date**: 2025-11-12
**Next Review**: After Stage 21_02 prototype

---

*Handoff complete. Tech Lead, please acknowledge receipt and kick off Stage 21_02.*
