# Legacy Refactor Cluster C · Butler Orchestrator & MCP-Aware Agent

## 1. Metadata
| Field | Value |
| --- | --- |
| Cluster | C |
| Scope | Butler orchestrator, MCP-aware agent, metrics alignment |
| Epic | EP23 (sub-epic) |
| Tech Lead | cursor_tech_lead_v1 |
| Date | 2025-11-16 |
| References | `legacy_refactor_proposal.md` §Cluster C, observability docs, `challenge_days_gap_closure_plan.md`, TL plan |

## 2. Objectives
1. Определить стабильный публичный API для `MCPAwareAgent` и `ButlerOrchestrator`; скрыть внутренние хелперы.
2. Добавить адаптер для legacy тестов при необходимости (без нарушения слоёв).
3. Синхронизировать метрики MCP-блоков с `docs/operational/observability_labels.md`.
4. Переписать тесты так, чтобы они использовали публичные интерфейсы и актуальные метрики.

## 3. Challenge Day Impact
- **Day 14 (Project analysis):** Multipass reviewer и Butler оркестратор станут основой официального walkthrough; доки будут ссылаться на стабилизированный API.
- **Day 18 (Real-world task):** Обновлённый Butler описывает реальное наблюдаемое задание (EP23), помогая закрыть рассказ для дня 18.
- **Day 22 (Citations context):** Метрики MCP/observability используются в новых примерах, поэтому labels должны строго соответствовать `observability_labels.md`.

## 4. Stages
| Stage | Цель | Owner | Duration | Dependencies | Evidence |
| --- | --- | --- | --- | --- | --- |
| TL-00 | API дизайн + inventory | Tech Lead + Architect | 1d | Cluster D (LLM interface) | API doc |
| TL-01 | Orchestrator/agent refactor | Dev F | 3d | TL-00 | Code diff, DI updates |
| TL-02 | Legacy adapter (если нужен) | Dev F | 1d | TL-01 | Adapter module |
| TL-03 | Metrics & tests | QA + Dev G | 2d | TL-02 | Updated tests, metrics |
| TL-04 | Docs + Challenge Days | Tech Lead | 1d | TL-03 | Doc diff, worklog |

## 5. Stage Details
### TL-00 · API Definition
- Document allowed methods (e.g., `run`, `handle_message`, `resolve_intent`) and mark internal ones as private.
- Identify tests touching private attributes; plan migration.
- Align FSM transitions with architecture doc.

### TL-01 · Core Refactor
- Rename/move internal helpers, ensure orchestrator + agent expose minimal surface.
- Inject dependencies via constructors (no global singletons).
- Update MCP metrics emission to use new helper that enforces label schema.

### TL-02 · Legacy Adapter (optional)
- Implement thin adapter `LegacyButlerAdapter` (if tests/users rely on old methods).
- Adapter translates old method names to new API; marked deprecated.
- Update tests referencing removed methods to use adapter temporarily.

### TL-03 · Metrics & Tests
- Update `tests/domain/agents/test_mcp_aware_agent*.py`, `tests/integration/butler/test_*` to use new API.
- Update metric assertions (labels, names) to match TL-04 instrumentation.
- Ensure no test pokes private attributes.

### TL-04 · Documentation & Challenge Days
- Document orchestrator API (short guide or update existing doc).
- Update `docs/challenge_days.md` Day 14 (project analysis) and Day 18 (real-world flow) referencing new orchestrator behaviour.
- Update work_log + acceptance matrix.

## 6. Acceptance Matrix
`legacy_cluster_c_acceptance_matrix.md`

## 7. Risks
- Ensure adapter doesn’t leak infrastructure details into domain.
- Keep orchestrator state machine documented to avoid regressions; consider sequence diagram for review.

