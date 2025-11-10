# Testing Review System - Comprehensive Guide

## Обзор проверки работоспособности

Система review полностью интегрирована в существующую инфраструктуру:

1. **Domain Layer** - Value Objects, Services (DiffAnalyzer)
2. **Application Layer** - Use Cases (ReviewSubmissionUseCase, EnqueueReviewTaskUseCase)
3. **Infrastructure Layer** - Repositories (LongTasksRepository), Archive Service, Clients
4. **Presentation Layer** - API Routes (интегрированы в mcp-server)
5. **Worker** - UnifiedTaskWorker (SummaryWorker обрабатывает оба типа задач)

## Уровни тестирования

### 1. Unit Tests (Быстрые, изолированные)

```bash
make review-test
```

**Что проверяется:**
- Value Objects (LongTask, CodeDiff, SubmissionArchive)
- Services (DiffAnalyzer)
- Use Cases (EnqueueReviewTaskUseCase)

**Требования:**
- ✅ Не требует MongoDB
- ✅ Не требует LLM
- ✅ Быстро (< 1 секунды)

### 2. E2E Tests (Реальная система)

```bash
# Убедитесь, что MongoDB запущена
docker-compose up -d mongodb

# Настройте LLM_URL (обязательно для E2E тестов)
export LLM_URL="http://localhost:8000"

# Опционально: настройте External API для полного тестирования
export EXTERNAL_API_URL="http://api.example.com"
export EXTERNAL_API_KEY="your-api-key"
export EXTERNAL_API_ENABLED="true"

make review-e2e
```

**Что проверяется (ВСЁ РЕАЛЬНОЕ):**
- ✅ Реальная работа с MongoDB (настоящее подключение)
- ✅ Реальная работа с LLM (UnifiedModelClient → HTTPLLMClient)
- ✅ Реальная работа с External API (если настроен, иначе mock)
- ✅ Реальная работа с ZIP архивами (ZipArchiveService)
- ✅ Реальная интеграция всех компонентов
- ✅ Использование MultiPassReviewerAgent (3-pass review)

**Требования:**
- ✅ Требует MongoDB (тесты пропускаются, если недоступна)
- ✅ Требует LLM_URL (реальный LLM сервис через UnifiedModelClient)
- ✅ Использует реальные ZIP архивы
- ✅ External API опционален (используется mock, если не настроен)

### 3. Health Check (Комплексная проверка)

```bash
make review-health-check
```

**Что проверяется:**
1. MongoDB connection
2. Archive extraction
3. Diff analysis
4. Use cases (enqueue, get_by_id)
5. Full pipeline (extract → diff → multi-pass review → save)

**Требования:**
- ✅ Требует MongoDB
- ✅ Требует LLM_URL (использует UnifiedModelClient)
- ✅ Создаёт и удаляет тестовые данные

### 4. API Testing (Ручное тестирование)

```bash
# Запустите mcp-server (включает review API)
docker-compose up -d mcp-server

# Или локально
python -m src.presentation.api

# В другом терминале
curl -X POST http://localhost:8004/api/v1/reviews \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "123",
    "assignment_id": "HW2",
    "new_submission_path": "/app/review_archives/submission.zip"
  }'

# Проверьте статус
curl http://localhost:8004/api/v1/reviews/{task_id}
```

**Примечание:** Review API интегрирован в mcp-server на порту 8004.

### 5. Worker Testing (Background processing)

```bash
# Запустите MongoDB и LLM
docker-compose up -d mongodb mistral-chat

# Запустите unified-task-worker
make unified-task-worker

# Или через Docker Compose
docker-compose up -d unified-task-worker

# В другом терминале создайте задачу через API
# Worker автоматически обработает задачу
```

## Полная проверка работоспособности

### Шаг 1: Unit Tests

```bash
make review-test
```

**Ожидаемый результат:**
```
3 passed in 0.2s
```

### Шаг 2: Health Check

```bash
# Убедитесь, что MongoDB запущена
docker-compose up -d mongodb

# Настройте LLM_URL
export LLM_URL="http://localhost:8000"

# Запустите health check
make review-health-check
```

**Ожидаемый результат:**
```
✅ MongoDB connection: OK
✅ Archive extraction: OK
✅ Diff analysis: OK
✅ Enqueue use case: OK
✅ Repository get_by_id: OK
✅ Use cases: OK
✅ Full pipeline: OK

Total: 6/6 tests passed
✅ All tests passed!
```

### Шаг 3: E2E Tests

```bash
# Убедитесь, что MongoDB и LLM запущены
docker-compose up -d mongodb mistral-chat

# Настройте LLM_URL
export LLM_URL="http://localhost:8000"

make review-e2e
```

**Ожидаемый результат:**
```
3 passed in X.Xs
```

### Шаг 4: API Testing

```bash
# Терминал 1: Запустите mcp-server
docker-compose up -d mcp-server

# Терминал 2: Создайте тестовый ZIP
mkdir -p ./review_archives
cd ./review_archives
echo 'def hello(): print("world")' > main.py
zip submission.zip main.py

# Создайте review task
curl -X POST http://localhost:8004/api/v1/reviews \
  -H "Content-Type: application/json" \
  -d "{
    \"student_id\": \"999\",
    \"assignment_id\": \"HW_TEST\",
    \"new_submission_path\": \"/app/review_archives/submission.zip\"
  }"

# Получите task_id из ответа и проверьте статус
curl http://localhost:8004/api/v1/reviews/{task_id}
```

### Шаг 5: Worker Testing

```bash
# Терминал 1: Запустите unified-task-worker
make unified-task-worker

# Терминал 2: Создайте задачу через API (см. Шаг 4)
# Worker автоматически обработает задачу

# Проверьте логи worker'а - должны увидеть:
# "Processing review task: task_id=..."
# "Review task completed: task_id=..., session_id=..."
```

## Проверка компонентов по отдельности

### MongoDB Connection

```python
from src.infrastructure.database.mongo import get_db

db = await get_db()
await db.admin.command("ping")
print("MongoDB OK")
```

### Archive Extraction

```python
from src.infrastructure.archive.archive_service import ZipArchiveService
from src.infrastructure.config.settings import get_settings

service = ZipArchiveService(get_settings())
archive = service.extract_submission("/path/to/archive.zip", "test_id")
print(f"Extracted {len(archive.code_files)} files")
```

### Diff Analysis

```python
from src.domain.services.diff_analyzer import DiffAnalyzer

analyzer = DiffAnalyzer()
diff = analyzer.analyze("def old(): pass", "def new(): pass")
print(f"Added {diff.lines_added} lines, {len(diff.functions_added)} functions")
```

### Use Cases

```python
from src.application.use_cases.enqueue_review_task_use_case import (
    EnqueueReviewTaskUseCase,
)
from src.infrastructure.repositories.long_tasks_repository import (
    LongTasksRepository,
)
from src.infrastructure.database.mongo import get_db

db = await get_db()
repo = LongTasksRepository(db)
use_case = EnqueueReviewTaskUseCase(repo)
task = await use_case.execute("123", "HW2", "/path/to/zip")
print(f"Created task: {task.task_id}, type: {task.task_type.value}")
```

### MultiPassReviewerAgent Integration

```python
import sys
from pathlib import Path

# Add shared to path
_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_root))
shared_path = _root / "shared"
sys.path.insert(0, str(shared_path))

from shared_package.clients.unified_client import UnifiedModelClient
from src.domain.agents.multi_pass_reviewer import MultiPassReviewerAgent
from src.infrastructure.archive.archive_service import ZipArchiveService
from src.domain.services.diff_analyzer import DiffAnalyzer
from src.infrastructure.config.settings import get_settings

settings = get_settings()
unified_client = UnifiedModelClient(timeout=settings.review_llm_timeout)
agent = MultiPassReviewerAgent(unified_client, token_budget=12000)

archive_service = ZipArchiveService(settings)
diff_analyzer = DiffAnalyzer()

report = await agent.review_from_archives(
    archive_reader=archive_service,
    diff_analyzer=diff_analyzer,
    new_archive_path="/path/to/new.zip",
    previous_archive_path="/path/to/old.zip",
    assignment_id="HW2",
    student_id="student123"
)

print(f"Review complete: session_id={report.session_id}, findings={report.total_findings}")
```

## Troubleshooting

### MongoDB недоступна

```bash
# Запустите MongoDB
docker-compose up -d mongodb

# Проверьте подключение
docker-compose ps mongodb
```

### LLM_URL не настроен

```bash
# Настройте LLM_URL для E2E тестов и health check
export LLM_URL="http://localhost:8000"

# Или в .env файле
echo "LLM_URL=http://localhost:8000" >> .env
```

### Worker не обрабатывает задачи

1. Проверьте, что worker запущен: `ps aux | grep unified-task-worker`
2. Проверьте логи worker'а: `docker-compose logs unified-task-worker`
3. Проверьте, что есть задачи в очереди:
   ```python
   from src.infrastructure.database.mongo import get_db
   from src.infrastructure.repositories.long_tasks_repository import LongTasksRepository
   from src.domain.value_objects.task_type import TaskType

   db = await get_db()
   repo = LongTasksRepository(db)
   count = await repo.get_queue_size(task_type=TaskType.CODE_REVIEW)
   print(f"Queued review tasks: {count}")
   ```

### UnifiedModelClient не доступен

```bash
# Проверьте, что shared package установлен
ls -la shared/shared_package/clients/unified_client.py

# Или установите зависимости
poetry install
```

## Чек-лист полной проверки

- [ ] Unit tests проходят: `make review-test`
- [ ] Health check проходит: `make review-health-check` (требует LLM_URL)
- [ ] E2E tests проходят: `make review-e2e` (требует LLM_URL)
- [ ] API создаёт задачи: `curl -X POST http://localhost:8004/api/v1/reviews`
- [ ] API возвращает статус: `curl http://localhost:8004/api/v1/reviews/{task_id}`
- [ ] Worker обрабатывает задачи: `make unified-task-worker`
- [ ] Метрики работают: проверьте Prometheus metrics endpoint

## Автоматизация проверки

Скрипт `scripts/quality/test_review_system.py` автоматически проверяет все компоненты:

```bash
make review-health-check
```

Этот скрипт:
- ✅ Проверяет MongoDB connection
- ✅ Тестирует archive extraction
- ✅ Тестирует diff analysis
- ✅ Тестирует use cases
- ✅ Тестирует полный pipeline с MultiPassReviewerAgent
- ✅ Автоматически очищает тестовые данные

**Требования:**
- MongoDB должна быть запущена
- LLM_URL должен быть настроен (для полного pipeline теста)
