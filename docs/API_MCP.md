# MCP Tool API (EN)

The Butler MCP server exposes a curated set of tools for digest and channel
operations, plus NLP intent helpers. Reminder/task tools and PDF digest have
been deprecated (see Stage 00_02 decisions).

## 1. Available Tools

| Tool Name | Purpose | Status |
|-----------|---------|--------|
| `channels_list` | List subscribed channels | Active |
| `channels_add` | Subscribe to a new channel | Active |
| `channels_remove` | Remove an existing subscription | Active |
| `channels_refresh` | Trigger content refresh | Active |
| `digest_generate` | Generate digest for channel(s) | Active |
| `digest_get_last` | Inspect latest digest metadata | Active |
| `nlp_parse_intent` | Parse intent classification sample | Active |

Deprecated tools (reminders, homework review, PDF digest) are hidden from
discovery and slated for archival.

## 2. Channel Tools

### 2.1 `channels_list`

- **Args**: `{ "user_id": int, "limit": int | null, "include_tags": bool | null }`
- **Returns**:

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

- **Args**: `{ "user_id": int, "channel_username": str, "tags": list[str] | null }`
- **Returns**:

```json
{
  "status": "subscribed",
  "channel_id": "507f1f77bcf86cd799439011"
}
```

Errors include `"already_subscribed"` or `"channel_not_found"`.

### 2.3 `channels_remove`

- **Args**: `{ "user_id": int, "channel_id": str | null, "channel_username": str | null }`
- **Returns**:

```json
{
  "status": "removed",
  "channel_id": "507f1f77bcf86cd799439011"
}
```

### 2.4 `channels_refresh`

- **Args**: `{ "channel_id": str | null, "channel_username": str | null, "hours": int | null }`
- **Effect**: Schedules immediate fetch job; returns `{"status": "scheduled"}`.

## 3. Digest Tools

### 3.1 `digest_generate`

- **Args**:

```json
{
  "user_id": 12345,
  "channel": "tech_news",
  "hours": 24,
  "format": "markdown"
}
```

- **Returns**:

```json
{
  "status": "success",
  "generated_at": "2025-11-09T11:00:00Z",
  "digest": {
    "channel": "tech_news",
    "summary": "Summary text…",
    "post_count": 5,
    "items": [
      {"title": "...", "url": "...", "summary": "..."}
    ]
  }
}
```

Supports `format` = `"markdown"` | `"json"` (default markdown).

### 3.2 `digest_get_last`

- **Args**: `{ "channel": str }`
- **Returns**:

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

## 4. NLP Tool

### `nlp_parse_intent`

- **Args**: `{ "text": str, "context": dict | null }`
- **Returns**:

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

Useful for CLI backoffice validation and automated testing.

## 5. Error Model

All tools return a consistent envelope:

```json
{
  "status": "error",
  "error": "human-readable message",
  "details": {...}  // optional
}
```

Common errors:

- `invalid_user_id`
- `channel_not_found`
- `digest_unavailable`
- `nlp_timeout`

## 6. Discovery & Health

```python
from src.presentation.mcp.client import MCPClient

client = MCPClient()
tools = await client.discover_tools()
print([tool["name"] for tool in tools])  # Active tool list
```

Health endpoint: `GET /health` (returns `{"status": "ok"}`).

## 7. Cross-References

- CLI backoffice (Stage 00_02) will reuse these tools internally.
- Telegram bot digest/channel flows map one-to-one onto this API.
- Russian localisation: `docs/API_MCP.ru.md`.

