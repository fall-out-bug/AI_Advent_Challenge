# Docker Deployment Guide - Phase 4

## Quick Start

### Full Stack Deployment (All Services)

```bash
# Create cache directory (persists models across rebuilds)
mkdir -p cache/models

# Build all containers
docker-compose -f docker-compose.full.yml build

# Start all services
docker-compose -f docker-compose.full.yml up -d

# View logs
docker-compose -f docker-compose.full.yml logs -f

# Stop all services
docker-compose -f docker-compose.full.yml down
```

**Models Cache**: Models are stored in `./cache/models/` to persist across `docker prune` operations. This directory is excluded from git via `.gitignore`.

## Services

### 1. Local Language Models (GPU Required)

| Service | Port | Model | Description |
|---------|------|-------|-------------|
| qwen-chat | 8000 | Qwen1.5-4B-Chat | Fast, efficient chat model |
| mistral-chat | 8001 | Mistral-7B-Instruct | High-quality instruction following |
| tinyllama-chat | 8002 | TinyLlama-1.1B | Lightweight model for testing |
| accumulating-chat | 8003 | StarCoder2-7B-Instruct | Code generation specialist |

### 2. MCP Server (Phase 4)

- Port: Internal (stdio only)
- Provides: Code generation, review, testing, formatting
- Connects to: local_models services
- Tools: formalize_task, generate_code, review_code, generate_tests, format_code, analyze_complexity

### 3. Main API (Optional)

- Port: 8080
- Provides: REST API interface
- Connects to: All services

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Docker Network                          │
│                    ai-challenge-network                         │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ qwen-chat   │  │ mistral-chat│  │ tinyllama   │            │
│  │  :8000      │  │  :8001      │  │  :8002      │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐                             │
│  │starcoder    │  │ MCP Server  │                             │
│  │  :8003      │  │  (stdio)    │                             │
│  └─────────────┘  └─────────────┘                             │
│                                                                 │
 стало ┌─────────────┐                                             │
│  │ Main API   │                                             │
│  │  :8080     │                                             │
│  └─────────────┘                                             │
└─────────────────────────────────────────────────────────────────┘
```

## Usage Examples

### Test Local Models

```bash
# Test Qwen model
curl http://localhost:8000/health

# Test Mistral model
curl http://localhost:8001/health

# Send a chat request to Mistral
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello!", "max_tokens": 100}'
```

### Use MCP Server

The MCP server is accessed via stdio (not HTTP). Use the Python CLI:

```bash
# Run streaming chat
make mcp-chat-streaming

# Or run interactive chat
make mcp-chat
```

### Check Service Status

```bash
# Check all services
docker-compose -f docker-compose.full.yml ps

# Check specific service logs
docker-compose -f docker-compose.full.yml logs mistral-chat

# Check MCP server logs
docker-compose -f docker-compose.full.yml logs mcp-server
```

## Resource Requirements

### Minimum
- **GPU**: 16GB VRAM (for one model at a time)
- **RAM**: 32GB
- **Storage**: 50GB (for models)

### Recommended
- **GPU**: 24GB+ VRAM (multiple models)
- **RAM**: 64GB
- **Storage**: 100GB SSD

## Troubleshooting

### GPU Not Available

```bash
# Check GPU
nvidia-smi

# If no GPU, models won't start properly
# Check logs:
docker-compose -f docker-compose.full.yml logs qwen-chat
```

### Services Won't Connect

```bash
# Check network
docker network inspect ai-challenge-network

# Restart services
docker-compose -f docker-compose.full.yml restart
```

### Out of Memory

```bash
# Check container memory
docker stats

# Increase limits in docker-compose.full.yml
# Or run fewer models at once
```

## Development vs Production

### Development
```bash
# Run with hot-reload (if available)
docker-compose -f docker-compose.full.yml up --build
```

### Production
```bash
# Run in detached mode with restart policies
docker-compose -f docker-compose.full.yml up -d

# Scale specific services
docker-compose -f docker-compose.full.yml up -d --scale mistral-chat=2
```

## Environment Variables

Create `.env` file (see `.env.example`):

```bash
# Copy example
cp .env.example .env

# Edit with your values
nano .env
```

Key variables:
- `HF_TOKEN`: Hugging Face token for gated models
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `MODEL_TIMEOUT_SECONDS`: Request timeout

## Backup and Restore

```bash
# Backup data
docker-compose -f docker-compose.full.yml exec api tar czf /tmp/backup.tar.gz /app/data

# Copy backup
docker cp mcp-server-day10:/tmp/backup.tar.gz ./backup.tar.gz
```

## Monitoring

```bash
# Real-time resource usage
docker stats

# Service health checks
docker-compose -f docker-compose.full.yml ps
```

## Clean Up

```bash
# Stop all services
docker-compose -f docker-compose.full.yml down

# Remove volumes (WARNING: deletes all data)
docker-compose -f docker-compose.full.yml down -v

# Clean up unused images
docker system prune -a
```

