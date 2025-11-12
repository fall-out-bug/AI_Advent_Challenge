# MCP Integration Documentation

## Overview

Model Context Protocol (MCP) integration enables standardized tool discovery and execution for AI Challenge capabilities. This integration exposes our SDK and agent capabilities via the MCP protocol, allowing external systems to discover and use our tools dynamically.

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
└── adapters.py      # Bridge to application layer
```

## Available Tools

### Calculator Tools (Demo/Validation)

- **`add(a: float, b: float)`** - Add two numbers
  - Returns: `{"result": float, "operation": "addition"}`

- **`multiply(a: float, b: float)`** - Multiply two numbers
  - Returns: `{"result": float, "operation": "multiplication"}`

### Model SDK Tools

- **`list_models()`** - List all available AI models
  - Returns: `{"local_models": [...], "api_models": [...]}`
  - Shows models from `shared_package/config/models.py`

- **`check_model(model_name: str)`** - Check if specific model is available
  - Returns: `{"available": bool, "error": str (optional)}`

### Agent Orchestration Tools

- **`generate_code(description: str, model: str = "starcoder")`** - Generate Python code
  - Returns: `{"success": bool, "code": str, "error": str (optional), "metadata": {...}}`
  - Uses CodeGeneratorAgent from `src/domain/agents/code_generator.py`

- **`review_code(code: str, model: str = "starcoder")`** - Review Python code
  - Returns: `{"success": bool, "review": str, "quality_score": int, "error": str (optional), "metadata": {...}}`
  - Uses CodeReviewerAgent from `src/domain/agents/code_reviewer.py`
  - Default uses **StarCoder**

- **`generate_and_review(description: str, gen_model: str = "starcoder", review_model: str = "starcoder")`** - Full workflow
  - Returns: `{"success": bool, "generation": {...}, "review": {...}, "workflow_time": float, "error": str (optional)}`
  - Uses MultiAgentOrchestrator from `src/application/orchestrators/multi_agent_orchestrator.py`

### Token Analysis Tool

- **`count_tokens(text: str)`** - Count tokens in text
  - Returns: `{"count": int, "error": str (optional)}`
  - Uses TokenAnalyzer from `src/domain/services/token_analyzer.py`

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

import asyncio
asyncio.run(main())
```

### Using Agent Tools

```python
from src.presentation.mcp.client import MCPClient

async def main():
    client = MCPClient()
    
    # Generate code via MCP (using StarCoder - specialized for code generation)
    result = await client.call_tool(
        "generate_code",
        {
            "description": "Create a function to calculate fibonacci"
            # model defaults to "starcoder" if not specified
        }
    )
    
    if result.get("success"):
        print(f"Generated code: {result['code']}")
    else:
        print(f"Error: {result['error']}")
    
    # Review code via MCP (using StarCoder)
    review_result = await client.call_tool(
        "review_code",
        {
            "code": "def hello(): print('world')"
            # model defaults to "starcoder" if not specified
        }
    )
    
    print(f"Quality score: {review_result.get('quality_score', 0)}")

import asyncio
asyncio.run(main())
```

### Running Complete Workflow

```python
from src.presentation.mcp.client import MCPClient

async def main():
    client = MCPClient()
    
    # Full generate and review workflow (both using StarCoder by default)
    result = await client.call_tool(
        "generate_and_review",
        {
            "description": "Create a REST API endpoint"
            # gen_model and review_model both default to "starcoder"
        }
    )
    
    if result.get("success"):
        print("✅ Workflow completed successfully")
        print(f"Generated code: {result['generation']['code'][:200]}...")
        print(f"Quality score: {result['review']['score']}/10")
        print(f"Time: {result['workflow_time']:.2f}s")
    else:
        print(f"❌ Workflow failed: {result.get('error')}")

import asyncio
asyncio.run(main())
```

## Quick Start

### 1. Install Dependencies

```bash
poetry install  # Adds mcp dependency
```

### 2. Discover Tools

```bash
make mcp-discover
```

### 3. Run Demo

```bash
make mcp-demo
```

### 4. Run Tests

```bash
make test-mcp
```

## Backward Compatibility

All existing Day 07-08 scripts continue to work unchanged:

- **`scripts/day_07_workflow.py`** - ✅ Unchanged
- **`scripts/day_08_compression.py`** - ✅ Unchanged

The MCP integration is purely additive and does not modify existing functionality. All orchestrators, agents, and use cases work exactly as before.

## Integration with Existing Architecture

### With Clean Architecture Layers

- **Domain**: Uses existing agents (`CodeGeneratorAgent`, `CodeReviewerAgent`) and services (`TokenAnalyzer`)
- **Application**: Leverages existing orchestrators (`MultiAgentOrchestrator`)
- **Presentation**: New MCP layer alongside existing API/CLI interfaces

### With Shared SDK

- Imports `UnifiedModelClient` from `shared_package.clients.unified_client`
- Uses `MODEL_CONFIGS` from `shared_package.config.models`
- Maintains existing error handling and exception hierarchy

### With Existing Scripts

- Reuses `ModelClientAdapter` pattern from `scripts/day_07_workflow.py`
- Compatible with all existing orchestrator workflows
- Same agent configuration and behavior

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
```

### Testing

```bash
# Run all MCP tests
make test-mcp

# Run specific test file
poetry run pytest src/tests/presentation/mcp/test_server.py -v
poetry run pytest src/tests/presentation/mcp/test_integration.py -v
```

## Benefits

1. **Standardized Interface**: MCP provides a standard protocol for tool discovery and execution
2. **Tool Discovery**: External systems can dynamically discover available capabilities
3. **Flexibility**: Easy to add new tools without breaking changes
4. **Integration**: Seamless integration with existing Clean Architecture components
5. **Backward Compatible**: Zero breaking changes to existing functionality

## Design Principles

Following the Zen of Python and Clean Architecture:

- **Simple is better than complex**: FastMCP for rapid development
- **Explicit is better than implicit**: Clear tool definitions with type hints
- **Readability counts**: Well-documented tools and examples
- **Separation of concerns**: MCP as presentation layer, delegates to application layer
- **Dependency inversion**: Use existing abstractions, not direct implementations

## Next Steps

1. Add more tools as needed (e.g., compression, token limit testing)
2. Extend resources and prompts support
3. Add streaming responses for long-running operations
4. Implement tool caching for performance
5. Add metrics and monitoring

