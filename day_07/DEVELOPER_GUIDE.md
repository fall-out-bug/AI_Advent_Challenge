# Developer Guide

This guide provides comprehensive information for developers working on the StarCoder Multi-Agent System.

## Table of Contents

- [Development Environment Setup](#development-environment-setup)
- [Project Architecture](#project-architecture)
- [Code Organization](#code-organization)
- [Development Workflow](#development-workflow)
- [Testing Strategy](#testing-strategy)
- [Debugging Tips](#debugging-tips)
- [Contributing Guidelines](#contributing-guidelines)
- [Performance Optimization](#performance-optimization)
- [Security Considerations](#security-considerations)

## Development Environment Setup

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- NVIDIA GPU (for StarCoder model)
- Poetry (for dependency management)
- Git

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd AI_Challenge/day_07
   ```

2. **Install Poetry:**
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   export PATH="$HOME/.local/bin:$PATH"
   ```

3. **Install dependencies:**
   ```bash
   poetry install
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your HuggingFace token
   ```

5. **Start StarCoder service:**
   ```bash
   cd ../local_models
   docker-compose up -d starcoder-chat
   ```

6. **Start agent services:**
   ```bash
   cd ../day_07
   make start
   ```

### IDE Configuration

#### VS Code

Recommended extensions:
- Python
- Pylance
- Black Formatter
- isort
- Docker
- GitLens

Settings (`.vscode/settings.json`):
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.flake8Args": ["--max-line-length=100"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

## Project Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Orchestrator  │    │  Code Generator │    │  Code Reviewer  │
│                 │    │     Agent       │    │     Agent       │
│  - Coordinates  │◄──►│  - Generates    │◄──►│  - Reviews      │
│  - Manages      │    │  - Creates      │    │  - Analyzes     │
│  - Saves        │    │  - Validates    │    │  - Scores       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Shared SDK     │
                    │  - StarCoder    │
                    │  - Mistral     │
                    │  - Qwen        │
                    │  - TinyLlama   │
                    └─────────────────┘
```

### Component Details

#### Orchestrator (`orchestrator.py`)
- **Purpose**: Coordinates the entire workflow
- **Responsibilities**:
  - Manages workflow execution
  - Handles error recovery
  - Saves results
  - Provides statistics

#### Code Generator Agent (`agents/core/code_generator.py`)
- **Purpose**: Generates Python code and tests
- **Responsibilities**:
  - Processes generation requests
  - Extracts code from model responses
  - Validates generated code
  - Creates test templates

#### Code Reviewer Agent (`agents/core/code_reviewer.py`)
- **Purpose**: Reviews and analyzes code quality
- **Responsibilities**:
  - Analyzes code quality
  - Checks PEP8 compliance
  - Evaluates test coverage
  - Provides recommendations

#### Communication Layer (`communication/`)
- **Purpose**: Handles inter-agent communication
- **Components**:
  - `agent_client.py`: HTTP client with retry logic
  - `message_schema.py`: Pydantic models for requests/responses

#### Model Integration (`agents/core/model_client_adapter.py`)
- **Purpose**: Abstracts model communication
- **Responsibilities**:
  - Handles different model types
  - Manages model-specific settings
  - Provides unified interface

## Code Organization

### Directory Structure

```
day_07/
├── agents/                    # Agent implementations
│   ├── api/                  # FastAPI services
│   │   ├── generator_api.py  # Generator HTTP API
│   │   └── reviewer_api.py   # Reviewer HTTP API
│   └── core/                 # Core agent logic
│       ├── base_agent.py     # Base agent class
│       ├── code_generator.py # Generator implementation
│       ├── code_reviewer.py  # Reviewer implementation
│       └── model_client_adapter.py # Model integration
├── communication/             # Inter-agent communication
│   ├── agent_client.py       # HTTP client
│   └── message_schema.py     # Request/response models
├── prompts/                  # Prompt templates
│   ├── generator_prompts.py  # Generation prompts
│   └── reviewer_prompts.py   # Review prompts
├── tests/                    # Test suite
├── examples/                 # Usage examples
├── orchestrator.py           # Main orchestrator
├── demo.py                   # Demo script
├── main.py                   # CLI entry point
└── constants.py              # Configuration constants
```

### Key Design Patterns

#### 1. Base Agent Pattern
All agents inherit from `BaseAgent` which provides:
- Model integration
- Statistics tracking
- Common utilities
- Logging

#### 2. Strategy Pattern
Different models are handled through the `ModelClientAdapter`:
- Unified interface for all models
- Model-specific configuration
- Easy addition of new models

#### 3. Factory Pattern
Agent creation uses factory methods:
- Consistent initialization
- Environment-based configuration
- Easy testing with mocks

## Development Workflow

### Adding New Features

1. **Create feature branch:**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Write tests first (TDD):**
   ```python
   # tests/test_new_feature.py
   def test_new_feature():
       # Test implementation
       pass
   ```

3. **Implement feature:**
   - Follow existing patterns
   - Add proper logging
   - Include error handling
   - Write docstrings

4. **Run tests:**
   ```bash
   poetry run pytest tests/test_new_feature.py -v
   ```

5. **Format code:**
   ```bash
   poetry run black .
   poetry run isort .
   ```

6. **Run linting:**
   ```bash
   poetry run flake8 .
   ```

7. **Commit changes:**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

### Code Review Process

1. **Create pull request**
2. **Ensure all checks pass:**
   - Tests pass
   - Code is formatted
   - No linting errors
   - Documentation updated

3. **Review checklist:**
   - [ ] Code follows project patterns
   - [ ] Tests cover new functionality
   - [ ] Documentation is updated
   - [ ] Error handling is appropriate
   - [ ] Logging is added where needed
   - [ ] Performance impact is considered

## Testing Strategy

### Test Types

#### 1. Unit Tests
- Test individual functions/methods
- Use mocks for external dependencies
- Focus on business logic

#### 2. Integration Tests
- Test component interactions
- Use real services where possible
- Test error scenarios

#### 3. End-to-End Tests
- Test complete workflows
- Use actual models
- Verify end-to-end functionality

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_generator.py

# Run with coverage
poetry run pytest --cov=. --cov-report=html

# Run integration tests only
poetry run pytest -m integration
```

### Test Data Management

- Use fixtures for common test data
- Create test data factories
- Mock external services
- Use environment variables for test configuration

## Debugging Tips

### Common Issues

#### 1. Model Connection Issues
```bash
# Check if StarCoder is running
curl http://localhost:8003/health

# Check logs
docker-compose logs starcoder-chat
```

#### 2. Agent Communication Issues
```bash
# Check agent health
curl http://localhost:9001/health
curl http://localhost:9002/health

# Check logs
docker-compose logs generator-agent
docker-compose logs reviewer-agent
```

#### 3. Memory Issues
```bash
# Check memory usage
docker stats

# Monitor GPU usage
nvidia-smi
```

### Debugging Tools

#### 1. Logging
```python
import logging
logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Detailed information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
```

#### 2. Debug Mode
Set environment variable:
```bash
export LOG_LEVEL=DEBUG
```

#### 3. Interactive Debugging
```python
import pdb; pdb.set_trace()
```

## Contributing Guidelines

### Code Standards

1. **Follow PEP 8**
2. **Use type hints**
3. **Write docstrings**
4. **Keep functions under 15 lines**
5. **Use meaningful names**
6. **Handle errors gracefully**

### Commit Message Format

```
type(scope): description

feat: add new feature
fix: fix bug
docs: update documentation
style: formatting changes
refactor: code refactoring
test: add tests
chore: maintenance tasks
```

### Pull Request Guidelines

1. **Keep PRs small and focused**
2. **Include tests for new features**
3. **Update documentation**
4. **Add changelog entry**
5. **Ensure CI passes**

## Performance Optimization

### Code Optimization

1. **Use async/await properly**
2. **Minimize database calls**
3. **Cache expensive operations**
4. **Use connection pooling**
5. **Optimize model calls**

### Monitoring

1. **Track response times**
2. **Monitor memory usage**
3. **Log performance metrics**
4. **Set up alerts**

### Scaling Considerations

1. **Horizontal scaling**
2. **Load balancing**
3. **Database optimization**
4. **Caching strategies**

## Security Considerations

### Code Security

1. **Validate all inputs**
2. **Use parameterized queries**
3. **Sanitize user data**
4. **Implement rate limiting**
5. **Use secure defaults**

### Infrastructure Security

1. **Run containers as non-root**
2. **Use minimal base images**
3. **Scan for vulnerabilities**
4. **Implement network policies**
5. **Use secrets management**

### API Security

1. **Implement authentication**
2. **Use HTTPS**
3. **Validate API keys**
4. **Implement CORS**
5. **Log security events**

## Troubleshooting

### Common Problems

#### 1. Import Errors
- Check Python path
- Verify virtual environment
- Check dependencies

#### 2. Docker Issues
- Check Docker daemon
- Verify image builds
- Check resource limits

#### 3. Model Issues
- Verify model availability
- Check GPU resources
- Monitor memory usage

### Getting Help

1. **Check logs first**
2. **Search existing issues**
3. **Create detailed bug report**
4. **Include environment info**
5. **Provide reproduction steps**

## Resources

- [Python Documentation](https://docs.python.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Pytest Documentation](https://docs.pytest.org/)

## Conclusion

This developer guide provides the foundation for contributing to the StarCoder Multi-Agent System. Follow these guidelines to ensure code quality, maintainability, and consistency across the project.

For questions or clarifications, please refer to the project documentation or create an issue in the repository.
