# AI Agent Pipeline для Digest Collection и PDF Export

## 📋 Содержание
1. [Архитектура](#архитектура)
2. [Структура проекта](#структура-проекта)
3. [API контракты](#api-контракты)
4. [Компоненты](#компоненты)
5. [Docker Compose](#docker-compose)
6. [Промпты и инструкции](#промпты-и-инструкции)
7. [Error Handling](#error-handling)
8. [Рекомендации по улучшению](#рекомендации-по-улучшению)

---

## Архитектура

### High-level диаграмма

```
┌──────────────┐
│ User Input   │ "собери дайджест по Набоке за 3 дня"
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│        Mistral-7B Agent (Docker)                │
│                                                 │
│  - Парсит намерение пользователя                │
│  - Оркестрирует MCP-tool вызовы                 │
│  - Управляет диалоговой историей                │
│  - Обрабатывает ошибки и retry                  │
└─────────────────────────────────────────────────┘
       │
       ├─────────────┬──────────────┬────────────────┐
       │             │              │                │
       ▼             ▼              ▼                ▼
   ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐
   │  MCP    │  │   MCP    │  │   MCP    │  │    MCP      │
   │ Subs    │  │  Posts   │  │ Collect  │  │  Summary &  │
   │ Tool    │  │  Tool    │  │  Posts   │  │    PDF      │
   │ :8001  │  │  :8002  │  │  :8003  │  │    :8004   │
   └────┬────┘  └────┬─────┘  └────┬────┘  └──────┬──────┘
        │             │             │               │
        └─────────────┴─────────────┴───────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
    ┌──────────────┐      ┌──────────────┐
    │   MongoDB    │      │    Redis     │
    │  - Posts     │      │ - Dialog     │
    │  - Channels  │      │   History    │
    │  - Config    │      │ - Caching    │
    └──────────────┘      └──────────────┘
```

### Workflow последовательность

```
1. User: "собери дайджест по Набоке за 3 дня"
         │
         ▼
2. Agent: call_tool("get_subscriptions")
         │
         ▼
3. Agent: Identify channel "onaboka"
         │
         ▼
4. Agent: call_tool("get_posts", channel_id="onaboka", limit=100, days=3)
         │
         ├─ Если постов недостаточно ─┐
         │                              │
         │                              ▼
         │                    5. Agent: call_tool("collect_posts", channel_id="onaboka")
         │                              │
         │                              ▼ (дождаться результата)
         │                    6. Agent: call_tool("get_posts", ...)
         │                              │
         └──────────────────────────────┘
                     │
                     ▼
         7. Agent: call_tool("generate_summary", posts_text)
                     │
                     ▼
         8. Agent: call_tool("export_pdf", summary_text, title, metadata)
                     │
                     ▼
         9. Return PDF path to user
```

---

## Структура проекта

```
ai-advent-challenge/
├── docker-compose.yml                  # Оркестрация сервисов
├── .env.example                        # Переменные окружения
│
├── agent/                              # Mistral Agent
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                         # Entry point
│   ├── agent.py                        # Agent логика
│   ├── mcp_client.py                   # MCP клиент для инструментов
│   ├── dialog_manager.py               # История диалогов (MongoDB)
│   ├── utils.py                        # Утилиты
│   └── config.py                       # Конфигурация
│
├── mcp_tools/                          # MCP сервер с инструментами
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                         # FastAPI сервер
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── subscriptions.py            # get_subscriptions, list_channels
│   │   ├── posts.py                    # get_posts, cached retrieval
│   │   ├── collect.py                  # collect_posts (async worker trigger)
│   │   ├── summarize.py                # generate_summary (Mistral API)
│   │   └── export_pdf.py               # export_to_pdf
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py                  # Pydantic models для валидации
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── mongo.py                    # MongoDB connection & queries
│   │   └── redis.py                    # Redis connection & cache
│   │
│   └── config.py                       # Конфигурация MCP-сервера
│
└── logs/                               # Логи контейнеров (volume)
```

---

## API контракты

### 1. **MCP Tool: get_subscriptions** (port 8001)

```http
POST /tools/get_subscriptions
Content-Type: application/json

Request Body:
{
  "user_id": "optional_string"
}

Response (200 OK):
{
  "status": "success",
  "data": [
    {
      "channel_id": "onaboka",
      "channel_name": "Набока",
      "description": "Блог про ML",
      "subscribers": 5000,
      "last_post_date": "2025-10-30T14:30:00Z"
    },
    {
      "channel_id": "another_channel",
      "channel_name": "Другой Канал",
      "description": "...",
      "subscribers": 1000,
      "last_post_date": "2025-10-30T10:00:00Z"
    }
  ]
}

Error Response (400/500):
{
  "status": "error",
  "error": "string",
  "code": "error_code"
}
```

### 2. **MCP Tool: get_posts** (port 8002)

```http
POST /tools/get_posts
Content-Type: application/json

Request Body:
{
  "channel_id": "onaboka",
  "limit": 100,
  "date_from": "2025-10-27T00:00:00Z",  # опционально
  "date_to": "2025-10-30T23:59:59Z"     # опционально
}

Response (200 OK):
{
  "status": "success",
  "channel_id": "onaboka",
  "posts_count": 23,
  "data": [
    {
      "post_id": "msg_12345",
      "text": "Текст поста...",
      "date": "2025-10-30T14:30:00Z",
      "views": 150,
      "reactions": {"👍": 5, "❤️": 3},
      "media": ["image_url_1", "image_url_2"],
      "forwarded_from": null
    },
    ...
  ],
  "cached": false  # true если из Redis cache
}

Error Response (404):
{
  "status": "error",
  "error": "Channel not found or no posts in date range",
  "code": "NO_POSTS_ERROR"
}
```

### 3. **MCP Tool: collect_posts** (port 8003)

```http
POST /tools/collect_posts
Content-Type: application/json

Request Body:
{
  "channel_id": "onaboka",
  "limit": 100,
  "wait_for_completion": false,  # async по умолчанию
  "timeout_seconds": 30          # макс ожидание если wait=true
}

Response (202 Accepted / 200 OK):
{
  "status": "processing",
  "job_id": "collect_job_uuid",
  "channel_id": "onaboka",
  "estimated_time_seconds": 15
}

или (если wait_for_completion=true и успел):

{
  "status": "success",
  "job_id": "collect_job_uuid",
  "collected_count": 45,
  "date_range": {
    "from": "2025-10-28T00:00:00Z",
    "to": "2025-10-30T23:59:59Z"
  }
}

Error Response (409):
{
  "status": "error",
  "error": "Collection already in progress",
  "code": "COLLECTION_IN_PROGRESS"
}
```

### 4. **MCP Tool: generate_summary** (port 8004)

```http
POST /tools/generate_summary
Content-Type: application/json

Request Body:
{
  "posts_text": "Объединённый текст всех постов",
  "posts_count": 23,
  "channel_name": "Набока",
  "language": "ru",
  "style": "bullet_points"  # или "paragraph"
}

Response (200 OK):
{
  "status": "success",
  "summary": "• Пункт 1\n• Пункт 2\n...",
  "summary_length": 1523,  # символов
  "original_length": 45123,
  "compression_ratio": 0.034
}

Error Response (503):
{
  "status": "error",
  "error": "Model inference failed",
  "code": "MODEL_ERROR"
}
```

### 5. **MCP Tool: export_pdf** (port 8004)

```http
POST /tools/export_pdf
Content-Type: application/json

Request Body:
{
  "summary_text": "Текст саммари",
  "title": "Дайджест Набока за 3 дня",
  "channel_name": "onaboka",
  "date_range": {
    "from": "2025-10-27",
    "to": "2025-10-30"
  },
  "metadata": {
    "posts_count": 23,
    "generated_at": "2025-10-30T16:30:00Z"
  }
}

Response (200 OK):
{
  "status": "success",
  "pdf_path": "/output/digest_onaboka_2025-10-27_2025-10-30.pdf",
  "file_size_bytes": 45123,
  "download_url": "http://localhost:8004/files/digest_..."
}

Error Response (400):
{
  "status": "error",
  "error": "Failed to generate PDF",
  "code": "PDF_GENERATION_ERROR"
}
```

---

## Компоненты

### Agent (main.py)

**Ответственность:**
- Слушает пользовательский ввод (stdin или API)
- Инициирует вызовы MCP-tools через orator
- Управляет историей диалога в MongoDB
- Обрабатывает ошибки и retry логику

**Основной loop:**
```
1. Get user input
2. Store in dialog history (MongoDB)
3. Build prompt с kontekstом истории
4. Call Mistral agent for tool calling
5. Execute recommended tools via MCP client
6. Aggregate results
7. Generate final response
8. Store response in dialog history
9. Return to user
```

### MCP Tools Server (FastAPI)

**Ответственность:**
- REST endpoints для 5 tools
- Валидация входных данных (Pydantic)
- Управление MongoDB/Redis соединениями
- Логирование всех операций
- Error handling с appropriate HTTP codes

**5 endpoints:**
- `POST /tools/get_subscriptions`
- `POST /tools/get_posts`
- `POST /tools/collect_posts`
- `POST /tools/generate_summary`
- `POST /tools/export_pdf`

---

## Docker Compose

```yaml
version: '3.8'

services:
  # MongoDB для хранения постов и истории диалогов
  mongodb:
    image: mongo:7.0-alpine
    container_name: agent_mongodb
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD:-rootpassword}
      MONGO_INITDB_DATABASE: agent_db
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
      - ./init-mongo.js:/docker-entrypoint-initdb.d/init-mongo.js
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - agent_network

  # Redis для кэширования постов и диалогов
  redis:
    image: redis:7-alpine
    container_name: agent_redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-redispassword}
    volumes:
      - redis_data:/data
    healthcheck:
      test: redis-cli --raw incr ping
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - agent_network

  # MCP Tools Server (FastAPI)
  mcp_tools:
    build:
      context: ./mcp_tools
      dockerfile: Dockerfile
    container_name: agent_mcp_tools
    environment:
      MONGODB_URI: mongodb://root:${MONGO_PASSWORD:-rootpassword}@mongodb:27017/agent_db?authSource=admin
      REDIS_URL: redis://:${REDIS_PASSWORD:-redispassword}@redis:6379/0
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      MISTRAL_API_KEY: ${MISTRAL_API_KEY}
      PYROGRAM_API_ID: ${PYROGRAM_API_ID}
      PYROGRAM_API_HASH: ${PYROGRAM_API_HASH}
    ports:
      - "8001-8004:8001-8004"  # 4 endpoints
    depends_on:
      mongodb:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
      - ./output:/app/output  # PDF files
    networks:
      - agent_network
    restart: unless-stopped

  # Mistral Agent (7B model)
  agent:
    build:
      context: ./agent
      dockerfile: Dockerfile
    container_name: agent_mistral
    environment:
      MONGODB_URI: mongodb://root:${MONGO_PASSWORD:-rootpassword}@mongodb:27017/agent_db?authSource=admin
      REDIS_URL: redis://:${REDIS_PASSWORD:-redispassword}@redis:6379/0
      MCP_TOOLS_URL: http://mcp_tools:8001
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      MISTRAL_MODEL: mistral-7b-instruct-v0.2
      DEVICE: cuda  # или cpu
      MAX_TOKENS: 2048
      CONTEXT_WINDOW: 4096
    depends_on:
      - mongodb
      - redis
      - mcp_tools
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    networks:
      - agent_network
    stdin_open: true
    tty: true
    restart: unless-stopped

volumes:
  mongodb_data:
    driver: local
  redis_data:
    driver: local

networks:
  agent_network:
    driver: bridge
```

### .env.example

```bash
# MongoDB
MONGO_PASSWORD=your_secure_password_here

# Redis
REDIS_PASSWORD=your_secure_password_here

# Logging
LOG_LEVEL=INFO

# Mistral (если используется API вместо локального)
MISTRAL_API_KEY=your_api_key_here

# Pyrogram (для Telegram)
PYROGRAM_API_ID=12345678
PYROGRAM_API_HASH=abcdef0123456789abcdef0123456789

# Device (cuda / cpu)
DEVICE=cuda

# Model parameters
MAX_TOKENS=2048
CONTEXT_WINDOW=4096
DIALOG_HISTORY_LIMIT_TOKENS=8000  # Limit for summarization trigger
```

---

## Промпты и инструкции

### System Prompt для Mistral Agent

```python
AGENT_SYSTEM_PROMPT = """
Ты — AI помощник для сбора и обработки новостных дайджестов из Telegram-каналов.

Твои обязанности:
1. Парсить намерение пользователя (какой канал, за какой период)
2. Использовать доступные инструменты (tools) для:
   - Получения списка подписок
   - Поиска постов в канале за период
   - Сбора новых постов если их недостаточно
   - Создания саммари
   - Экспорта в PDF

Доступные инструменты:
- get_subscriptions(): получить список всех подписанных каналов
- get_posts(channel_id, limit, date_from, date_to): получить посты
- collect_posts(channel_id): запустить фоновый сбор новых постов
- generate_summary(posts_text, channel_name): создать саммари
- export_pdf(summary_text, title, channel_name, date_range): сохранить в PDF

Процесс работы:
1. Если пользователь просит "дайджест по Набоке за 3 дня":
   a. Вызови get_subscriptions() → найти channel_id для "Набока"
   b. Вызови get_posts(channel_id="onaboka", date_from="3 дня назад")
   c. Если постов < 5 → вызови collect_posts(channel_id="onaboka")
   d. Подожди 15-30 сек и повторно получи посты
   e. Объедини посты в одну строку
   f. Вызови generate_summary(posts_text)
   g. Вызови export_pdf(summary_text, ...)
   h. Верни пользователю path к PDF

Правила:
- Всегда проверяй наличие постов перед саммаризацией
- Если канал не найден → спроси у пользователя правильное имя
- Если сбор занял > 40 сек → используй имеющиеся посты
- Логируй все действия для отладки
- Обрабатывай ошибки gracefully

Язык: русский
"""
```

### Пример диалога

```
User: "Собери мне дайджест по Набоке за последние 3 дня"

Agent (вывод логики):
1. ✓ Получу список подписок...
2. ✓ Нашел канал: onaboka (Набока)
3. ✓ Получу посты за 2025-10-27 - 2025-10-30...
4. ✓ Найдено 18 постов
5. ✓ Генерирую саммари...
6. ✓ Создаю PDF...

User Respons (возвращаемый результат):
✅ Дайджест готов!
📄 Файл: /output/digest_onaboka_2025-10-27_2025-10-30.pdf
📊 Статистика:
   - Постов: 18
   - Исходный размер: 12.5 KB
   - Саммари: 2.1 KB
   - Компрессия: 83%
```

---

## Error Handling

### Сценарии и обработка

| Сценарий | HTTP Code | Action | Retry? |
|----------|-----------|--------|--------|
| Канал не найден в get_subscriptions | 404 | Спросить у пользователя альтернативное имя | Нет |
| Нет постов в диапазоне дат | 404 | Вызвать collect_posts, ждать | Да (1 раз) |
| Collect_posts уже запущен | 409 | Ждать 30 сек, повторить get_posts | Да (1 раз) |
| MongoDB недоступна | 503 | Вернуть ошибку пользователю | Да (3 раза с backoff) |
| Redis недоступна | 503 | Работать без кэша (операция медленнее) | Автоматически |
| Mistral inference failed | 503 | Retry на другом устройстве или CPU | Да (2 раза) |
| PDF generation failed | 400 | Возвращаемый текст вместо PDF | Нет |
| MCP Tools Server недоступен | 503 | Retry подключения | Да (5 раз) |
| Timeout на collect_posts | 504 | Использовать имеющиеся посты | Нет |

### Пример error handling в Agent

```python
try:
    posts = await mcp_client.get_posts(channel_id, limit=100, date_from=3_days_ago)
except HTTPError as e:
    if e.status_code == 404:
        logger.info(f"No posts found, triggering collection for {channel_id}")
        await mcp_client.collect_posts(channel_id, wait_for_completion=True, timeout=30)
        posts = await mcp_client.get_posts(channel_id, limit=100, date_from=3_days_ago)
    elif e.status_code == 409:
        logger.warning("Collection in progress, waiting...")
        await asyncio.sleep(20)
        posts = await mcp_client.get_posts(channel_id, limit=100, date_from=3_days_ago)
    else:
        raise
except Exception as e:
    logger.error(f"Failed to retrieve posts: {e}", exc_info=True)
    raise AgentException(f"Не удалось получить посты: {str(e)}")
```

---

## Рекомендации по улучшению

### 1. **Архитектура MCP Tools**

**Текущий подход:** 4 отдельных port на одном сервере (8001-8004)

**Рекомендация:** Объединить в один FastAPI с namespace:
```
POST /api/v1/subscriptions
POST /api/v1/posts
POST /api/v1/posts/collect
POST /api/v1/summarize
POST /api/v1/export/pdf
```

**Преимущества:**
- Одна точка входа → проще балансировка нагрузки
- Shared middleware (auth, logging, metrics)
- Easier deployment & versioning

---

### 2. **Dialog History Management**

**Текущий подход:** Сохранять полный диалог в MongoDB

**Рекомендация:** Многоуровневое кэширование:
```
1. Redis (последние 10 сообщений) — быстрый доступ
2. MongoDB (полная история) — долгосрочное хранилище
3. Trigger саммаризации: если токены > 8000
   - Вызвать summarize на истории
   - Заменить старый диалог на "Summary: ..."
   - Освободить контекст для новых сообщений
```

**Код примера:**
```python
async def check_and_summarize_history(session_id: str, token_limit: int = 8000):
    history_tokens = await count_tokens(session_id)
    if history_tokens > token_limit:
        logger.info(f"History exceeds {token_limit} tokens, summarizing...")
        summary = await mcp_client.generate_summary(
            await get_dialog_text(session_id),
            channel_name="Dialog History"
        )
        await compress_dialog_history(session_id, summary)
```

---

### 3. **Retry логика с exponential backoff**

**Использовать:** `tenacity` library

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def get_posts_with_retry(channel_id: str):
    return await mcp_client.get_posts(channel_id)
```

---

### 4. **Monitoring & Observability**

**Добавить метрики:**
```python
# Prometheus metrics
tool_call_duration = Histogram('agent_tool_call_seconds', 'Tool call duration', ['tool_name'])
dialog_history_size = Gauge('agent_dialog_tokens', 'Current dialog token count', ['session_id'])
errors_total = Counter('agent_errors_total', 'Total errors', ['error_type'])
```

**Логирование:**
```python
logger.info(f"Tool call", extra={
    "tool": "get_posts",
    "channel_id": "onaboka",
    "duration_ms": 1234,
    "status": "success"
})
```

---

### 5. **Async/await для параллелизма**

**Где применить:**
```python
# Параллельный сбор постов из нескольких каналов
async def get_multiple_digests(channels: List[str]):
    tasks = [
        get_posts(channel_id)
        for channel_id in channels
    ]
    return await asyncio.gather(*tasks)
```

---

### 6. **Type hints everywhere**

**Пример:**
```python
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

async def get_posts(
    channel_id: str,
    limit: int = 100,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> Dict[str, Any]:
    """Get posts from channel with optional date filtering."""
    pass
```

---

### 7. **Testing strategy**

**Структура тестов:**
```
tests/
├── unit/
│   ├── test_agent_logic.py
│   ├── test_mcp_client.py
│   └── test_dialog_manager.py
├── integration/
│   ├── test_agent_with_mcp_tools.py
│   └── test_mongodb_redis_integration.py
└── fixtures/
    ├── mock_posts.json
    └── mock_subscriptions.json
```

**Пример unit test:**
```python
@pytest.mark.asyncio
async def test_parse_user_intent():
    user_input = "собери дайджест по Набоке за 3 дня"
    intent = parse_intent(user_input)
    assert intent.channel == "onaboka"
    assert intent.days == 3
    assert intent.action == "digest"
```

---

### 8. **Graceful shutdown**

**Добавить в agent:**
```python
async def shutdown(signal):
    logger.info(f"Received {signal}, shutting down gracefully...")
    await dialog_manager.save_state()
    await mcp_client.close()
    await mongodb.close()
    await redis.close()

for sig in (signal.SIGINT, signal.SIGTERM):
    asyncio.get_event_loop().add_signal_handler(
        sig, lambda s=sig: asyncio.create_task(shutdown(s))
    )
```

---

## Файлы конфигурации

### init-mongo.js

```javascript
db = db.getSiblingDB('agent_db');

db.createCollection('dialogs');
db.createCollection('posts');
db.createCollection('channels');
db.createCollection('collection_jobs');

db.dialogs.createIndex({ session_id: 1, created_at: 1 });
db.posts.createIndex({ channel_id: 1, date: 1 });
db.posts.createIndex({ channel_id: 1 });
db.channels.createIndex({ channel_id: 1 }, { unique: true });

db.channels.insertMany([
  {
    channel_id: "onaboka",
    channel_name: "Набока",
    description: "Блог про ML",
    subscribers: 5000
  }
]);

print("✓ MongoDB initialized with collections and indexes");
```

---

## Запуск

```bash
# 1. Создать .env из .env.example
cp .env.example .env

# 2. Запустить стек
docker-compose up -d

# 3. Проверить здоровье
docker-compose ps

# 4. Смотреть логи
docker-compose logs -f agent

# 5. Подключиться к агенту
docker exec -it agent_mistral python main.py
```

---

## Что генерирует Cursor

На основе этих спек Cursor может автоматически создать:

1. ✅ `agent/agent.py` — main agent logic с tool calling
2. ✅ `agent/mcp_client.py` — HTTP client для MCP tools
3. ✅ `agent/dialog_manager.py` — MongoDB integration for history
4. ✅ `mcp_tools/main.py` — FastAPI endpoints
5. ✅ `mcp_tools/tools/` — все 5 функций инструментов
6. ✅ `mcp_tools/db/mongo.py` — MongoDB queries
7. ✅ `mcp_tools/db/redis.py` — Redis caching
8. ✅ Tests для ключевых компонентов
9. ✅ Docker files и docker-compose.yml
10. ✅ CI/CD конфиг (если нужен)

---

## Дополнительные ресурсы

- [Mistral Models](https://docs.mistral.ai/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Motor (async MongoDB)](https://motor.readthedocs.io/)
- [Redis-py](https://redis-py.readthedocs.io/)
- [Langchain Tool Calling](https://python.langchain.com/docs/modules/tools/)
- [Docker Compose](https://docs.docker.com/compose/)
