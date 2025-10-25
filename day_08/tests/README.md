# Day 08 Test Suite Documentation

## Overview

The Day 08 test suite provides comprehensive testing coverage for the enhanced token analysis system with SDK integration. The test suite is organized into multiple categories to ensure thorough validation of all components.

## Test Structure

### Test Categories

#### 1. Unit Tests (`tests/test_*.py`)
- **Purpose**: Test individual components in isolation
- **Coverage**: Core functionality, edge cases, error handling
- **Files**: 
  - `test_token_analyzer.py` - Token counting and analysis
  - `test_text_compressor.py` - Text compression strategies
  - `test_ml_client.py` - ML client and hybrid token counter
  - `test_experiments.py` - Experiment management
  - `test_config.py` - Configuration validation
  - `test_utils.py` - Utility functions
  - `test_compressors.py` - Compression strategy implementations
  - `test_protocols.py` - Protocol implementations
  - `test_zen_implementations.py` - Zen of Python compliance
  - `test_accurate_token_counter.py` - Accurate token counting
  - `test_token_counter_factory.py` - Factory pattern tests

#### 2. Integration Tests (`tests/integration/`)
- **Purpose**: Test component interactions and end-to-end workflows
- **Files**:
  - `test_integration.py` - Core system integration
  - `test_sdk_integration.py` - SDK agent integration

#### 3. Property-Based Tests (`tests/property/`)
- **Purpose**: Test properties and invariants using Hypothesis
- **Files**:
  - `test_token_analyzer_properties.py` - Token counting properties
  - `test_compressor_properties.py` - Compression properties
  - `test_statistics_properties.py` - Statistics properties

#### 4. Performance Tests (`tests/performance/`)
- **Purpose**: Baseline performance measurements
- **Files**:
  - `test_performance_baseline.py` - Performance benchmarks

#### 5. Regression Tests (`tests/regression/`)
- **Purpose**: Ensure behavior preservation
- **Files**:
  - `test_baseline_behavior.py` - Baseline behavior validation

#### 6. Smoke Tests (`tests/smoke/`)
- **Purpose**: Basic functionality verification
- **Files**:
  - `test_demos.py` - Demo script validation

#### 7. Application Tests
- **Purpose**: Test application-level components
- **Files**:
  - `test_main_refactoring.py` - Application bootstrap
  - `test_di_container.py` - Dependency injection
  - `test_model_switching_demo.py` - Model switching demo
  - `test_console_reporter_refactoring.py` - Console reporting
  - `test_token_service_refactoring.py` - Token service
  - `test_docker_manager.py` - Docker management

## Test Configuration

### pytest.ini
```ini
[tool:pytest]
minversion = 6.0
addopts = 
    -ra
    -q
    --strict-markers
    --strict-config
    --disable-warnings
    --tb=short
    --asyncio-mode=auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    property: marks tests as property-based tests
    performance: marks tests as performance tests
    regression: marks tests as regression tests
    smoke: marks tests as smoke tests
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
    ignore::RuntimeWarning:asyncio
    ignore::RuntimeWarning:coroutine
    ignore::UserWarning
    ignore::FutureWarning
```

## Test Markers

### Available Markers
- `@pytest.mark.slow` - Slow tests (>1 second)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.property` - Property-based tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.regression` - Regression tests
- `@pytest.mark.smoke` - Smoke tests

### Usage Examples
```python
@pytest.mark.slow
def test_large_text_compression():
    """Test compression of large text files."""
    pass

@pytest.mark.integration
def test_end_to_end_workflow():
    """Test complete workflow integration."""
    pass

@pytest.mark.property
@given(text=st.text())
def test_token_count_properties(text: str):
    """Test token counting properties."""
    pass
```

## Running Tests

### Basic Commands
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=utils --cov=agents

# Run specific categories
pytest -m unit
pytest -m integration
pytest -m property
pytest -m performance
pytest -m regression
pytest -m smoke

# Run specific files
pytest tests/test_token_analyzer.py
pytest tests/integration/
pytest tests/property/

# Run with verbose output
pytest -v

# Run with detailed output
pytest -s

# Run only failed tests
pytest --lf

# Run tests in parallel
pytest -n auto
```

### Advanced Commands
```bash
# Run tests excluding slow ones
pytest -m "not slow"

# Run tests with specific pattern
pytest -k "token_count"

# Run tests with maximum failures
pytest --maxfail=5

# Run tests with timeout
pytest --timeout=300

# Run tests with profiling
pytest --profile
```

## Test Data and Fixtures

### Mock Configuration
```python
from tests.mocks import MockConfiguration

@pytest.fixture
def mock_config():
    """Provide mock configuration for tests."""
    return MockConfiguration()
```

### Sample Data
```python
@pytest.fixture
def sample_text():
    """Provide sample text for testing."""
    return "This is a sample text for token analysis."

@pytest.fixture
def sample_experiment_results():
    """Provide sample experiment results."""
    return [
        ExperimentResult(
            experiment_name="Test",
            model_name="starcoder",
            original_query="Test query",
            processed_query="Test query",
            response="Test response",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            response_time=1.5,
            compression_applied=False,
            compression_result=None,
            timestamp=datetime.now(),
        )
    ]
```

## Best Practices

### Test Organization
1. **One test file per module** - Keep tests organized by functionality
2. **Descriptive test names** - Use clear, descriptive test method names
3. **Arrange-Act-Assert** - Structure tests with clear sections
4. **Single responsibility** - Each test should test one thing
5. **Independent tests** - Tests should not depend on each other

### Test Data
1. **Use fixtures** - Create reusable test data with pytest fixtures
2. **Mock external dependencies** - Use mocks for external services
3. **Edge cases** - Test boundary conditions and error cases
4. **Realistic data** - Use realistic test data when possible

### Async Testing
1. **Use pytest-asyncio** - Mark async tests with `@pytest.mark.asyncio`
2. **Proper async mocking** - Use `AsyncMock` for async functions
3. **Await all coroutines** - Ensure all async operations are awaited
4. **Timeout handling** - Set appropriate timeouts for async operations

### Property-Based Testing
1. **Use Hypothesis** - Leverage property-based testing for invariants
2. **Define clear properties** - Test specific properties, not random behavior
3. **Use appropriate strategies** - Choose suitable data generation strategies
4. **Handle edge cases** - Ensure properties hold for edge cases

## Test Coverage

### Current Coverage
- **Overall**: 74% coverage
- **Core modules**: 85%+ coverage
- **Integration tests**: 90%+ coverage
- **Critical paths**: 95%+ coverage

### Coverage Goals
- **Minimum**: 70% overall coverage
- **Target**: 80% overall coverage
- **Critical modules**: 90%+ coverage
- **New code**: 90%+ coverage

### Coverage Commands
```bash
# Generate coverage report
pytest --cov=core --cov=utils --cov=agents --cov-report=html

# View coverage in terminal
pytest --cov=core --cov-report=term-missing

# Coverage with specific modules
pytest --cov=core.token_analyzer --cov=core.text_compressor
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Ensure proper Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Install in development mode
pip install -e .
```

#### 2. Async Test Issues
```python
# Use proper async test markers
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

#### 3. Mock Issues
```python
# Use proper mock patterns
from unittest.mock import Mock, AsyncMock, patch

# For async functions
mock_async = AsyncMock(return_value="result")
result = await mock_async()
```

#### 4. Configuration Issues
```python
# Use mock configuration
from tests.mocks import MockConfiguration
config = MockConfiguration()
```

### Debug Commands
```bash
# Run tests with debug output
pytest -s --log-cli-level=DEBUG

# Run specific test with debug
pytest tests/test_token_analyzer.py::TestSimpleTokenCounter::test_count_tokens_simple_text -s

# Run tests with pdb
pytest --pdb

# Run tests with trace
pytest --trace
```

## Continuous Integration

### GitHub Actions
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.10
      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-cov pytest-asyncio
      - name: Run tests
        run: pytest --cov=core --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

### Pre-commit Hooks
```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## Maintenance

### Regular Tasks
1. **Update test data** - Keep test data current and realistic
2. **Review coverage** - Monitor coverage trends and gaps
3. **Update fixtures** - Maintain and update test fixtures
4. **Clean up tests** - Remove obsolete tests and consolidate duplicates
5. **Performance monitoring** - Track test execution times

### Test Review Checklist
- [ ] Tests are well-organized and documented
- [ ] All critical paths are covered
- [ ] Edge cases and error conditions are tested
- [ ] Tests are independent and repeatable
- [ ] Mock usage is appropriate and minimal
- [ ] Async tests are properly handled
- [ ] Property-based tests validate invariants
- [ ] Performance tests establish baselines

## Resources

### Documentation
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)

### Tools
- **pytest** - Test framework
- **pytest-cov** - Coverage reporting
- **pytest-asyncio** - Async test support
- **pytest-xdist** - Parallel test execution
- **Hypothesis** - Property-based testing
- **unittest.mock** - Mocking framework

### Best Practices References
- [Python Testing Best Practices](https://docs.python.org/3/library/unittest.html)
- [pytest Best Practices](https://docs.pytest.org/en/latest/goodpractices.html)
- [Async Testing Patterns](https://pytest-asyncio.readthedocs.io/en/latest/reference/patterns.html)
- [Property-Based Testing Guide](https://hypothesis.readthedocs.io/en/latest/quickstart.html)
