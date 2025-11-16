# Legacy Refactor Cluster D · LLM Clients & Map-Reduce Summarizer

## 1. Metadata
| Field | Value |
| --- | --- |
| Cluster | D |
| Scope | LLM client adapters, map-reduce summarizer |
| Epic | EP23 (sub-epic) |
| Tech Lead | cursor_tech_lead_v1 |
| Date | 2025-11-16 |
| References | `legacy_refactor_proposal.md` §Cluster D, `docs/operational/observability_labels.md`, `challenge_days_gap_closure_plan.md`, TL plan |

## 2. Objectives
1. Ввести единый интерфейс `LLMClient` с чёткими методами (`generate`, `chat`, и т.д.) и конфигурацией URL через settings.
2. Переписать map-reduce summarizer так, чтобы `_summarize_chunk` принимал структурированный объект и не ломал тесты.
3. Обновить тесты для клиентов и summarizer’а, убрав хардкоды URL/keyword mismatches.

## 3. Challenge Day Impact
- **Day 4 (Temperature)** – стабилизированный клиент позволяет демонстрировать разные профили без правок infra.
- **Day 5 (Model variants)** – отчёты используют единый интерфейс для сравнения моделей.
- **Day 6 (CoT)** – map-reduce summarizer участвует в примерах CoT vs non-CoT.
- **Day 20–21 (RAG & rerank)** – единый LLM клиент облегчает измерение вариативности и reranking метрик.

## 4. Stages
| Stage | Цель | Owner | Duration | Dependencies | Evidence |
| --- | --- | --- | --- | --- | --- |
| TL-00 | Дизайн интерфейсов | Tech Lead + Architect | 1d | Cluster B TL-01 (SummarizerService spec) | Interface proposal |
| TL-01 | Settings + Client Protocol | Dev C | 2d | TL-00 | `LLMClientProtocol`, settings diff |
| TL-02 | Map-Reduce refactor | Dev C + Dev B | 2d | TL-01 | Summarizer code diff |
| TL-03 | Tests & adapters | QA | 2d | TL-02 | Updated tests, coverage |
| TL-04 | Docs & Observability tie-in | Tech Lead | 1d | TL-03 | Docs, challenge plan updates |

## 5. Stage Details
### TL-00 · Interface Design
- Draft interface (Protocol/dataclass) for LLM client operations.
- Decide configuration layout (`settings.llm.base_url`, suffixes).
- Outline map-reduce data structures.
- Align with Cluster B SummarizerService to avoid duplicate abstractions.

### TL-01 · Client Protocol & Settings
- Add `LLMClientProtocol` + `LLMClientConfig`.
- Update `settings.py` to include `LLMSettings(base_url: HttpUrl, chat_path: str, generate_path: str, timeout: int, ...)`.
- Refactor existing clients (`MistralClient` etc.) to implement interface.
- Provide factory `llm_client_factory(config)` for DI.

### TL-02 · Map-Reduce Refactor
- Create dataclass `ChunkSummaryParams`.
- Update `MapReduceSummarizer` to accept protocol + params dataclass.
- Remove positional kwarg mismatches; add docstrings.
- Ensure summarizer can be injected into `SummarizerService`.

### TL-03 · Tests & Adapters
- Update `tests/llm/test_llm_client.py` to mock protocol, not raw HTTP.
- Update `tests/unit/infrastructure/llm/summarizers/test_map_reduce_summarizer.py` to use new params.
- Add regression tests for old bugs (URL mismatch, unexpected kwargs).
- Ensure coverage ≥ previous level; include negative cases (HTTP error, chunk failure).

### TL-04 · Docs & Observability
- Document LLM settings in `docs/guides/en/config_llm_clients.md`.
- Update `docs/challenge_days.md` (Days 4,5,6) referencing stabilized summarizer pipeline.
- Update `work_log.md` (Cluster D section) + acceptance matrix.

## 6. Acceptance Matrix
See `legacy_cluster_d_acceptance_matrix.md`.

## 7. Risks / Notes
- Dependent on Cluster B for SummarizerService integration; coordinate merges.
- Ensure no direct references from domain to infrastructure (interfaces live in domain/application).
- Prepare migration guide for any scripts referencing old clients (update CLI/backoffice).
