# Review System Architecture & Infrastructure Integration

## Архитектурные принципы

Система code review полностью интегрирована в существующую инфраструктуру:

1. **Единая очередь задач**: Используется `LongTasksRepository` с поддержкой типов (SUMMARIZATION, CODE_REVIEW)
2. **Единый worker**: `SummaryWorker` обрабатывает оба типа задач
3. **Производственная система review**: Используется `MultiPassReviewerAgent` (5 стадий: 3 passes + статический анализ + Pass 4 логов)
4. **Правильные границы слоев**: Domain не импортирует infrastructure (dependency injection)

## Как работают E2E тесты

### Тесты без Worker

**Почему тесты вызывают use cases напрямую?**

E2E тесты проверяют **бизнес-логику**, а не инфраструктуру worker'а. Это стандартная практика:

1. **Worker** - это инфраструктурный слой (polling, graceful shutdown, метрики)
2. **Use Cases** - это бизнес-логика (extract → diff → multi-pass review → save)
3. Тестируем use cases напрямую, чтобы:
   - Быстрее запускать тесты (нет polling delays)
   - Легче отлаживать (прямой вызов)
   - Тестировать логику независимо от worker'а

**В production:**
```
UnifiedTaskWorker → ReviewSubmissionUseCase.execute(task)
```

**В тестах:**
```
Test → ReviewSubmissionUseCase.execute(task)  # Тот же use case!
```

### Тесты с реальным LLM

**Почему используется UnifiedModelClient?**

1. **Переиспользование инфраструктуры**: UnifiedModelClient уже используется в MultiPassReviewerAgent
2. **Реальное тестирование**: E2E тесты проверяют реальную систему, включая LLM
3. **Требования**: LLM_URL должен быть настроен для E2E тестов

```python
# Переиспользуем существующую инфраструктуру
unified_client = UnifiedModelClient(timeout=settings.review_llm_timeout)
review_use_case = ReviewSubmissionUseCase(
    unified_client=unified_client,
    # ...
)
```

## Переиспользование инфраструктуры

### 1. Repository Pattern

**LongTasksRepository** используется для всех типов задач:

- `pick_next_queued(task_type=TaskType.CODE_REVIEW)` - фильтрация по типу
- `create()` - идемпотентность (как раньше)
- `get_queue_size(task_type=TaskType.CODE_REVIEW)` - для метрик

**Преимущества:**
- Единая кодовая база для всех асинхронных задач
- Единые индексы MongoDB
- Единые метрики

### 2. Worker Pattern

**SummaryWorker** обрабатывает оба типа задач:

```python
# summary_worker._process_long_tasks() - SUMMARIZATION
async def _process_long_tasks(self):
    task = await long_tasks_repo.pick_next_queued(task_type=TaskType.SUMMARIZATION)
    result = await process_use_case.execute(task)
    # метрики, логирование

# summary_worker._process_review_tasks() - CODE_REVIEW
async def _process_review_tasks(self):
    task = await long_tasks_repo.pick_next_queued(task_type=TaskType.CODE_REVIEW)
    result = await review_use_case.execute(task)
    # метрики, логирование
```

**Преимущества:**
- Единый worker для всех типов задач
- Единое управление жизненным циклом
- Единые метрики и логирование

### 3. MultiPassReviewerAgent

**Производственная система review** используется для всех review задач и включает:

- **Pass 1**: Architecture overview (детектирование компонентов, baseline)
- **Pass 2**: Component deep-dive (технологически-специфичный анализ)
- **Pass 3**: Synthesis and integration (рекомендации и интеграционные риски)
- **Static Analysis**: Запуск Flake8, Pylint, MyPy, Black, isort и агрегация результатов
- **Pass 4**: Log Analysis (группировка логов, LLM-диагностика, рекомендации)
- **Haiku + Publishing**: Автоматическое хайку и публикация через MCP tool call

**Интеграция с архивами:**
```python
report = await agent.review_from_archives(
    archive_reader=archive_service,
    diff_analyzer=diff_analyzer,
    new_archive_path=new_zip,
    previous_archive_path=old_zip,
    assignment_id="HW2",
    student_id="student123"
)
```

**Преимущества:**
- Используется существующая производственная система
- Высокое качество review (3-pass анализ)
- Переиспользование UnifiedModelClient и SessionManager

### 4. Существующие компоненты

**Что переиспользуется:**
- ✅ `LongTasksRepository` - единый репозиторий для всех задач
- ✅ `HomeworkReviewRepository` - существующий репозиторий для review sessions
- ✅ `MultiPassReviewerAgent` - производственная система review
- ✅ `UnifiedModelClient` - единый клиент для LLM
- ✅ `Settings` - существующая конфигурация
- ✅ `get_db()` - существующее подключение к MongoDB
- ✅ `ReviewLogger` - существующий логгер для review
- ✅ `TaskStatus`, `TaskType` - существующие enums
- ✅ `BaseWorker` - базовый класс для worker'ов

### 5. Day 17 компоненты

- ✅ `CodeQualityChecker` и адаптеры линтеров (Flake8, Pylint, MyPy, Black, isort) – результаты добавляются в `MultiPassReport.static_analysis_results`.
- ✅ `LogParserImpl` + `LogNormalizer` + `LLMLogAnalyzer` – полный pipeline Pass 4 с фильтрацией по уровню, группировкой и LLM-диагностикой.
- ✅ `MCPHTTPClient` – HTTP-клиент для вызова внешнего MCP-инструмента `submit_review_result`.
- ✅ `ExternalAPIClient` – fallback-публикатор, если MCP недоступен или отключён.
- ✅ Новые настройки: `hw_checker_mcp_url`, `hw_checker_mcp_enabled`, расширенные таймауты лог-аналитики.
- ✅ Автоматическая генерация хайку (позитивный fallback при ошибках LLM).
- ✅ Контрактные тесты для OpenAPI/JSON Schema, проверяющие обязательное поле `new_commit` и новые разделы отчёта.

## Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                    E2E Tests                            │
│  (вызывают use cases напрямую, без worker'а)          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│          ReviewSubmissionUseCase                        │
│  (бизнес-логика: extract → diff → multi-pass → save)  │
│  → использует MultiPassReviewerAgent                    │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│        UnifiedTaskWorker (SummaryWorker)                │
│  (polling, graceful shutdown, метрики)                 │
│  → вызывает ReviewSubmissionUseCase.execute()         │
│  → обрабатывает SUMMARIZATION и CODE_REVIEW            │
└─────────────────────────────────────────────────────────┘
```

## Docker Compose Integration

### Unified Task Worker

```yaml
unified-task-worker:
  build:
    dockerfile: Dockerfile.worker
  command: ["python", "-m", "src.workers"]
  environment:
    - LLM_URL=http://mistral-chat:8000
    - EXTERNAL_API_URL=${EXTERNAL_API_URL:-}
    - EXTERNAL_API_ENABLED=${EXTERNAL_API_ENABLED:-false}
    - HW_CHECKER_MCP_URL=${HW_CHECKER_MCP_URL:-http://mcp-server:8005}
    - HW_CHECKER_MCP_ENABLED=${HW_CHECKER_MCP_ENABLED:-true}
  volumes:
    - ./review_archives:/app/review_archives:ro
  networks:
    - butler-network
    - ai-challenge-network  # For external API
```

### MCP Server (Review API)

Review API интегрирован в `mcp-server`:

```yaml
mcp-server:
  ports:
    - "8004:8004"  # Review API на /api/v1/reviews
  environment:
    - EXTERNAL_API_URL=${EXTERNAL_API_URL:-}
    - REVIEW_LLM_TIMEOUT=${REVIEW_LLM_TIMEOUT:-120}
  volumes:
    - ./review_archives:/app/review_archives:ro
```

## MCP publishing flow

1. **LLM tool call**: Посредством `MCPHTTPClient` use case обнаруживает `submit_review_result` и запрашивает у LLM корректные аргументы (student_id, submission_hash, review_content, session_id, overall_score).
2. **Execution**: MCP возвращает статус публикации; при успехе в логах фиксируется `Published review via MCP tool`.
3. **Fallback**: Любая ошибка → `ExternalAPIClient.publish_review(payload)`; payload включает `new_commit`, `session_id`, агрегированный скор.
4. **Telemetry**: В отчёт сохраняются оба пути (успешный MCP или fallback) и полное тело отправленного сообщения.

## Выводы

1. **Единая инфраструктура**: Все задачи используют LongTasksRepository и SummaryWorker
2. **Производственная система**: MultiPassReviewerAgent используется для всех review
3. **Правильные границы**: Domain не импортирует infrastructure (dependency injection)
4. **Переиспользование**: Максимальное использование существующих компонентов
5. **Нет дублей**: Удалены все дублирующие репозитории, workers, use cases
6. **Day 17 улучшения**: Статический анализ, Pass 4 логов и MCP-публикация встроены в production-пайплайн
