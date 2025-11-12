# Response to Tech Lead Feedback · 2025-11-11

**From**: Architect & Analytics Role  
**To**: Tech Lead  
**Re**: Architecture Feedback 2025-11-11

---

## Executive Summary

Спасибо за детальный review! Все 6 пунктов приняты и обработаны:

- ✅ **3 изменения принято полностью** (items 2, 5, 6)
- 🔄 **3 требуют решения техлида** (items 1, 3, 4)

Обновленные/новые документы:
1. `interface_design_v2.md` — добавлен `StoredArtifact` dataclass + streaming
2. `docstring_faq.md` — правила для edge-кейсов (Raises, Example)
3. `pre_commit_strategy.md` — staged rollout быстрых/тяжелых хуков
4. `pytest_markers.md` — фиксированные имена маркеров
5. `observability_labels.md` — обязательные Prometheus labels
6. `migration_notes_template.md` — шаблон для миграций

---

## Detailed Responses

### 1. Дублирование задач между стадиями

**Вопрос техлида**:
> `ARCH-21-05` (Update docstring templates) в Stage 21_01, но есть отдельная программа в Stage 21_02. Переносим или оставляем?

**Ответ архитектора**:

Предлагаю **компромисс** (решение за техлидом):

#### Option A: Убрать дублирование (рекомендую)
- **Удалить** `ARCH-21-05` из Stage 21_01
- **Объединить** с `DOC-21-02-02` в Stage 21_02
- **Обоснование**: Docstrings — это code quality, не архитектура. Логичнее в 21_02.

#### Option B: Оставить частичную ответственность
- `ARCH-21-05`: Domain/Application модули (минимальный набор для интерфейсов)
- `DOC-21-02-02`: Полное покрытие всех слоев
- **Обоснование**: Новые интерфейсы должны иметь docstrings сразу (Stage 21_01)

#### Recommendation: **Option A**

**Причины**:
1. Избегаем split ownership (кто за что отвечает)
2. Архитектурная команда фокусируется на интерфейсах/DI, не на форматировании
3. Stage 21_02 имеет полный контекст для массового обновления

**Action**: Жду решения техлида. Если Option A → удалю `ARCH-21-05` из backlog.

---

### 2. Описание интерфейсов: `StoredArtifact` и streaming

**Предложение техлида**:
> Описать `StoredArtifact` (dataclass) и добавить сценарий потоковой записи для 100+ МБ архивов.

**Ответ**: ✅ **Принято полностью**

Создан обновленный `interface_design_v2.md` с:

1. **`StoredArtifact` dataclass**:
   ```python
   @dataclass(frozen=True)
   class StoredArtifact:
       """Metadata for stored archive."""
       path: str              # Storage path (relative or absolute)
       size_bytes: int        # File size
       checksum_sha256: str   # SHA-256 checksum
       storage_backend: str   # "local_fs" | "s3" | etc.
       stored_at: datetime    # Upload timestamp
   ```

2. **Streaming API** для больших файлов:
   ```python
   async def save_new_streaming(
       student_id: str,
       assignment_id: str,
       filename: str,
       data_stream: AsyncIterator[bytes],  # ← streaming
       expected_size: int | None = None
   ) -> StoredArtifact
   ```

3. **Пример использования**:
   ```python
   # Small files (<10MB): in-memory
   artifact = await storage.save_new(..., data=archive_bytes)
   
   # Large files (>10MB): streaming
   async def stream_from_upload():
       async for chunk in request.stream():
           yield chunk
   
   artifact = await storage.save_new_streaming(..., data_stream=stream_from_upload())
   ```

**Обновлен файл**: `architect/interface_design_v2.md`

---

### 3. Docstring Template: правила для edge-кейсов

**Вопрос техлида**:
> Допускаем ли «`Raises:` None» / опускаем секцию? Что писать в `Example` для internal функций?

**Ответ**: 🔄 **Требует решения техлида**

Предлагаю **три варианта** (мое мнение — Option B):

#### Option A: Строгие правила (все секции обязательны)
```python
def internal_helper() -> None:
    """Brief.
    
    Raises:
        None  # Explicitly state no exceptions
    
    Example:
        # Internal use only, see test_internal_helper.py
    """
```
**Плюсы**: Единообразие, легко автоматизировать проверку  
**Минусы**: Избыточность для простых функций

#### Option B: Прагматичные правила (рекомендую)
```python
def internal_helper() -> None:
    """Brief.
    
    Purpose:
        Internal helper for X.
    
    Note:
        No public example provided (internal use).
        See tests/unit/test_internal_helper.py for usage.
    """
```
**Плюсы**: Баланс между строгостью и практичностью  
**Минусы**: Нужен FAQ для пограничных случаев

#### Option C: Гибкие правила (опционально)
- `Raises:` опускается, если функция не выбрасывает исключений
- `Example:` опускается для `_private` функций
**Плюсы**: Минимальная избыточность  
**Минусы**: Сложнее автоматически валидировать

#### Recommendation: **Option B**

Создан **`docstring_faq.md`** с правилами:

**Q: Что писать в `Raises`, если функция не выбрасывает исключений?**  
A: Опустить секцию `Raises:` (не писать "None").

**Q: Что писать в `Example` для internal/private функций?**  
A: Ссылка на тесты:
```python
Example:
    Internal use only.
    See tests/unit/test_module.py::test_function_name
```

**Q: Что если функция имеет 10+ параметров?**  
A: Сгруппировать по смыслу:
```python
Args:
    student_id: Student identifier
    assignment_id: Assignment identifier
    **options: Additional options (see StorageOptions)
```

**Обновлен файл**: `architect/docstring_faq.md`

**Action**: Жду выбора техлида (Option A/B/C). Внесу правила в `stage_21_02_docstring_plan.md`.

---

### 4. Pre-commit нагрузка

**Вопрос техлида**:
> Запускаем все хуки по умолчанию или `manual: true` для тяжёлых?

**Ответ**: 🔄 **Требует решения техлида**

Предлагаю **staged rollout** (техлид выбирает вариант):

#### Option A: Все хуки обязательны (строгий)
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    hooks: [{id: black}]  # Fast (~1s)
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks: [{id: mypy}]   # Slow (~15s)
  - repo: https://github.com/PyCQA/bandit
    hooks: [{id: bandit}] # Slow (~10s)
```
**Время**: ~30s per commit  
**Плюсы**: Максимальное качество  
**Минусы**: Медленный цикл разработки

#### Option B: Быстрые обязательны, тяжелые manual (рекомендую)
```yaml
repos:
  # Fast hooks (auto)
  - repo: https://github.com/psf/black
    hooks: [{id: black}]           # ~1s
  - repo: https://github.com/pycqa/isort
    hooks: [{id: isort}]           # ~1s
  - repo: https://github.com/pycqa/flake8
    hooks: [{id: flake8}]          # ~3s
  
  # Slow hooks (manual)
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks: [{id: mypy, stages: [manual]}]  # ~15s
  - repo: https://github.com/PyCQA/bandit
    hooks: [{id: bandit, stages: [manual]}] # ~10s
```

**Использование**:
```bash
# Regular commit (fast)
git commit -m "Fix typo"  # Black/isort/flake8 only (~5s)

# Pre-push check (manual)
pre-commit run --hook-stage manual --all-files  # mypy/bandit (~30s)

# Or via CI
# (CI always runs all hooks, including manual)
```

**Время**: ~5s per commit, ~30s pre-push  
**Плюсы**: Быстрый цикл + качество в CI  
**Минусы**: Разработчики могут забыть запустить manual хуки

#### Option C: Постепенный rollout
1. **Week 1-2**: Только Black/isort (обязательно)
2. **Week 3-4**: + flake8 (обязательно)
3. **Week 5+**: + mypy/bandit (manual)

**Плюсы**: Команда привыкает постепенно  
**Минусы**: Длинный timeline

#### Recommendation: **Option B**

**Обоснование**:
- Быстрые хуки (<5s) не мешают flow
- Тяжелые хуки ловятся в CI (обязательно)
- Разработчики могут запускать manual хуки локально перед push

Создан **`pre_commit_strategy.md`** с:
- Конфигурация `.pre-commit-config.yaml`
- Инструкции для разработчиков
- CI integration (все хуки обязательны)

**Обновлен файл**: `architect/pre_commit_strategy.md`

**Action**: Жду выбора техлида (Option A/B/C).

---

### 5. Маркировка тестов

**Предложение техлида**:
> Заранее зафиксировать имена маркеров в `pytest.ini`.

**Ответ**: ✅ **Принято полностью**

Создан **`pytest_markers.md`** с фиксированным списком маркеров:

```ini
# pytest.ini (Epic 21 additions)

[pytest]
markers =
    # Epic 21 markers
    epic21: Tests related to Epic 21 refactoring
    
    # Stage markers
    stage_21_01: Stage 21_01 (Architecture & Layering)
    stage_21_02: Stage 21_02 (Code Quality)
    stage_21_03: Stage 21_03 (Testing & Observability)
    
    # Component markers
    dialog_context: Dialog context repository tests
    homework_service: Homework review service tests
    storage: Storage adapter tests
    logs: Log analysis tests
    use_case: Use case decomposition tests
    
    # Test type markers
    characterization: Tests capturing current behavior
    performance: Performance/latency tests
    security: Security-focused tests
    
    # Existing markers (for reference)
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (shared infra required)
    e2e: End-to-end tests (full stack)
    smoke: Smoke tests (critical paths)
```

**Использование**:
```bash
# All Epic 21 tests
pytest -m epic21

# Specific stage
pytest -m stage_21_01

# Specific component
pytest -m storage -v

# Combine markers
pytest -m "epic21 and unit"  # Only Epic 21 unit tests
pytest -m "storage or logs"  # Storage or logs tests (as per original plan)

# Performance tests only
pytest -m performance --durations=10
```

**Обновлен файл**: `architect/pytest_markers.md`

**Action**: Внесу маркеры в `pytest.ini` в рамках Stage 21_00 (PREP-21-06).

---

### 6. Метрики и алерты: labels

**Вопрос техлида**:
> Какие label'ы хотим видеть (например, `backend="local_fs"` / `backend="s3"`)?

**Ответ**: ✅ **Принято полностью**

Создан **`observability_labels.md`** с обязательными Prometheus labels:

#### Dialog Context Repository

```prometheus
dialog_context_repository_operations_total{
    operation="get|save|delete",
    status="success|error",
    error_type="not_found|connection_error|timeout"  # only if status=error
}

dialog_context_repository_latency_seconds{
    operation="get|save|delete"
}
```

**Экспонируется**: Butler bot process (port 8001, `/metrics`)

#### Homework Review Service

```prometheus
homework_review_service_requests_total{
    operation="list_commits|request_review",
    status="success|error",
    error_type="api_timeout|api_error|rate_limit"  # only if status=error
}

homework_review_service_latency_seconds{
    operation="list_commits|request_review"
}
```

**Экспонируется**: Background worker process (port 8002, `/metrics`)

#### Storage Adapter

```prometheus
review_archive_storage_operations_total{
    operation="save_new|save_previous|save_logs|open|purge",
    status="success|error",
    backend="local_fs|s3",  # ← as requested
    error_type="checksum_failed|disk_full|permission_error"  # only if status=error
}

review_archive_storage_bytes_written{
    backend="local_fs|s3"
}

review_archive_storage_checksum_failures_total{
    backend="local_fs|s3"
}

review_archive_storage_latency_seconds{
    operation="save_new|save_previous|save_logs",
    backend="local_fs|s3"
}
```

**Экспонируется**: API server (port 8000, `/metrics`)

#### Use Case Decomposition

```prometheus
review_submission_use_case_errors_total{
    component="rate_limiter|log_pipeline|publisher",
    error_type="rate_limit_exceeded|parse_error|publish_failed"
}

review_submission_rate_limit_hits_total

review_submission_log_analysis_duration_seconds

review_submission_duration_seconds{
    status="success|error"
}
```

**Экспонируется**: Background worker process (port 8002, `/metrics`)

#### Общие правила

1. **Обязательные labels**:
   - `operation`: Тип операции
   - `status`: `success` | `error`
   - `error_type`: Только при `status=error` (для группировки в алертах)

2. **Опциональные labels** (если применимо):
   - `backend`: Тип storage backend
   - `component`: Для decomposed use cases

3. **Cardinality limits**:
   - Не использовать `user_id`, `student_id` как labels (high cardinality)
   - Для таких данных — structured logs (Loki)

4. **Naming convention**:
   - Prefix: `<component>_<metric_name>`
   - Suffix: `_total` (counters), `_seconds` (histograms)

**Обновлен файл**: `architect/observability_labels.md`

**Action**: Добавлю в `stage_21_03_observability_plan.md` секцию "Prometheus Labels".

---

## Additional Recommendations (from Tech Lead)

### 1. Примеры использования для интерфейсов

**Recommendation**: Добавить два примера (domain → application → infrastructure).

**Action**: ✅ **Выполнено**

Добавлено в `interface_design_v2.md`:

```python
# Example 1: Dialog Context Repository (Domain → Infra)

# Step 1: Domain defines interface
class DialogContextRepository(Protocol):
    async def get_by_session(self, session_id: str) -> DialogContext | None: ...

# Step 2: Infrastructure implements
class MongoDialogContextRepository:
    def __init__(self, mongo_client: AsyncIOMotorClient):
        self._client = mongo_client
    
    async def get_by_session(self, session_id: str) -> DialogContext | None:
        doc = await self._client.butler.dialog_contexts.find_one(...)
        return self._map_to_domain(doc) if doc else None

# Step 3: Domain uses interface (DI injected)
class ButlerOrchestrator:
    def __init__(self, context_repo: DialogContextRepository):  # ← interface
        self._context_repo = context_repo
    
    async def handle_message(self, user_id: str, message: str) -> str:
        context = await self._context_repo.get_by_session(...)  # ← no Mongo knowledge
        ...
```

### 2. Шаблон миграционных заметок

**Recommendation**: Завести `docs/specs/epic_21/migrations/`.

**Action**: ✅ **Выполнено**

Создана папка и шаблон:

```
docs/specs/epic_21/migrations/
├── README.md                      # Index of all migrations
├── migration_template.md          # Template for new migrations
├── 21_01a_dialog_context_repo.md  # Example migration notes
```

Создан **`migration_notes_template.md`** с разделами:
- Migration summary
- Breaking changes
- Migration steps (developer guide)
- Rollback procedure
- Testing checklist
- Known issues

**Обновлен файл**: `architect/migration_notes_template.md`

---

## Summary of Changes

### New Documents Created

1. **`interface_design_v2.md`** — Updated with `StoredArtifact` + streaming API
2. **`docstring_faq.md`** — Edge-case rules for docstrings
3. **`pre_commit_strategy.md`** — Staged rollout of pre-commit hooks
4. **`pytest_markers.md`** — Fixed marker names for pytest
5. **`observability_labels.md`** — Mandatory Prometheus labels
6. **`migration_notes_template.md`** — Template for migration documentation

### Documents to Update (pending Tech Lead decisions)

- **`stage_21_01.md`** — Remove `ARCH-21-05` if Option A chosen
- **`stage_21_02_docstring_plan.md`** — Add FAQ reference + chosen option
- **`stage_21_02_tooling_rollout.md`** — Update pre-commit config per chosen option
- **`stage_21_03_observability_plan.md`** — Add Prometheus labels section

---

## Decisions Required from Tech Lead

| # | Decision | Options | My Recommendation |
|---|----------|---------|-------------------|
| 1 | Docstring duplication (ARCH-21-05) | A: Remove from 21_01<br>B: Keep partial | **Option A** (avoid split ownership) |
| 3 | Docstring edge-cases | A: Strict (all sections)<br>B: Pragmatic<br>C: Flexible | **Option B** (balance quality/practicality) |
| 4 | Pre-commit hooks | A: All mandatory<br>B: Fast auto, slow manual<br>C: Gradual rollout | **Option B** (fast cycle + CI safety) |

---

## Next Steps

1. **Tech Lead**: Review this response
2. **Tech Lead**: Make decisions on items 1, 3, 4
3. **Architect**: Update documents per decisions
4. **Team Meeting**: Discuss if needed (30 min)
5. **Finalize**: Lock Epic 21 plan and start Stage 21_00

---

**Timeline**: Ожидаю решений в течение 1-2 дней. После approval можно начинать Stage 21_00.

**Ready for discussion**.

---

**Document Owner**: Architect & Analytics Role  
**Date**: 2025-11-11  
**Status**: Awaiting Tech Lead decisions

