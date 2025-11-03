# Butler Agent Testing Guide (Phase 5)

## Overview

This directory contains comprehensive tests for Butler Agent refactoring (Phase 5). The test suite follows TDD principles and Clean Architecture patterns.

## Test Structure

### Unit Tests (`tests/unit/`)

Fast, isolated tests for individual components:

- **Domain Layer**: State machine, handlers, orchestrator, mode classifier
- **Application Layer**: Use cases (CreateTask, CollectData)
- **Infrastructure Layer**: MistralClient, MCP adapter, Tools Registry
- **Presentation Layer**: ButlerBot, factory, handlers

**Coverage Target**: 85%+ per layer

### Integration Tests (`tests/integration/`)

Tests component interactions across layers:

- **Full Message Flow**: Complete workflows from message to response
- **Mode Transitions**: Switching between TASK, DATA, REMINDERS, IDLE modes
- **Error Recovery**: Graceful degradation and error handling
- **Use Case Integration**: Use cases with real orchestrator components

**Coverage Target**: 80%+ for integration paths

### E2E Tests (`tests/e2e/telegram/`)

End-to-end tests for complete Telegram bot workflows:

- **All 4 Modes**: TASK, DATA, REMINDERS, IDLE
- **Error Scenarios**: Service unavailable, invalid input, long messages
- **Complete Flows**: From Telegram message to bot response

**Coverage Target**: 100% for critical user paths

## Running Tests

### Quick Start

```bash
# Run all tests
make test

# Run specific test types
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-e2e          # E2E tests only

# Run with coverage
make test-coverage     # Coverage report with 80% threshold
make test-all          # All tests + coverage + XML report
```

### Using pytest directly

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# E2E tests (with marker)
pytest tests/e2e/ -v -m e2e

# With coverage
pytest tests/ --cov=src --cov-report=html --cov-fail-under=80
```

### Run specific test file

```bash
pytest tests/unit/presentation/bot/test_factory.py -v
```

### Run with specific markers

```bash
pytest tests/ -m "e2e"      # Only E2E tests
pytest tests/ -m "not slow" # Skip slow tests
```

## Test Fixtures

### Using Butler Fixtures

All fixtures are available via `tests/fixtures/butler_fixtures.py`:

```python
@pytest.mark.asyncio
async def test_example(butler_orchestrator, sample_task_message):
    """Example test using fixtures."""
    # butler_orchestrator: Fully configured ButlerOrchestrator
    # sample_task_message: Sample task creation message
    
    # Configure mocks
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="TASK"
    )
    
    # Execute
    response = await butler_orchestrator.handle_user_message(
        user_id="123",
        message=sample_task_message,
        session_id="456"
    )
    
    # Verify
    assert response is not None
```

### Key Fixtures

- `butler_orchestrator`: Main fixture with all dependencies mocked
- `mock_llm_client_protocol`: Mock LLM client
- `mock_tool_client_protocol`: Mock MCP tool client
- `mock_mongodb`: Mock MongoDB database
- `mock_telegram_bot`: Mock Telegram bot for E2E tests

See `tests/fixtures/butler_fixtures.py` for complete list.

## Writing New Tests

### Unit Test Example

```python
"""Unit tests for MyComponent."""

import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_my_component_success(mock_dependency):
    """Test successful operation."""
    # Arrange
    component = MyComponent(dependency=mock_dependency)
    mock_dependency.method = AsyncMock(return_value="success")
    
    # Act
    result = await component.process()
    
    # Assert
    assert result == "success"
    mock_dependency.method.assert_called_once()
```

### Integration Test Example

```python
"""Integration tests for component interactions."""

import pytest
from tests.fixtures.butler_fixtures import butler_orchestrator

@pytest.mark.asyncio
async def test_full_workflow(butler_orchestrator):
    """Test complete workflow."""
    # Configure orchestrator mocks
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="TASK"
    )
    
    # Execute
    response = await butler_orchestrator.handle_user_message(
        user_id="123",
        message="Create task: Test",
        session_id="456"
    )
    
    # Verify complete flow
    assert response is not None
```

### E2E Test Example

```python
"""E2E tests for Telegram bot."""

import pytest
from tests.e2e.telegram.conftest import e2e_orchestrator

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_task_creation_e2e(e2e_orchestrator, mock_telegram_message):
    """Test complete Telegram task creation flow."""
    # Configure
    e2e_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="TASK"
    )
    mock_telegram_message.text = "Create a task: Buy milk"
    
    # Execute
    response = await e2e_orchestrator.handle_user_message(
        user_id=str(mock_telegram_message.from_user.id),
        message=mock_telegram_message.text,
        session_id=f"{mock_telegram_message.from_user.id}:{mock_telegram_message.message_id}"
    )
    
    # Verify
    assert response is not None
```

## Coverage Requirements

### Overall Coverage

- **Minimum**: 80% (enforced via `--cov-fail-under=80`)
- **Target**: 85%+

### Per-Layer Coverage

| Layer | Target | Current |
|-------|--------|---------|
| Domain | 85% | ~85% |
| Application | 85% | ~85% |
| Infrastructure | 80% | ~80% |
| Presentation | 75% | ~75% |

### Checking Coverage

```bash
# Generate HTML report
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html

# Terminal report with missing lines
pytest tests/ --cov=src --cov-report=term-missing

# XML report (for CI/CD)
pytest tests/ --cov=src --cov-report=xml
```

## Test Best Practices

### 1. Use Fixtures

Always use fixtures for dependencies:

```python
# Good
async def test_example(butler_orchestrator):
    ...

# Bad
async def test_example():
    orchestrator = ButlerOrchestrator(...)  # Don't create manually
```

### 2. Mock External Dependencies

Mock all external services (LLM, MCP, MongoDB):

```python
butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
    return_value="TASK"
)
```

### 3. Test Both Happy and Error Paths

```python
async def test_success():
    """Test happy path."""
    ...

async def test_error_handling():
    """Test error handling."""
    ...
```

### 4. One Assertion Per Test (When Possible)

```python
# Good: Focused test
async def test_returns_task_id():
    result = await create_task()
    assert result.task_id == "task_123"

# Bad: Multiple unrelated assertions
async def test_everything():
    result = await create_task()
    assert result.task_id == "task_123"
    assert result.created is True
    assert result.error is None
```

### 5. Use Descriptive Names

```python
# Good
async def test_create_task_with_clarification_returns_question():
    ...

# Bad
async def test_task():
    ...
```

## CI/CD Integration

Tests are automatically run in CI/CD (`.github/workflows/ci.yml`):

- **test-unit**: Unit tests with coverage
- **test-integration**: Integration tests
- **test-e2e**: E2E tests
- **test-coverage**: Overall coverage report

All jobs must pass for PR merge.

## Troubleshooting

### Tests Fail Due to Import Errors

Ensure you're running from project root:
```bash
cd /path/to/AI_Challenge
pytest tests/
```

### Async Test Warnings

Use `@pytest.mark.asyncio` for async tests:
```python
@pytest.mark.asyncio
async def test_async_function():
    ...
```

### Fixture Not Found

Check fixture is imported in `tests/conftest.py` or test file.

### Coverage Below Threshold

Run coverage report to see which files need more tests:
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Main Testing Documentation](../docs/TESTING.md)

