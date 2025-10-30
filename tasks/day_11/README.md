# Day 11: 24/7 Personal Butler Telegram Bot

A comprehensive Telegram bot for task management and channel digest with natural language processing, scheduled notifications, and MCP integration.

## Overview

The Butler Bot provides:
- **Natural Language Task Management**: Create tasks using plain English
- **Automated Summaries**: Daily morning task summaries
- **Channel Digests**: Evening digests from subscribed Telegram channels
- **Interactive Menu**: Easy navigation via inline keyboards
- **MCP Integration**: Tools accessible via Model Context Protocol

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────┐
│ Telegram Bot│────▶│  MCP Server  │────▶│ MongoDB  │
└─────────────┘     └──────────────┘     └──────────┘
                            ▲
                            │
                    ┌───────┴────────┐
                    │               │
            ┌───────▼───┐    ┌──────▼─────┐
            │ Bot Handlers│   │   Worker   │
            └────────────┘    └────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Python 3.11+ (for local development)

### Running with Docker Compose

1. Set environment variable:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
```

2. Start all services:
```bash
docker-compose -f docker-compose.day11.yml up -d
```

3. Verify services:
```bash
docker-compose -f docker-compose.day11.yml ps
```

Services:
- `mongodb`: MongoDB database (port 27017)
- `mcp-server`: MCP server (port 8004)
- `telegram-bot`: Telegram bot service
- `summary-worker`: Background worker for scheduled notifications

### Local Development

1. Install dependencies:
```bash
poetry install
```

2. Start MongoDB:
```bash
docker-compose -f docker-compose.day11.yml up -d mongodb
```

3. Start MCP server:
```bash
python -m src.presentation.mcp.server
```

4. Start bot:
```bash
export TELEGRAM_BOT_TOKEN="your_token"
python -m src.presentation.bot.butler_bot
```

5. Start worker (in separate terminal):
```bash
export TELEGRAM_BOT_TOKEN="your_token"
python -m src.workers.summary_worker
```

## Usage

### Commands

- `/start` - Start the bot
- `/help` - Show help message
- `/menu` - Open main menu

### Natural Language Task Creation

Send plain text messages to create tasks:

```
"Buy milk tomorrow at 5pm"
"High priority: Finish project report by Friday"
"Review code with tags: urgent, backend"
```

The bot will:
1. Parse your intent
2. Ask clarifying questions if needed
3. Create the task automatically

### Menu Navigation

Use `/menu` to access:
- **Tasks**: View, complete, delete tasks
- **Channels**: Subscribe to Telegram channels for digests

### Scheduled Notifications

- **Morning Summary**: Sent at 9:00 AM (configurable)
- **Evening Digest**: Sent at 8:00 PM (configurable)
- **Quiet Hours**: No notifications between 22:00-08:00

## Configuration

Environment variables:

```bash
# Required
TELEGRAM_BOT_TOKEN=your_bot_token

# MongoDB
MONGODB_URL=mongodb://localhost:27017
DB_NAME=butler

# MCP Server
MCP_SERVER_URL=http://localhost:8004

# Scheduling
MORNING_SUMMARY_TIME=09:00
EVENING_DIGEST_TIME=20:00
QUIET_HOURS_START=22
QUIET_HOURS_END=8

# LLM (optional)
LLM_MODEL=mistral-7b-instruct-v0.2
LLM_TEMPERATURE=0.2
```

## Troubleshooting

### Bot not responding

1. Check bot token is correct:
```bash
echo $TELEGRAM_BOT_TOKEN
```

2. Check bot logs:
```bash
docker-compose -f docker-compose.day11.yml logs telegram-bot
```

3. Verify services are running:
```bash
docker-compose -f docker-compose.day11.yml ps
```

### Database connection errors

1. Check MongoDB is accessible:
```bash
docker exec -it butler-mongodb-day11 mongosh --eval "db.runCommand({ ping: 1 })"
```

2. Verify connection string:
```bash
docker-compose -f docker-compose.day11.yml config | grep MONGODB_URL
```

### MCP server errors

1. Check MCP server health:
```bash
curl http://localhost:8004/health
```

2. View MCP logs:
```bash
docker-compose -f docker-compose.day11.yml logs mcp-server
```

### Worker not sending notifications

1. Check worker logs:
```bash
docker-compose -f docker-compose.day11.yml logs summary-worker
```

2. Verify schedule settings:
```bash
docker-compose -f docker-compose.day11.yml config | grep -E "(MORNING|EVENING|QUIET)"
```

3. Check if it's quiet hours:
```python
from datetime import datetime
from src.workers.schedulers import is_quiet_hours
print(is_quiet_hours(datetime.utcnow(), 22, 8))
```

## Testing

Run tests:

```bash
# All tests
pytest

# E2E tests only
pytest src/tests/e2e/ -m e2e

# With coverage
pytest --cov=src --cov-report=term-missing
```

## Project Structure

```
src/
├── application/          # Business logic
│   ├── orchestration/    # Intent orchestrator
│   └── services/         # Date parser, etc.
├── domain/               # Entities and models
├── infrastructure/       # Database, LLM, clients
├── presentation/         # Bot handlers, MCP tools
├── workers/              # Background workers
└── tests/                # Test suite
    ├── e2e/              # End-to-end tests
    ├── application/      # Service tests
    └── presentation/     # Handler tests
```

## API Documentation

See [docs/day11/api.md](../docs/day11/api.md) for MCP tools API reference.

## License

Part of AI Challenge project.

