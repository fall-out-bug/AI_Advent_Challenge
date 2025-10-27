# Async Testing Best Practices for Day 08

## Overview

This document outlines best practices for testing asynchronous code in the Day 08 project. It covers patterns, tools, and techniques for writing reliable async tests.

## Table of Contents

- [Async Test Setup](#async-test-setup)
- [Basic Async Testing](#basic-async-testing)
- [Async Mocking Patterns](#async-mocking-patterns)
- [Error Handling in Async Tests](#error-handling-in-async-tests)
- [Performance Testing](#performance-testing)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)
- [Best Practices Summary](#best-practices-summary)

## Async Test Setup

### Prerequisites

Ensure you have the required dependencies:

```bash
pip install pytest pytest-asyncio
```

### Configuration

The project uses `pytest-asyncio` with auto mode enabled in `pytest.ini`:

```ini
[tool:pytest]
addopts = --asyncio-mode=auto
```

This automatically detects and runs async test functions without requiring explicit markers.

## Basic Async Testing

### Simple Async Test

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_async_function():
    """Test an async function."""
    result = await async_function()
    assert result is not None
```

### Async Test with Fixtures

```python
@pytest.fixture
async def async_fixture():
    """Async fixture that sets up resources."""
    resource = await create_resource()
    yield resource
    await cleanup_resource(resource)

@pytest.mark.asyncio
async def test_with_async_fixture(async_fixture):
    """Test using async fixture."""
    result = await process_resource(async_fixture)
    assert result.success
```

### Async Test with Parameters

```python
@pytest.mark.asyncio
@pytest.mark.parametrize("input_value,expected", [
    ("test1", "result1"),
    ("test2", "result2"),
])
async def test_async_with_params(input_value, expected):
    """Test async function with parameters."""
    result = await async_function(input_value)
    assert result == expected
```

## Async Mocking Patterns

### Basic Async Mock

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_with_async_mock():
    """Test with async mock."""
    mock_client = AsyncMock()
    mock_client.fetch_data.return_value = {"data": "test"}
    
    result = await fetch_and_process(mock_client)
    assert result == "processed test"
    mock_client.fetch_data.assert_called_once()
```

### Mocking Async Context Managers

```python
@pytest.mark.asyncio
async def test_async_context_manager():
    """Test async context manager mocking."""
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_client
    mock_context.__aexit__.return_value = None
    
    with patch('module.async_client', return_value=mock_context):
        result = await use_async_client()
        assert result is not None
```

### Mocking HTTP Requests

```python
import aiohttp
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_http_request():
    """Test HTTP request mocking."""
    mock_response = AsyncMock()
    mock_response.json.return_value = {"status": "success"}
    mock_response.status = 200
    
    mock_session = AsyncMock()
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await make_http_request()
        assert result["status"] == "success"
```

### Mocking SDK Agents

```python
@pytest.mark.asyncio
async def test_sdk_agent_integration():
    """Test SDK agent integration."""
    mock_generator = AsyncMock(spec=CodeGeneratorAgent)
    mock_generator.generate_code.return_value = "generated code"
    
    mock_reviewer = AsyncMock(spec=CodeReviewerAgent)
    mock_reviewer.review_code.return_value = CodeQualityMetrics(
        score=0.9,
        issues=[]
    )
    
    adapter = DirectAdapter()
    adapter.register_agent("generator", mock_generator)
    adapter.register_agent("reviewer", mock_reviewer)
    
    orchestrator = SequentialOrchestrator()
    result = await orchestrator.execute("test task", adapter)
    
    assert result.success
    mock_generator.generate_code.assert_called_once()
    mock_reviewer.review_code.assert_called_once()
```

## Error Handling in Async Tests

### Testing Async Exceptions

```python
@pytest.mark.asyncio
async def test_async_exception():
    """Test async function raises exception."""
    with pytest.raises(ValueError, match="Invalid input"):
        await async_function_with_validation("invalid")
```

### Testing Timeout Handling

```python
import asyncio

@pytest.mark.asyncio
async def test_timeout():
    """Test async function timeout."""
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(slow_async_function(), timeout=0.1)
```

### Testing Circuit Breaker

```python
@pytest.mark.asyncio
async def test_circuit_breaker():
    """Test circuit breaker pattern."""
    mock_client = AsyncMock()
    mock_client.request.side_effect = Exception("Service unavailable")
    
    circuit_breaker = CircuitBreaker(mock_client)
    
    # First few calls should fail
    with pytest.raises(Exception):
        await circuit_breaker.execute("test")
    
    # After threshold, should return circuit breaker error
    with pytest.raises(CircuitBreakerOpenError):
        await circuit_breaker.execute("test")
```

## Performance Testing

### Async Performance Baseline

```python
import time
import pytest

@pytest.mark.asyncio
@pytest.mark.performance
async def test_async_performance():
    """Test async function performance."""
    start_time = time.time()
    
    result = await async_function()
    
    execution_time = time.time() - start_time
    assert execution_time < 1.0  # Should complete within 1 second
    assert result is not None
```

### Concurrent Execution Testing

```python
@pytest.mark.asyncio
async def test_concurrent_execution():
    """Test concurrent async execution."""
    tasks = [
        async_function(f"task_{i}")
        for i in range(10)
    ]
    
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 10
    assert all(result.success for result in results)
```

## Common Patterns

### Testing Async Iterators

```python
@pytest.mark.asyncio
async def test_async_iterator():
    """Test async iterator."""
    async def async_generator():
        for i in range(3):
            yield i
    
    results = []
    async for value in async_generator():
        results.append(value)
    
    assert results == [0, 1, 2]
```

### Testing Async Context Managers

```python
@pytest.mark.asyncio
async def test_async_context_manager():
    """Test async context manager."""
    async with AsyncResource() as resource:
        result = await resource.process()
        assert result is not None
    
    # Resource should be cleaned up
    assert resource.is_closed
```

### Testing Async Queues

```python
@pytest.mark.asyncio
async def test_async_queue():
    """Test async queue operations."""
    queue = asyncio.Queue()
    
    # Producer
    await queue.put("item1")
    await queue.put("item2")
    
    # Consumer
    item1 = await queue.get()
    item2 = await queue.get()
    
    assert item1 == "item1"
    assert item2 == "item2"
```

### Testing Async Locks

```python
@pytest.mark.asyncio
async def test_async_lock():
    """Test async lock."""
    lock = asyncio.Lock()
    shared_resource = []
    
    async def worker(worker_id):
        async with lock:
            shared_resource.append(worker_id)
            await asyncio.sleep(0.01)  # Simulate work
    
    # Run multiple workers concurrently
    tasks = [worker(i) for i in range(5)]
    await asyncio.gather(*tasks)
    
    assert len(shared_resource) == 5
    assert set(shared_resource) == {0, 1, 2, 3, 4}
```

## Troubleshooting

### Common Issues

#### 1. Coroutine Not Awaited

**Problem**: `RuntimeWarning: coroutine 'function' was never awaited`

**Solution**: Ensure all async functions are awaited:

```python
# Wrong
result = async_function()  # Returns coroutine

# Correct
result = await async_function()  # Returns actual result
```

#### 2. Event Loop Issues

**Problem**: `RuntimeError: There is no current event loop`

**Solution**: Use proper async test markers:

```python
@pytest.mark.asyncio
async def test_function():
    # This will run in proper event loop
    pass
```

#### 3. Mock Not Working

**Problem**: Mock doesn't work with async functions

**Solution**: Use `AsyncMock`:

```python
# Wrong
mock = Mock()
mock.async_function.return_value = "result"

# Correct
mock = AsyncMock()
mock.async_function.return_value = "result"
```

#### 4. Timeout Issues

**Problem**: Tests hang or timeout

**Solution**: Set appropriate timeouts:

```python
@pytest.mark.asyncio
async def test_with_timeout():
    result = await asyncio.wait_for(
        slow_function(),
        timeout=5.0
    )
    assert result is not None
```

### Debug Commands

```bash
# Run async tests with debug output
pytest -s --log-cli-level=DEBUG tests/test_async.py

# Run specific async test
pytest tests/test_async.py::test_async_function -v

# Run with asyncio debug mode
PYTHONPATH=. python -m pytest --asyncio-mode=debug tests/test_async.py
```

## Best Practices Summary

### 1. Test Structure

- **Use `@pytest.mark.asyncio`** for all async tests
- **Keep tests focused** - one async operation per test
- **Use descriptive names** - clearly indicate async nature
- **Arrange-Act-Assert** - structure async tests clearly

### 2. Mocking

- **Use `AsyncMock`** for async functions
- **Mock external dependencies** - don't test external services
- **Verify async calls** - use `assert_called_once()` etc.
- **Mock context managers** - handle `__aenter__` and `__aexit__`

### 3. Error Handling

- **Test exceptions** - verify async functions raise expected exceptions
- **Test timeouts** - ensure functions complete within expected time
- **Test circuit breakers** - verify resilience patterns
- **Test retry logic** - ensure retry mechanisms work

### 4. Performance

- **Set baselines** - establish performance expectations
- **Test concurrency** - verify concurrent execution works
- **Monitor resource usage** - ensure tests don't leak resources
- **Use appropriate timeouts** - prevent hanging tests

### 5. Resource Management

- **Use async fixtures** - properly manage async resources
- **Clean up resources** - ensure proper cleanup in teardown
- **Test context managers** - verify resource lifecycle
- **Avoid resource leaks** - monitor for memory/resource leaks

### 6. Integration Testing

- **Test SDK integration** - verify SDK agents work correctly
- **Test orchestration** - verify async orchestration patterns
- **Test adapters** - verify communication adapters work
- **Test end-to-end** - verify complete async workflows

### 7. Documentation

- **Document async behavior** - explain async patterns in tests
- **Provide examples** - show common async test patterns
- **Explain mocking** - document async mocking strategies
- **Troubleshoot issues** - provide solutions for common problems

## Examples from Day 08

### SDK Agent Testing

```python
@pytest.mark.asyncio
async def test_code_generator_adapter():
    """Test SDK code generator adapter."""
    adapter = CodeGeneratorAdapter(model_name="starcoder")
    
    result = await adapter.generate_code_with_compression(
        task_description="Write a function",
        model_name="starcoder",
        max_tokens=1000
    )
    
    assert result.success
    assert result.response is not None
    assert result.input_tokens > 0
```

### Orchestration Testing

```python
@pytest.mark.asyncio
async def test_sequential_orchestration():
    """Test sequential orchestration pattern."""
    orchestrator = SequentialOrchestrator()
    adapter = DirectAdapter()
    
    # Register mock agents
    adapter.register_agent("generator", mock_generator)
    adapter.register_agent("reviewer", mock_reviewer)
    
    result = await orchestrator.execute("test task", adapter)
    
    assert result.success
    assert result.steps_completed == 2
```

### Model Switching Testing

```python
@pytest.mark.asyncio
async def test_model_switching():
    """Test model switching functionality."""
    orchestrator = ModelSwitcherOrchestrator(models=["starcoder", "mistral"])
    
    # Test model availability
    available = await orchestrator.check_model_availability("starcoder")
    assert available
    
    # Test model switching
    await orchestrator.switch_to_model("mistral")
    current_model = orchestrator.get_current_model()
    assert current_model == "mistral"
```

## Conclusion

Async testing in Day 08 follows these key principles:

1. **Proper async setup** - Use pytest-asyncio with auto mode
2. **Comprehensive mocking** - Mock all external dependencies
3. **Error handling** - Test all error conditions and edge cases
4. **Performance validation** - Ensure async operations meet performance requirements
5. **Resource management** - Properly manage async resources and cleanup
6. **Integration testing** - Verify SDK integration and orchestration patterns

By following these practices, you can write reliable, maintainable async tests that properly validate the asynchronous behavior of the Day 08 system.
