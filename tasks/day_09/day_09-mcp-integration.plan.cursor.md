<!-- dd97e29b-9234-437a-ba82-90e29d8b472c 98b9be3e-76bc-4765-887d-66daa20655f6 -->
# Day 09 MCP Integration Plan

## Overview

Integrate Model Context Protocol (MCP) directly into the main `src/` Clean Architecture as a new presentation layer interface. This extends the existing project with standardized tool discovery while maintaining full backward compatibility with all existing Day 07-08 demos and scripts.

## Architecture Decisions

1. **Location**: Add MCP as new module in `src/presentation/mcp/` (presentation layer)
2. **Integration**: Expose SDK + full Agent system from `shared/` and `src/` layers
3. **Tool Count**: Minimal set (5-8 tools) focusing on core capabilities
4. **Framework**: FastMCP with adapters to existing Clean Architecture use cases
5. **Compatibility**: Zero breaking changes - all existing scripts work unchanged

## Key Implementation Strategy

- Add MCP presentation layer alongside existing CLI/API interfaces
- Leverage existing use cases from `src/application/use_cases/`
- Reuse orchestrators from `src/application/orchestrators/`
- Bridge to domain services and agents in `src/domain/`
- Maintain existing `scripts/day_07_workflow.py` and `scripts/day_08_compression.py` unchanged
- Add new example script `scripts/day_09_mcp_discovery.py`

## Project Structure (Changes Only)

```
src/
├── presentation/
│   ├── api/              # Existing FastAPI interface
│   ├── cli/              # Existing CLI interface
│   └── mcp/              # NEW: MCP interface
│       ├── __init__.py
│       ├── server.py     # FastMCP server with tool definitions
│       ├── client.py     # MCP client for discovery/execution
│       └── adapters.py   # Bridge to application layer use cases

examples/
├── mcp/                  # NEW: MCP examples
│   ├── __init__.py
│   ├── basic_discovery.py
│   └── tool_execution.py

scripts/
├── day_07_workflow.py    # UNCHANGED
├── day_08_compression.py # UNCHANGED
└── day_09_mcp_demo.py    # NEW: MCP demonstration

tests/
└── src/
    └── tests/
        └── presentation/
            └── mcp/      # NEW: MCP tests
                ├── __init__.py
                ├── test_server.py
                ├── test_client.py
                └── test_integration.py

pyproject.toml            # UPDATED: Add mcp dependency
Makefile                  # UPDATED: Add mcp commands
```

## Tool Definitions

### 1. Calculator Tools (Demo/Validation)

- `add(a: float, b: float)` - Basic addition
- `multiply(a: float, b: float)` - Basic multiplication

### 2. Model SDK Tools

- `list_models()` - List available models from `shared/config/models.py`
- `check_model(model_name: str)` - Check model availability via UnifiedModelClient

### 3. Agent Orchestration Tools

- `generate_code(description: str, model: str)` - Code generation via existing use cases
- `review_code(code: str, model: str)` - Code review via existing use cases
- `generate_and_review(description: str, gen_model: str, review_model: str)` - Full workflow via MultiAgentOrchestrator

### 4. Token Analysis Tool

- `count_tokens(text: str)` - Token counting via TokenAnalyzer domain service

## Implementation Steps

### Phase 1: Add MCP Dependencies

**File**: `pyproject.toml`

Add to dependencies:

```toml
mcp = "^1.0.0"
```

Update after adding dependency:

```bash
poetry lock
poetry install
```

### Phase 2: Create MCP Presentation Layer

**File**: `src/presentation/mcp/__init__.py`

```python
"""MCP presentation layer for tool discovery and execution."""
from .server import mcp_server
from .client import MCPClient

__all__ = ["mcp_server", "MCPClient"]
```

**File**: `src/presentation/mcp/adapters.py`

Create adapters to bridge MCP to application layer:

```python
"""Adapters to bridge MCP tools to application layer use cases."""
import sys
from pathlib import Path
from typing import Any, Dict

# Add shared to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from shared_package.clients.unified_client import UnifiedModelClient
from shared_package.config.models import MODEL_CONFIGS
from src.domain.agents.code_generator import CodeGeneratorAgent
from src.domain.agents.code_reviewer import CodeReviewerAgent
from src.application.orchestrators.multi_agent_orchestrator import MultiAgentOrchestrator
from src.domain.services.token_analyzer import TokenAnalyzer


class ModelClientAdapter:
    """Adapter from scripts/day_07_workflow.py pattern."""
    # Reuse existing pattern for compatibility


class MCPApplicationAdapter:
    """Bridges MCP tools to application layer."""
    
    def __init__(self):
        self.unified_client = UnifiedModelClient()
        self.token_analyzer = TokenAnalyzer()
    
    async def list_available_models(self) -> Dict[str, Any]:
        """List all configured models."""
        # Return MODEL_CONFIGS data
    
    async def check_model_availability(self, model_name: str) -> Dict[str, bool]:
        """Check if model is available."""
        # Use unified_client.check_availability()
    
    async def generate_code_via_agent(
        self, description: str, model: str
    ) -> Dict[str, Any]:
        """Generate code using CodeGeneratorAgent."""
        # Create agent, call process, return structured result
    
    async def review_code_via_agent(
        self, code: str, model: str
    ) -> Dict[str, Any]:
        """Review code using CodeReviewerAgent."""
        # Create agent, call process, return structured result
    
    async def orchestrate_generation_and_review(
        self, description: str, gen_model: str, review_model: str
    ) -> Dict[str, Any]:
        """Full workflow via MultiAgentOrchestrator."""
        # Use existing orchestrator from day_07_workflow.py pattern
    
    def count_text_tokens(self, text: str) -> Dict[str, int]:
        """Count tokens using TokenAnalyzer."""
        # Use token_analyzer.count_tokens()
    
    async def close(self) -> None:
        """Cleanup resources."""
        await self.unified_client.close()
```

**File**: `src/presentation/mcp/server.py`

```python
"""FastMCP server exposing AI Challenge capabilities."""
from mcp.server.fastmcp import FastMCP
from .adapters import MCPApplicationAdapter

# Create FastMCP server
mcp = FastMCP(
    "AI Challenge MCP Server",
    instructions="Expose SDK and agent capabilities via MCP protocol"
)

# Initialize adapter (will be singleton)
_adapter: MCPApplicationAdapter | None = None


def get_adapter() -> MCPApplicationAdapter:
    """Get or create adapter instance."""
    global _adapter
    if _adapter is None:
        _adapter = MCPApplicationAdapter()
    return _adapter


# Calculator Tools (Demo)
@mcp.tool()
def add(a: float, b: float) -> dict[str, float]:
    """Add two numbers.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        Dictionary with result and operation type
    """
    return {"result": a + b, "operation": "addition"}


@mcp.tool()
def multiply(a: float, b: float) -> dict[str, float]:
    """Multiply two numbers.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        Dictionary with result and operation type
    """
    return {"result": a * b, "operation": "multiplication"}


# Model SDK Tools
@mcp.tool()
async def list_models() -> dict[str, list]:
    """List all available AI models.
    
    Returns:
        Dictionary containing local and external model lists
    """
    adapter = get_adapter()
    return await adapter.list_available_models()


@mcp.tool()
async def check_model(model_name: str) -> dict[str, bool]:
    """Check if a specific model is available.
    
    Args:
        model_name: Name of the model to check
    
    Returns:
        Dictionary with availability status
    """
    adapter = get_adapter()
    return await adapter.check_model_availability(model_name)


# Agent Orchestration Tools
@mcp.tool()
async def generate_code(description: str, model: str = "starcoder") -> dict:
    """Generate Python code from description using AI agent.
    
    Args:
        description: Description of code to generate
        model: Model to use (default: starcoder)
    
    Returns:
        Dictionary with generated code and metadata
    """
    adapter = get_adapter()
    return await adapter.generate_code_via_agent(description, model)


@mcp.tool()
async def review_code(code: str, model: str = "mistral") -> dict:
    """Review Python code for quality and issues.
    
    Args:
        code: Python code to review
        model: Model to use (default: mistral)
    
    Returns:
        Dictionary with review results and quality score
    """
    adapter = get_adapter()
    return await adapter.review_code_via_agent(code, model)


@mcp.tool()
async def generate_and_review(
    description: str,
    gen_model: str = "starcoder",
    review_model: str = "mistral"
) -> dict:
    """Generate code and review it in single workflow.
    
    Args:
        description: Description of code to generate
        gen_model: Model for generation (default: starcoder)
        review_model: Model for review (default: mistral)
    
    Returns:
        Dictionary with generation and review results
    """
    adapter = get_adapter()
    return await adapter.orchestrate_generation_and_review(
        description, gen_model, review_model
    )


# Token Analysis Tool
@mcp.tool()
def count_tokens(text: str) -> dict[str, int]:
    """Count tokens in text.
    
    Args:
        text: Text to analyze
    
    Returns:
        Dictionary with token count
    """
    adapter = get_adapter()
    return adapter.count_text_tokens(text)


if __name__ == "__main__":
    # Run MCP server via stdio
    mcp.run()
```

### Phase 3: Create MCP Client

**File**: `src/presentation/mcp/client.py`

```python
"""MCP client for tool discovery and execution."""
from typing import Any, Dict, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """Client for discovering and executing MCP tools."""
    
    def __init__(self, server_script: str = "src/presentation/mcp/server.py"):
        self.server_params = StdioServerParameters(
            command="python",
            args=[server_script]
        )
        self.session: ClientSession | None = None
    
    async def discover_tools(self) -> List[Dict[str, Any]]:
        """Discover all available tools.
        
        Returns:
            List of tool metadata dictionaries
        """
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_response = await session.list_tools()
                
                tools = []
                for tool in tools_response.tools:
                    tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    })
                
                return tools
    
    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool with arguments.
        
        Args:
            tool_name: Name of tool to call
            arguments: Tool arguments
        
        Returns:
            Tool execution result
        """
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return result.content[0].text if result.content else {}
    
    async def interactive_mode(self) -> None:
        """Interactive CLI for tool exploration."""
        print("MCP Interactive Mode")
        print("Commands: list, call <tool> <args>, quit")
        
        while True:
            command = input("\nmcp> ").strip()
            
            if command == "quit":
                break
            elif command == "list":
                tools = await self.discover_tools()
                for tool in tools:
                    print(f"  - {tool['name']}: {tool['description']}")
            elif command.startswith("call "):
                # Parse and execute tool call
                pass
```

### Phase 4: Create Examples

**File**: `examples/mcp/basic_discovery.py`

```python
"""Basic MCP tool discovery example."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.presentation.mcp.client import MCPClient


async def main():
    """Demonstrate tool discovery."""
    print("="*70)
    print("MCP Tool Discovery Demo")
    print("="*70)
    
    client = MCPClient()
    
    # Discover tools
    print("\nDiscovering available tools...")
    tools = await client.discover_tools()
    
    print(f"\nFound {len(tools)} tools:")
    for tool in tools:
        print(f"\n  • {tool['name']}")
        print(f"    {tool['description']}")
    
    # Test calculator tool
    print("\n" + "="*70)
    print("Testing calculator tool...")
    result = await client.call_tool("add", {"a": 5, "b": 3})
    print(f"add(5, 3) = {result}")
    
    print("\n✅ Discovery demo completed!")


if __name__ == "__main__":
    asyncio.run(main())
```

**File**: `scripts/day_09_mcp_demo.py`

```python
"""Day 09: MCP integration demonstration with backward compatibility check."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from src.presentation.mcp.client import MCPClient


async def test_mcp_tools():
    """Test all MCP tools."""
    print("="*70)
    print("🔥 Day 09: MCP Integration Demo")
    print("="*70)
    
    client = MCPClient()
    
    # 1. List models
    print("\n1. Testing list_models tool...")
    models = await client.call_tool("list_models", {})
    print(f"   Available models: {len(models.get('local_models', []))} local, {len(models.get('api_models', []))} API")
    
    # 2. Check model
    print("\n2. Testing check_model tool...")
    result = await client.call_tool("check_model", {"model_name": "qwen"})
    print(f"   Qwen available: {result.get('available', False)}")
    
    # 3. Count tokens
    print("\n3. Testing count_tokens tool...")
    tokens = await client.call_tool("count_tokens", {"text": "Hello world, this is a test"})
    print(f"   Tokens: {tokens.get('count', 0)}")
    
    # 4. Generate code (if models available)
    print("\n4. Testing generate_code tool...")
    try:
        code_result = await client.call_tool(
            "generate_code",
            {"description": "Create a function to calculate fibonacci", "model": "starcoder"}
        )
        if code_result.get("success"):
            print("   ✅ Code generation successful")
        else:
            print("   ⚠️  Code generation returned no success flag")
    except Exception as e:
        print(f"   ⚠️  Code generation failed (model may not be available): {e}")
    
    print("\n✅ MCP demo completed!")


async def verify_backward_compatibility():
    """Verify Day 07-08 scripts still work."""
    print("\n" + "="*70)
    print("🔍 Verifying Backward Compatibility")
    print("="*70)
    
    # Import and check day 07-08 modules can still be imported
    try:
        from scripts.day_07_workflow import main as day07_main
        print("   ✅ Day 07 workflow imports successfully")
    except Exception as e:
        print(f"   ❌ Day 07 import failed: {e}")
    
    try:
        from scripts.day_08_compression import Day08EnhancedDemo
        print("   ✅ Day 08 compression imports successfully")
    except Exception as e:
        print(f"   ❌ Day 08 import failed: {e}")
    
    print("\n✅ Backward compatibility verified!")


async def main():
    """Main entry point."""
    await test_mcp_tools()
    await verify_backward_compatibility()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

### Phase 5: Add Tests

**File**: `src/tests/presentation/mcp/test_server.py`

```python
"""Tests for MCP server tools."""
import pytest
from src.presentation.mcp.server import add, multiply, count_tokens


def test_add_tool():
    """Test addition tool."""
    result = add(5, 3)
    assert result["result"] == 8
    assert result["operation"] == "addition"


def test_multiply_tool():
    """Test multiplication tool."""
    result = multiply(4, 3)
    assert result["result"] == 12
    assert result["operation"] == "multiplication"


def test_count_tokens_tool():
    """Test token counting tool."""
    result = count_tokens("Hello world")
    assert "count" in result
    assert result["count"] > 0


@pytest.mark.asyncio
async def test_list_models_tool():
    """Test model listing tool."""
    from src.presentation.mcp.server import list_models
    
    result = await list_models()
    assert "local_models" in result
    assert isinstance(result["local_models"], list)
```

**File**: `src/tests/presentation/mcp/test_integration.py`

```python
"""Integration tests for MCP client-server workflow."""
import pytest
from src.presentation.mcp.client import MCPClient


@pytest.mark.asyncio
async def test_full_discovery_workflow():
    """Test full tool discovery workflow."""
    client = MCPClient()
    
    # Discover tools
    tools = await client.discover_tools()
    assert len(tools) >= 8
    
    # Verify calculator tools exist
    tool_names = [t["name"] for t in tools]
    assert "add" in tool_names
    assert "multiply" in tool_names
    assert "list_models" in tool_names
    assert "count_tokens" in tool_names


@pytest.mark.asyncio
async def test_calculator_tool_execution():
    """Test calculator tool execution via client."""
    client = MCPClient()
    
    result = await client.call_tool("add", {"a": 10, "b": 20})
    assert "result" in result
    assert result["result"] == 30
```

### Phase 6: Update Configuration Files

**File**: `Makefile` (add new targets)

```makefile
# Add after existing targets

mcp-discover:
	poetry run python examples/mcp/basic_discovery.py

mcp-demo:
	poetry run python scripts/day_09_mcp_demo.py

test-mcp:
	poetry run pytest src/tests/presentation/mcp -v
```

### Phase 7: Documentation

**File**: `docs/MCP_INTEGRATION.md` (new file)

Create comprehensive documentation:

- MCP overview and benefits
- Tool reference with examples
- Integration with existing architecture
- Usage examples
- Backward compatibility notes

## Integration Points

### With Shared SDK (`shared/`)

- Import `UnifiedModelClient` from `shared_package.clients.unified_client`
- Import `MODEL_CONFIGS` from `shared_package.config.models`
- Use existing exception hierarchy

### With Clean Architecture (`src/`)

- MCP as new presentation layer in `src/presentation/mcp/`
- Leverage `src/application/orchestrators/` for workflows
- Use `src/domain/agents/` for code generation/review
- Access `src/domain/services/` for token analysis

### With Existing Scripts

- `scripts/day_07_workflow.py` - UNCHANGED
- `scripts/day_08_compression.py` - UNCHANGED
- Reuse `ModelClientAdapter` pattern
- New `scripts/day_09_mcp_demo.py` demonstrates MCP

## Success Criteria

1. MCP server runs and exposes 8 tools
2. Tool discovery works via MCP client
3. All tools execute successfully
4. Day 07-08 scripts work unchanged (verified)
5. Agent orchestration accessible via MCP
6. 80%+ test coverage for new MCP code
7. Clear documentation
8. Zero breaking changes to existing code

## Development Workflow

1. Install: `poetry install` (adds mcp dependency)
2. Run discovery: `make mcp-discover`
3. Run demo: `make mcp-demo`
4. Run tests: `make test-mcp`
5. Verify compatibility: Run existing day 07-08 scripts unchanged

## Notes

- MCP added as presentation layer, not separate project
- Follows Clean Architecture separation of concerns
- FastMCP handles JSON Schema generation automatically
- All existing code continues to work
- New capability without disruption
- MCP tools delegate to existing use cases/orchestrators

### To-dos

- [ ] Create day_09/ directory structure and initialize Poetry project with MCP dependencies
- [ ] Implement adapters.py to bridge MCP to shared/ SDK and src/ agents
- [ ] Create mcp_server.py with FastMCP and 8 tool definitions (calculator, model SDK, agents, token analysis)
- [ ] Create mcp_client.py with discovery, execution, and interactive mode
- [ ] Implement basic_discovery.py and backward_compat_demo.py examples
- [ ] Create comprehensive test suite (server, client, integration tests)
- [ ] Create README.md with quick start, API reference, and integration guide
- [ ] Verify Day 07-08 demos still work and test MCP tool equivalents