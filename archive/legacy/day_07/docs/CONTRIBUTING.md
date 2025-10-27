# Contributing to StarCoder Multi-Agent System

Thank you for your interest in contributing to the StarCoder Multi-Agent System! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style Guide](#code-style-guide)
- [Testing Requirements](#testing-requirements)
- [Commit Message Format](#commit-message-format)
- [Pull Request Process](#pull-request-process)
- [Code Review Checklist](#code-review-checklist)
- [CI/CD Pipeline](#cicd-pipeline)
- [Documentation Standards](#documentation-standards)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

This project follows a code of conduct that ensures a welcoming environment for all contributors. Please:

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Report inappropriate behavior

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git
- NVIDIA GPU (for StarCoder model)
- Basic understanding of:
  - Python async programming
  - FastAPI
  - Docker
  - AI/ML concepts

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/AI_Challenge.git
   cd AI_Challenge/day_07
   ```

3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/original-owner/AI_Challenge.git
   ```

## Development Setup

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio pytest-cov black isort flake8 mypy
```

### 2. Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

### 3. Docker Development

```bash
# Start StarCoder service
cd ../local_models
docker-compose up -d starcoder-chat

# Start agent services
cd ../day_07
docker-compose up -d

# Check services
make health
```

### 4. IDE Configuration

#### VS Code Settings

Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.sortImports.args": ["--profile", "black"],
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"]
}
```

#### PyCharm Configuration

1. Set Python interpreter to virtual environment
2. Enable Black formatter
3. Configure pytest as test runner
4. Enable type checking with mypy

## Code Style Guide

### Python Style

We follow **PEP 8** with some modifications:

```python
# Line length: 100 characters (not 79)
def long_function_name(
    parameter_one: str,
    parameter_two: int,
    parameter_three: bool = False,
) -> Optional[Dict[str, Any]]:
    """Function with proper type hints and docstring."""
    pass
```

### Type Hints

**Required** for all functions and methods:

```python
from typing import List, Dict, Optional, Union, Any
from datetime import datetime

def process_data(
    items: List[str],
    config: Optional[Dict[str, Any]] = None,
    timeout: float = 30.0
) -> Union[Dict[str, Any], None]:
    """Process data with proper type hints."""
    pass
```

### Docstrings

Use **Google Style** docstrings:

```python
def calculate_score(
    code: str,
    tests: str,
    requirements: List[str]
) -> float:
    """Calculate code quality score.
    
    Args:
        code: The Python code to evaluate
        tests: Associated test code
        requirements: List of requirements to check
        
    Returns:
        Quality score between 0.0 and 10.0
        
    Raises:
        ValidationError: If code is invalid
        ValueError: If requirements are malformed
        
    Examples:
        >>> score = calculate_score("def test(): pass", "def test_test(): pass", [])
        >>> 0 <= score <= 10
        True
        
    Note:
        This function uses static analysis and doesn't execute code.
    """
    pass
```

### Import Organization

```python
# Standard library imports
import os
import sys
from typing import Dict, List

# Third-party imports
import httpx
from fastapi import FastAPI
from pydantic import BaseModel

# Local imports
from .base_agent import BaseAgent
from ..communication.message_schema import CodeGenerationRequest
```

### Error Handling

```python
# Good: Specific exceptions
try:
    result = await agent.process(request)
except httpx.HTTPError as e:
    logger.error(f"HTTP error: {e}")
    raise CodeGenerationError(f"Request failed: {e}") from e
except ValidationError as e:
    logger.warning(f"Validation error: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise CodeGenerationError("Unexpected error occurred") from e

# Bad: Bare except
try:
    result = await agent.process(request)
except:
    pass  # Never do this
```

### Constants

Use constants instead of magic numbers:

```python
# Good
from .constants import MAX_RETRIES, TIMEOUT_SECONDS

for attempt in range(MAX_RETRIES):
    await asyncio.sleep(TIMEOUT_SECONDS)

# Bad
for attempt in range(3):
    await asyncio.sleep(2)
```

## Testing Requirements

### Test Structure

```
tests/
├── unit/
│   ├── test_base_agent.py
│   ├── test_code_generator.py
│   └── test_code_reviewer.py
├── integration/
│   ├── test_orchestrator.py
│   └── test_api_endpoints.py
├── fixtures/
│   ├── sample_code.py
│   └── mock_responses.py
└── conftest.py
```

### Test Naming

```python
# Test functions
def test_generate_code_with_valid_input():
    """Test code generation with valid input."""
    pass

def test_generate_code_with_invalid_input_raises_error():
    """Test code generation raises error with invalid input."""
    pass

def test_review_code_returns_quality_score():
    """Test code review returns quality score."""
    pass
```

### Test Coverage

- **Minimum coverage**: 80%
- **Target coverage**: 90%
- **Critical paths**: 100% coverage required

```bash
# Run tests with coverage
pytest --cov=. --cov-report=html --cov-report=term

# Check coverage threshold
pytest --cov=. --cov-fail-under=80
```

### Async Testing

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_async_function():
    """Test async function properly."""
    with patch('module.external_call', new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"result": "success"}
        
        result = await async_function()
        
        assert result == "success"
        mock_call.assert_called_once()
```

### Mocking Guidelines

```python
# Mock external dependencies
@patch('httpx.AsyncClient.post')
async def test_api_call(mock_post):
    mock_post.return_value.json.return_value = {"status": "ok"}
    mock_post.return_value.raise_for_status.return_value = None
    
    result = await make_api_call()
    
    assert result["status"] == "ok"
```

## Commit Message Format

We use **Conventional Commits**:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
# Good commits
feat(api): add rate limiting to all endpoints
fix(generator): handle empty code validation
docs(readme): update installation instructions
test(orchestrator): add integration tests
refactor(agent): extract common functionality to base class

# Bad commits
fix stuff
update
WIP
```

### Commit Body

For complex changes, include a detailed body:

```
feat(api): add code refinement endpoint

- Add POST /refine endpoint to generator API
- Implement Pydantic validation for refine requests
- Add comprehensive error handling
- Update API documentation

Closes #123
```

## Pull Request Process

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Changes

- Write code following style guidelines
- Add tests for new functionality
- Update documentation
- Ensure all tests pass

### 3. Commit Changes

```bash
git add .
git commit -m "feat(api): add new endpoint"
```

### 4. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Create PR with:
- Clear title and description
- Link to related issues
- Screenshots for UI changes
- Test results

### 5. PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

## Code Review Checklist

### For Reviewers

- [ ] **Functionality**: Does the code work as intended?
- [ ] **Tests**: Are there adequate tests?
- [ ] **Style**: Does code follow style guidelines?
- [ ] **Documentation**: Is documentation updated?
- [ ] **Performance**: Are there performance implications?
- [ ] **Security**: Are there security concerns?
- [ ] **Error Handling**: Is error handling appropriate?

### For Authors

- [ ] **Self-review**: Review your own code first
- [ ] **Tests**: Ensure all tests pass
- [ ] **Documentation**: Update relevant docs
- [ ] **Breaking Changes**: Document any breaking changes
- [ ] **Performance**: Consider performance impact

### Review Guidelines

- Be constructive and specific
- Suggest improvements, don't just criticize
- Test the changes locally when possible
- Ask questions if something is unclear
- Approve when ready, don't rush

## CI/CD Pipeline

### Automated Checks

Every PR runs:

1. **Code Quality**:
   ```bash
   black --check .
   isort --check-only .
   flake8 .
   mypy .
   ```

2. **Testing**:
   ```bash
   pytest tests/ --cov=. --cov-fail-under=80
   ```

3. **Security**:
   ```bash
   bandit -r .
   safety check
   ```

4. **Docker Build**:
   ```bash
   docker-compose build
   docker-compose up -d
   make health
   ```

### Pre-commit Configuration

`.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

## Documentation Standards

### Code Documentation

- **Docstrings**: Required for all public functions/classes
- **Type Hints**: Required for all function signatures
- **Comments**: Explain complex logic, not obvious code
- **README**: Keep updated with setup instructions

### API Documentation

- **OpenAPI**: Keep API docs current
- **Examples**: Include practical examples
- **Error Codes**: Document all possible errors
- **Rate Limits**: Document rate limiting rules

### User Documentation

- **Clear Instructions**: Step-by-step guides
- **Examples**: Working code examples
- **Troubleshooting**: Common issues and solutions
- **FAQ**: Frequently asked questions

## Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Ubuntu 20.04]
- Python: [e.g., 3.11.0]
- Docker: [e.g., 20.10.0]
- GPU: [e.g., RTX 3080]

## Additional Context
Any other relevant information
```

### Feature Requests

Use the feature request template:

```markdown
## Feature Description
Clear description of the feature

## Use Case
Why is this feature needed?

## Proposed Solution
How should this be implemented?

## Alternatives
Other solutions considered

## Additional Context
Any other relevant information
```

## Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: General questions and ideas
- **Pull Requests**: Code contributions

### Resources

- [Python Documentation](https://docs.python.org/3/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Docker Documentation](https://docs.docker.com/)

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to the StarCoder Multi-Agent System! 🚀
