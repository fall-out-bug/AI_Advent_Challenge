# Testing Strategy - Phase 1C

## Overview

This document outlines the comprehensive testing strategy for the AI Challenge Clean Architecture implementation.

## Testing Pyramid

```
        /\
       /E2E\          [10% - Critical user journeys]
      /------\
     /Integration\    [20% - Component interaction]
    /------------\
   /   Unit Tests  \  [70% - Individual components]
  /----------------\
```

## Test Coverage Goals

### Current Status (Phase 1C)
- **Domain Layer**: 85%+ ✅
- **Application Layer**: 70%+ ✅
- **Infrastructure Layer**: 50%+ ✅
- **Presentation Layer**: 20%+ ⚠️
- **Overall**: 46.44% → **Target: 80%+**

## Test Layers

### 1. Unit Tests ✅

**Location**: `src/tests/unit/`

**Purpose**: Test individual components in isolation

**Coverage**:
- ✅ Domain entities
- ✅ Value objects
- ✅ Domain services
- ✅ Application use cases
- ✅ Infrastructure repositories
- ⚠️ Infrastructure adapters (needs more)
- ⚠️ Infrastructure clients (needs more)
- ❌ Presentation layer (needs tests)

**Command**: `make unit` or `pytest src/tests/unit/`

### 2. Integration Tests ✅

**Location**: `src/tests/integration/`

**Purpose**: Test component interaction

**Coverage**:
- ✅ Adapter integration
- ✅ Repository integration
- ⚠️ API integration (needs more)
- ⚠️ Database integration (when implemented)

**Command**: `make integration` or `pytest src/tests/integration/`

### 3. E2E Tests ✅

**Location**: `src/tests/e2e/`

**Purpose**: Test complete user workflows

**Coverage**:
- ✅ Code generation workflow
- ✅ Code review workflow
- ✅ Generate + Review workflow
- ✅ Task persistence

**Command**: `make e2e` or `pytest src/tests/e2e/`

## Testing Best Practices

### Zen of Python Applied

1. **Simple is better than complex** - Each test tests one thing
2. **Readable tests** - Descriptive names and clear structure
3. **Explicit testing** - No magic, clear assertions
4. **DRY principles** - Use fixtures for setup

### Test Structure

```python
def test_something() -> None:
    """
    Test description.
    
    Given: Initial state
    When: Action occurs
    Then: Expected outcome
    """
    # Arrange
    entity = SomeEntity(...)
    
    # Act
    result = entity.some_method()
    
    # Assert
    assert result == expected
```

### Fixtures Pattern

```python
@pytest.fixture
def entity() -> Entity:
    """Create entity for testing."""
    return Entity(id="test", ...)

def test_entity_behavior(entity: Entity) -> None:
    """Test entity with fixture."""
    assert entity.id == "test"
```

## Coverage by Layer

### Domain Layer ✅ (85%+)

**Files**:
- `test_entities.py` - 6 tests
- `test_model_config.py` - 6 tests
- `test_token_info.py` - 6 tests
- `test_code_quality_checker.py` - 5 tests

**Coverage**: Excellent ✅

### Application Layer ✅ (70%+)

**Files**:
- `test_use_cases.py` - 3 tests

**Coverage**: Good ✅

### Infrastructure Layer ⚠️ (50%+)

**Files**:
- `test_repositories.py` - 5 tests
- ⚠️ Clients need tests
- ⚠️ Adapters need more tests

**Coverage**: Needs improvement ⚠️

### Presentation Layer ❌ (20%+)

**Files**:
- ❌ API routes need tests
- ❌ CLI needs tests

**Coverage**: Needs tests ❌

## Running Tests

### All Tests
```bash
make test
# or
pytest src/tests/
```

### With Coverage
```bash
make coverage
# or
pytest src/tests/ --cov=src --cov-report=html
```

### Specific Tests
```bash
# Unit only
make unit

# Integration only
make integration

# E2E only
make e2e

# By marker
pytest -m unit
pytest -m integration
pytest -m e2e
```

## Coverage Reporting

### HTML Report
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Terminal Report
```bash
pytest --cov=src --cov-report=term-missing
```

### CI Report
```bash
pytest --cov=src --cov-report=xml
```

## Test Commands

### Makefile Commands

```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run specific test types
make unit
make integration
make e2e

# Lint and format
make lint
make format

# Clean temporary files
make clean
```

### Pytest Commands

```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Run specific test
pytest src/tests/unit/domain/test_entities.py::test_agent_task_creation

# Run by marker
pytest -m slow
pytest -m "not slow"

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: make install
      - run: make test
      - run: make coverage
      - uses: codecov/codecov-action@v3
```

## Best Practices Checklist

- ✅ Tests are isolated and independent
- ✅ Use fixtures for setup
- ✅ Clear test names
- ✅ AAA pattern (Arrange, Act, Assert)
- ✅ Test edge cases
- ✅ Test error handling
- ✅ Mock external dependencies
- ✅ Async tests use pytest-asyncio
- ✅ Type hints in tests
- ⚠️ More integration tests needed
- ❌ API tests needed
- ❌ CLI tests needed

## Next Steps

### Immediate (Phase 1C)
1. ✅ Unit tests for domain (DONE)
2. ✅ Unit tests for application (DONE)
3. ✅ Unit tests for infrastructure (DONE)
4. ⚠️ Add infrastructure adapter tests
5. ⚠️ Add infrastructure client tests
6. ❌ Add presentation layer tests

### Short Term
1. API route tests
2. CLI command tests
3. Performance benchmarks
4. Load testing

### Long Term
1. Property-based testing
2. Mutation testing
3. Chaos engineering
4. Security testing

## Coverage Goals

| Layer | Current | Target | Status |
|-------|---------|--------|--------|
| Domain | 85% | 90% | ✅ Good |
| Application | 70% | 80% | ✅ Good |
| Infrastructure | 50% | 75% | ⚠️ Needs work |
| Presentation | 20% | 80% | ❌ Needs tests |
| **Overall** | **46%** | **80%** | ⚠️ In progress |

## Conclusion

Phase 1C testing is well underway with strong domain and application coverage. Next focus:
1. Infrastructure layer tests
2. Presentation layer tests
3. Integration test expansion
4. E2E test completion

