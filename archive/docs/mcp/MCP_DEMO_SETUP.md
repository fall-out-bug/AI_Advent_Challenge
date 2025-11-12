# MCP Demo - Minimal Setup

## Overview

This guide shows how to run the MCP demo with **only the necessary models** - reducing resource usage and startup time.

## Required Models

For the MCP demo, you only need:

1. **Mistral** (`mistralai/Mistral-7B-Instruct-v0.2`)
   - Used for orchestration and chat interactions
   - Port: `8001`

2. **StarCoder** (`TechxGenus/starcoder2-7b-instruct`)  
   - Used for code generation
   - Port: `8003`

3. **MCP Server** (HTTP API)
   - Connects to Mistral and StarCoder
   - Port: `8004`

## Quick Start

### 1. Start Minimal MCP Demo

```bash
make mcp-demo-start
```

This will start:
- Mistral model server on port 8001
- StarCoder model server on port 8003
- MCP HTTP server on port 8004

### 2. Run CLI with Docker MCP Server

```bash
make mcp-chat-docker
```

### 3. Monitor Logs

```bash
make mcp-demo-logs
```

### 4. Stop Services

```bash
make mcp-demo-stop
```

## Resource Comparison

### Full Stack (all 4 models)
```bash
make docker-up-full
```
- Models: Qwen, Mistral, TinyLlama, StarCoder
- GPU Memory: ~24-32GB
- Startup Time: 5-10 minutes

### Minimal Stack (2 models)
```bash
make mcp-demo-start
```
- Models: Mistral, StarCoder
- GPU Memory: ~14-16GB
- Startup Time: 3-5 minutes

**Savings: ~40% GPU memory, ~40% faster startup**

## Model Configuration

The minimal setup uses these model URLs:

```bash
MODEL_BASE_URLS=mistral=http://mistral-chat:8000,starcoder=http://starcoder-chat:8000
```

## Troubleshooting

### Check Service Status
```bash
docker-compose -f docker-compose.mcp-demo.yml ps
```

### Check Individual Logs
```bash
# Mistral
docker logs ai_challenge-mistral-chat-1 --tail 50

# StarCoder  
docker logs ai_challenge-starcoder-chat-1 --tail 50

# MCP Server
docker logs mcp-server-day10 --tail 50
```

### Test MCP Server Health
```bash
curl http://localhost:8004/health
```

Expected response:
```json
{
  "status": "healthy",
  "available_tools": 12
}
```

### Verify Model Connections
```bash
# Check Mistral
curl http://localhost:8001/health

# Check StarCoder
curl http://localhost:8003/health
```

## When to Use Minimal vs Full Stack

**Use Minimal Stack (`mcp-demo-start`):**
- For MCP demo and testing
- Limited GPU memory available
- Faster development iteration
- Only need code generation + chat

**Use Full Stack (`docker-up-full`):**
- Need all models for comparison
- Running comprehensive tests
- Development of all features
- Need TinyLlama for fast prototyping or Qwen for analysis
