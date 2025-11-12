<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Я думаю, можно сохранить очередь и бд, но уточнить, что надо переиспользовать текущие задания, работаем над архивом с кодом, Advanced diff анализ и Retry логика тоже можно сотавить

У нас уже есть: код-ревью архива, mongodb, логирование

Отлично! Тогда переработаем MVP с учётом того, что у вас уже есть — это существенно меняет картину и делает решение более production-ready.

***

## **MVP v2 — с учётом существующей инфраструктуры**

### **1. Что уже есть (переиспользуем)**

✅ Архив с кодом + история сабмитов
✅ MongoDB (метаданные, результаты)
✅ Логирование (structured logging)
✅ Code-review система
✅ Существующие задания (задачи)

**Это значит:**

- Не нужно создавать файловую систему (работаем с архивом)
- Не нужно парсить данные с нуля (они уже структурированы в MongoDB)
- Логирование + мониторинг уже есть
- Можем переиспользовать шаги code-review

***

### **2. Что добавляем в MVP**

✨ **Очередь задач** (Redis + Celery или RQ) — для асинхронной обработки сабмитов
✨ **Advanced diff анализ** — сравнение кодов на уровне семантики
✨ **Retry логика** — надёжность при сбоях LLM/API
✨ **LLM интеграция** — сравнение двух сабмитов и генерация JSON
✨ **Публикация результата** — отправка во внешнее API

***

### **3. Новая архитектура MVP v2**

```
[Event: Новый сабмит]
    ↓
[FastAPI endpoint]
    ├→ Получить current submission из архива
    ├→ Получить previous submission из MongoDB/архива
    ↓
[Task Queue (Redis/Celery)]
    ↓
[Processing Worker]
    ├→ [Advanced Diff Analysis] — семантический diff
    ├→ [Log Parser] — анализ логов тестов
    ├→ [LLM Integration] — промпт + генерация JSON
    ├→ [Retry Handler] — при ошибках LLM/API
    ├→ [MongoDB] — сохранение результатов
    └→ [External API Client] — публикация с retry
        ↓
    [Webhook/Notification] — обратная связь студенту
```


***

### **4. Структура проекта MVP v2**

```
ai-code-reviewer-mvp-v2/
├── src/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app
│   ├── config.py                    # Settings (БД, очередь, LLM)
│   ├── models.py                    # Pydantic schemas
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                # API endpoints
│   │
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── diff_analyzer.py         # Advanced diff анализ
│   │   ├── log_parser.py            # Парсинг логов тестов
│   │   └── result_mapper.py         # Маппинг в JSON
│   │
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── celery_app.py            # Celery конфиг
│   │   └── review_tasks.py          # Асинхронные задачи
│   │
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── llm_client.py            # LLM с retry логикой
│   │   ├── external_api.py          # API клиент с retry
│   │   ├── archive_service.py       # Работа с архивом кода
│   │   └── mongodb_service.py       # MongoDB операции
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py                # Structured logging
│       ├── diff_utils.py            # Утилиты для diff
│       └── retry.py                 # Retry decorator
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml           # App + Redis, MongoDB
│
├── config/
│   └── prompts.yaml                 # LLM prompts
│
├── requirements.txt
├── .env.example
├── Makefile
├── pyproject.toml
└── README.md
```


***

### **5. Ключевые модули MVP v2**

#### **5.1 config.py — Конфигурация**

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "code_review"

    # Redis + Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER: str = "redis://localhost:6379/0"
    CELERY_BACKEND: str = "redis://localhost:6379/1"

    # LLM
    OPENAI_API_KEY: str
    LLM_MODEL: str = "gpt-4-turbo"
    LLM_TIMEOUT: int = 60
    LLM_MAX_RETRIES: int = 3

    # External API
    EXTERNAL_API_URL: str
    EXTERNAL_API_KEY: str
    EXTERNAL_API_TIMEOUT: int = 30
    EXTERNAL_API_MAX_RETRIES: int = 3

    # Archive
    ARCHIVE_PATH: str = "/data/submissions"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
```


#### **5.2 diff_analyzer.py — Advanced Diff анализ**

```python
from typing import Dict, List, Any
import difflib
from pathlib import Path

class DiffAnalyzer:
    """Анализ изменений между двумя версиями кода"""

    @staticmethod
    def analyze(previous_code: str, new_code: str) -> Dict[str, Any]:
        """
        Семантический diff с метриками
        """
        diff = list(difflib.unified_diff(
            previous_code.splitlines(keepends=True),
            new_code.splitlines(keepends=True),
            fromfile="previous",
            tofile="new",
            lineterm=""
        ))

        # Подсчёт метрик
        lines_added = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        lines_removed = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
        lines_changed = max(lines_added, lines_removed)

        # Анализ типов изменений
        has_refactor = any(keyword in new_code for keyword in ['def ', 'class '])
        has_new_imports = any(
            imp in new_code and imp not in previous_code
            for imp in ['import ', 'from ']
        )

        return {
            "diff": ''.join(diff),
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "lines_changed": lines_changed,
            "change_ratio": (lines_changed / max(len(new_code.split('\n')), 1)) * 100,
            "has_refactor": has_refactor,
            "has_new_imports": has_new_imports,
            "total_files_changed": 1  # TODO: для мультифайлов
        }
```


#### **5.3 llm_client.py — LLM с retry логикой**

```python
import httpx
import json
import asyncio
import logging
from typing import Dict, Any
from src.utils.retry import async_retry
from src.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    """LLM интеграция с retry логикой и обработкой ошибок"""

    def __init__(self):
        self.model = settings.LLM_MODEL
        self.api_key = settings.OPENAI_API_KEY
        self.timeout = settings.LLM_TIMEOUT
        self.max_retries = settings.LLM_MAX_RETRIES

    @async_retry(
        max_retries=3,
        delay=1,
        backoff=2,
        exceptions=(httpx.HTTPError, json.JSONDecodeError, ValueError)
    )
    async def generate_review(self, prompt: str) -> Dict[str, Any]:
        """
        Генерирует review в формате JSON с авторетрай
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "response_format": {"type": "json_object"}
                },
                timeout=self.timeout
            )

        if response.status_code != 200:
            logger.error(f"LLM API error: {response.text}")
            raise httpx.HTTPError(f"LLM API failed: {response.status_code}")

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Парсим и валидируем JSON
        parsed = json.loads(content)
        self._validate_json_structure(parsed)

        return parsed

    @staticmethod
    def _validate_json_structure(data: Dict[str, Any]) -> None:
        """Валидирует обязательные поля"""
        required_fields = ["overall_score", "progress_summary", "code_review_comments"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field in LLM response: {field}")
```


#### **5.4 retry.py — Retry Decorator**

```python
import asyncio
import logging
from functools import wraps
from typing import Callable, Type, Tuple

logger = logging.getLogger(__name__)

def async_retry(
    max_retries: int = 3,
    delay: float = 1,
    backoff: float = 2,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """Декоратор для retry асинхронных функций с exponential backoff"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay

            for attempt in range(max_retries):
                try:
                    logger.info(f"Attempt {attempt + 1}/{max_retries} for {func.__name__}")
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries - 1:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}")
                        raise

                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {current_delay}s..."
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

        return wrapper
    return decorator
```


#### **5.5 review_tasks.py — Celery задачи**

```python
from celery import shared_task
import logging
from src.tasks.celery_app import celery_app
from src.integrations.llm_client import LLMClient
from src.integrations.external_api import ExternalAPIClient
from src.integrations.archive_service import ArchiveService
from src.integrations.mongodb_service import MongoDBService
from src.pipeline.diff_analyzer import DiffAnalyzer
from src.utils.logger import get_logger

logger = get_logger(__name__)

@celery_app.task(bind=True, max_retries=3)
def process_submission_review(
    self,
    student_id: str,
    assignment_id: str,
    new_submission_id: str,
    previous_submission_id: str = None
):
    """
    Основная асинхронная задача для code review
    """
    try:
        logger.info(
            f"Starting review: student={student_id}, assignment={assignment_id}, "
            f"new_sub={new_submission_id}"
        )

        # 1. Получить оба сабмита из архива
        archive_svc = ArchiveService()
        new_submission = archive_svc.get_submission(new_submission_id)
        previous_submission = (
            archive_svc.get_submission(previous_submission_id)
            if previous_submission_id else None
        )

        # 2. Advanced diff анализ
        diff_analyzer = DiffAnalyzer()
        diff_info = diff_analyzer.analyze(
            previous_submission.get("code", "") if previous_submission else "",
            new_submission.get("code", "")
        )

        # 3. Формирование промпта для LLM
        prompt = _build_prompt(
            new_submission,
            previous_submission,
            diff_info,
            assignment_id
        )

        # 4. LLM генерирует review
        llm_client = LLMClient()
        review_result = asyncio.run(llm_client.generate_review(prompt))

        # 5. Обогащение результата метаданными
        final_payload = {
            "student_id": student_id,
            "assignment_id": assignment_id,
            "new_submission_id": new_submission_id,
            "previous_submission_id": previous_submission_id,
            "diff_info": diff_info,
            "review_result": review_result,
            "timestamp": datetime.now().isoformat()
        }

        # 6. Сохранение в MongoDB
        mongo_svc = MongoDBService()
        result_id = mongo_svc.save_review(final_payload)

        # 7. Публикация во внешнее API
        api_client = ExternalAPIClient()
        api_response = asyncio.run(api_client.publish_review(final_payload))

        logger.info(f"Review completed: result_id={result_id}, api_status={api_response['status']}")

        return {
            "result_id": result_id,
            "external_api_status": api_response["status"],
            "success": True
        }

    except Exception as exc:
        logger.error(f"Task failed: {str(exc)}", exc_info=True)
        # Retry с exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

def _build_prompt(new_sub, prev_sub, diff_info, assignment_id):
    """Формирование промпта для LLM"""
    return f"""
Ты - опытный code reviewer для курса ML System Design.

Сравни два сабмита студента и дай детальный фидбек в JSON.

ЗАДАНИЕ: {assignment_id}

ПРЕДЫДУЩИЙ КОД:
{prev_sub.get('code', 'N/A') if prev_sub else 'Первый сабмит'}

НОВЫЙ КОД:
{new_sub.get('code')}

ЛОГИ ТЕСТОВ (новый):
{new_sub.get('test_logs', 'N/A')}

АНАЛИЗ ИЗМЕНЕНИЙ:
- Строк добавлено: {diff_info['lines_added']}
- Строк удалено: {diff_info['lines_removed']}
- Процент изменений: {diff_info['change_ratio']:.1f}%
- Есть рефакторинг: {diff_info['has_refactor']}

Дай оценку в JSON с полями:
- overall_score (0-100)
- progress_summary (текст)
- code_quality_score (0-100)
- code_review_comments (список)
- recommendations (список)
"""
```


#### **5.6 external_api.py — Публикация с retry**

```python
import httpx
from src.utils.retry import async_retry
from src.config import settings
import logging

logger = logging.getLogger(__name__)

class ExternalAPIClient:
    """Клиент для публикации результатов во внешнее API"""

    def __init__(self):
        self.api_url = settings.EXTERNAL_API_URL
        self.api_key = settings.EXTERNAL_API_KEY
        self.timeout = settings.EXTERNAL_API_TIMEOUT
        self.max_retries = settings.EXTERNAL_API_MAX_RETRIES

    @async_retry(
        max_retries=3,
        delay=1,
        backoff=2,
        exceptions=(httpx.HTTPError, httpx.TimeoutException)
    )
    async def publish_review(self, payload: dict) -> dict:
        """
        Публикует review во внешнее API с retry логикой
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/api/v1/reviews",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=self.timeout
            )

        if response.status_code not in [200, 201]:
            logger.error(f"External API error: {response.status_code} - {response.text}")
            raise httpx.HTTPError(f"API failed: {response.status_code}")

        logger.info(f"Review published successfully: {response.status_code}")
        return {
            "status": "published",
            "external_id": response.json().get("id"),
            "response": response.json()
        }
```


#### **5.7 routes.py — API endpoints**

```python
from fastapi import APIRouter, HTTPException, BackgroundTasks
from src.models import ReviewRequest
from src.tasks.review_tasks import process_submission_review
from src.integrations.mongodb_service import MongoDBService
import logging

router = APIRouter(prefix="/api/v1", tags=["reviews"])
logger = logging.getLogger(__name__)
mongo_svc = MongoDBService()

@router.post("/submissions/{submission_id}/review")
async def create_review(
    submission_id: str,
    student_id: str,
    assignment_id: str,
    previous_submission_id: str = None
):
    """
    Триггерит асинхронный review сабмита
    """
    try:
        # Постановка в очередь
        task = process_submission_review.delay(
            student_id=student_id,
            assignment_id=assignment_id,
            new_submission_id=submission_id,
            previous_submission_id=previous_submission_id
        )

        logger.info(f"Review task queued: task_id={task.id}")

        return {
            "task_id": task.id,
            "status": "queued",
            "message": "Review processing started"
        }
    except Exception as e:
        logger.error(f"Failed to queue review: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reviews/{task_id}")
async def get_review_status(task_id: str):
    """Получить статус/результат review"""
    task = process_submission_review.AsyncResult(task_id)

    if task.state == "PENDING":
        return {"status": "pending", "task_id": task_id}
    elif task.state == "SUCCESS":
        result = mongo_svc.get_review_by_task_id(task_id)
        return {"status": "completed", "result": result}
    elif task.state == "FAILURE":
        return {"status": "failed", "error": str(task.info), "task_id": task_id}

    return {"status": task.state, "task_id": task_id}

@router.get("/health")
async def health_check():
    return {"status": "ok"}
```


***

### **6. Docker Compose MVP v2**

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=mongodb://mongo:27017
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER=redis://redis:6379/0
      - CELERY_BACKEND=redis://redis:6379/1
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - EXTERNAL_API_URL=${EXTERNAL_API_URL}
      - EXTERNAL_API_KEY=${EXTERNAL_API_KEY}
    depends_on:
      - mongo
      - redis
    volumes:
      - ./src:/app/src
      - /data/submissions:/data/submissions

  worker:
    build: .
    command: celery -A src.tasks.celery_app worker --loglevel=info --concurrency=4
    environment:
      - MONGODB_URL=mongodb://mongo:27017
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER=redis://redis:6379/0
      - CELERY_BACKEND=redis://redis:6379/1
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - EXTERNAL_API_URL=${EXTERNAL_API_URL}
      - EXTERNAL_API_KEY=${EXTERNAL_API_KEY}
    depends_on:
      - mongo
      - redis
    volumes:
      - ./src:/app/src
      - /data/submissions:/data/submissions

  mongo:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  mongo_data:
  redis_data:
```


***

### **7. Requirements MVP v2**

```
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.5.0
pydantic-settings==2.1.0
httpx==0.25.2
celery==5.3.4
redis==5.0.1
pymongo==4.6.0
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.23.2
```


***

### **8. Что изменилось от MVP v1**

| Компонент | MVP v1 | MVP v2 |
| :-- | :-- | :-- |
| Очередь | ❌ | ✅ Redis + Celery |
| БД | ❌ (логи только) | ✅ MongoDB |
| Retry логика | ❌ | ✅ Exponential backoff |
| Advanced diff | ❌ | ✅ Метрики + анализ |
| Архив | ❌ | ✅ Переиспользуем |
| Асинхронность | ❌ | ✅ Полная |
| Код строк | ~500 | ~800 |


***

### **9. Как запустить MVP v2**

```bash
# 1. Переменные окружения
cp .env.example .env
# Отредактировать .env

# 2. Через Docker Compose
docker-compose up -d

# 3. Проверить здоровье
curl http://localhost:8000/health

# 4. Создать review задачу
curl -X POST http://localhost:8000/api/v1/submissions/sub_123/review \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "s123",
    "assignment_id": "hw_05",
    "previous_submission_id": "sub_122"
  }'

# 5. Проверить статус
curl http://localhost:8000/api/v1/reviews/{task_id}

# 6. Посмотреть логи
docker-compose logs -f worker
```


***

**Готов расписать другие модули или полный код? MVP v2 с очередью, БД, retry и diff анализом — это уже серьёзное решение.**
