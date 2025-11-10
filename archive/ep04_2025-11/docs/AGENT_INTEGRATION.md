# MCP-Aware Agent Integration Guide

[English](AGENT_INTEGRATION.md) | [Русский](AGENT_INTEGRATION.ru.md)

## Overview

The MCP-aware agent is an intelligent assistant that can automatically discover and use MCP (Model Context Protocol) tools to fulfill user requests. It integrates with a local LLM (Mistral) to understand user intent and execute appropriate tools.

## Architecture

```
┌─────────────────┐
│  Telegram Bot   │
│   (ButlerBot)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ MCPAwareAgent   │
│                 │
│  - LLM Client   │
│  - Tools        │
│  - Registry     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────────┐
│ Robust │ │   Dialog     │
│  MCP   │ │   Manager    │
│ Client │ │              │
└───┬────┘ └──────┬───────┘
    │             │
    ▼             ▼
┌────────┐   ┌──────────┐
│   MCP  │   │ MongoDB  │
│ Server │   │          │
└────────┘   └──────────┘
```

## Components

### 1. MCPAwareAgent

The core agent that processes user requests using LLM and MCP tools.

**Location:** `src/domain/agents/mcp_aware_agent.py`

**Features:**
- Automatic tool discovery via MCPToolsRegistry
- LLM-based tool selection
- Parameter validation
- Error handling with metrics

**Usage:**
```python
from src.domain.agents.mcp_aware_agent import MCPAwareAgent
from src.presentation.mcp.client import MCPClient
from shared_package.clients.unified_client import UnifiedModelClient

# Initialize
mcp_client = MCPClient()
llm_client = UnifiedModelClient()
agent = MCPAwareAgent(mcp_client=mcp_client, llm_client=llm_client)

# Process request
request = AgentRequest(
    user_id=12345,
    message="Собери дайджест по каналу onaboka",
    session_id="session_123"
)
response = await agent.process(request)
```

### 2. MCPToolsRegistry

Caches and manages MCP tool metadata.

**Location:** `src/presentation/mcp/tools_registry.py`

**Features:**
- Tool discovery caching (5 minute TTL)
- Prompt building for LLM
- Tool metadata parsing

**Usage:**
```python
from src.presentation.mcp.tools_registry import MCPToolsRegistry

registry = MCPToolsRegistry(mcp_client=client)
tools = await registry.discover_tools()
prompt = registry.build_tools_prompt()
```

### 3. RobustMCPClient

Wraps base MCP client with retry logic and error handling.

**Location:** `src/infrastructure/clients/mcp_client_robust.py`

**Features:**
- Exponential backoff retry (max 3 attempts)
- Error classification (retryable vs non-retryable)
- Prometheus metrics integration

**Configuration:**
- `MAX_RETRIES = 3`
- `INITIAL_WAIT = 1.0` seconds
- `MAX_WAIT = 10.0` seconds
- `EXPONENTIAL_BASE = 2.0`

**Usage:**
```python
from src.infrastructure.clients.mcp_client_robust import RobustMCPClient
from src.presentation.mcp.client import MCPClient

base_client = MCPClient()
robust_client = RobustMCPClient(base_client=base_client)
result = await robust_client.call_tool("get_posts", {"channel_id": "test"})
```

### 4. DialogManager

Manages conversation history in MongoDB with automatic compression.

**Location:** `src/infrastructure/dialogs/dialog_manager.py`

**Features:**
- Message storage in MongoDB
- Automatic compression when token limit exceeded (8000 tokens)
- Context retrieval with token limits

**Configuration:**
- `COMPRESSION_THRESHOLD = 8000` tokens
- `MAX_CONTEXT_TOKENS = 8000`

**Usage:**
```python
from src.infrastructure.dialogs.dialog_manager import DialogManager
from src.infrastructure.database.mongo import get_db

mongodb = await get_db()
manager = DialogManager(mongodb=mongodb, llm_client=llm_client)

# Add messages
await manager.add_message("session_123", "user", "Hello!")
await manager.add_message("session_123", "assistant", "Hi there!")

# Get context
context = await manager.get_context("session_123", max_tokens=1000)
```

### 5. HistoryCompressor

Compresses dialog history using LLM when token limit is exceeded.

**Location:** `src/infrastructure/dialogs/history_compressor.py`

**Features:**
- LLM-based summarization
- Preserves key context
- Configurable compression parameters

**Usage:**
```python
from src.infrastructure.dialogs.history_compressor import HistoryCompressor

compressor = HistoryCompressor(llm_client=llm_client)
summary = await compressor.compress("session_123", messages)
```

## Integration with Telegram Bot

The agent is integrated into ButlerBot for natural language processing:

```python
# In butler_bot.py
async def handle_natural_language(self, message: Message) -> None:
    # Get dialog context
    context = await self._dialog_manager.get_context(session_id)

    # Create agent request
    request = AgentRequest(
        user_id=message.from_user.id,
        message=message.text,
        session_id=session_id,
        context={"dialog_context": context}
    )

    # Process with agent
    response = await self._agent.process(request)

    # Save dialog
    await self._dialog_manager.add_message(session_id, "user", message.text)
    await self._dialog_manager.add_message(session_id, "assistant", response.text)

    # Send response
    await message.answer(response.text)
```

## Configuration

### Environment Variables

- `TELEGRAM_BOT_TOKEN`: Telegram bot token (required)
- `MCP_SERVER_URL`: MCP server URL (optional, defaults to stdio)
- `MONGODB_URL`: MongoDB connection string (required)
- `DB_NAME`: Database name (default: `ai_challenge`)

### Default Constants

- **Agent:**
  - `DEFAULT_MODEL_NAME = "mistral"`
  - `DEFAULT_MAX_TOKENS = 2048`
  - `DEFAULT_TEMPERATURE = 0.7`

- **Dialog Manager:**
  - `COMPRESSION_THRESHOLD = 8000` tokens
  - `MAX_CONTEXT_TOKENS = 8000`

- **Retry Logic:**
  - `MAX_RETRIES = 3`
  - `INITIAL_WAIT = 1.0` seconds
  - `MAX_WAIT = 10.0` seconds

## Monitoring

Prometheus metrics are automatically collected:

- `agent_requests_total`: Total agent requests
- `agent_tokens_used_total`: Total tokens used
- `agent_request_duration_seconds`: Request duration histogram
- `agent_tools_used_total`: Tool usage counter
- `mcp_client_retries_total`: Retry counter
- `llm_requests_total`: LLM request counter

## Error Handling

The agent handles errors gracefully:

1. **LLM Errors:** Returns error response with details
2. **Invalid Tools:** Validates tool existence before execution
3. **MCP Errors:** Retries with exponential backoff
4. **MongoDB Errors:** Logs and continues (graceful degradation)

## Testing

Run tests:

```bash
# Unit tests
pytest tests/domain/agents/
pytest tests/infrastructure/clients/test_mcp_client_robust.py
pytest tests/infrastructure/dialogs/

# Integration tests
pytest tests/integration/
```

## Best Practices

1. **Session Management:** Use unique session IDs per user
2. **Token Limits:** Monitor token usage to avoid context overflow
3. **Error Monitoring:** Check Prometheus metrics for error rates
4. **Tool Discovery:** Registry caches tools for 5 minutes
5. **Graceful Shutdown:** Use GracefulShutdown manager for clean shutdown

## Troubleshooting

### Agent not selecting tools

- Check if tools are discovered: `await registry.discover_tools()`
- Verify LLM prompt includes tool descriptions
- Check LLM response format (should be JSON for tool calls)

### High retry rates

- Check MCP server availability
- Verify network connectivity
- Review error logs for root cause

### Dialog compression issues

- Ensure LLM client is configured
- Check MongoDB connection
- Verify token estimation accuracy
