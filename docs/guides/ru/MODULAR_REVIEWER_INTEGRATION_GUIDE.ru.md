# Руководство по интеграции модульного ревьюера

Документ описывает, как подключить переиспользуемый пакет `multipass-reviewer`
к существующему проекту с архитектурой Clean Architecture и общей инфраструктурой
AI Challenge.

## 1. Установка

### Вариант A. Зависимость по относительному пути (monorepo)

1. Скопируйте `packages/multipass-reviewer/` в свой репозиторий (или добавьте как git submodule).
2. Дополните `pyproject.toml`:

```toml
[tool.poetry.dependencies]
multipass-reviewer = { path = "packages/multipass-reviewer", develop = true }
```

3. Выполните `poetry install`.

### Вариант B. Git-зависимость

Если пакет опубликован в git-репозитории (тег `v0.3.0`):

```toml
[tool.poetry.dependencies]
multipass-reviewer = { git = "https://example.com/multipass-reviewer.git", tag = "v0.3.0" }
```

Далее запустите `poetry install`.

Пакет требует Python 3.10+, `httpx 0.27` и `prometheus-client 0.20`. Poetry подтянет зависимости автоматически.

### Срез Stage 01_03 (релиз 0.3.0)

- Включены строгие lint/type-gate (flake8 + mypy) для критичных модулей ревьюера.
- Интеграционные и модульные тесты покрывают ≥94% пакета и ≥90% shared SDK.
- Модульный ревьюер активен всегда: флаг `use_modular_reviewer` удалён.

## 2. Переменные окружения

```bash
MONGODB_URL=mongodb://admin:<password>@shared-mongo:27017/butler?authSource=admin
LLM_URL=http://llm-api:8000
LLM_MODEL=qwen
PROMETHEUS_URL=http://shared-prometheus:9090
```

- `LLM_MODEL` — короткий алиас (`qwen`, `mistral` и т.п.). Длинные имена тоже поддерживаются, но алиасы упрощают валидацию.
- Начиная с версии `0.3.0` модульный ревьюер включён постоянно; дополнительных флагов не требуется.

## 3. Подключение сервиса

В приложении создайте адаптеры по примеру `src/application/services/modular_review_service.py`:

```python
from multipass_reviewer.application.config import ReviewConfigBuilder
from multipass_reviewer.application.orchestrator import MultiPassReviewerAgent
from multipass_reviewer.domain.interfaces.archive_reader import ArchiveReader
from multipass_reviewer.domain.interfaces.llm_client import LLMClientProtocol
from multipass_reviewer.domain.interfaces.review_logger import ReviewLoggerProtocol


class ZipArchiveAdapter(ArchiveReader):
    def __init__(self, archive_service):
        self._archive_service = archive_service

    async def read_latest(self, archive_path: str, *_a, **_kw):
        submission = self._archive_service.extract_submission(archive_path, "sub")
        return submission.code_files


class LLMClientAdapter(LLMClientProtocol):
    def __init__(self, client: LLMClientProtocol, default_model: str) -> None:
        self._client = client
        self._default = default_model.lower().split(" ")[0].split("-")[0]

    async def make_request(self, model_name: str, prompt: str, **kwargs):
        model = self._default if model_name == "summary" else model_name
        return await self._client.make_request(model, prompt, **kwargs)


class ModularReviewService:
    def __init__(self, archive_service, diff_analyzer, llm_client, review_logger):
        settings = get_settings()
        archive_adapter = ZipArchiveAdapter(archive_service)
        llm_adapter = LLMClientAdapter(llm_client, settings.llm_model)
        config = (
            ReviewConfigBuilder()
            .with_language("python")
            .with_static_analysis(["linter", "type_checker"])
            .enable_haiku()
            .build()
        )
        self._reviewer = MultiPassReviewerAgent(
            archive_reader=archive_adapter,
            llm_client=llm_adapter,
            logger=review_logger,
            config=config,
        )

    async def review_submission(self, new_archive, previous_archive, assignment_id, student_id):
        report = await self._reviewer.review_from_archives(
            new_archive_path=new_archive,
            previous_archive_path=previous_archive,
            assignment_id=assignment_id,
            student_id=student_id,
        )
        return report
```

### Ключевые моменты

- Используйте адаптеры для преобразования инфраструктурных сервисов в интерфейсы пакета.
- `ReviewLogger` из AI Challenge поддерживает `trace_id` для корреляции логов и метрик.
- Метрики Prometheus экспонируются модулем `multipass_reviewer.infrastructure.monitoring.metrics`.

## 4. Ошибки и метрики

- Каждая ревью-проходка возвращает статус/ошибку в `PassFindings`. Сохраняйте эти поля в отчётах.
- Ретраи с экспоненциальной задержкой реализованы через Tenacity. См. логи по `trace_id`.
- Для записи метрик используйте `observe_pass` (см. `src/infrastructure/monitoring/checker_metrics.py`).

## 5. Тесты

Повторно используйте тесты AI Challenge:

```bash
poetry run pytest tests/integration/test_modular_review_service.py -v
poetry run pytest tests/unit/application/services/test_modular_review_service.py -v
```

Покрываются:
- успешный сценарий с фейковым LLM;
- кастомные конфигурации;
- совместимость с реальным LLM (можно пропустить, если `LLM_URL` не задан);
- негативные сценарии (ошибки архива/пакета).

## 6. Бенчмарки (опционально)

```bash
LLM_URL=http://127.0.0.1:8000 \
LLM_MODEL=qwen poetry run python - <<'PY'
# пример для измерения ModularReviewService.review_submission
PY
```

Последние измерения (Qwen/Qwen1.5-4B-Chat):
- Dummy LLM: ~0.00068s (3 прогона).
- Реальный LLM `/v1/chat/completions`: ~4.08s (5 прогонов).

## 7. Чек-лист интеграции

1. Добавить зависимость (`path` или `git tag`).
2. Подключить адаптеры (`ArchiveReader`, `LLMClient`, `ReviewLogger`).
3. Настроить окружение (`MONGODB_URL`, `LLM_URL`, `LLM_MODEL`, Prometheus).
4. Запустить unit/integration тесты.
5. (Опционально) Измерить производительность и настроить мониторинг.
