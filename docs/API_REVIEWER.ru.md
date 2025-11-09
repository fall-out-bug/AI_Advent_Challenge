# Модульный ревьюер — API (RU)

## 1. Область применения

Модульный ревьюер — основная реализация автоматической проверки кода.
Его можно вызывать из:

- Службы приложения (`ModularReviewService.review_submission`)
- MCP-инструмента проверки домашек
- Фоновых воркеров (Unified Task Worker)
- Ручных скриптов или CLI-утилит

Документ описывает точку интеграции, входные/выходные контракты и метрики.

## 2. Контракт сервисного слоя

Файл: `src/application/services/modular_review_service.py`

### Сигнатура

```python
await ModularReviewService.review_submission(
    new_archive: SubmissionArchive,
    previous_archive: SubmissionArchive | None,
    assignment_id: str,
    student_id: str,
) -> MultiPassReport
```

### Входные данные

- `new_archive`: распакованные файлы (`SubmissionArchive.code_files`)
- `previous_archive`: опциональный архив предыдущей попытки
- `assignment_id`: идентификатор задания
- `student_id`: идентификатор студента

Внутри сервис:

1. Адаптирует архив и LLM-клиент под интерфейсы пакета.
2. Собирает `ReviewConfig` через `ReviewConfigBuilder`.
3. Запускает `MultiPassReviewerAgent.review_from_archives`.
4. Конвертирует пакетный отчёт в `MultiPassReport`.
5. Сохраняет результат и публикует метрики.

### Выход (`MultiPassReport`)

Определение: `src/domain/models/code_review_models.py`.

```python
@dataclass(slots=True)
class MultiPassReport:
    assignment_id: str | None
    student_id: str | None
    passes: list[PassFindings]
    summary: str
    errors: list[dict[str, Any]]
    created_at: datetime
```

Каждый `PassFindings` содержит:

- `name`: имя прохода (`architecture`, `components`, `synthesis`)
- `status`: `"completed"` или `"failed"`
- `summary`: краткое описание (по умолчанию RU)
- `findings`: список замечаний
- `error`: сообщение об ошибке (если есть)

### Обработка ошибок

- Частичные ошибки → `status="failed"` только у конкретного прохода, отчёт остаётся валидным.
- Критические ошибки бросают `ReviewSubmissionError` и помечают задачу как failed.
- Все события логируются с `trace_id`.

## 3. MCP-инструмент проверки домашек

Файл: `src/presentation/mcp/tools/homework_review_tool.py`

### Имя инструмента

`review_homework_archive`

### Параметры

| Поле | Тип | Описание |
|------|-----|----------|
| `archive_path` | `str` | Путь к загруженному ZIP |
| `assignment_id` | `str` | Идентификатор задания |
| `student_id` | `str` | Идентификатор студента |
| `language` | `str` | Язык программирования (по умолчанию `"python"`) |
| `previous_archive_path` | `str` | Опциональный путь к прошлому архиву |

### Ответ

```json
{
  "status": "success",
  "report": {
    "summary": "...",
    "passes": [
      {
        "name": "architecture",
        "status": "completed",
        "summary": "...",
        "findings": [
          {"severity": "warning", "title": "...", "details": "..."}
        ]
      }
    ],
    "errors": []
  }
}
```

При ошибке:

```json
{
  "status": "error",
  "error": "Причина ошибки"
}
```

### Поведение

- Использует `ZipArchiveService` (валидирует пути, защищает от zip-бомб).
- Вызывает `ModularReviewService` с боевыми настройками.
- Логирует события с `trace_id`.
- Возвращает статус/ошибки по каждому проходу.

## 4. Наблюдаемость

### Метрики

Модуль `multipass_reviewer.infrastructure.monitoring.metrics` экспортирует:

- `multipass_checker_findings_total{checker,severity}`
- `multipass_checker_runtime_seconds{checker}`
- `multipass_pass_runtime_seconds{pass_name}`
- `multipass_llm_tokens_total{model,direction}`
- `multipass_llm_latency_seconds{model}`

Адаптер `src/infrastructure/monitoring/checker_metrics.py` агрегирует результаты на уровне приложения.

### Логирование

`ReviewLogger` пишет:

- `trace_id`
- статус проходов, время выполнения, количество findings
- метаинформацию по LLM-запросам

Получить записи можно через `ReviewLogger.get_all_logs()`.

## 5. Feature flags и настройки

| Настройка | Значение по умолчанию | Назначение |
|-----------|-----------------------|------------|
| `USE_MODULAR_REVIEWER` | `True` | Переключение между модульной и легаси реализацией |
| `review_rate_limit_*` | см. `settings.py` | Ограничения по студенту и заданию |
| `llm_model`, `llm_timeout` | значения из Settings | Алиас модели и таймаут HTTP |
| `allowed_archive_globs` | список из Settings | Допустимые шаблоны файлов при извлечении |

Конфигурация управляется через `src/infrastructure/config/settings.py` (Pydantic Settings).

## 6. Пример использования (скрипт)

```python
from src.application.services.modular_review_service import ModularReviewService
from src.infrastructure.archive.archive_service import ZipArchiveService
from src.infrastructure.diff.diff_analyzer import DiffAnalyzer
from shared.shared_package.clients.unified_client import UnifiedModelClient
from src.infrastructure.logging.review_logger import ReviewLogger

archive_service = ZipArchiveService()
diff_analyzer = DiffAnalyzer()
llm_client = UnifiedModelClient(timeout=120.0)
review_logger = ReviewLogger()

service = ModularReviewService(
    archive_service=archive_service,
    diff_analyzer=diff_analyzer,
    llm_client=llm_client,
    review_logger=review_logger,
)

report = await service.review_submission(
    new_archive="/tmp/submissions/new.zip",
    previous_archive=None,
    assignment_id="HW2",
    student_id="student123",
)

print(report.summary)
```

## 7. Что дальше

- Использовать CLI backoffice (в разработке) для ручных запусков.
- Сверяться с `docs/USER_GUIDE.md` (бенчмарки и troubleshooting).
- Для англоязычной версии см. `docs/API_REVIEWER.md`.

