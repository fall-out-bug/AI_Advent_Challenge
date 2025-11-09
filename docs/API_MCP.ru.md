# API MCP-инструментов (RU)

Сервер MCP предоставляет инструменты для управления каналами, генерации дайджестов и проверки NLP-интентов. Инструменты для напоминаний, домашек и PDF-отчётов выведены из эксплуатации (см. Stage 00_02).

## 1. Доступные инструменты

| Имя | Назначение | Статус |
|-----|------------|--------|
| `channels_list` | Список подписок | Активен |
| `channels_add` | Подписка на канал | Активен |
| `channels_remove` | Удаление подписки | Активен |
| `channels_refresh` | Принудительная выборка постов | Активен |
| `digest_generate` | Генерация дайджеста | Активен |
| `digest_get_last` | Метаданные последнего дайджеста | Активен |
| `nlp_parse_intent` | Проверка NLP-классификатора | Активен |

## 2. Инструменты каналов

### 2.1 `channels_list`

- **Параметры**: `{ "user_id": int, "limit": int | null, "include_tags": bool | null }`
- **Ответ**:

```json
{
  "status": "success",
  "channels": [
    {
      "channel_id": "507f1f77bcf86cd799439011",
      "username": "tech_news",
      "title": "Tech News",
      "tags": ["analytics"],
      "active": true,
      "subscribed_at": "2025-11-09T10:00:00Z"
    }
  ],
  "count": 1
}
```

### 2.2 `channels_add`

- **Параметры**: `{ "user_id": int, "channel_username": str, "tags": list[str] | null }`
- **Ответ**:

```json
{
  "status": "subscribed",
  "channel_id": "507f1f77bcf86cd799439011"
}
```

Ошибки: `"already_subscribed"`, `"channel_not_found"`.

### 2.3 `channels_remove`

- **Параметры**: `{ "user_id": int, "channel_id": str | null, "channel_username": str | null }`
- **Ответ**:

```json
{
  "status": "removed",
  "channel_id": "507f1f77bcf86cd799439011"
}
```

### 2.4 `channels_refresh`

- **Параметры**: `{ "channel_id": str | null, "channel_username": str | null, "hours": int | null }`
- **Результат**: Планирует задачу на сбор постов → `{"status": "scheduled"}`.

## 3. Инструменты дайджестов

### 3.1 `digest_generate`

- **Параметры**:

```json
{
  "user_id": 12345,
  "channel": "tech_news",
  "hours": 24,
  "format": "markdown"
}
```

- **Ответ**:

```json
{
  "status": "success",
  "generated_at": "2025-11-09T11:00:00Z",
  "digest": {
    "channel": "tech_news",
    "summary": "Краткое содержание…",
    "post_count": 5,
    "items": [
      {"title": "...", "url": "...", "summary": "..."}
    ]
  }
}
```

Поддерживает `format` = `"markdown"` или `"json"`.

### 3.2 `digest_get_last`

- **Параметры**: `{ "channel": str }`
- **Ответ**:

```json
{
  "status": "success",
  "last_digest": {
    "generated_at": "2025-11-08T09:30:00Z",
    "post_count": 3,
    "summary": "…"
  }
}
```

## 4. NLP-инструмент

### `nlp_parse_intent`

- **Параметры**: `{ "text": str, "context": dict | null }`
- **Ответ**:

```json
{
  "status": "success",
  "intent": {
    "mode": "digest",
    "confidence": 0.92,
    "slots": {
      "channel": "tech_news",
      "hours": 24
    },
    "needs_clarification": false
  }
}
```

Используется для CLI backoffice и регрессионных тестов NLP.

## 5. Модель ошибок

Все ошибки имеют общий формат:

```json
{
  "status": "error",
  "error": "человеко-понятное описание",
  "details": {...}
}
```

Типовые ошибки: `invalid_user_id`, `channel_not_found`, `digest_unavailable`, `nlp_timeout`.

## 6. Discovery и здоровье

```python
from src.presentation.mcp.client import MCPClient

client = MCPClient()
tools = await client.discover_tools()
print([tool["name"] for tool in tools])
```

Проверка состояния: `GET /health` → `{"status": "ok"}`.

## 7. Связанные документы

- CLI backoffice (Stage 00_02) использует те же операции.
- Сценарии Telegram-бота для каналов/дайджестов повторяют этот API.
- Англоязычная версия: `docs/API_MCP.md`.

