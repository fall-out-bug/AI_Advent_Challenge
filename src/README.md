# AI Challenge - Clean Architecture

This directory contains the new Clean Architecture implementation for the AI Challenge project, following Domain-Driven Design patterns.

## Directory Structure

```
src/
├── domain/              # Core business logic (no dependencies)
│   ├── entities/       # Domain entities with identity
│   ├── value_objects/  # Immutable value objects
│   ├── repositories/   # Repository interfaces
│   ├── services/       # Domain services
│   └── exceptions/     # Domain exceptions
├── application/        # Application layer (use cases)
│   ├── use_cases/     # Business use cases
│   ├── dtos/          # Data transfer objects
│   └── interfaces/    # Application interfaces
├── infrastructure/     # Infrastructure layer
│   ├── repositories/  # Concrete repository implementations
│   ├── clients/       # External service clients
│   ├── config/        # Configuration management
│   └── adapters/      # Compatibility adapters
├── presentation/      # Presentation layer
│   ├── api/           # REST API endpoints
│   ├── cli/           # CLI interface
│   └── web/           # Web interface
└── tests/             # Tests organized by layer
```

## Architecture Principles

### 1. Clean Architecture
- **Domain Layer**: Pure business logic, no framework dependencies
- **Application Layer**: Use cases and orchestration
- **Infrastructure Layer**: External services and implementations
- **Presentation Layer**: API endpoints, CLI, web interfaces

### 2. Dependency Rule
```
Presentation → Application → Domain ← Infrastructure
```

Dependencies point inward toward the domain.

### 3. SOLID Principles
- **Single Responsibility**: Each class has one reason to change
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Subtypes must be substitutable
- **Interface Segregation**: Many client-specific interfaces
- **Dependency Inversion**: Depend on abstractions, not concretions

## Key Components

### Domain Layer

#### Entities
- `AgentTask`: Agent task execution entities
- `ModelConfig`: Model configuration entities
- `ExperimentRun`: Experiment run entities

#### Value Objects
- `TokenInfo`: Token usage information
- `TokenCount`: Token count metrics
- `QualityScore`: Code quality scores
- `Metrics`: Comprehensive quality metrics
- `CompressionRatio`: Compression metrics

#### Services
- `TokenAnalyzer`: Token analysis service
- `CodeQualityChecker`: Code quality checking service

### Application Layer

#### Use Cases
- `GenerateCodeUseCase`: Code generation use case
- `ReviewCodeUseCase`: Code review use case

#### DTOs
- `AgentTaskDTO`: Agent task data transfer objects
- `ModelConfigDTO`: Model configuration DTOs

### Infrastructure Layer

#### Repositories
- `JsonAgentRepository`: JSON-based agent repository
- `InMemoryModelRepository`: In-memory model repository

#### Clients
- `ModelClient`: Abstract model client interface
- `SimpleModelClient`: Simple stub implementation

### Presentation Layer

#### API
- `agent_routes.py`: Agent API routes
- `__main__.py`: FastAPI application entry point

## Usage

### Running the API

```bash
# Install dependencies
poetry install

# Run API server
poetry run uvicorn src.presentation.api.__main__:create_app --reload
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
poetry run black src

# Check types
poetry run mypy src

# Lint code
poetry run flake8 src
```

## Development Guidelines

1. **Always follow the dependency rule**: Inner layers never depend on outer layers
2. **Use value objects for immutable data**: TokenInfo, QualityMetrics, etc.
3. **Domain entities have identity**: AgentTask, ModelConfig, ExperimentRun
4. **Repository interfaces in domain layer**: Implementation in infrastructure
5. **Use dependency injection**: Pass dependencies through constructors
6. **Write tests first**: Follow TDD principles
7. **100% type hints**: All function signatures must be typed
8. **Document with docstrings**: Every public function needs docs

## Zen of Python

This implementation follows the Zen of Python:
- Beautiful is better than ugly
- Simple is better than complex
- Readability counts
- There should be one obvious way to do it
- If the implementation is hard to explain, it's a bad idea
- If the implementation is easy to explain, it may be a good idea

## Next Steps

1. Implement remaining use cases
2. Add integration tests
3. Build compatibility adapters for day_07 and day_08
4. Add comprehensive documentation
5. Set up CI/CD pipeline

