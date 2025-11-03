# HW Checker MCP API Documentation

## Обзор

HW Checker предоставляет REST API для интеграции с системой проверки домашних работ через Model Context Protocol (MCP). API позволяет запускать проверки, отслеживать их статус, просматривать историю и перезапускать проверки.

## Базовый URL

### Вне Docker (с хоста)
```
http://localhost:8005
```

### Из другого контейнера в ai-challenge-network
```
http://hw_checker-mcp-server-1:8005
```

**Примечание:** Сервер подключен к внешней сети `ai-challenge-network`, поэтому доступен из любых контейнеров в этой сети по имени хоста `hw_checker-mcp-server-1`.

## Аутентификация

Текущая версия API не требует аутентификации. В будущем может быть добавлена поддержка API ключей или OAuth.

## Endpoints

### 1. Health Check

**GET** `/health`

Проверка доступности сервера.

**Ответ:**
```json
{
  "status": "healthy"
}
```

**Пример:**
```bash
curl http://localhost:8005/health
```

---

### 2. Run Check (Запуск проверки)

**POST** `/api/run_check`

Запускает новую проверку домашней работы.

**Запрос:**
```json
{
  "student_id": "Иванов_Иван",
  "assignment": "HW2",
  "submission_url": "https://github.com/student/hw2_submission.zip",
  "timeout": 1800
}
```

**Параметры:**
- `student_id` (required): Идентификатор студента
- `assignment` (required): Название задания (HW2, HW3)
- `submission_url` (required): URL архива с решением
- `timeout` (optional): Таймаут в секундах (по умолчанию 1800)

**Ответ:**
```json
{
  "job_id": "mock_job_Иванов_Иван_HW2",
  "status": "queued",
  "progress": "Job received, will start processing soon"
}
```

**Пример:**
```bash
curl -X POST http://localhost:8005/api/run_check \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "Иванов_Иван",
    "assignment": "HW2",
    "submission_url": "https://example.com/submission.zip"
  }'
```

---

### 3. Check Status (Статус проверки)

**GET** `/api/check_status/{job_id}`

Получает текущий статус проверки.

**Параметры:**
- `job_id` (path): Уникальный идентификатор задачи

**Ответ:**
```json
{
  "job_id": "abc123",
  "status": "running",
  "progress": "In progress",
  "error_message": null,
  "student_id": "Иванов_Иван",
  "assignment": "HW2",
  "archive_name": "Иванов_Иван_hw2.zip",
  "enqueued_at": "2024-11-02T16:00:00Z",
  "started_at": "2024-11-02T16:01:00Z",
  "completed_at": null,
  "gdrive_link": null
}
```

**Возможные статусы:**
- `queued`: Ожидает запуска
- `running`: Выполняется
- `passed`: Успешно завершена
- `failed`: Не прошла проверку
- `error`: Ошибка при выполнении
- `timeout`: Превышен таймаут

**Пример:**
```bash
curl http://localhost:8005/api/check_status/abc123
```

---

### 4. All Checks Status (Все проверки)

**GET** `/api/all_checks_status`

Получает список всех проверок с опциональной фильтрацией.

**Параметры запроса:**
- `assignment` (optional): Фильтр по заданию (HW2, HW3)
- `limit` (optional): Максимальное количество результатов (по умолчанию 100)

**Ответ:**
```json
{
  "checks": [
    {
      "job_id": "abc123",
      "status": "passed",
      "progress": "Completed successfully",
      "student_id": "Иванов_Иван",
      "assignment": "HW2",
      "archive_name": "Иванов_Иван_hw2.zip",
      "completed_at": "2024-11-02T16:05:00Z"
    }
  ],
  "total": 1
}
```

**Пример:**
```bash
curl "http://localhost:8005/api/all_checks_status?assignment=HW2&limit=10"
```

---

### 5. Queue Status (Статус очереди)

**GET** `/api/queue_status`

Получает текущий статус очереди с подсчетом задач по статусам.

**Ответ:**
```json
{
  "total_count": 50,
  "queued_count": 2,
  "running_count": 1,
  "completed_count": 45,
  "failed_count": 2,
  "jobs": [
    {
      "job_id": "abc123",
      "status": "queued",
      "progress": "Waiting to start",
      "student_id": "Иванов_Иван",
      "assignment": "HW2"
    }
  ]
}
```

**Пример:**
```bash
curl http://localhost:8005/api/queue_status
```

---

### 6. Checks by Date (Проверки по дате)

**GET** `/api/checks_by_date`

Получает проверки за указанный период с поддержкой пагинации.

**Параметры запроса:**
- `start_date` (required): Начальная дата (YYYY-MM-DD или ISO8601)
- `end_date` (required): Конечная дата (YYYY-MM-DD или ISO8601)
- `assignment` (optional): Фильтр по заданию
- `limit` (optional): Количество результатов (по умолчанию 100)
- `offset` (optional): Смещение для пагинации (по умолчанию 0)

**Ответ:**
```json
{
  "start_date": "2024-11-02",
  "end_date": "2024-11-03",
  "assignment": null,
  "total_count": 15,
  "limit": 100,
  "offset": 0,
  "count": 15,
  "checks": [...]
}
```

**Пример:**
```bash
curl "http://localhost:8005/api/checks_by_date?start_date=2024-11-02&end_date=2024-11-03&limit=50"
```

---

### 7. Retry Check (Повторная проверка)

**POST** `/api/retry_check`

Перезапускает ранее выполненную проверку.

**Запрос:**
```json
{
  "job_id": "abc123",
  "assignment": "HW2"
}
```

или

```json
{
  "archive_name": "Иванов_Иван_hw2.zip",
  "assignment": "HW2"
}
```

или

```json
{
  "commit_hash": "a1b2c3d4",
  "assignment": "HW2"
}
```

**Параметры:**
- `job_id` (optional): ID существующей задачи
- `archive_name` (optional): Имя архива для повторной проверки
- `commit_hash` (optional): Хеш коммита для повторной проверки
- `assignment` (optional): Фильтр по заданию

**Ответ:**
```json
{
  "job_id": "abc123",
  "status": "queued",
  "message": "Job abc123 reset and queued for retry"
}
```

**Пример:**
```bash
curl -X POST http://localhost:8005/api/retry_check \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "abc123"
  }'
```

---

## Коды ошибок

- `400 Bad Request`: Неверные параметры запроса
- `404 Not Found`: Задача не найдена
- `500 Internal Server Error`: Внутренняя ошибка сервера
- `501 Not Implemented`: Функционал не доступен (например, база данных не настроена)

## Пример интеграции

### Python

```python
import requests

# Для доступа с хоста:
BASE_URL = "http://localhost:8005"

# Для доступа из контейнера в ai-challenge-network:
# BASE_URL = "http://hw_checker-mcp-server-1:8005"

# Запуск проверки
def run_check(student_id: str, assignment: str, submission_url: str):
    response = requests.post(
        f"{BASE_URL}/api/run_check",
        json={
            "student_id": student_id,
            "assignment": assignment,
            "submission_url": submission_url
        }
    )
    return response.json()

# Проверка статуса
def get_status(job_id: str):
    response = requests.get(f"{BASE_URL}/api/check_status/{job_id}")
    return response.json()

# Получение всех проверок
def get_all_checks(assignment: str = None):
    params = {}
    if assignment:
        params["assignment"] = assignment
    response = requests.get(f"{BASE_URL}/api/all_checks_status", params=params)
    return response.json()

# Использование
job = run_check("Иванов_Иван", "HW2", "https://example.com/submission.zip")
status = get_status(job["job_id"])
print(status)
```

### JavaScript/TypeScript

```typescript
// Для доступа с хоста:
const BASE_URL = "http://localhost:8005";

// Для доступа из контейнера в ai-challenge-network:
// const BASE_URL = "http://hw_checker-mcp-server-1:8005";

// Запуск проверки
async function runCheck(studentId: string, assignment: string, submissionUrl: string) {
  const response = await fetch(`${BASE_URL}/api/run_check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      student_id: studentId,
      assignment,
      submission_url: submissionUrl
    })
  });
  return await response.json();
}

// Проверка статуса
async function getStatus(jobId: string) {
  const response = await fetch(`${BASE_URL}/api/check_status/${jobId}`);
  return await response.json();
}

// Использование
const job = await runCheck("Иванов_Иван", "HW2", "https://example.com/submission.zip");
const status = await getStatus(job.job_id);
console.log(status);
```

---

## Запуск сервера

### Локальная разработка

```bash
cd mlsd/hw_checker
poetry run uvicorn hw_checker.mcp.api_server:app --host 0.0.0.0 --port 8005 --reload
```

### Docker Compose

```bash
cd mlsd/hw_checker
docker-compose -f docker-compose.infra.yml up -d mcp-server
```

Сервер будет доступен на `http://localhost:8005`.

### Проверка работоспособности

**С хоста:**
```bash
curl http://localhost:8005/health
```

**Из контейнера в ai-challenge-network:**
```bash
# Пример из контейнера butler-bot
docker exec butler-bot curl http://hw_checker-mcp-server-1:8005/health
```

**Результат:**
```json
{"status":"healthy"}
```

---

## Автоматическая документация

FastAPI предоставляет автоматическую интерактивную документацию:

- **Swagger UI**: http://localhost:8005/docs
- **ReDoc**: http://localhost:8005/redoc

---

## Требования

- Python 3.10+
- PostgreSQL (для хранения статусов проверок)
- Docker (для запуска в контейнере)

## Конфигурация

Сервер использует переменные окружения из `.env.infra`:

- `HW_DB_JOB_TRACKING=true`: Включение отслеживания в базе данных
- `HW_DB_HOST=postgres`: Хост базы данных
- `HW_DB_PORT=5432`: Порт базы данных
- `HW_DB_NAME=checker`: Имя базы данных

---

## Поддержка

Для вопросов и проблем обращайтесь к документации проекта или создавайте issues в репозитории.

