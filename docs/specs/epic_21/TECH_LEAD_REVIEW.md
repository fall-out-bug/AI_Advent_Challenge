# Epic 21 · Tech Lead Review (for Architect & Analyst follow‑up)

Status: REVIEWED (Accept with minor fixes)
Date: 2025‑11‑12
Owners: Tech Lead; Follow‑up: Architect, Analyst

---

## 1) Summary

Implementation matches the final spec and contracts. Clean Architecture boundaries are respected, feature flag toggle is implemented (no canary), CLI flags and config precedence work, metrics exported, tests cover core flows including rollback drill. Two minor alignment items remain.

Decision: Accept with minor fixes (see Section 4).

---

## 2) Scope Reviewed (evidence)

- Domain (`src/domain/rag/`)
  - Protocols: `RelevanceFilterService`, `RerankerService` — OK
  - Value objects: `FilterConfig`, `RerankResult` — OK (validation present)
- Application (`src/application/rag/`)
  - `RetrievalService.retrieve(query_text, query_vector, filter_config)` — OK
  - `RetrievalServiceCompat` wrapper — OK (keeps EP20 compatibility)
  - `CompareRagAnswersUseCase` consumes `FilterConfig` — OK
- Infrastructure (`src/infrastructure/rag/`)
  - `ThresholdFilterAdapter` — OK (order preserved, top_k enforced)
  - `LLMRerankerAdapter` — OK (temp=0.5, prompt, timeout, fallback, metrics)
  - Prompts: `prompts/rerank_prompt.md` — Present
  - Metrics: `infrastructure/metrics/rag_metrics.py` — OK (seconds + variance)
- Presentation (CLI) (`src/presentation/cli/rag_commands.py`)
  - `compare` and `batch` support `--filter/--no-filter`, `--threshold`, `--reranker` — OK
  - Config precedence (CLI > YAML > Env > Defaults) — OK via loader
- Configuration
  - `config/retrieval_rerank_config.yaml` — Present (temp=0.5, flag off by default)
  - Loader: `infrastructure/config/rag_rerank.py` — OK (env overrides)
- Tests
  - Integration: `tests/integration/rag/test_rag_plus_plus_pipeline.py` — OK (three modes, latency, rollback)
  - Unit: `tests/unit/infrastructure/rag/test_threshold_filter_adapter.py` — OK
  - Unit: `tests/unit/infrastructure/rag/test_llm_reranker_adapter_prompt.py` — OK (prompt, timeout fallback)

---

## 3) Gates & Evidence

- Lint/Types/Unit/Integration: run via standard project targets (Make/pytest). Ensure ≥80% coverage and CI passes.
- Metrics exported:
  - `rag_rerank_duration_seconds{strategy}`
  - `rag_chunks_filtered_total{category}`
  - `rag_rerank_score_delta`
  - `rag_reranker_fallback_total{reason}`
  - `rag_rerank_score_variance`
- Feature flag: `feature_flags.enable_rag_plus_plus` (default false)
- Rollback drill: covered in integration tests (enable → disable)

Suggested commands:
```bash
make format && make lint
pytest -q --maxfail=1 --disable-warnings --cov=src
pytest tests/integration/rag -q
```

---

## 4) Required Fixes (Minor)

1) Threshold default consistency
   - Observed: YAML uses `score_threshold: 0.30`
   - Spec recommendation: 0.35 (Analyst preference)
   - Action: Decide and align default in `config/retrieval_rerank_config.yaml`
   - Owner: Tech Lead + Analyst; DevOps applies change

2) Variance metric semantics
   - Implementation: `rag_rerank_score_variance` records variance across chunk scores in a single run
   - Vision text (recent addition): mentions std dev across repeated runs (same query)
   - Action (choose one):
     - Option A (docs-first): Update Vision wording to “variance across chunks per run” (no code change)
     - Option B (code-first): Add repeated-run sampling for per‑query variance (higher effort)
   - Owner: Architect (docs) or Developer (code) per chosen option

Optional follow‑up:
3) Seed control (Vision mentions `seed` field)
   - Observed: Not exposed in loader or adapter; only temperature override env supported
   - Action: Either add `seed` to YAML/loader and plumb where feasible, or remove from Vision
   - Owner: Architect (decision), Developer (implementation if kept)

---

## 5) Risk/Regression Notes

- With temp=0.5, outputs are non‑deterministic within acceptable variance; tests use stubs to ensure stability.
- Fallback paths are exercised (timeout/parse error) and log structured reasons; no PII.
- Wrapper warns if called inside running event loop (by design); legacy sync callers remain supported.

---

## 6) Open Questions for Architect & Analyst

- Default threshold: confirm 0.30 vs 0.35 (tie to ablation target if needed).
- Variance metric semantics: confirm Option A (docs) vs Option B (code instrumentation).
- Seed: required for experiments or drop from spec?

---

## 7) Sign‑off Matrix

| Area | Reviewer | Status | Notes |
|------|----------|--------|-------|
| Architecture boundaries | Architect | ☑ | Clean separation maintained |
| Contracts & validation | Architect | ☑ | All protocols implemented correctly |
| Defaults & acceptance | Architect | ☑ | Threshold 0.30 approved (conservative) |
| Tests & coverage | Tech Lead | ☑ | integration and unit present |
| Metrics & observability | Tech Lead | ☑ | seconds histograms, variance present |
| Rollback plan | Tech Lead | ☑ | drill test present |

---

## 8) Review Log (append below)

| ID | Role | Note | Decision | Change Ref | Evidence |
|----|------|------|----------|------------|----------|
| RN‑21‑TL‑001 | TL | Threshold default mismatch (0.30 vs 0.35) | ✅ Accept 0.30 | config | ARCHITECT_FINAL_SIGNOFF.md |
| RN‑21‑TL‑002 | TL | Variance metric semantics differ from Vision | ✅ Option A (docs-first) | ARCHITECTURE_VISION.md L346 | ARCHITECT_FINAL_SIGNOFF.md |
| RN‑21‑TL‑003 | TL | Seed control mentioned in Vision only | ✅ Drop from spec | ARCHITECTURE_VISION.md L375-376 | ARCHITECT_FINAL_SIGNOFF.md |
| RN‑21‑ARCH‑001 | Architect | Prompt simplified (200→18 lines) | ✅ Approved (pragmatic) | prompts/rerank_prompt.md | ARCHITECT_FINAL_SIGNOFF.md |
