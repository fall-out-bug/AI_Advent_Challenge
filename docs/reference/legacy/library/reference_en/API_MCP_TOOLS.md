# MCP Tools API Reference

This document describes the MCP (Model Context Protocol) tools available for task management and channel digests.

## Task Management Tools

### add_task

Create a new task with optional scheduling.

**Args**:
- `user_id` (int): Telegram user ID (must be > 0)
- `title` (str): Task title (max 256 chars, required)
- `description` (str): Optional description (max 2048 chars)
- `deadline` (str|None): ISO datetime string (e.g., "2025-12-01T15:00:00Z")
- `priority` (str): Priority level - "low"|"medium"|"high" (default: "medium")
- `tags` (list[str]): Optional tags (max 50 tags, each max 32 chars)

**Returns**:
```json
{
  "task_id": "507f1f77bcf86cd799439011",
  "created_at": "2025-10-29T12:00:00Z",
  "status": "created"
}
```

**Error Response**:
```json
{
  "status": "error",
  "error": "user_id must be a positive integer"
}
```

**Example**:
```python
from src.presentation.mcp.client import MCPClient

client = MCPClient()
result = await client.call_tool("add_task", {
    "user_id": 12345,
    "title": "Call mom",
    "deadline": "2025-10-30T15:00:00Z",
    "priority": "high"
})
print(result["task_id"])
```

### list_tasks

List user tasks with filtering.

**Args**:
- `user_id` (int): Telegram user ID (must be > 0)
- `status` (str): Filter status - "all"|"active"|"completed" (default: "active")
- `limit` (int): Maximum tasks to return (max 500, default: 100)

**Returns**:
```json
{
  "tasks": [
    {
      "id": "507f1f77bcf86cd799439011",
      "title": "Call mom",
      "description": "",
      "deadline": "2025-10-30T15:00:00Z",
      "priority": "high",
      "completed": false,
      "tags": []
    }
  ],
  "total": 10,
  "filtered": 5
}
```

**Example**:
```python
result = await client.call_tool("list_tasks", {
    "user_id": 12345,
    "status": "active",
    "limit": 50
})
```

### update_task

Update task fields by ID.

**Args**:
- `task_id` (str): Task ID string (required)
- `updates` (dict): Dictionary of fields to update

**Allowed fields**: `title`, `description`, `deadline`, `priority`, `completed`, `tags`

**Returns**:
```json
{
  "task_id": "507f1f77bcf86cd799439011",
  "updated_fields": ["priority", "completed"],
  "status": "updated"
}
```

**Example**:
```python
result = await client.call_tool("update_task", {
    "task_id": "507f1f77bcf86cd799439011",
    "updates": {
        "priority": "high",
        "completed": true
    }
})
```

### delete_task

Delete a task by ID.

**Args**:
- `task_id` (str): Task ID string (required)

**Returns**:
```json
{
  "status": "deleted",
  "task_id": "507f1f77bcf86cd799439011"
}
```

### get_summary

Get a summary of tasks for a timeframe.

**Args**:
- `user_id` (int): Telegram user ID (must be > 0)
- `timeframe` (str): Time period - "today"|"tomorrow"|"week"|"last_24h"|"last_7d" (default: "today")

**Returns**:
```json
{
  "tasks": [...],
  "stats": {
    "total": 10,
    "completed": 3,
    "overdue": 1,
    "high_priority": 2
  }
}
```

**Example**:
```python
result = await client.call_tool("get_summary", {
    "user_id": 12345,
    "timeframe": "today"
})
print(f"Total tasks: {result['stats']['total']}")
```

## Channel Digest Tools

### add_channel

Subscribe to a Telegram channel for digest.

**Args**:
- `user_id` (int): Telegram user ID
- `channel_username` (str): Channel username without @
- `tags` (list[str]): Optional annotation tags

**Returns**:
```json
{
  "channel_id": "507f1f77bcf86cd799439011",
  "status": "subscribed"
}
```

### get_channel_digest

Generate digest from subscribed channels.

**Args**:
- `user_id` (int): Telegram user ID
- `hours` (int): Hours to look back (default: 24)

**Returns**:
```json
{
  "digests": [
    {
      "channel": "tech_news",
      "summary": "Summary of posts in Russian...",
      "post_count": 5,
      "tags": []
    }
  ],
  "generated_at": "2025-10-29T12:00:00Z"
}
```

**Example**:
```python
result = await client.call_tool("get_channel_digest", {
    "user_id": 12345,
    "hours": 24
})
for digest in result["digests"]:
    print(f"{digest['channel']}: {digest['summary']}")
```

## Error Handling

All tools return consistent error responses:

```json
{
  "status": "error",
  "error": "Human-readable error message"
}
```

Common errors:
- `user_id must be a positive integer`: Invalid user ID
- `title is required and must be a string`: Missing or invalid title
- `Failed to create task: ...`: Database or validation error

## Tool Discovery

Discover available tools programmatically:

```python
client = MCPClient()
tools = await client.discover_tools()
for tool in tools:
    print(f"{tool['name']}: {tool['description']}")
```
