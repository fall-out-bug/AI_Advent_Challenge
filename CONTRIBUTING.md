# Contributing to AI Challenge

Thank you for your interest in contributing to the AI Challenge project!

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone.

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what is best for the community

## Getting Started

### Prerequisites

- Python 3.10+
- Poetry (dependency management)
- Docker (for local models)
- Git

### Fork and Clone

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/your-username/AI_Challenge.git
cd AI_Challenge

# Add upstream remote
git remote add upstream https://github.com/original-owner/AI_Challenge.git
```

## Development Setup

### 1. Install Dependencies

```bash
# Install Poetry if not installed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Activate virtual environment
poetry shell
```

### 2. Configure Environment

```bash
# Copy example API key file
cp api_key.txt.example api_key.txt

# Add your API keys to api_key.txt
```

### 3. Run Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test
pytest src/tests/unit/domain/test_agent_task.py -v
```

### 4. Start Local Models (Optional)

```bash
cd local_models
docker-compose up -d

# Verify models are running
curl http://localhost:8000/health
```

## Development Workflow

### 1. Create a Branch

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Or bugfix branch
git checkout -b bugfix/your-bugfix-name
```

### 2. Make Changes

Follow the code standards below.

### 3. Run Quality Checks

```bash
# Format code
make format

# Check types
make type-check

# Lint code
make lint

# Run all checks
make quality
```

### 4. Run Tests

```bash
# Run tests
make test

# Check coverage
make test-coverage
```

### 5. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add new feature X"
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

### 6. Push to Fork

```bash
git push origin feature/your-feature-name
```

### 7. Create Pull Request

Open a pull request on GitHub with:
- Clear description of changes
- Link to related issues
- Screenshots (if applicable)
- Test coverage information

## Code Standards

### Python Style Guide

We follow **PEP 8** and the **Zen of Python**.

#### Key Principles

1. **Readability Counts**
   ```python
   # Good
   def calculate_fibonacci(n: int) -> int:
       """Calculate Fibonacci number."""
       if n < 2:
           return n
       return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)

   # Bad
   def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)
   ```

2. **Explicit is Better than Implicit**
   ```python
   # Good
   from typing import List, Dict
   def process_items(items: List[str]) -> Dict[str, int]:
       pass

   # Bad
   def process_items(items):
       pass
   ```

3. **Simple is Better than Complex**
   ```python
   # Good - Clear and simple
   def is_even(n: int) -> bool:
       return n % 2 == 0

   # Bad - Unnecessarily complex
   def is_even(n: int) -> bool:
       return bool((n >> 1) << 1 == n)
   ```

### Function Length

**Maximum 15 lines per function** where possible.

```python
# Good - Focused function
def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email:
        return False
    return "@" in email and "." in email.split("@")[1]

# Bad - Too long, multiple responsibilities
def process_user_data(data):
    # 50+ lines of code doing multiple things
    pass
```

### Type Hints

**All functions must have type hints.**

```python
# Good
def process_task(
    task_id: str,
    priority: int = 1,
    timeout: Optional[float] = None
) -> Dict[str, Any]:
    """Process a task."""
    pass

# Bad
def process_task(task_id, priority=1, timeout=None):
    pass
```

### Docstrings

**Every public function needs a docstring.**

Format:
```python
def function_name(param1: type, param2: type) -> return_type:
    """Brief description.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is invalid

    Example:
        >>> function_name("example", 42)
        "result"
    """
    pass
```

### Clean Code Practices

1. **Remove dead code**
   ```bash
   # Before committing
   # Remove unused imports
   # Remove print statements
   # Remove commented-out code
   ```

2. **Meaningful names**
   ```python
   # Good
   def calculate_total_price(items: List[Item]) -> float:
       pass

   # Bad
   def calc_tp(itms):
       pass
   ```

3. **One responsibility**
   ```python
   # Good - Single responsibility
   def calculate_tax(price: float, rate: float) -> float:
       return price * rate

   def calculate_total(items: List[Item]) -> float:
       return sum(item.price for item in items)

   # Bad - Multiple responsibilities
   def calculate_tax_and_total(items: List[Item], rate: float):
       tax = sum(item.price * rate for item in items)
       total = sum(item.price for item in items) + tax
       return tax, total
   ```

## Testing Guidelines

### TDD Workflow

1. **Red**: Write failing test
2. **Green**: Write minimal code to pass
3. **Refactor**: Improve code while keeping tests green

### Test Coverage

- **Minimum**: 80% overall coverage
- **Critical paths**: 90%+ coverage
- **Domain layer**: 85%+ coverage

### Test Organization

```
src/tests/
├── unit/              # Unit tests (fast, isolated)
├── integration/       # Integration tests
└── e2e/              # End-to-end tests
```

### Test Naming

```python
def test_function_name_should_do_what():
    """Test description."""
    pass
```

### Test Structure

```python
@pytest.mark.asyncio
async def test_orchestrator_handles_errors_gracefully():
    """Test that orchestrator handles errors without crashing."""
    # Arrange
    orchestrator = MultiAgentOrchestrator()
    request = OrchestratorRequest(task_description="invalid task")

    # Act
    response = await orchestrator.process_task(request)

    # Assert
    assert response.success is False
    assert response.error_message is not None
```

## Documentation

### Docstrings

Every module, class, and public function needs a docstring:

```python
"""Module-level docstring describing the module."""

class MyClass:
    """Class docstring describing the class.

    Attributes:
        attribute1: Description of attribute1
        attribute2: Description of attribute2
    """

    def method(self, param: str) -> str:
        """Method docstring.

        Args:
            param: Parameter description

        Returns:
            Return value description
        """
        pass
```

### Documentation Files

When adding new features:
1. Update `README.md` if needed
2. Add/update relevant docs in `docs/`
3. Update `CHANGELOG.md`
4. Update API docs if adding endpoints

## Pull Request Process

### Before Submitting

1. ✓ All tests pass
2. ✓ Code coverage maintained (80%+)
3. ✓ Linting passes
4. ✓ Type checking passes
5. ✓ Documentation updated
6. ✓ No merge conflicts

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No new linting errors
- [ ] Commit messages follow guidelines

### Review Process

1. Maintainers will review your PR
2. Address any feedback
3. Get approval from at least one maintainer
4. Merge to main branch

## Getting Help

- **Documentation**: See [docs/](docs/)
- **Questions**: Open an issue
- **Bugs**: Report in issues
- **Features**: Discuss in issues first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

