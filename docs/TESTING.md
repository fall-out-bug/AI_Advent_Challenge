# Testing Documentation

## Overview

This document describes the testing strategy, coverage targets, and guidelines for the AI Challenge project.

## Testing Strategy

### Test Pyramid

The project follows a testing pyramid approach:

```
         /\
        /E2E\       ← End-to-end tests (9 tests)
       /------\
      /Integration\ ← Integration tests (9 tests)
     /------------\
    /    Unit      \ ← Unit tests (223 tests)
   /----------------\
```

### Test Distribution

- **Unit Tests**: 223 tests - Fast, isolated, test individual components
- **Integration Tests**: 9 tests - Test component interactions
- **E2E Tests**: 9 tests - Test complete workflows
- **Total**: 241 tests

## Test Organization

### Directory Structure

```
src/tests/
├── unit/                    # Unit tests
│   ├── application/        # Orchestrator tests
│   ├── domain/             # Domain logic tests
│   ├── infrastructure/      # Infrastructure tests
│   └── presentation/       # API/CLI tests
├── integration/            # Integration tests
│   └── test_agent_workflows.py
└── e2e/                    # End-to-end tests
    └── test_full_workflow.py
```

## Running Tests

### Run All Tests
```bash
pytest src/tests/ -v
```

### Run by Category
```bash
# Unit tests only
pytest src/tests/unit/ -v

# Integration tests only
pytest src/tests/integration/ -v

# E2E tests only
pytest src/tests/e2e/ -v
```

### Run with Coverage
```bash
pytest --cov=src --cov-report=html --cov-report=term
```

### Run Specific Test
```bash
pytest src/tests/unit/application/test_multi_agent_orchestrator.py -v
```

## Coverage Targets

### Current Status
- **Overall Coverage**: 70%+
- **Critical Paths**: 70%+ (orchestrators, agents)
- **Domain Layer**: 80%+ (business logic)

### Coverage by Layer

| Layer | Target | Current |
|-------|--------|---------|
| Domain | 80% | 75% |
| Application | 70% | 75% |
| Infrastructure | 65% | 70% |
| Presentation | 60% | 65% |

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

## Fixtures

### Common Fixtures

```python
@pytest.fixture
def mock_generator():
    """Mock code generator."""
    return AsyncMock(spec=CodeGeneratorAgent)

@pytest.fixture
def orchestrator(mock_generator, mock_reviewer):
    """Orchestrator with mocks."""
    return MultiAgentOrchestrator(
        generator_agent=mock_generator,
        reviewer_agent=mock_reviewer
    )
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

