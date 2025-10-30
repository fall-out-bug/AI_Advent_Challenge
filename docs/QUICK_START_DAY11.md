# Butler Bot Quick Start Guide

This guide helps you get started with Butler Bot's Day 11 improvements: FSM-based conversation flow, natural language task creation, and MCP integration.

## Installation

```bash
# Clone and setup
cd AI_Challenge
make install

# Configure environment
cp .env.example .env
# Edit .env: add TELEGRAM_BOT_TOKEN
```

## Usage Examples

### Creating Tasks via Natural Language

#### Example 1: Simple Task

```
User: "Buy milk"
Bot: "✅ Task added: Buy milk"
```

No clarification needed - intent is clear.

#### Example 2: Task with Deadline

```
User: "Call mom on 2025-12-01 15:00 high"
Bot: "✅ Task added: Call mom"
```

Complete intent with deadline and priority.

#### Example 3: Requires Clarification

```
User: "Remind me to call mom tomorrow"
Bot: "What is the deadline (date and time)?"
User: "2025-12-01 15:00"
Bot: "✅ Task added: Call mom"
```

Bot asks for missing deadline information.

#### Example 4: Russian Language

```
User: "Купить молоко завтра в 15:00"
Bot: "✅ Задача добавлена: Купить молоко"
```

Supports Russian language input.

#### Example 5: Multiple Missing Fields

```
User: "Add task"
Bot: "What should I name the task?"
User: "Buy groceries"
Bot: "What is the deadline (date and time)?"
User: "2025-12-01 15:00"
Bot: "✅ Task added: Buy groceries"
```

Multiple clarification rounds when needed.

### Using Menu Commands

#### Summary Command

```
User: /menu
Bot: [Shows inline keyboard with Summary and Digest buttons]
User: [Clicks "📋 Summary"]
Bot: "📋 Summary (today)

Total: 5
Completed: 2
Overdue: 1
High priority: 2"
```

#### Digest Command

```
User: /menu
Bot: [Shows inline keyboard]
User: [Clicks "📰 Digest"]
Bot: "📰 tech_news: Новости о выпуске iOS 18 с улучшениями производительности..."
```

## Command Reference

### `/task` - Start Task Creation

Enters task creation flow, prompts for natural language input.

```
User: /task
Bot: "What task would you like to add?"
User: "Buy milk tomorrow at 3pm"
Bot: "✅ Task added: Buy milk"
```

### `/menu` - Show Main Menu

Displays inline keyboard with Summary and Digest actions.

## Integration with MCP Tools

Butler Bot uses MCP (Model Context Protocol) tools for task management:

```python
from src.presentation.mcp.client import MCPClient

client = MCPClient()

# Create task programmatically
result = await client.call_tool("add_task", {
    "user_id": 12345,
    "title": "Call mom",
    "deadline": "2025-12-01T15:00:00Z",
    "priority": "high"
})

# Get summary
summary = await client.call_tool("get_summary", {
    "user_id": 12345,
    "timeframe": "today"
})
```

See [API_MCP_TOOLS.md](API_MCP_TOOLS.md) for full API reference.

## Architecture Overview

Butler Bot uses:

1. **FSM (Finite State Machine)**: Manages conversation flow with states:
   - `waiting_for_task`: Initial input
   - `waiting_for_clarification`: Collecting answers

2. **Intent Orchestrator**: Parses natural language, detects missing fields

3. **MCP Tools**: Backend task management and channel digests

See [ARCHITECTURE_FSM.md](ARCHITECTURE_FSM.md) for detailed architecture.

## Troubleshooting

### Bot Not Responding

- Check `TELEGRAM_BOT_TOKEN` in `.env`
- Verify bot is running: `make run-bot` (if available)
- Check logs for errors

### Clarification Not Working

- Ensure `IntentOrchestrator` is properly initialized
- Check FSM storage is configured (MemoryStorage for dev)

### MCP Tools Failing

- Verify MongoDB connection settings
- Check MCP server is accessible
- Review error messages in logs

## Next Steps

- Read [ARCHITECTURE_FSM.md](ARCHITECTURE_FSM.md) for implementation details
- See [API_MCP_TOOLS.md](API_MCP_TOOLS.md) for complete API reference
- Explore test files in `tests/` directory for examples

