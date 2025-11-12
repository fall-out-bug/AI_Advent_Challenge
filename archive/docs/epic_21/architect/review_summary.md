# Epic 21 · Architecture Review Summary

**Для**: Tech Lead  
**От**: Architect & Analytics Role  
**Дата**: 2025-11-11  
**Статус**: 🟡 Требует критических доработок перед началом

---

## TL;DR (Executive Summary)

Epic 21 — **хороший план** по рефакторингу архитектуры, но **не готов к реализации** без доработок:

### ✅ Что хорошо:
- Правильная архитектурная цель (Clean Architecture + интерфейсы)
- Детальный dependency audit с примерами нарушений
- Alignment matrix связывает проблемы со спецификациями

### 🔴 Критические проблемы (блокеры):
1. **Нарушение TDD**: тесты идут ПОСЛЕ рефакторинга (нарушает repo rules)
2. **Нет deployment/rollback стратегии**: невозможно безопасно развернуть в production
3. **Слишком широкий scope** Stage 21_01: 4 компонента меняются параллельно (высокий риск)

### 🟡 Серьезные замечания:
4. DI strategy не детализирована (нет примеров wiring)
5. Monitoring metrics не специфицированы
6. Performance regression risk не учтен
7. Отсутствуют архитектурные диаграммы

---

## Критика и рекомендации

### 1. TDD Violation (🔴 БЛОКЕР)

**Проблема**:
```
Текущий план:
Stage 21_01 (Architecture) → Stage 21_02 (Quality) → Stage 21_03 (Tests)
                                                       ^^^^^^^^^^^^
                                                       Тесты в КОНЦЕ!
```

**Repo rules говорят**:
> Write tests first, then the implementation (red-green-refactor).

**Решение**:
- Добавить **characterization tests** перед каждым ARCH-* таском
- Структура: `ARCH-21-01a: Тесты → ARCH-21-01b: Интерфейс → ARCH-21-01c: Миграция`
- Создан документ: `testing_strategy.md` с test-first approach

**Action Item**: Обновить Stage 21_01 backlog с тестами в начале каждой задачи.

---

### 2. Deployment Strategy (🔴 БЛОКЕР)

**Проблема**:
- Нет feature flags для постепенного включения изменений
- Нет rollback procedures если что-то сломается
- Не учтены deployment windows из operations.md (Saturday 02:00-06:00 UTC)

**Решение**:
- **Создан Stage 21_00 (Preparation)**:
  - Feature flags: `USE_NEW_DIALOG_CONTEXT_REPO`, etc. (все `false` по умолчанию)
  - Rollback план по каждому stage
  - Baseline metrics для сравнения
- **Создан документ**: `rollback_plan.md` с пошаговыми процедурами
- **Создан документ**: `deployment_checklist.md` по шаблону operations.md

**Action Item**: Начать Epic 21 с Stage 21_00, не с 21_01.

---

### 3. Stage 21_01 Scope (🔴 БЛОКЕР)

**Проблема**:
ARCH-21-01..04 затрагивают 4 критичных компонента **одновременно**:
- ButlerOrchestrator (dialog contexts)
- HomeworkHandler (hw checker)
- ReviewRoutes (file storage)  ← самый рискованный
- ReviewSubmissionUseCase (orchestration)

**Риск**: Если ломается один → сложно изолировать причину.

**Решение**:
Разбить Stage 21_01 на **sub-stages** (последовательно):
```
21_01a: Dialog Context Repository (1 week) — низкий риск, изолирован
21_01b: Homework Review Service (1 week) — низкий риск, external API
21_01c: Storage Abstraction (2 weeks) — HIGH RISK, security-sensitive
21_01d: Use Case Decomposition (1 week) — зависит от 21_01c
```

**Action Item**: Обновить epic_21.md и stage_21_01.md с sub-stages.

---

### 4. DI Strategy (🟡 Важно)

**Проблема**:
Упоминается "DI container", но нет:
- Конкретной технологии (manual vs dependency-injector?)
- Примеров wiring (как presentation слой получает интерфейсы?)

**Решение**:
Рекомендую **manual DI** (проще для проекта такого размера):

```python
# src/infrastructure/di/container.py
class DIContainer:
    @cached_property
    def dialog_context_repo(self) -> DialogContextRepository:
        if settings.USE_NEW_DIALOG_CONTEXT_REPO:
            return MongoDialogContextRepository(...)
        return LegacyMongoAdapter(...)  # backward compat

# src/presentation/api/routes.py
@router.post("/dialog")
async def handle_dialog(container: DIContainer = Depends(get_container)):
    orchestrator = container.butler_orchestrator  # ← injected
    ...
```

**Action Item**: Добавить wiring примеры в `stage_21_01_interface_design.md`.

---

### 5. Monitoring Metrics (🟡 Важно)

**Проблема**:
OBS-21-03 упоминает "refresh Prometheus/Grafana", но **не специфицированы новые метрики**.

**Решение**:
Добавить в Stage 21_03:
```prometheus
# Dialog Context Repository
dialog_context_repository_operations_total{operation, status}
dialog_context_repository_latency_seconds{operation}

# Storage Adapter
review_archive_storage_checksum_failures_total
review_archive_storage_operations_total{operation, status}

# Use Case
review_submission_rate_limit_hits_total
```

**Action Item**: Добавить секцию "New Metrics" в `stage_21_03_observability_plan.md`.

---

### 6. Performance Risk (🟡 Важно)

**Проблема**:
DI + interface layers могут добавить latency. MCP tools имеют строгие SLOs (operations.md):
- Tool discovery: 1.50s
- Dialog handling: текущий baseline <100ms

**Решение**:
- Добавить performance tests в TEST-21-01:
  ```python
  @pytest.mark.performance
  async def test_dialog_context_repo_latency(repo):
      start = time.perf_counter()
      await repo.get_by_session("test")
      assert (time.perf_counter() - start) < 0.1  # <100ms
  ```
- Benchmark до/после каждого stage

**Action Item**: Добавить performance tests в `testing_strategy.md` (уже сделано).

---

### 7. Architecture Diagrams (🟡 Желательно)

**Проблема**:
Exit criteria Stage 21_01 упоминает "dependency diagram", но его нет.

**Решение**:
Создан `architecture_diagrams.md` с Mermaid диаграммами:
- Current state (violations)
- Target state (Clean Architecture)
- Migration path (stage-by-stage)
- Component interactions (sequence diagrams)

**Action Item**: Включить диаграммы в Stage 21_01 deliverables.

---

## Созданные документы

В папке `docs/specs/epic_21/architect/`:

### Критичные (must-have перед стартом):
1. **`stage_21_00_preparation.md`** — новый stage для подготовки
2. **`rollback_plan.md`** — процедуры отката по каждому stage
3. **`testing_strategy.md`** — test-first approach, characterization tests
4. **`deployment_checklist.md`** — пошаговый чеклист по шаблону operations.md

### Важные (should-have):
5. **`architecture_diagrams.md`** — Mermaid диаграммы (current/target/migration)
6. **`architecture_review.md`** — полный анализ (этот документ детальный)

### Дополнительные:
7. **`review_summary.md`** — этот документ (краткая версия для техлида)

---

## Что делать дальше?

### Шаг 1: Критические правки (2-3 дня)

- [ ] **Принять Stage 21_00** как первый этап (из `stage_21_00_preparation.md`)
- [ ] **Разбить Stage 21_01** на sub-stages (21_01a..d последовательно)
- [ ] **Обновить backlog** с test-first задачами перед каждым ARCH-*
- [ ] **Добавить wiring примеры** в interface_design.md

### Шаг 2: Важные дополнения (1-2 дня)

- [ ] **Специфицировать metrics** в stage_21_03_observability_plan.md
- [ ] **Добавить performance tests** в TEST-21-01
- [ ] **Включить диаграммы** в Stage 21_01 deliverables

### Шаг 3: Валидация

- [ ] **Ревью обновленного плана** с DevOps, QA, Security
- [ ] **Kickoff meeting** с командой
- [ ] **Начать Stage 21_00** (preparation)

---

## Revised Timeline

```
Оригинальный план: 6 недель
Stage 21_01 → 21_02 → 21_03

Рекомендуемый план: 9 недель
Week 1:  Stage 21_00 (Preparation)
Week 2:  Stage 21_01a (Dialog Context Repo)
Week 3:  Stage 21_01b (Homework Review Service)
Week 4-5: Stage 21_01c (Storage Abstraction) — 2 недели, high risk
Week 6:  Stage 21_01d (Use Case Decomposition)
Week 7-9: Stage 21_02 (Quality) — параллельно с тестами из 21_01

Stage 21_03 (Guardrails) — параллельно с 21_01/21_02, не отдельный этап
```

**Rationale**: Test-first + sub-stages + preparation добавляет 3 недели, но **драматически снижает риск**.

---

## Acceptance Criteria для Epic 21 (обновленные)

### Оригинальные (из epic_21.md):
- ✅ All modules respect Clean Architecture import rules
- ✅ Public functions/classes comply with docstring template
- ✅ Critical workflows have ≥80% coverage
- ✅ Security/ops guidelines reflected in config

### Добавленные (из архитектурного ревью):
- ✅ **Feature flags** для всех новых интерфейсов (контролируемый rollout)
- ✅ **Characterization tests** перед каждым рефакторингом (TDD compliance)
- ✅ **Rollback drill** выполнен в staging перед каждым production deploy
- ✅ **Performance benchmarks** до/после (latency не увеличилась)
- ✅ **Monitoring dashboards** обновлены с новыми метриками
- ✅ **Architecture diagrams** отражают target state

---

## Сравнение с предыдущими Epic

### Patterns to follow (из Epic 01-06):

| Epic | Best Practice | Применимо к Epic 21? |
|------|--------------|----------------------|
| EP01 | Feature flag inventory | ✅ Добавлено в Stage 21_00 |
| EP01 | Rollout checklist | ✅ Создан deployment_checklist.md |
| EP03 | Risk register | ⚠️ Нужно добавить в epic_21.md |
| EP03 | SLO recommendations | ✅ Покрыто в testing_strategy (performance tests) |
| EP04 | Communication plan | ⚠️ Нужно добавить (stakeholder notifications) |
| EP04 | Signoff log | ⚠️ Нужно добавить (approval tracking) |

### Missing from Epic 21 (consider adding):

- **Communication plan** (когда/как уведомлять stakeholders)
- **Risk register** (centralized risk tracking like Epic 03)
- **Signoff log** (approval tracking like Epic 04)

---

## Final Verdict

### 🟡 Conditional Approval

Epic 21 **architecturally sound**, но **operationally incomplete**.

**Можно начинать ТОЛЬКО ПОСЛЕ**:
1. ✅ Stage 21_00 создан с feature flags + rollback plan
2. ✅ Stage 21_01 разбит на sub-stages с test-first approach
3. ✅ DI strategy уточнена с примерами wiring
4. ✅ Monitoring metrics специфицированы

**Estimated Effort**: 2-3 дня на критические правки.

**Risk Assessment**:
- **Before fixes**: 🔴 High risk (TDD violation, no rollback, wide scope)
- **After fixes**: 🟡 Medium risk (controlled rollout, test-first, monitoring)

---

## Questions for Tech Lead

1. **DI Approach**: Manual factories или dependency-injector library?
   - **Recommendation**: Manual (проще для проекта)

2. **Stage 21_01 Sequencing**: Параллельные sub-stages или последовательные?
   - **Recommendation**: Последовательные (21_01a → 21_01b → 21_01c → 21_01d)

3. **Test Coverage Target**: 80% или 85%?
   - **Recommendation**: 85% для refactored modules (высокая критичность)

4. **Deployment Windows**: Можем ли забронировать 4 окна (по одному на sub-stage)?
   - **Recommendation**: Да, каждую субботу 02:00-06:00 UTC

---

## Next Steps

1. **Tech Lead**: Прочитать этот summary
2. **Tech Lead**: Ревью детальных документов в `architect/` (опционально)
3. **Team Meeting**: Обсудить критические правки (1 hour)
4. **Action Items**: Назначить owner'ов на Stage 21_00 tasks
5. **Kickoff**: Начать Stage 21_00 после approval

---

**Готов обсудить любые вопросы по плану.**

**Контакты**: Architect & Analytics Role  
**Review Date**: 2025-11-11  
**Next Check-in**: После Stage 21_00 completion

