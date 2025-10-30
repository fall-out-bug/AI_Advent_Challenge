# Day 11 MCP Tools API Reference

API documentation for all MCP (Model Context Protocol) tools available in the Butler Bot.

## Overview

All tools are accessible via the MCP server running on port 8004 (default). Tools return JSON dictionaries with `status` field indicating success or error.

## Reminder Tools

### `add_task`

Create a new task.

**Parameters:**
- `user_id` (int, required): User ID (must be > 0)
- `title` (str, required): Task title (max 256 chars)
- `description` (str, optional): Task description (max 2048 chars)
- `deadline` (str, optional): ISO format deadline string
- `priority` (str, optional): Priority level - "high", "medium", or "low" (default: "medium")
- `tags` (list[str], optional): List of tags (max 50, each max 32 chars)

**Request Example:**
```json
{
  "user_id": 12345,
  "title": "Buy groceries",
  "description": "milk, bread, eggs",
  "deadline": "2025-12-31T10:00:00",
  "priority": "high",
  "tags": ["shopping", "urgent"]
}
```

**Success Response:**
```json
{
  "task_id": "507f1f77bcf86cd799439011",
  "created_at": "2025-01-15T10:00:00",
  "status": "created"
}
```

**Error Response:**
```json
{
  "status": "error",
  "error": "user_id must be a positive integer"
}
```

---

### `list_tasks`

List user tasks with filtering.

**Parameters:**
- `user_id` (int, required): User ID (must be > 0)
- `status` (str, optional): Filter by status - "all", "active", or "completed" (default: "active")
- `limit` (int, optional): Maximum tasks to return (max 500, default: 100)

**Request Example:**
```json
{
  "user_id": 12345,
  "status": "active",
  "limit": 10
}
```

**Success Response:**
```json
{
  "tasks": [
    {
      "id": "507f1f77bcf86cd799439011",
      "title": "Buy groceries",
      "description": "milk, bread, eggs",
      "priority": "high",
      "completed": false,
      "deadline": "2025-12-31T10:00:00",
      "tags": ["shopping"]
    }
  ],
  "total": 5,
  "filtered": 1
}
```

**Error Response:**
```json
{
  "status": "error",
  "error": "user_id must be a positive integer",
  "tasks": [],
  "total": 0,
  "filtered": 0
}
```

---

### `update_task`

Update task fields by ID.

**Parameters:**
- `task_id` (str, required): Task ID string
- `updates` (dict, required): Dictionary of fields to update

**Allowed Fields:**
- `title` (str): Task title (max 256 chars)
- `description` (str): Task description (max 2048 chars)
- `deadline` (str): ISO format deadline
- `priority` (str): "high", "medium", or "low"
- `completed` (bool): Completion status
- `tags` (list[str]): List of tags

**Request Example:**
```json
{
  "task_id": "507f1f77bcf86cd799439011",
  "updates": {
    "completed": true,
    "priority": "high"
  }
}
```

**Success Response:**
```json
{
  "task_id": "507f1f77bcf86cd799439011",
  "updated_fields": ["completed", "priority"],
  "status": "updated"
}
```

**Task Not Found:**
```json
{
  "task_id": "507f1f77bcf86cd799439011",
  "updated_fields": [],
  "status": "not_found"
}
```

---

### `delete_task`

Delete a task by ID.

**Parameters:**
- `task_id` (str, required): Task ID string

**Request Example:**
```json
{
  "task_id": "507f1f77bcf86cd799439011"
}
```

**Success Response:**
```json
{
  "status": "deleted",
  "task_id": "507f1f77bcf86cd799439011"
}
```

**Task Not Found:**
```json
{
  "status": "not_found",
  "task_id": "507f1f77bcf86cd799439011"
}
```

---

### `get_summary`

Get a summary of tasks for a timeframe.

**Parameters:**
- `user_id` (int, required): User ID (must be > 0)
- `timeframe` (str, optional): Timeframe - "today", "tomorrow", or "week" (default: "today")

**Request Example:**
```json
{
  "user_id": 12345,
  "timeframe": "today"
}
```

**Success Response:**
```json
{
  "tasks": [
    {
      "id": "507f1f77bcf86cd799439011",
      "title": "Buy groceries",
      "priority": "high",
      "completed": false
    }
  ],
  "stats": {
    "total": 5,
    "high_priority": 2,
    "completed": 1
  }
}
```

---

## NLP Tools

### `parse_task_intent`

Parse natural language text into task intent.

**Parameters:**
- `text` (str, required): Natural language text describing the task
- `user_context` (dict, optional): User context (currently unused)

**Request Example:**
```json
{
  "text": "Buy milk tomorrow at 5pm",
  "user_context": {}
}
```

**Success Response (with intent):**
```json
{
  "needs_clarification": false,
  "title": "Buy milk",
  "description": "",
  "deadline": "2025-01-16T17:00:00",
  "priority": "medium",
  "tags": []
}
```

**Response (needs clarification):**
```json
{
  "needs_clarification": true,
  "questions": [
    {
      "text": "What priority level?",
      "field": "priority"
    },
    {
      "text": "When is the deadline?",
      "field": "deadline"
    }
  ]
}
```

---

## Digest Tools

### `add_channel`

Subscribe to a Telegram channel for digests.

**Parameters:**
- `user_id` (int, required): User ID (must be > 0)
- `channel_username` (str, required): Channel username (without @)

**Request Example:**
```json
{
  "user_id": 12345,
  "channel_username": "tech_news"
}
```

**Success Response:**
```json
{
  "status": "subscribed",
  "channel_id": "507f1f77bcf86cd799439011"
}
```

**Already Subscribed:**
```json
{
  "status": "already_subscribed",
  "channel_id": "507f1f77bcf86cd799439011"
}
```

---

### `list_channels`

List subscribed channels for a user.

**Parameters:**
- `user_id` (int, required): User ID (must be > 0)
- `limit` (int, optional): Maximum channels to return (default: 100)

**Request Example:**
```json
{
  "user_id": 12345,
  "limit": 10
}
```

**Success Response:**
```json
{
  "channels": [
    {
      "id": "507f1f77bcf86cd799439011",
      "channel_username": "tech_news",
      "tags": ["technology"],
      "active": true
    }
  ],
  "count": 1
}
```

---

### `delete_channel`

Unsubscribe from a channel.

**Parameters:**
- `user_id` (int, required): User ID (must be > 0)
- `channel_id` (str, required): Channel ID string

**Request Example:**
```json
{
  "user_id": 12345,
  "channel_id": "507f1f77bcf86cd799439011"
}
```

**Success Response:**
```json
{
  "status": "deleted",
  "channel_id": "507f1f77bcf86cd799439011"
}
```

---

### `get_channel_digest`

Get a digest of recent channel posts.

**Parameters:**
- `user_id` (int, required): User ID (must be > 0)
- `hours` (int, optional): Number of hours to look back (default: 24)

**Request Example:**
```json
{
  "user_id": 12345,
  "hours": 24
}
```

**Success Response:**
```json
{
  "digests": [
    {
      "channel": "tech_news",
      "summary": "Summary of recent posts...",
      "post_count": 5
    }
  ]
}
```

---

## Error Handling

All tools follow consistent error handling:

1. **Validation Errors**: Invalid input parameters return `{"status": "error", "error": "message"}`
2. **Not Found Errors**: Missing resources return `{"status": "not_found", ...}`
3. **Database Errors**: Internal errors return `{"status": "error", "error": "message"}`

## Rate Limits

- No explicit rate limits, but tools log all operations
- Database queries are optimized with indexes
- Task limits: max 500 tasks per user query
- Tag limits: max 50 tags, each max 32 chars

## Notes

- All timestamps are in ISO 8601 format (UTC)
- Task IDs are MongoDB ObjectIds (24-char hex strings)
- Channel usernames should not include the @ symbol
- Priority values are case-insensitive but normalized to lowercase

