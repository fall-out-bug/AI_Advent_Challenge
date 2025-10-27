# MCP Troubleshooting Guide

Common issues and solutions for MCP integration.

## Table of Contents

- [Connection Issues](#connection-issues)
- [Model Availability](#model-availability)
- [Code Generation Errors](#code-generation-errors)
- [Validation Errors](#validation-errors)
- [Performance Issues](#performance-issues)
- [Testing Issues](#testing-issues)

## Connection Issues

### Issue: "Failed to connect to MCP server"

**Symptoms:**
- Client cannot discover tools
- `stdio_client` connection errors
- Server process not starting

**Causes:**
1. Server script not found
2. Python path not configured
3. Missing dependencies

**Solutions:**
```bash
# Verify server script exists
ls -la src/presentation/mcp/server.py

# Check Python path
python -c "import sys; print(sys.path)"

# Reinstall dependencies
poetry install

# Test server directly
poetry run python src/presentation/mcp/server.py
```

### Issue: "Module import errors"

**Symptoms:**
- `ImportError: No module named 'shared_package'`
- Path manipulation issues

**Solutions:**
```bash
# Add root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use sys.path insertion (already in code)
# Verify in each adapter file
```

## Model Availability

### Issue: "Model not available" error

**Symptoms:**
- `check_model` returns `{"available": False}`
- Model operations fail immediately

**Causes:**
1. Model server not running
2. Wrong model name
3. Network issues

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
curl http://localhost:PORT/health

# Verify model name
# Common names: mistral, starcoder, qwen, tinyllama
```

## Code Generation Errors

### Issue: "Code generation failed" with `MCPAgentError`

**Symptoms:**
- `generate_code` returns `{"success": False}`
- No code generated

**Causes:**
1. Invalid model selected
2. Network timeout
3. Model server overload

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
    
# Try with simpler description
result = await generate_code(
    description="def hello(): print('world')",  # Simpler
    model="mistral"
)
```

### Issue: "Empty code generated"

**Symptoms:**
- Generation succeeds but code is empty
- Metadata shows 0 lines of code

**Solutions:**
```python
# Verify description is clear
description = "Create a Python function to sort a list of numbers"
result = await generate_code(description, model="mistral")

# Check generated code
if not result.get("code"):
    # Try different model or simpler request
    pass
```

## Validation Errors

### Issue: `MCPValidationError` on empty inputs

**Symptoms:**
- Validation errors with empty strings
- Error context shows field name

**Example Error:**
```
MCPValidationError: Description cannot be empty
Context: {"field": "description"}
```

**Solutions:**
```python
# Always validate inputs before calling
description = user_input.strip()
if not description:
    raise ValueError("Description cannot be empty")

# Use helper validation functions
from src.presentation.mcp.adapters.generation_adapter import GenerationAdapter
adapter = GenerationAdapter(client, model_name="mistral")
try:
    adapter._validate_description(description)
except MCPValidationError as e:
    print(f"Validation failed: {e.context['field']}")
```

## Performance Issues

### Issue: Tool discovery takes > 1 second

**Symptoms:**
- Slow tool discovery
- High latency on tool calls

**Causes:**
1. Network latency
2. Heavy imports
3. Synchronous operations

**Solutions:**
```python
# Use async throughout
import asyncio

async def discover_tools_fast():
    import time
    start = time.time()
    
    client = MCPClient()
    tools = await client.discover_tools()
    
    elapsed = time.time() - start
    print(f"Discovery took {elapsed:.2f}s")
    
    return tools

# Profile slow operations
import cProfile
cProfile.run('asyncio.run(discover_tools_fast())')

# Consider caching tool lists
_cached_tools = None

async def get_tools():
    global _cached_tools
    if _cached_tools is None:
        client = MCPClient()
        _cached_tools = await client.discover_tools()
    return _cached_tools
```

### Issue: Memory usage high

**Symptoms:**
- Memory consumption grows over time
- Out of memory errors

**Solutions:**
```python
# Explicitly close clients
async def with_resource_cleanup():
    client = MCPClient()
    try:
        result = await client.call_tool("generate_code", {...})
    finally:
        await client.close()  # Cleanup

# Use context managers
from contextlib import asynccontextmanager

@asynccontextmanager
async def mcp_client():
    client = MCPClient()
    try:
        yield client
    finally:
        await client.close()

async def use_client():
    async with mcp_client() as client:
        return await client.call_tool(...)
```

## Testing Issues

### Issue: Tests failing with `ImportError`

**Symptoms:**
- Import errors in test files
- Module not found

**Solutions:**
```bash
# Run tests from project root
cd /path/to/AI_Challenge
poetry run pytest src/tests/presentation/mcp/

# Verify PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
poetry run pytest src/tests/presentation/mcp/ -v

# Check imports
poetry run python -c "
import sys
sys.path.insert(0, 'src/presentation/mcp/adapters')
from model_adapter import ModelAdapter
print('Import successful')
"
```

### Issue: Mocking issues in tests

**Symptoms:**
- Tests calling real services
- Unpredictable test behavior

**Solutions:**
```python
# Use proper mocking
from unittest.mock import Mock, AsyncMock

@pytest.fixture
def mock_client():
    client = Mock()
    client.check_availability = AsyncMock(return_value=True)
    return client

# Patch external dependencies
from unittest.mock import patch

@patch('src.presentation.mcp.adapters.UnifiedModelClient')
async def test_with_mock(mock_client_class):
    mock_client = mock_client_class.return_value
    mock_client.check_availability = AsyncMock(return_value=True)
    
    # Test with mocked client
    result = await check_model_availability("mistral")
    assert result["available"] is True
```

## Common Error Messages

### "Description cannot be empty"

**Cause:** Empty or whitespace-only description provided

**Fix:**
```python
description = input().strip()
if not description:
    print("Description cannot be empty")
    return
```

### "Model not found"

**Cause:** Invalid model name

**Fix:**
```python
# Check available models first
models = await list_models()
available = [m["name"] for m in models["local_models"]]
if model_name not in available:
    print(f"Model {model_name} not available")
```

### "Code generation failed"

**Cause:** Model server down or network issue

**Fix:**
```python
# Add retry logic
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

## Debugging Tips

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now all MCP operations will log details
client = MCPClient()
# ... operations will show debug logs
```

### Inspect Exception Context

```python
try:
    result = await generate_code("")
except MCPValidationError as e:
    print(f"Error: {e}")
    print(f"Context: {e.context}")
    print(f"Field: {e.context.get('field')}")
```

### Test Individual Components

```python
# Test adapters directly
from src.presentation.mcp.adapters.model_adapter import ModelAdapter

adapter = ModelAdapter(unified_client)
models = adapter.list_available_models()
print(models)
```

## Getting Help

If you encounter issues not covered here:

1. Check logs for detailed error messages
2. Run tests: `make test-mcp`
3. Verify dependencies: `poetry check`
4. Check model server status
5. Review API reference: `docs/MCP_API_REFERENCE.md`

## Reporting Issues

When reporting issues, include:

1. Error message and traceback
2. Input parameters used
3. Model names involved
4. Environment details (Python version, OS)
5. Relevant log output

Example:
```
Error: MCPValidationError - Description cannot be empty
Input: description="", model="mistral"
Context: {"field": "description"}
Python: 3.10.12
OS: Linux
```
