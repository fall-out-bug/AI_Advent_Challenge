# Быстрая проверка работоспособности Review System

## 🚀 Быстрый старт

### 1. Unit тесты (не требует сервисов)
```bash
make review-test
```

### 2. Полная проверка (требует MongoDB и LLM)
```bash
# Запустите MongoDB
docker-compose up -d mongodb

# Установите LLM_URL (если не в .env)
export LLM_URL="http://localhost:8000"

# Запустите health check
make review-health-check
```

### 3. E2E тесты (РЕАЛЬНАЯ СИСТЕМА)
```bash
export LLM_URL="http://localhost:8000"
# Опционально: для полного тестирования External API
export EXTERNAL_API_URL="http://api.example.com"
export EXTERNAL_API_KEY="your-key"
export EXTERNAL_API_ENABLED="true"

make review-e2e
```

**Все компоненты реальные:**
- ✅ Реальная MongoDB
- ✅ Реальный LLM (UnifiedModelClient → HTTPLLMClient)
- ✅ Реальные ZIP архивы
- ✅ Реальный External API (если настроен)
- ✅ MultiPassReviewerAgent (3-pass review)

## 📋 Что проверяется

### Health Check (`make review-health-check`)
- ✅ MongoDB connection
- ✅ Archive extraction
- ✅ Diff analysis
- ✅ Use cases (enqueue, get_by_id)
- ✅ Full pipeline (extract → diff → multi-pass review → save) - **требует LLM_URL**

### E2E Tests (`make review-e2e`) - **ВСЁ РЕАЛЬНОЕ**
- ✅ Полный pipeline с реальными ZIP архивами
- ✅ Реальная работа с MongoDB
- ✅ Реальная работа с LLM (UnifiedModelClient)
- ✅ Реальная работа с External API (если настроен)
- ✅ Использование MultiPassReviewerAgent (3-pass review)
- ✅ Первый submission (без предыдущего)
- ✅ Submission с предыдущей версией
- ✅ Невалидный ZIP архив

## 🔧 Ручное тестирование

### API (интегрирован в mcp-server)
```bash
# Запустите mcp-server (включает review API)
docker-compose up -d mcp-server

# Или локально
python -m src.presentation.api

# Создайте задачу
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

**Примечание:** Review API доступен на порту 8004 (mcp-server).

### Worker (Unified Task Worker)
```bash
# Запустите unified-task-worker
make unified-task-worker

# Или через Docker Compose
docker-compose up -d unified-task-worker

# Создайте задачу через API (см. выше)
# Worker автоматически обработает задачу
```

## 🏗️ Архитектура

Система полностью интегрирована в существующую инфраструктуру:

- **Единая очередь**: `LongTasksRepository` для всех типов задач
- **Единый worker**: `SummaryWorker` обрабатывает SUMMARIZATION и CODE_REVIEW
- **Производственная система**: `MultiPassReviewerAgent` для всех review
- **Правильные границы**: Domain не импортирует infrastructure

## 📚 Подробная документация

См. `docs/testing_review_system.md` и `docs/review_system_architecture.md` для полного руководства.
