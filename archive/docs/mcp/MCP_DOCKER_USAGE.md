# MCP Server Docker Integration

## Overview

The MCP (Model Context Protocol) server can now run in Docker and be accessed via HTTP, allowing the CLI tools to connect over the network instead of spawning local stdio processes.

## Architecture

```
┌─────────────────┐      HTTP/REST       ┌──────────────────┐
│  CLI (Host)     │ ◄──────────────────► │  MCP Server      │
│                 │   http://localhost:  │  (Docker)        │
│ - Chat          │      8004            │  - FastAPI       │
│ - Orchestrator  │                      │  - MCP Tools     │
└─────────────────┘                      └──────────────────┘
```

## Quick Start

### 1. Start MCP Server in Docker

```bash
# Start only MCP server
make mcp-server-start

# Or start all services (models + MCP + API)
make docker-up-full
```

### 2. Run CLI with Docker MCP Server

```bash
# Streaming chat with Docker MCP server
make mcp-chat-docker

# Or set environment variable manually
MCP_USE_DOCKER=true poetry run python src/presentation/mcp/cli/streaming_chat.py
```

### 3. Verify Connection

```bash
# Check server health
curl http://localhost:8004/health

# List available tools
curl http://localhost:8004/tools
```

## Usage Modes

### Mode 1: Stdio (Legacy, Still Supported)

Run CLI with local stdio MCP server (spawns local Python process):

```bash
make mcp-chat-streaming
```

### Mode 2: Docker HTTP (New)

Run CLI connecting to Docker MCP server via HTTP:

```bash
make mcp-chat-docker
```

## Configuration

### Environment Variables

- `MCP_USE_DOCKER`: Set to `true` to use Docker MCP server
- `MCP_DOCKER_URL`: URL of Docker MCP server (default: `http://localhost:8004`)

### Docker Compose Configuration

The MCP server is configured in:
- `docker-compose.mcp.yml` - Standalone MCP server
- `docker-compose.full.yml` - Full stack (models + MCP + API)

Port mapping: `8004:8004`

## API Endpoints

The MCP HTTP server exposes:

### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "available_tools": 12
}
```

### GET `/tools`
List all available MCP tools.

**Response:**
```json
{
  "tools": [
    {
      "name": "generate_code",
      "description": "...",
      "input_schema": {...}
    }
  ]
}
```

### POST `/call`
Call an MCP tool.

**Request:**
```json
{
  "tool_name": "generate_code",
  "arguments": {
    "description": "Add two numbers",
    "model": "mistral"
  }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "code": "def add(a, b): return a + b"
  }
}
```

## Files Modified

### New Files
- `src/presentation/mcp/http_server.py` - FastAPI HTTP wrapper for MCP server
- `src/presentation/mcp/http_client.py` - HTTP client for MCP tools

### Modified Files
- `src/presentation/mcp/orchestrators/mcp_mistral_wrapper.py` - Added `use_docker` parameter
- `src/presentation/mcp/cli/streaming_chat.py` - Updated to use Docker by default
- `src/presentation/mcp/cli/interactive_mistral_chat.py` - Updated to use Docker by default
- `Dockerfile.mcp` - Added FastAPI/uvicorn timeout curl for healthchecks
- `docker-compose.mcp.yml` - Added port exposure and HTTP healthcheck
- `docker-compose.full.yml` - Added port exposure for MCP server
- `Makefile` - Added new targets for Docker mode

## Troubleshooting

### Cannot connect to MCP server

```bash
# Check if MCP server is running
docker ps | grep mcp-server

# Check server logs
docker logs mcp-server-day10

# Check if port 8004 is accessible
curl http://localhost:8004/health
```

### Tool execution errors

```bash
# Check if model servers are accessible from MCP server
docker exec mcp-server-day10 curl http://mistral-chat:8000/health

# Check MCP server logs for errors
docker logs -f mcp-server-day10
```

### Rebuild MCP server image

```bash
# Stop running container
make mcp-server-stop

# Rebuild image
docker-compose -f docker-compose.mcp.yml build

# Start again
make mcp-server-start
```

## Benefits

1. **Isolation**: MCP server runs in isolated Docker environment
2. **Scalability**: Can run multiple CLI instances connecting to one MCP server
3. **Monitoring**: HTTP endpoints enable monitoring and health checks
4. **Integration**: Can be integrated with other HTTP-based services
5. **Flexibility**: CLI can connect to remote MCP servers over network
