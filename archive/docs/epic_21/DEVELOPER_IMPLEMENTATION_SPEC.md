# Epic 21 · Developer Implementation Spec (Final)

Status: READY FOR DEVELOPMENT
Owners: Dev A (domain/app), Dev B (infra/cli), QA (tests), DevOps (metrics)

---

## 1) Decisions Snapshot (authoritative)

- Feature control: Single feature flag `enable_rag_plus_plus` (no canary; toggle only).
- LLM reranker temperature: 0.5 (balanced creativity). Prompts should be detailed.
- Determinism: No strict idempotency; minor variance acceptable at temp=0.5.
- Seed controls: not part of MVP; use env override `RAG_RERANK_TEMPERATURE` for debug.
- Metrics: seconds-based histograms/counters plus variance histogram.
- Rollback: Config-only (disable flag). Drill test required in integration suite.

---

## 2) Scope and Boundaries

- Domain/application/infra/presentation must follow Clean Architecture boundaries.
- Backward compatibility: provide wrapper for old `RetrievalService.retrieve(...)` signature until Stage 21_04.

---

## 3) Tasks by Layer (test-first)

### Domain (`src/domain/rag/`)
- Add protocols:
  - `RelevanceFilterService` (filter by threshold, O(n), pure)
  - `RerankerService` (async rerank, returns `RerankResult`)
- Add value objects with validation:
  - `FilterConfig` (threshold, top_k, flags/strategy)
  - `RerankResult` (chunks, scores map, strategy, latency_ms, optional reasoning)
- Unit tests (strict validation, edge cases):
  - `tests/unit/domain/rag/test_filter_config_validation.py`
  - `tests/unit/domain/rag/test_rerank_result_ordering.py`

### Application (`src/application/rag/`)
- Extend `RetrievalService.retrieve(query_text, query_vector, filter_config)`:
  - Headroom: fetch `top_k * 2`; apply threshold filtering; optional rerank; return ≤ `top_k`.
- Add compatibility wrapper that delegates to the new API using current settings.
- Update `CompareRagAnswersUseCase` to pass `query_text` + `FilterConfig`.
- Unit tests:
  - `test_retrieval_service_filtering.py`
  - `test_retrieval_service_reranking.py`
  - `test_reranking_fallback.py`

### Infrastructure (`src/infrastructure/rag/`)
- Implement adapters:
  - `threshold_filter_adapter.py` (pure threshold filter)
  - `llm_reranker_adapter.py` (prompt-based scoring; temp=0.5; timeout=3s; top-3 input)
- Prompts:
  - `src/infrastructure/rag/prompts/rerank_prompt.md` (detailed criteria, tie-breakers)
- Metrics (`src/infrastructure/metrics/rag_metrics.py`):
  - Histogram `rag_rerank_duration_seconds` (label: strategy)
  - Counter `rag_chunks_filtered_total` (label: category)
  - Histogram `rag_rerank_score_delta`
  - Counter `rag_reranker_fallback_total` (label: reason)
  - Histogram `rag_rerank_score_variance` (variance across chunks per run)
- Unit tests:
  - `test_threshold_filter_adapter.py`
  - `test_llm_reranker_adapter_prompt.py`
  - `test_llm_reranker_timeout.py`

### Presentation (CLI) (`src/presentation/cli/rag_commands.py`)
- Add CLI flags for compare/batch:
  - `--filter/--no-filter` (default off)
  - `--threshold FLOAT` (default from config; recommended 0.35)
  - `--reranker {off,llm,cross_encoder}` (default off)
- Map flags to `FilterConfig`; honor feature flag `enable_rag_plus_plus`.
- Smoke tests for CLI commands.

### Configuration
- YAML: `config/retrieval_rerank_config.yaml`:
  - `retrieval.top_k`, `retrieval.score_threshold`, `retrieval.vector_search_headroom_multiplier`
  - `reranker.enabled`, `reranker.strategy`, `reranker.llm.temperature: 0.5`, `temperature_override_env`
  - `feature_flags.enable_rag_plus_plus`
- `Settings` additions (if needed): ensure env fallback and precedence.
- Precedence: CLI > YAML > Env > Defaults.

---

## 4) File Paths to Add/Update

- Domain:
  - `src/domain/rag/interfaces.py` (add protocols)
  - `src/domain/rag/value_objects.py` (add `FilterConfig`, `RerankResult`)
- Application:
  - `src/application/rag/retrieval_service.py` (extend + wrapper)
- Infrastructure:
  - `src/infrastructure/rag/threshold_filter_adapter.py`
  - `src/infrastructure/rag/llm_reranker_adapter.py`
  - `src/infrastructure/rag/prompts/rerank_prompt.md`
  - `src/infrastructure/metrics/rag_metrics.py` (extend if exists)
- Presentation:
  - `src/presentation/cli/rag_commands.py` (flags + mapping)
- Config:
  - `config/retrieval_rerank_config.yaml` (new)

---

## 5) Testing Plan (pytest)

- Unit (domain/application/infra): add tests as listed above.
- Integration (`tests/integration/rag/`):
  - `test_rag_plus_plus_e2e.py` (mock index + LLM stub)
  - `test_three_modes_comparison.py` (Baseline ≠ RAG ≠ RAG++)
  - `test_rerank_latency.py` (p95 <5s dialog mode)
  - `test_feature_flag_rollback.py` (rollback drill)
- Markers: `contract`, `integration`, `smoke`, `observability`, `security` (reuse where applicable).
- Coverage: ≥80% overall; prefer diff coverage ≥90% on changed files.

Suggested commands:
```bash
make format && make lint
pytest -q --maxfail=1 --disable-warnings --cov=src --cov-report=xml:reports/ep21/21_03/coverage.xml
pytest tests/unit/domain -q
pytest tests/integration/rag -q --junitxml=reports/ep21/21_03/integration.xml
```

---

## 6) Metrics & Observability

- Implement and export:
  - `rag_rerank_duration_seconds{strategy}` — Histogram
  - `rag_chunks_filtered_total{category}` — Counter
  - `rag_rerank_score_delta` — Histogram
  - `rag_reranker_fallback_total{reason}` — Counter
  - `rag_rerank_score_variance` — Histogram
- Logging: structured, truncate query text to 50 chars, no PII.

---

## 7) Feature Flag & Rollback

- Flag: `enable_rag_plus_plus` (single toggle; default false).
- Rollback plan (config-only, SLA <5m):
  1) Set `enable_rag_plus_plus=false`, 2) Reload, 3) Verify metrics back to baseline.
- Integration test must simulate enable → disable and check mode + metrics.

---

## 8) Acceptance Criteria (evidence mapping)

- Modes: Baseline, RAG, RAG++ produce different outputs.
- Filtering removes chunks below threshold; Rerank reorders candidates.
- Latency: dialog p95 <5s (RAG++ mode).
- CLI flags control filter/reranker behavior.
- Metrics exported: duration, chunks_filtered, scores_delta, fallback, variance.
- Coverage ≥80%; tests pass including rollback drill.
- MADR updated with defaults (threshold/reranker strategy).
- For experiments use temperature override (`RAG_RERANK_TEMPERATURE`); seed control deferred.

Artifacts:
- `reports/ep21/21_03/coverage.xml`
- `reports/ep21/21_03/integration.xml`
- `reports/ep21/21_03/slo.json` (latency snapshot)
- `reports/ep21/21_03/observability.xml` (if applicable)

---

## 9) CI Gates (minimum)

| Step | Tool | Gate | Evidence |
|---|---|---|---|
| Format/Lint | black, isort, flake8 | 0 errors | lint logs |
| Types | mypy --strict | 0 errors | mypy.txt |
| Unit | pytest+cov | ≥80% | coverage.xml |
| Contract | pytest (domain) | 100% pass | contract.xml |
| Integration | pytest | 100% pass | integration.xml |
| Security | bandit, safety | No high/critical | bandit.xml, safety.txt |
| Smoke | pytest -m smoke | 100% pass | smoke.xml |

---

## 10) Developer Notes

- TDD: write tests first per contract docs.
- Docstrings + type hints required for all public APIs.
- Keep functions ≤15 lines where practical; split modules >150 lines.
- Do not import from outer layers into inner layers.
- Use constructor injection and pass protocols, not concrete classes.

---

## 11) Runbook Snippets (local)

```bash
# Configure flag off (default)
export ENABLE_RAG_PLUS_PLUS=false

# Optional: override temperature for experiments
export RAG_RERANK_TEMPERATURE=0.5

# Run single compare
poetry run python -m src.presentation.cli.backoffice.main rag compare --question "Что такое MapReduce?"

# Batch
poetry run python -m src.presentation.cli.backoffice.main rag batch \
  --queries docs/specs/epic_20/queries.jsonl \
  --out results_ep21.jsonl
```

---

## 12) Cross-References

- `docs/specs/epic_21/ARCHITECTURE_VISION.md`
- `docs/specs/epic_21/INTERFACES_CONTRACTS.md`
- `docs/specs/epic_21/HANDOFF_TO_TECH_LEAD.md`
