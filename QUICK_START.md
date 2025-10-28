# Phase 4 - Quick Start Guide

## 🚀 Quick Start (Docker - Recommended)

### Step 1: Start All Services

```bash
# Start everything (local models + MCP server + API)
make docker-up-full
```

**Note**: Models will be downloaded on first run to `./cache/models/` (20-50GB). This cache persists across container rebuilds.

This will start:
- 4 local language models (Qwen, Mistral, TinyLlama, StarCoder)
- MCP Server with Phase 4 features
- Main API

### Step 2: Wait for Services to Initialize

```bash
# Check status
make docker-status

# Watch logs
make docker-logs
```

Models need ~30-60 seconds to load.

### Step 3: Run the Chat Interface

```bash
# Interactive chat
make mcp-chat

# Or streaming chat with animations
make mcp-chat-streaming
```

### Step 4: Try It Out

Once in the chat:
```
You: Create a simple web server in Python
Assistant: [Generates code using MCP tools]
```

Commands in chat:
- `/help` - Show commands
- `/tools` - List available MCP tools
- `/history` - View conversation
- `/exit` - Quit

---

## 🖥️ Local Development (Without Docker)

### Prerequisites

```bash
# Install dependencies
poetry install
# OR
pip install -r requirements.txt
```

### Start Local Models

```bash
# Start local models in another terminal
cd local_models
docker-compose up -d
```

### Run Chat

```bash
# Interactive chat
make mcp-chat

# Streaming chat
make mcp-chat-streaming
```

---

## 📦 Available Services

### Local Models (Ports)

- **Qwen**: http://localhost:8000
- **Mistral**: http://localhost:8001
- **TinyLlama**: http://localhost:8002
- **StarCoder**: http://localhost:8003

### MCP Server Features

- ✅ Result caching
- ✅ Error recovery with retries
- ✅ Plan optimization
- ✅ Context window management
- ✅ Streaming responses

### Available Tools

- `formalize_task` - Convert tasks to structured plans
- `generate_code` - Generate Python code
- `review_code` - Review and improve code
- `generate_tests` - Generate test code
- `format_code` - Format with black
- `analyze_complexity` - Analyze code complexity

---

## 🛠️ Management Commands

```bash
# View all running services
make docker-status

# View logs
make docker-logs

# Stop all services
make docker-down-full

# Rebuild and restart
make docker-down-full
make docker-up-full
```

---

## 🔧 Troubleshooting

### GPU Issues

```bash
# Check GPU
nvidia-smi

# If no GPU, models won't start
# Solution: Use smaller models or CPU fallback
```

### Port Conflicts

```bash
# Check what's using ports
sudo lsof -i :8000
sudo lsof -i :8001

# Kill process if needed
sudo kill -9 <PID>
```

### Services Won't Start

```bash
# Check logs
make docker-logs

# Restart specific service
docker-compose -f docker-compose.full.yml restart mistral-chat
```

### Reset Everything

```bash
# Stop and remove all containers
make docker-down-full

# Remove volumes (CAUTION: deletes data)
docker volume rm ai-challenge-network

# Start fresh
make docker-up-full
```

---

## 📝 Example Session

```bash
# Terminal 1: Start services
make docker-up-full

# Terminal 2: Run chat
make mcp-chat-streaming

# In chat:
You: Create a REST API with FastAPI
Assistant: [Displays generated code]

You: Review this code
Assistant: [Displays code review results]

You: Generate tests for it
Assistant: [Displays generated tests]
```

---

## 🎯 Next Steps

1. Read `README.DOCKER.md` for detailed Docker info
2. Read `tasks/day_10/README.phase4.md` for Phase 4 features
3. Try the examples in `examples/`
4. Run tests: `make test`

Enjoy your AI-powered development assistant! 🚀

