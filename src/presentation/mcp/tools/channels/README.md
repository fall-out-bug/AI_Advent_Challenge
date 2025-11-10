# Channel MCP Tools

This module provides MCP (Model Context Protocol) tools for Telegram channel operations including digest generation, metadata retrieval, and post collection.

## Available Tools

### 1. `generate_channel_digest_by_name`

Generates a text digest for a Telegram channel by name.

**Parameters:**
- `channel_name` (string): Telegram channel username (e.g., "@channel")
- `timeframe` (string, optional): Time range ("last_24h", "last_7d", "all")
- `max_posts` (integer, optional): Maximum number of posts to include

**Returns:**
- Text digest with channel posts summary

**Example:**
```python
result = await mcp_client.call_tool(
    "generate_channel_digest_by_name",
    {
        "channel_name": "@technews",
        "timeframe": "last_24h",
        "max_posts": 10
    }
)
```

### 2. `generate_pdf_digest_by_name`

Generates a PDF digest for a Telegram channel by name.

**Parameters:**
- `channel_name` (string): Telegram channel username
- `timeframe` (string, optional): Time range
- `include_metadata` (boolean, optional): Include channel title/description

**Returns:**
- PDF file path (cached for 1 hour)

**Example:**
```python
result = await mcp_client.call_tool(
    "generate_pdf_digest_by_name",
    {
        "channel_name": "@technews",
        "timeframe": "last_7d",
        "include_metadata": True
    }
)
```

### 3. `get_channel_metadata`

Retrieves channel metadata (title, description, subscriber count).

**Parameters:**
- `channel_name` (string): Telegram channel username

**Returns:**
- Channel metadata dictionary

**Example:**
```python
metadata = await mcp_client.call_tool(
    "get_channel_metadata",
    {"channel_name": "@technews"}
)
```

### 4. `list_subscribed_channels`

Lists all channels subscribed for digest generation.

**Parameters:** None

**Returns:**
- List of subscribed channel names

**Example:**
```python
channels = await mcp_client.call_tool(
    "list_subscribed_channels",
    {}
)
```

### 5. `subscribe_channel_with_collection`

Subscribes to a channel and starts automatic post collection.

**Parameters:**
- `channel_name` (string): Telegram channel username
- `auto_collect` (boolean, optional): Enable automatic hourly collection

**Returns:**
- Subscription confirmation

**Example:**
```python
result = await mcp_client.call_tool(
    "subscribe_channel_with_collection",
    {
        "channel_name": "@technews",
        "auto_collect": True
    }
)
```

## Tool Implementation

### File Structure

```
channels/
├── channel_digest.py          # Main digest generation tool
├── channel_metadata.py        # Metadata retrieval tool
└── README.md                  # This file
```

### Key Components

- **Channel Resolution**: Resolves channel names to Telegram entities
- **Post Collection**: Automatic hourly collection via `PostFetcherWorker`
- **Deduplication**: Hybrid deduplication (message_id + content_hash)
- **Caching**: PDF caching with 1-hour TTL
- **MongoDB Storage**: Posts stored with 7-day TTL

## Integration

These tools are automatically discovered by the MCP-aware agent:

```python
from src.domain.agents.mcp_aware_agent import MCPAwareAgent

agent = MCPAwareAgent()
# Tools automatically discovered via MCPToolsRegistry
response = await agent.process("Generate digest for @technews")
```

## Related Documentation

- [MCP Tools API](../../../../../docs/day12/api.md)
- [PDF Digest User Guide](../../../../../docs/day12/USER_GUIDE.md)
- [Channel Resolution Strategy](../../../../../docs/reference/en/CHANNEL_RESOLUTION.md)
