# MCP (Model Context Protocol) Guide

Complete guide for using the Model Context Protocol integration in AI Challenge.

## Overview

Model Context Protocol (MCP) integration enables standardized tool discovery and execution for AI Challenge capabilities. Jacob Davis exposes our SDK and agent capabilities via the MCP protocol, allowing external systems to discover and use our tools dynamically.

### Key Features

- **Standardized Interface**: Standard protocol for tool discovery and execution
- **Tool Discovery**: Dynamically discover available capabilities
- **Flexibility**: Add new tools without breaking changes
- **Clean Architecture**: Seamless integration with existing components
- **Backward Compatible**: Zero breaking changes to existing functionality
- **HTTP & Stdio Modes**: Use via Docker HTTP or local stdio processes

## Architecture

### Integration Points

- **Presentation Layer**: `src/presentation/mcp/` - MCP server and client implementation
- **Application Layer**: Uses existing orchestrators from `src/application/orchestrators/`
- **Domain Layer**: Leverages agents from `src/domain/agents/` and services from `src/domain/services/`
- **Shared SDK**: Connects to `shared_package/` for unified model interaction

### Component Structure

```
src/presentation/mcp/
├── __init__.py      # Module exports
├── server.py        # FastMCP server with tool definitions
├── client.py        # MCP client for discovery/execution
├── adapters.py      # Bridge to application layer
├── http_server.py   # FastAPI HTTP wrapper
├── http_client.py   # HTTP client for tools
└── adapters/        # Specialized adapters
    ├── model_adapter.py
    ├── generation_adapter.py
    ├── review_adapter.py
    ├── orchestration_adapter.py
    ├── token_adapter.py
    └── model_client_adapter.py
```

## Available Tools

### Calculator Tools (2)

- **`add(a: float, b: float)`** - Add two numbers
- **`multiply(a: float, b: float)`** - Multiply two numbers

### Model SDK Tools (2)

- **`list_models()`** - List all available AI models
  - Returns: `{"local_models": [...], "api_models": [...]}`

- **`check_model(model_name: str)`** - Check if specific model is available
  - Returns: `{"available": bool, "error": str (optional)}`

### Agent Orchestration Tools (5)

- **`generate_code(description: str, model: str = "starcoder")`** - Generate Python code
  - Returns: `{"success": bool, "code": str, "tests": str, "metadata": {...}}`

- **`review_code(code: str, model: str = "starcoder")`** - Review Python code
  - Returns: `{"success": bool, "quality_score": int, "issues": [...], "recommendations": [...]}`

- **`generate_and_review(description, gen_model, review_model)`** - Full workflow
  - Returns: Combined generation and review results

- **`generate_tests(code, test_framework, coverage_target)`** - Generate unit tests
  - Returns: `{"success": bool, "tests": str, "test_count": int, "coverage_estimate": int}`

- **`format_code(code, formatter, line_length)`** - Format code with Black
  - Returns: `{"success": bool, "formatted_code": str, "changes_made": [...]}`

### Utility Tools (3)

- **`count_tokens(text: str)`** - Count tokens in text
  - Returns: `{"count": int, "error": str (optional)}`

- **`analyze_complexity(code, detailed)`** - Analyze code complexity metrics
  - Returns: `{"success": bool, "cyclomatic": int, "cognitive": int, "maintainability": float}`

- **`formalize_task(informal_request, context)`** - Convert task to structured plan
  - Returns: `{"success": bool, "plan": {"requirements": [...], "steps": [...]}}`

**Total: 12 tools**

## Quick Start

### 1. Install Dependencies

```bash
poetry install  # Adds mcp dependency
```

### 2. Start Services

Choose your deployment mode:

#### Option A: Minimal Demo (Recommended for testing)

```bash
make mcp-demo-start
# Starts: Mistral + StarCoder + MCP Server (Docker HTTP mode)
```

#### Option B: Full Stack (All models)

```bash
make docker-up-full
# Starts: All 4 models + MCP Server + API
```

#### Option C: Stdio Mode (Legacy)

```bash
poetry run python src/presentation/mcp/server.py
```

### 3. Discover Tools

```bash
make mcp-discover
```

### 4. Run Demo

```bash
# Interactive demo
make mcp-chat-docker

# Comprehensive demo with reports
make mcp-demo-report

# Streamed chat
make mcp-chat-streaming
```

### 5. Run Tests

```bash
make test-mcp
```

## Usage Examples

### Basic Tool Discovery

```python
from src.presentation.mcp.client import MCPClient

async def main():
    client = MCPClient()
    
    # Discover available tools
    tools = await client.discover_tools()
    for tool in tools:
        print(f"{tool['name']}: {tool['description']}")
    
    # Call a calculator tool
    result = await client.call_tool("add", {"a": 5, "b": 3})
    print(f"Result: {result}")

asyncio.run(main())
```

### Code Generation and Review

```python
from src.presentation.mcp.client import MCPClient

async def main():
    client = MCPClient()
    
    # Generate code (defaults to starcoder)
    result = await client.call_tool(
        "generate_code",
        {"description": "Create a function to calculate fibonacci"}
    )
    
    if result.get("success"):
        print(f"Generated code: {result['code']}")
    
    # Review code
    review_result = await client.call_tool(
        "review_code",
        {"code": result['code']}
    )
    print(f"Quality score: {review_result.get('quality_score', 0)}")

asyncio.run(main())
```

### Complete Workflow

```python
from src.presentation.mcp.client import MCPClient

async def main():
    client = MCPClient()
    
    # Full generate and review workflow
    result = await client.call_tool(
        "generate_and_review",
        {"description": "Create a REST API endpoint"}
    )
    
    if result.get("success"):
        print("✅ Workflow completed successfully")
        print(f"Generated code: {result['generation']['code'][:200]}...")
        print(f"Quality score: {result['review']['score']}/10")
        print(f"Time: {result['workflow_time']:.2f}s")

asyncio.run(main())
```

## Deployment Modes

### HTTP Mode (Docker, Recommended)

Use Docker-based MCP server accessed via HTTP:

```bash
# Start Docker MCP server
make mcp-server-start

# Run CLI with Docker connection
make mcp-chat-docker

# Or set environment variable
MCP_USE_DOCKER=true poetry run python src/presentation/mcp/cli/streaming_chat.py
```

**Advantages:**
- Isolation: Server runs in Docker
- Scalability: Multiple CLI instances
- Monitoring: HTTP health checks
- Network: Connect to remote servers

### Stdio Mode (Legacy)

Use local stdio MCP server:

```bash
# Run CLI with local stdio connection
make mcp-chat-streaming
```

**Advantages:**
- Simplicity: No Docker required
- Debugging: Easier to debug local process

### Configuration

```bash
# Environment variables
export MCP_USE_DOCKER=true      # Use Docker server
export MCP_DOCKER_URL=http://localhost:8004  # Server URL
```

## API Reference

### Response Schemas

All tools return structured responses:

```python
# Base response
{
    "success": bool,
    "error": str | None
}

# Code generation response
{
    "success": bool,
    "code": str,
    "tests": str,
    "metadata": {
        "model_used": str,
        "complexity": str,
        "lines_of_code": int
    },
    "error": str | None
}

# Code review response
{
    "success": bool,
    "quality_score": int,        # 0-10
    "issues": list[str],
    "recommendations": list[str],
    "review": str,
    "metadata": {...},
    "error": str | None
}
```

### Error Handling

Domain-specific exceptions:

- `MCPValidationError`: Invalid input
- `MCPModelError`: Model operation failed
- `MCPAgentError`: Agent operation failed
- `MCPOrchestrationError`: Workflow failed
- `MCPAdapterError`: Adapter operation failed

```python
try:
    result = await generate_code("")
except MCPValidationError as e:
    print(e.context["field"])  # "description"
```

## HTTP API Endpoints

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

List all available tools with schemas.

### POST `/call`

Call an MCP tool.

**Request:**
```json
{
  "tool_name": "generate_code",
  "arguments": {
    "description": "Add two numbers",
    "model": "starcoder"
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

## Troubleshooting

### Connection Issues

**Issue:** "Failed to connect to MCP server"

**Solutions:**
```bash
# Verify server is running
docker ps | grep mcp-server

# Check server logs
docker logs mcp-server-day10

# Test server health
curl http://localhost:8004/health

# Verify port access
curl http://localhost:8004/tools
```

### Model Availability

**Issue:** "Model not available" error

**Solutions:**
```bash
# List available models
poetry run python -c "
from src.presentation.mcp.client import MCPClient
import asyncio

async def main():
    client = MCPClient()
    models = await client.call_tool('list_models', {})
    print(models)

asyncio.run(main())
"

# Check model server status
curl http://localhost:8001/health  # Mistral
curl http://localhost:8003/health  # StarCoder
```

### Code Generation Errors

**Issue:** "Code generation failed"

**Solutions:**
```python
# Use a working model
result = await generate_code(
    description="Create a hello function",
    model="mistral"  # Known working model
)

# Check error details
if not result.get("success"):
    print(f"Error: {result.get('error')}")

# Retry with retry logic
import asyncio

async def generate_with_retry(description, model, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = await generate_code(description, model)
            if result.get("success"):
                return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
    return None
```

### Performance Issues

**Issue:** Tool discovery takes > 1 second

**Solutions:**
```python
# Use caching
_cached_tools = None

async def get_tools():
    global _cached_tools
    if _cached_tools is None:
        client = MCPClient()
        _cached_tools = await client.discover_tools()
    return _cached_tools

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Issues

**Issue:** Tests failing with import errors

**Solutions:**
```bash
# Run tests from project root
cd /path/to/AI_Challenge
poetry run pytest src/tests/presentation/mcp/ -v

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Use proper mocking
from unittest.mock import Mock, AsyncMock

@pytest.fixture
def mock_client():
    client = Mock()
    client.check_availability = AsyncMock(return_value=True)
    return client
```

## Development

### Running MCP Server Standalone

```bash
poetry run python src/presentation/mcp/server.py
```

### Running Examples

```bash
# Basic discovery
poetry run python examples/mcp/basic_discovery.py

# Full demo
poetry run python scripts/day_09_mcp_demo.py

# Comprehensive demo
poetry run python scripts/mcp_comprehensive_demo.py
```

### Testing

```bash
# Run all MCP tests
make test-mcp

# Run specific test file
poetry run pytest src/tests/presentation/mcp/test_server.py -v
poetry run pytest src/tests/presentation/mcp/test_integration.py -v
poetry run pytest src/tests/presentation/mcp/test_adapters.py -v
```

## Resource Requirements

### Minimal Demo Setup

**Models Required:**
- Mistral (port 8001): ~7GB GPU memory
- StarCoder (port 8003): ~7GB GPU memory
- MCP Server (port 8004)

**Total:** ~14-16GB GPU memory

### Full Stack Setup

**Models Required:**
- Qwen (port 8000): ~8GB GPU memory
- Mistral (port 8001): ~7GB GPU memory
- TinyLlama (port 8002): ~4GB GPU memory
- StarCoder (port 8003): ~7GB GPU memory
- MCP Server (port 8004)

**Total:** ~24-32GB GPU memory

**Recommendation:** Use minimal setup for development and testing.

## Architecture & Design Principles

Following the Zen of Python and Clean Architecture:

- **Simple is better than complex**: FastMCP for rapid development
- **Explicit is better than implicit**: Clear tool definitions with type hints
- **Readability counts**: Well-documented tools and examples
- **Separation of concerns**: MCP as presentation layer, delegates to application layer
- **Dependency inversion**: Use existing abstractions, not direct implementations
- **Single Responsibility**: Each adapter handles one concern
- **Error handling**: Domain-specific exceptions with context
- **Configuration**: External YAML for runtime customization

## Next Steps

1. Explore individual tools via HTTP API
2. Build custom workflows combining multiple tools
3. Integrate with CI/CD pipelines
4. Add custom tools following existing patterns
5. Monitor performance via health endpoints

## Additional Resources

- **API Reference**: Full API details in code docstrings
- **Configuration**: See `config/mcp_config.yaml`
- **Tests**: `src/tests/presentation/mcp/`
- **Examples**: `examples/mcp/` and `scripts/`
- **Architecture**: See `docs/ARCHITECTURE.md`

