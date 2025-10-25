# Day 08 AI Agent Guidelines

## Overview

This document provides comprehensive guidelines for AI agents working with the Day 08 Enhanced Token Analysis System. It covers project structure, common tasks, testing workflows, documentation standards, and code quality requirements.

## Project Structure for AI Agents

### Core Directory Structure
```
day_08/
├── core/                    # Core business logic
│   ├── token_analyzer.py    # Token counting strategies
│   ├── text_compressor.py   # Text compression with strategy pattern
│   ├── ml_client.py         # ML service client with retry logic
│   ├── experiments.py       # Experiment management
│   ├── compressors/         # Compression strategy implementations
│   ├── factories/           # Factory pattern implementations
│   ├── builders/            # Builder pattern implementations
│   └── validators/          # Request validation
├── domain/                  # Domain layer (DDD)
│   ├── entities/           # Domain entities
│   ├── value_objects/       # Immutable value objects
│   ├── repositories/       # Repository interfaces
│   └── services/           # Domain services
├── application/             # Application layer
│   ├── use_cases/          # Business use cases
│   ├── services/           # Application services
│   └── dto/                # Data transfer objects
├── infrastructure/         # Infrastructure layer
│   ├── repositories/       # Repository implementations
│   ├── external/           # External service integrations
│   └── config/             # Configuration management
├── tests/                  # Comprehensive test suite
│   ├── integration/        # End-to-end tests
│   ├── regression/         # Baseline behavior tests
│   ├── performance/        # Performance baseline tests
│   └── mocks/              # Test doubles
├── docs/                   # Technical documentation
├── examples/               # Usage examples
├── reports/                # Demo and analysis reports
└── .cursor/                # AI agent resources
    ├── phases/day_08/      # Phase reports and history
    └── day_08_agent_guide.md # This file
```

### Key Files and Their Purposes

#### Core Implementation Files
- **`core/token_analyzer.py`**: Token counting strategies (SimpleTokenCounter, AccurateTokenCounter)
- **`core/text_compressor.py`**: Text compression with strategy pattern (5 algorithms)
- **`core/ml_client.py`**: ML service client with retry logic and circuit breaker
- **`core/experiments.py`**: Experiment management with builder pattern

#### Domain Layer Files
- **`domain/entities/`**: Core business entities (TokenAnalysisDomain, CompressionJob)
- **`domain/value_objects/`**: Immutable value objects (TokenCount, CompressionRatio)
- **`domain/repositories/`**: Repository interfaces for data access
- **`domain/services/`**: Domain services for complex business logic

#### Test Files
- **`tests/test_token_analyzer.py`**: Token analyzer unit tests
- **`tests/test_text_compressor.py`**: Text compressor unit tests
- **`tests/test_ml_client.py`**: ML client unit tests
- **`tests/integration/`**: End-to-end integration tests
- **`tests/mocks/`**: Mock configurations and test doubles

#### Documentation Files
- **`README.md`**: Comprehensive project documentation (English)
- **`README.ru.md`**: Executive summary (Russian)
- **`docs/DEVELOPMENT_GUIDE.md`**: Development practices and guidelines
- **`docs/DOMAIN_GUIDE.md`**: Domain-driven design patterns
- **`docs/ML_ENGINEERING.md`**: ML Engineering framework guide
- **`architecture.md`**: System architecture documentation
- **`api.md`**: API reference documentation

## Common Tasks and Make Commands

### Development Commands
```bash
# Install dependencies
make install-dev

# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test categories
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-performance   # Performance tests only

# Run linting
make lint

# Run security checks
make security

# Format code
make format

# Run all quality checks
make quality-check
```

### Demo Commands
```bash
# Basic demo
make demo

# Enhanced demo with reports
make demo-enhanced

# Demo specific model
make demo-model MODEL=starcoder

# Demo all models
make demo-all

# Run task demonstration
python examples/task_demonstration.py
```

### Development Workflow Commands
```bash
# Install pre-commit hooks
make pre-commit

# Run pre-commit checks
make pre-commit-run

# Clean up
make clean

# Build documentation
make docs
```

## Testing Workflow

### Test Categories

#### Unit Tests
- **Location**: `tests/test_*.py`
- **Purpose**: Test individual components in isolation
- **Coverage**: Core business logic, utilities, helpers
- **Command**: `make test-unit`

#### Integration Tests
- **Location**: `tests/integration/`
- **Purpose**: Test component interactions
- **Coverage**: End-to-end workflows, API integrations
- **Command**: `make test-integration`

#### Regression Tests
- **Location**: `tests/regression/`
- **Purpose**: Ensure backward compatibility
- **Coverage**: Baseline behavior preservation
- **Command**: `make test-regression`

#### Performance Tests
- **Location**: `tests/performance/`
- **Purpose**: Establish performance baselines
- **Coverage**: Response times, memory usage, throughput
- **Command**: `make test-performance`

### Test Execution Guidelines

#### Running Tests
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_token_analyzer.py

# Run specific test function
pytest tests/test_token_analyzer.py::test_simple_token_counter

# Run with coverage
pytest --cov=core --cov-report=html
```

#### Test Data Management
- **Mock Configurations**: Use `tests/mocks/mock_config.py`
- **Test Fixtures**: Define in `conftest.py`
- **Test Data**: Store in `tests/data/`
- **Temporary Files**: Use pytest's `tmp_path` fixture

### Testing Best Practices

#### Test Structure
```python
def test_function_name():
    """Test description."""
    # Arrange
    config = MockConfiguration()
    counter = SimpleTokenCounter(config=config)
    
    # Act
    result = counter.count_tokens("test text", "starcoder")
    
    # Assert
    assert result.count > 0
    assert result.model_name == "starcoder"
```

#### Test Naming
- Use descriptive test names
- Follow pattern: `test_<function>_<scenario>_<expected_result>`
- Examples: `test_count_tokens_with_valid_text_returns_positive_count`

#### Test Coverage
- Aim for 80%+ coverage on core modules
- Test happy path, edge cases, and error conditions
- Use `pytest-cov` for coverage reporting

## Documentation Standards

### Code Documentation

#### Google Style Docstrings
```python
def count_tokens(self, text: str, model_name: str) -> TokenInfo:
    """Count tokens using heuristic estimation.
    
    Args:
        text: The input text to count tokens for.
        model_name: The model name to use for counting.
        
    Returns:
        TokenInfo object containing token count and metadata.
        
    Raises:
        ValueError: If text is empty or model_name is invalid.
        
    Example:
        >>> config = MockConfiguration()
        >>> counter = SimpleTokenCounter(config=config)
        >>> result = counter.count_tokens("Hello world", "starcoder")
        >>> print(result.count)
        2
    """
```

#### Type Hints
```python
from typing import List, Optional, Dict, Any

def process_text(
    text: str,
    max_tokens: int,
    model_name: str = "starcoder",
    strategy: str = "truncation"
) -> CompressionResult:
    """Process text with compression."""
```

### Documentation Files

#### README Structure
- **Overview**: Project description and key features
- **Quick Start**: Installation and basic usage
- **Architecture**: System design and components
- **API Reference**: Function and class documentation
- **Examples**: Practical usage examples
- **Testing**: How to run tests
- **Development**: Guidelines for contributors

#### Technical Documentation
- **Architecture**: System design patterns and layers
- **Domain Guide**: Domain-driven design implementation
- **ML Engineering**: ML framework and best practices
- **Development Guide**: Coding standards and practices

## Code Quality Requirements

### PEP 8 Compliance
- **Line Length**: 88 characters (Black default)
- **Imports**: Use `isort` for import sorting
- **Formatting**: Use `black` for code formatting
- **Naming**: Follow Python naming conventions

### Type Safety
- **Type Hints**: Required for all public functions
- **Return Types**: Always specify return types
- **Optional Types**: Use `Optional[T]` for nullable values
- **Generic Types**: Use `List[T]`, `Dict[K, V]` for collections

### Error Handling
```python
from core.exceptions import TokenAnalysisError, CompressionError

def safe_operation():
    """Example of proper error handling."""
    try:
        result = risky_operation()
        return result
    except TokenAnalysisError as e:
        logger.error(f"Token analysis failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise TokenAnalysisError(f"Operation failed: {e}") from e
```

### Logging Standards
```python
import logging

logger = logging.getLogger(__name__)

def process_data(data: str) -> str:
    """Process data with proper logging."""
    logger.info(f"Processing data of length {len(data)}")
    
    try:
        result = complex_processing(data)
        logger.info("Data processing completed successfully")
        return result
    except Exception as e:
        logger.error(f"Data processing failed: {e}")
        raise
```

## Architecture Guidelines

### Clean Architecture Layers

#### Domain Layer
- **Entities**: Core business objects
- **Value Objects**: Immutable domain concepts
- **Repositories**: Data access interfaces
- **Services**: Complex business logic

#### Application Layer
- **Use Cases**: Business workflows
- **Services**: Application-specific logic
- **DTOs**: Data transfer objects

#### Infrastructure Layer
- **Repositories**: Data access implementations
- **External Services**: Third-party integrations
- **Configuration**: Environment and settings

### Design Patterns

#### Strategy Pattern
```python
class CompressionStrategy(ABC):
    @abstractmethod
    def compress(self, text: str, max_tokens: int) -> str:
        """Compress text using specific strategy."""
        pass

class TruncationStrategy(CompressionStrategy):
    def compress(self, text: str, max_tokens: int) -> str:
        """Compress by truncation."""
        return text[:max_tokens]
```

#### Factory Pattern
```python
class TokenCounterFactory:
    @staticmethod
    def create(counter_type: str, config: Configuration) -> TokenCounter:
        """Create token counter based on type."""
        if counter_type == "simple":
            return SimpleTokenCounter(config)
        elif counter_type == "accurate":
            return AccurateTokenCounter(config)
        else:
            raise ValueError(f"Unknown counter type: {counter_type}")
```

#### Builder Pattern
```python
class ExperimentResultBuilder:
    def __init__(self):
        self._result = ExperimentResult()
    
    def with_experiment_name(self, name: str) -> 'ExperimentResultBuilder':
        self._result.experiment_name = name
        return self
    
    def build(self) -> ExperimentResult:
        return self._result
```

## Quick Navigation Map

### For Code Analysis
1. **Start**: `README.md` - Project overview
2. **Architecture**: `architecture.md` - System design
3. **Core Logic**: `core/` directory - Main implementation
4. **Tests**: `tests/` directory - Test coverage
5. **Examples**: `examples/` directory - Usage patterns

### For Feature Development
1. **Domain**: `domain/` directory - Business logic
2. **Application**: `application/` directory - Use cases
3. **Infrastructure**: `infrastructure/` directory - External integrations
4. **Tests**: Write tests first (TDD approach)
5. **Documentation**: Update relevant docs

### For Bug Fixes
1. **Reproduce**: Create failing test
2. **Fix**: Implement solution
3. **Verify**: Run tests
4. **Document**: Update relevant documentation
5. **Review**: Check code quality

### For Performance Optimization
1. **Baseline**: Run performance tests
2. **Profile**: Identify bottlenecks
3. **Optimize**: Implement improvements
4. **Measure**: Verify improvements
5. **Document**: Update performance docs

## Common Issues and Solutions

### Import Errors
```python
# Correct imports
from core.token_analyzer import SimpleTokenCounter
from tests.mocks.mock_config import MockConfiguration

# Avoid relative imports in tests
# Wrong: from ..core.token_analyzer import SimpleTokenCounter
```

### Configuration Issues
```python
# Always use mock config in tests
config = MockConfiguration()
counter = SimpleTokenCounter(config=config)

# Don't use real config in tests
# Wrong: config = Configuration()  # May fail in CI
```

### Async Testing
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async functions properly."""
    result = await async_function()
    assert result is not None
```

### Mock Usage
```python
from unittest.mock import Mock, patch

def test_with_mock():
    """Use mocks for external dependencies."""
    with patch('core.ml_client.MLClient') as mock_client:
        mock_client.return_value.count_tokens.return_value = TokenInfo(count=10)
        # Test implementation
```

## Best Practices Summary

### Code Quality
- ✅ Follow PEP 8 and use Black for formatting
- ✅ Use type hints for all public functions
- ✅ Write comprehensive docstrings
- ✅ Handle errors gracefully with proper logging
- ✅ Keep functions under 15 lines when possible

### Testing
- ✅ Write tests first (TDD approach)
- ✅ Aim for 80%+ test coverage
- ✅ Test happy path, edge cases, and errors
- ✅ Use descriptive test names
- ✅ Mock external dependencies

### Architecture
- ✅ Follow Clean Architecture principles
- ✅ Use Domain-Driven Design patterns
- ✅ Apply SOLID principles
- ✅ Implement appropriate design patterns
- ✅ Maintain separation of concerns

### Documentation
- ✅ Use Google Style docstrings
- ✅ Keep README up to date
- ✅ Document architectural decisions
- ✅ Provide practical examples
- ✅ Include troubleshooting guides

---

**For detailed information**: See individual documentation files in `docs/` directory  
**For phase history**: See `.cursor/phases/day_08/README.md`  
**For project metrics**: See `FINAL_METRICS_REPORT.md`
