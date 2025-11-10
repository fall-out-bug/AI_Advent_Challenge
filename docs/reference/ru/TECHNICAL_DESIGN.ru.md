# Техническая документация проекта AI Challenge

Версия: 1.0 • Дата: 2025-11-07

Документ объединяет системный дизайн, архитектуру сервисов, потоки данных, практики production-ready и операционные процедуры. Все примеры и контракты сверены с текущим репозиторием, `docker-compose.butler.yml`, и исходниками в `src/`.

## 1. System Design Document

### 1.1. Функциональные требования
- Прием заявок на код-ревью через REST API:
  - POST `/api/v1/reviews` — multipart загрузка архивов (новый код, предыдущий код, логи) с метаданными (`student_id`, `assignment_id`, `new_commit`, `old_commit?`).
  - GET `/api/v1/reviews/{task_id}` — получение статуса и результата.
- Асинхронная обработка задач:
  - Очередь в MongoDB (`LongTasksRepository`).
  - `unified-task-worker` обрабатывает SUMMARIZATION и CODE_REVIEW.
- Производственный пайплайн ревью:
  - `MultiPassReviewerAgent`: Pass 1..3, статический анализ, Pass 4 (анализ логов), публикация через MCP или fallback External API.
- Интеграции:
  - MCP HTTP сервер (инструмент `submit_review_result`).
  - LLM (Mistral) для классификации/анализа/суммаризации.
  - Telegram Butler Bot (диалоговый слой, FSM, MCP-вызовы).

### 1.2. Нефункциональные требования
- Архитектура: Clean Architecture, DDD, строгие границы слоев.
- Наблюдаемость: Prometheus + Grafana, метрики сервисов.
- Надежность: healthchecks, ретраи, идемпотентность репозиториев.
- Производительность: таймауты LLM/HTTP, лимиты архивов, асинхронность.
- Конфигурация: env + Pydantic Settings, безопасные дефолты.
- Тестирование: pytest, покрытие ≥80%, юнит/интеграционные/E2E.
- Безопасность: секреты через env/secret store; не логировать чувствительные данные.

### 1.3. Масштабирование и отказоустойчивость
- Горизонтальное масштабирование статeless-компонентов:
  - API (`mcp-server` FastAPI), Butler Bot, `unified-task-worker` (за счет конкуренции воркеров).
  - Модель Mistral — отдельное масштабирование/шардинг, лимит CPU/GPU.
- База данных:
  - MongoDB — replica set в проде, резервные копии, мониторинг.
  - Очередь задач на Mongo — поллинг с backoff, минимальные блокировки.
- Надежность:
  - Healthchecks во всех контейнерах.
  - Retry/timeout для LLM и внешних API (см. Settings).
  - Fallback для публикации (MCP → External API).
- Наблюдаемость:
  - Экспорт метрик `/metrics` (Prometheus), дашборды Grafana.

### 1.4. Стратегия восстановления (Disaster Recovery)
- Данные:
  - Регулярные бэкапы MongoDB (с проверкой восстановления).
  - Хранение `review_archives/` (в проде — объектное хранилище, версионирование).
- Секреты: восстановление из секрет-хранилища (Vault/AWS SM).
- Инфраструктура:
  - Образы контейнеров — зафиксированные версии, возможность roll-back по тэгам.
  - IaC/compose манифесты под версионированием.
- Процедуры DR:
  - Остановка сервисов → восстановление БД → восстановление артефактов → запуск сервисов → валидация (health, smoke-тесты, дашборды, ошибки 5xx < порога).

## 2. Service Architecture

### 2.1. Диаграмма зависимостей сервисов

```
┌───────────────┐      ┌───────────┐
│  butler-bot   │──┐   │ grafana   │
└──────┬────────┘  │   └────┬──────┘
       │            │        │
       │            │   ┌────▼──────┐
       │            └──▶│prometheus │
       │                └────┬──────┘
       │                     │
┌──────▼────────┐       ┌────▼──────────┐
│  mcp-server   │◀──────│ mistral-chat │
└──────┬────────┘       └───────────────┘
       │
  ┌────▼──────────────┐
  │ unified-task-worker│
  └────┬──────────────┘
       │
  ┌────▼──────┐
  │ mongodb   │
  └───────────┘

Сети: `butler-network` (внутренняя), `ai-challenge-network` (внешние интеграции)
```

### 2.2. API контракты (между компонентами)

- Code Review API (`mcp-server` → FastAPI):
  - POST `/api/v1/reviews` — создаёт задание на ревью.
  - GET `/api/v1/reviews/{task_id}` — статус/результат.

Пример (фрагмент OpenAPI):

```yaml
openapi: 3.0.3
paths:
  /api/v1/reviews:
    post:
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required: [student_id, assignment_id, new_commit, new_zip]
              properties:
                student_id: { type: string }
                assignment_id: { type: string }
                new_commit: { type: string, minLength: 1 }
                old_commit: { type: string, nullable: true }
                new_zip: { type: string, format: binary }
                old_zip: { type: string, format: binary, nullable: true }
                logs_zip: { type: string, format: binary, nullable: true }
```

Пример curl:

```bash
curl -X POST http://localhost:8004/api/v1/reviews \
  -F student_id=student_123 \
  -F assignment_id=HW2 \
  -F new_commit=abc123 \
  -F new_zip=@/path/new.zip \
  -F old_zip=@/path/old.zip \
  -F logs_zip=@/path/logs.zip
```

### 2.3. Конфигурация сервисов

Ключевые фрагменты `docker-compose.butler.yml`:

```yaml
services:
  mcp-server:
    environment:
      - MONGODB_URL=mongodb://mongodb:27017
      - DB_NAME=butler
      - LLM_URL=http://mistral-chat:8000
      - LOG_LEVEL=INFO
      - EXTERNAL_API_URL=${EXTERNAL_API_URL:-}
      - EXTERNAL_API_ENABLED=${EXTERNAL_API_ENABLED:-false}
      - HW_CHECKER_MCP_URL=${HW_CHECKER_MCP_URL:-http://mcp-server:8005}
      - HW_CHECKER_MCP_ENABLED=${HW_CHECKER_MCP_ENABLED:-true}
      - REVIEW_LLM_TIMEOUT=${REVIEW_LLM_TIMEOUT:-120}
      - ARCHIVE_MAX_TOTAL_SIZE_MB=${ARCHIVE_MAX_TOTAL_SIZE_MB:-100}

  butler-bot:
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - MONGODB_URL=mongodb://mongodb:27017
      - MISTRAL_API_URL=http://mistral-chat:8000
      - MCP_SERVER_URLS=${MCP_SERVER_URLS:-http://mcp-server:8004}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - METRICS_PORT=9091

  unified-task-worker:
    environment:
      - MCP_SERVER_URL=http://mcp-server:8004
      - LLM_URL=http://mistral-chat:8000
      - MONGODB_URL=mongodb://mongodb:27017
      - EXTERNAL_API_URL=${EXTERNAL_API_URL:-}
      - EXTERNAL_API_ENABLED=${EXTERNAL_API_ENABLED:-false}
      - REVIEW_WORKER_POLL_INTERVAL=${REVIEW_WORKER_POLL_INTERVAL:-5}
      - ARCHIVE_MAX_TOTAL_SIZE_MB=${ARCHIVE_MAX_TOTAL_SIZE_MB:-100}
```

Внутренние настройки (фрагменты `src/infrastructure/config/settings.py`):

```python
class Settings(BaseSettings):
    mongodb_url: str = Field(default="mongodb://localhost:27017")
    db_name: str = Field(default="butler")
    llm_url: str = Field(default="")
    archive_max_total_size_mb: int = Field(default=50)
    review_llm_timeout: float = Field(default=180.0)
    review_max_retries: int = Field(default=3)
    external_api_enabled: bool = Field(default=False)
    hw_checker_mcp_enabled: bool = Field(default=True)
    # ... валидаторы pydantic для числовых границ и доп. полей
```

## 3. Data Flow

### 3.1. Путь данных от источника до модели
1) Клиент вызывает API `POST /api/v1/reviews` c архивами и метаданными.
2) FastAPI сохраняет архивы в `review_archives/`, валидирует поля:

```python
# src/presentation/api/review_routes.py (фрагмент)
if not new_commit.strip():
    raise HTTPException(status_code=400, detail="new_commit cannot be empty")
if new_zip.size > max_archive_size_mb * 1024 * 1024:
    raise HTTPException(status_code=413, detail=f"new_zip exceeds size limit: {max_archive_size_mb}MB")
with open(new_submission_path, "wb") as f:
    content = await new_zip.read()
    f.write(content)
task = await enqueue_use_case.execute(...)
```

3) Use case ставит задание в очередь (`LongTasksRepository`).
4) `unified-task-worker` поллит очередь, обрабатывает:
   - Извлечение/дифф архивов, пропуская неразрешенные глобы (`Settings.archive_allowed_globs`).
   - `MultiPassReviewerAgent`:
     - Pass 1..3 — архитектура/компоненты/синтез.
     - Статический анализ — запуск линтеров, агрегация.
     - Pass 4 — анализ логов: нормализация/группировка/LLM-диагностика.
   - Публикация результата: MCP `submit_review_result` → fallback `ExternalAPIClient`.
5) Результаты сохраняются (review repo), статус обновляется; клиент читает `GET /api/v1/reviews/{task_id}`.

### 3.2. Трансформации на каждом этапе
- Валидация входа (формы/архивы, лимиты): HTTP 400/413.
- Файловые операции: запись архивов, контроль размера.
- Извлечение/фильтрация файлов по паттернам.
- Дифф двух версий архива.
- Нормализация логов, агрегация по severity/группам.
- Приведение результатов в контракт ответа (JSON, схемы OpenAPI/JSONSchema).

### 3.3. Валидация данных
- На уровне API: обязательные поля, `new_commit != ""`, лимит размера архива.
- На уровне Settings: строгие валидаторы pydantic (диапазоны, positivity):

```python
@field_validator("review_llm_timeout")
def validate_review_llm_timeout(cls, v: float) -> float:
    if v <= 0: raise ValueError("review_llm_timeout must be positive"); return v
```

- Контрактные тесты: OpenAPI/JSON Schema (см. `tests/contracts`).

## 4. Production Readiness

### 4.1. Логи и трейсинг
- Логи:
  - Python `logging` с уровнем из `LOG_LEVEL` (см. `docker-compose`, Settings).
  - Пример использования в API:

```python
logger = logging.getLogger(__name__)
logger.info(f"Saved new submission: {new_submission_path}")
logger.error("Failed to create review: %s", e, exc_info=True)
```

- Рекомендации для продакшена:
  - Единый формат (JSON) и агрегация (ELK/Loki).
  - Корреляция по `task_id`/`request_id` (middleware у FastAPI).

- Трейсинг (рекомендуется):
  - Интеграция OpenTelemetry для FastAPI и httpx:

```bash
pip install opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-httpx
```

```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

app = create_app()
FastAPIInstrumentor.instrument_app(app)
HTTPXClientInstrumentor().instrument()
```

Экспорт в OTLP/Tempo — по переменным окружения.

### 4.2. Стратегия масштабирования
- API (`mcp-server`) и Bot — статлесс, масштабируются горизонтально.
- Worker — увеличить количество реплик для пропускной способности.
- LLM (`mistral-chat`) — масштабирование/шардинг; следить за GPU/CPU.
- MongoDB — replica set, отдельный storage, индексы под запросы.
- Автоскейлинг по SLO: p95 latency, error rate, queue depth.

### 4.3. Обработка ошибок и fallbacks
- API коды: 400/413 для валидации, 500 — сбои.
- Retry/timeout для LLM/внешних API (см. Settings: `review_max_retries`, `review_llm_timeout`).
- Публикация результата: при ошибке MCP — `ExternalAPIClient` (fallback) c тем же payload (включая `new_commit`, `session_id`).

## 5. Операционные процедуры

### 5.1. Как запустить систему

Подготовка внешней сети (однократно):

```bash
docker network create ai-challenge-network
```

Запуск сервисов:

```bash
docker-compose -f docker-compose.butler.yml up -d
```

Для hot-reload в dev:

```bash
docker-compose -f docker-compose.butler.yml -f docker-compose.butler.dev.yml up -d
```

Проверки:

```bash
curl -f http://localhost:8004/health      # MCP/Review API
curl -f http://localhost:9090/-/healthy   # Prometheus
curl -f http://localhost:3000/api/health  # Grafana
```

### 5.2. Как добавить новый pipeline
- Domain/Application:
  - Добавить новый тип задачи (enum), use case и интеграцию в `unified-task-worker`.
  - Соблюдать Clean Architecture: интерфейсы в `domain`, реализации — в `infrastructure`.
- Presentation/API:
  - Добавить маршруты FastAPI (отдельный роутер), схемы запросов/ответов.
  - Контрактные тесты (`tests/contracts`) и интеграционные тесты.
- Конфигурация:
  - Новые поля в `Settings` + валидаторы + `docker-compose` env.
- Наблюдаемость:
  - Метрики (счетчики/гистограммы), дашборды/алерты.

### 5.3. Как мониторить здоровье системы
- Prometheus: http://localhost:9090 (targets, графы, запросы).
- Grafana: http://localhost:3000 (дашборды `app-health.json`, др.).
- Примеры PromQL:

```promql
sum(rate(http_requests_total[5m]))
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100
```

### 5.4. Rollback процедуры
- Быстрый откат Compose:
  - Переключить тэги образов на предыдущие версии → `docker-compose up -d`.
- Данные:
  - Остановить сервисы → восстановить Mongo из последнего валидного бэкапа → поднять сервисы → smoke-тест.
- Конфигурация:
  - Вернуть прошлый commit/ветку, восстановить `.env`/секреты.

## Приложения

### A. Пример `.env`

```bash
TELEGRAM_BOT_TOKEN=xxxx
MONGODB_URL=mongodb://mongodb:27017/butler
MISTRAL_API_URL=http://mistral-chat:8000
LOG_LEVEL=INFO
REVIEW_LLM_TIMEOUT=120
EXTERNAL_API_ENABLED=false
HW_CHECKER_MCP_ENABLED=true
ARCHIVE_MAX_TOTAL_SIZE_MB=100
```

### B. Пример запроса/ответа API

```bash
# Создать задание
curl -s -X POST http://localhost:8004/api/v1/reviews \
  -F student_id=student_123 -F assignment_id=HW2 -F new_commit=abc123 \
  -F new_zip=@/path/new.zip | jq .

# Получить статус
curl -s http://localhost:8004/api/v1/reviews/<task_id> | jq .
```

Пример ответа:

```json
{
  "task_id": "task_abc123",
  "status": "completed",
  "student_id": "student_123",
  "assignment_id": "HW2",
  "created_at": "2025-01-15T10:30:00Z",
  "finished_at": "2025-01-15T10:35:00Z",
  "result": { "overall_score": 4.5, "passes": { "pass4_logs": {"groups": 12} } }
}
```

### C. Чек-лист prod-ready
- [ ] HEALTH/metrics доступны, targets зелёные
- [ ] Ошибки 5xx < 1% за 15 минут
- [ ] p95 latency в SLA
- [ ] Бэкапы Mongo успешны, тест восстановления пройден за квартал
- [ ] Секреты вне репозитория, доступ ограничен
- [ ] Откат проверен на staging
