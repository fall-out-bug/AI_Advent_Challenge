# Testing Documentation

## Overview

This document describes the testing strategy, coverage targets, and guidelines for the AI Challenge project.

## Testing Strategy

### Test Pyramid

The project follows a testing pyramid approach:

```
         /\
        /E2E\       ← End-to-end tests (bot + review pipelines)
       /------\
      /Integration\ ← API + worker integration suites
     /------------\
    /    Unit      \ ← Core domain/application coverage
   /----------------\
```

### Test Distribution

- **Unit Tests**: Fast, isolated checks covering domain, application, and infrastructure layers
- **Integration Tests**: Validate interactions between API, worker, repositories, and MCP clients
- **E2E Tests**: Exercise complete user workflows (Telegram bot, review queue, publishing)
- **Contract Tests**: Ensure OpenAPI/JSON schema compatibility with external systems

## Test Organization (Phase 5)

### Directory Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── fixtures/
│   ├── mcp_fixtures.py            # MCP-specific fixtures
│   └── butler_fixtures.py         # Butler-specific fixtures (Phase 5)
├── unit/                          # Unit tests
│   ├── domain/                    # Domain layer tests
│   │   └── agents/
│   │       ├── services/          # ModeClassifier tests
│   │       └── handlers/          # Handler tests
│   ├── application/               # Application layer tests
│   │   └── use_cases/             # Use case tests
│   ├── infrastructure/            # Infrastructure layer tests
│   │   ├── llm/                   # MistralClient tests
│   │   └── mcp/                   # Tools Registry tests
│   └── presentation/              # Presentation layer tests
│       └── bot/                   # ButlerBot, factory tests
├── integration/                   # Integration tests
│   ├── conftest.py                # Integration fixtures (Phase 5)
│   ├── presentation/bot/          # Bot integration tests
│   └── butler/                    # Butler integration tests (Phase 5)
│       ├── test_full_message_flow.py
│       ├── test_mode_transitions.py
│       ├── test_error_recovery.py
│       └── test_use_case_integration.py
└── e2e/                           # End-to-end tests
    ├── telegram/                  # Telegram bot E2E (Phase 5)
    │   ├── conftest.py            # E2E fixtures
    │   ├── test_butler_e2e.py     # Complete workflows
    │   └── fixtures/              # Test message fixtures
    └── test_full_workflow.py      # Legacy E2E tests
```

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
# or using make
make test
```

### Run by Category
```bash
# Unit tests only
pytest tests/unit/ -v
make test-unit

# Integration tests only
pytest tests/integration/ -v
make test-integration

# E2E tests only
pytest tests/e2e/ -v -m e2e
make test-e2e
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=80
make test-coverage
```

### Run with Coverage
```bash
pytest --cov=src --cov-report=html --cov-report=term
```

### Run Specific Test
```bash
pytest src/tests/unit/application/test_multi_agent_orchestrator.py -v
```

### Targeted Suites (Day 17)
```bash
# Pass 4 log analysis
pytest tests/unit/application/use_cases/test_review_submission_pass4.py -v

# MCP publishing & fallback
pytest tests/unit/application/use_cases/test_review_submission_llm_mcp.py -v

# Integration contracts (OpenAPI + JSON schema)
pytest tests/contracts/ -v
```

## Coverage Targets (Phase 5)

### Current Status
- **Overall Coverage**: 80%+ (enforced via `--cov-fail-under=80`)
- **Critical Paths**: 85%+ (orchestrators, handlers, use cases)
- **Domain Layer**: 85%+ (business logic)

### Coverage by Layer

| Layer | Target | Phase 5 Status |
|-------|--------|----------------|
| Domain | 85% | 85%+ ✅ |
| Application | 85% | 85%+ ✅ |
| Infrastructure | 80% | 80%+ ✅ |
| Presentation | 75% | 75%+ ✅ |

### Coverage Configuration

Coverage thresholds are configured in `pyproject.toml`:
- Overall: 80% (fail_under)
- Excludes: test files, migrations, __pycache__
- HTML reports: `htmlcov/index.html`
- XML reports: `coverage.xml` (for CI/CD)

## Test Types

### Unit Tests

Test individual components in isolation.

**Example:**
```python
@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator initialization."""
    orchestrator = MultiAgentOrchestrator()

    assert orchestrator.generator is not None
    assert orchestrator.reviewer is not None
```

### Integration Tests

Test component interactions.

**Example:**
```python
@pytest.mark.asyncio
async def test_generation_to_review_workflow():
    """Test complete workflow."""
    # Setup
    orchestrator = MultiAgentOrchestrator(...)

    # Execute
    response = await orchestrator.process_task(request)

    # Verify
    assert response.success is True
```

### E2E Tests

Test complete user workflows.

**Example:**
```python
@pytest.mark.e2e
async def test_full_pipeline():
    """Test complete pipeline."""
    # Setup, execute, verify
    ...
```

## Writing Tests

### Test Structure

```python
class TestFeature:
    """Test suite for feature X."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        # Arrange
        ...

        # Act
        ...

        # Assert
        ...
```

### Naming Conventions

- Test files: `test_*.py`
- Test classes: `TestFeature`
- Test methods: `test_what_it_does()`

### Best Practices

1. **One Assert Per Test** (when possible)
2. **Arrange-Act-Assert** pattern
3. **Descriptive names** that explain what is tested
4. **Use fixtures** for setup/teardown
5. **Mock external dependencies**

## Fixtures (Phase 5)

### Butler-Specific Fixtures

Located in `tests/fixtures/butler_fixtures.py`:

```python
# LLM and MCP clients
mock_llm_client_protocol    # Mock LLMClientProtocol
mock_tool_client_protocol   # Mock ToolClientProtocol
mock_mongodb                # Mock MongoDB database

# Domain components
mock_mode_classifier        # ModeClassifier with mocked LLM
mock_intent_orchestrator    # Mock IntentOrchestrator
mock_task_handler           # TaskHandler with dependencies
mock_data_handler           # DataHandler with dependencies
mock_chat_handler           # ChatHandler with dependencies

# Complete orchestrator
butler_orchestrator         # Full ButlerOrchestrator with all mocks

# Test data
sample_dialog_context       # Sample DialogContext
sample_task_message         # Sample task message
sample_data_message         # Sample data message
sample_idle_message         # Sample chat message

# Telegram mocks
mock_telegram_bot           # Mock aiogram Bot
mock_telegram_dispatcher    # Mock aiogram Dispatcher
mock_telegram_message       # Mock Telegram Message
```

### Usage Example

```python
@pytest.mark.asyncio
async def test_task_creation(butler_orchestrator):
    """Test task creation using butler_orchestrator fixture."""
    # Configure mocks
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="TASK"
    )

    # Execute
    response = await butler_orchestrator.handle_user_message(
        user_id="123", message="Create task", session_id="456"
    )

    # Verify
    assert response is not None
```

## Test Markers

### pytest Markers

```python
@pytest.mark.asyncio      # Async tests
@pytest.mark.e2e          # E2E tests
@pytest.mark.integration  # Integration tests
@pytest.mark.skip         # Skip test
@pytest.mark.parametrize  # Parameterized tests
```

## Mocking

### Using unittest.mock

```python
from unittest.mock import AsyncMock, MagicMock

# Mock async methods
mock_agent = AsyncMock()
mock_agent.process.return_value = expected_result

# Mock sync methods
mock_service = MagicMock()
mock_service.method.return_value = value
```

## Test Data

### Test Fixtures Location
- Use pytest fixtures for test data
- Keep test data minimal and focused
- Use factories for complex data generation

## CI/CD Integration

### Pre-commit Checks
```bash
# Run tests before commit
pytest src/tests/ -v

# Check coverage
pytest --cov=src --cov-report=term-missing

# Lint code
black src/
flake8 src/
mypy src/
```

## TDD Workflow

### Red-Green-Refactor

1. **Red**: Write failing test
2. **Green**: Write minimal code to pass
3. **Refactor**: Improve code while keeping tests green

### Example

```python
# 1. Write test
def test_new_feature():
    result = new_feature()
    assert result == expected

# 2. Implement minimal code
def new_feature():
    return expected

# 3. Refactor with tests as safety net
```

## Performance Testing

### Benchmark Tests

```python
import pytest
import time

def test_performance():
    start = time.time()
    result = expensive_operation()
    elapsed = time.time() - start

    assert elapsed < 1.0  # 1 second limit
    assert result is not None
```

## Continuous Improvement

### Test Metrics

- **Test count**: 241 tests
- **Pass rate**: 100%
- **Coverage**: 70%+
- **Critical path coverage**: 70%+

### Regular Reviews

- Review test coverage monthly
- Add tests for new features
- Refactor tests to improve readability
- Remove obsolete tests

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [TDD Guide](https://en.wikipedia.org/wiki/Test-driven_development)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
