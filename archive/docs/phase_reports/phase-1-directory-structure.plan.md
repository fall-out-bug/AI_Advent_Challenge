<!-- 74f5316f-4ead-4494-9702-44d6b2d2cfce ff016fe3-b7f3-41c5-bbb0-792117b3bdd4 -->
# Phase 1: Create New Directory Structure

## Overview

Create a production-ready Clean Architecture structure with Domain-Driven Design patterns, preserving existing `day_XX` projects while establishing the foundation for unified system migration.

## Architecture Decision

**Clean Architecture + DDD with Compatibility Layer**

- Domain layer: Pure business logic (agents, models, experiments)
- Application layer: Use cases and orchestration
- Infrastructure layer: External services, databases, APIs
- Presentation layer: CLI, API endpoints, web interfaces
- Compatibility layer: Adapters for day_XX project integration

## Directory Structure

```
AI_Challenge/
├── day_01/ ... day_08/           # Existing projects (archived reference)
├── shared/                       # Existing SDK (will integrate)
├── local_models/                 # Existing models (unchanged)
├── src/                          # NEW: Clean Architecture root
│   ├── domain/                   # Core business logic
│   │   ├── __init__.py
│   │   ├── entities/             # Domain entities with identity
│   │   │   ├── __init__.py
│   │   │   ├── agent_task.py     # AgentTask entity
│   │   │   ├── model_config.py   # ModelConfiguration entity
│   │   │   └── experiment_run.py # ExperimentRun entity
│   │   ├── value_objects/        # Immutable value objects
│   │   │   ├── __init__.py
│   │   │   ├── token_info.py     # TokenCount, TokenInfo
│   │   │   ├── quality_metrics.py # QualityScore, Metrics
│   │   │   └── compression_result.py # CompressionRatio
│   │   ├── repositories/         # Repository interfaces
│   │   │   ├── __init__.py
│   │   │   ├── agent_repository.py
│   │   │   ├── model_repository.py
│   │   │   └── experiment_repository.py
│   │   ├── services/             # Domain services
│   │   │   ├── __init__.py
│   │   │   ├── token_analyzer.py # Token analysis logic
│   │   │   ├── code_quality_checker.py
│   │   │   └── experiment_manager.py
│   │   └── exceptions/           # Domain exceptions
│   │       ├── __init__.py
│   │       └── domain_errors.py
│   ├── application/              # Application layer
│   │   ├── __init__.py
│   │   ├── use_cases/            # Business use cases
│   │   │   ├── __init__.py
│   │   │   ├── generate_code.py  # Code generation use case
│   │   │   ├── review_code.py    # Code review use case
│   │   │   ├── analyze_tokens.py # Token analysis use case
│   │   │   └── run_experiment.py # Experiment execution
│   │   ├── dtos/                 # Data Transfer Objects
│   │   │   ├── __init__.py
│   │   │   ├── agent_dtos.py
│   │   │   ├── model_dtos.py
│   │   │   └── experiment_dtos.py
│   │   └── interfaces/           # Application interfaces
│   │       ├── __init__.py
│   │       ├── agent_interface.py
│   │       └── model_interface.py
│   ├── infrastructure/           # Infrastructure layer
│   │   ├── __init__.py
│   │   ├── repositories/         # Concrete implementations
│   │   │   ├── __init__.py
│   │   │   ├── json_agent_repository.py
│   │   │   └── json_experiment_repository.py
│   │   ├── clients/              # External service clients
│   │   │   ├── __init__.py
│   │   │   ├── model_client.py   # Unified model client
│   │   │   └── ml_service_client.py
│   │   ├── config/               # Configuration management
│   │   │   ├── __init__.py
│   │   │   ├── settings.py
│   │   │   └── model_configs.py
│   │   └── adapters/             # Compatibility adapters
│   │       ├── __init__.py
│   │       ├── day_07_adapter.py # Adapter for day_07 agents
│   │       └── day_08_adapter.py # Adapter for day_08 components
│   ├── presentation/             # Presentation layer
│   │   ├── __init__.py
│   │   ├── api/                  # REST API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── agent_routes.py
│   │   │   └── experiment_routes.py
│   │   ├── cli/                  # CLI interface
│   │   │   ├── __init__.py
│   │   │   └── main_cli.py
│   │   └── web/                  # Web interface (future)
│   │       └── __init__.py
│   ├── tests/                    # Tests organized by layer
│   │   ├── unit/
│   │   │   ├── domain/
│   │   │   ├── application/
│   │   │   └── infrastructure/
│   │   ├── integration/
│   │   └── e2e/
│   └── __init__.py
├── config/                       # Root configuration
│   ├── model_limits.yaml
│   ├── agent_configs.yaml
│   └── .env.example
├── docs/                         # Unified documentation
│   ├── architecture/
│   ├── api/
│   └── guides/
├── scripts/                      # Utility scripts
│   ├── setup.sh
│   └── migrate.sh
├── pyproject.toml                # Root Python project
├── poetry.lock
├── Makefile                      # Unified commands
├── docker-compose.yml            # Full stack deployment
├── Dockerfile
└── README.md                     # Updated documentation
```

## Implementation Steps

### Step 1: Create Root Structure

- Create `src/` directory with main layer folders
- Create `config/`, `docs/`, `scripts/` directories
- Set up root `pyproject.toml` with Poetry
- Create `.gitignore` updates

### Step 2: Domain Layer Foundation

- Create domain entities (AgentTask, ModelConfig, ExperimentRun)
- Implement value objects (TokenInfo, QualityMetrics, CompressionResult)
- Define repository interfaces
- Implement domain services (TokenAnalyzer, CodeQualityChecker)
- Set up domain exceptions hierarchy

### Step 3: Application Layer

- Implement use cases (GenerateCode, ReviewCode, AnalyzeTokens, RunExperiment)
- Create DTOs for layer communication
- Define application interfaces
- Set up dependency injection configuration

### Step 4: Infrastructure Layer

- Implement JSON-based repositories
- Create unified model client (integrating shared SDK)
- Set up configuration management (YAML + environment)
- Build compatibility adapters for day_07 and day_08

### Step 5: Presentation Layer

- Create FastAPI application with agent routes
- Implement CLI interface for common operations
- Set up API documentation (OpenAPI)
- Add health check and metrics endpoints

### Step 6: Testing Infrastructure

- Set up pytest configuration
- Create test fixtures and mocks
- Implement unit tests for domain layer
- Add integration tests for application layer
- Create E2E tests for full workflows

### Step 7: Documentation & Deployment

- Update README with new structure
- Create architecture documentation
- Write migration guide
- Set up Docker and Docker Compose
- Create Makefile with common commands

## Key Files to Create

### Root Configuration Files

1. `pyproject.toml` - Poetry project configuration
2. `Makefile` - Development and deployment commands
3. `docker-compose.yml` - Full stack orchestration
4. `Dockerfile` - Multi-stage production build

### Domain Layer (Priority: High)

1. `src/domain/entities/agent_task.py` - Core agent task entity
2. `src/domain/value_objects/token_info.py` - Token counting value objects
3. `src/domain/services/token_analyzer.py` - Token analysis service
4. `src/domain/repositories/agent_repository.py` - Agent repository interface

### Application Layer (Priority: High)

1. `src/application/use_cases/generate_code.py` - Code generation use case
2. `src/application/use_cases/review_code.py` - Code review use case
3. `src/application/dtos/agent_dtos.py` - Agent DTOs

### Infrastructure Layer (Priority: High)

1. `src/infrastructure/clients/model_client.py` - Unified model client
2. `src/infrastructure/config/settings.py` - Configuration management
3. `src/infrastructure/adapters/day_07_adapter.py` - Day 07 compatibility

### Presentation Layer (Priority: Medium)

1. `src/presentation/api/__main__.py` - FastAPI application
2. `src/presentation/cli/main_cli.py` - CLI entry point

## Integration with Existing Components

### Shared SDK Integration

- Import `shared_package.agents` into infrastructure layer
- Wrap SDK clients with infrastructure adapters
- Maintain backward compatibility with existing SDK API

### Day 07 Agents Integration

- Create adapters for CodeGeneratorAgent and CodeReviewerAgent
- Map day_07 orchestrator to new use cases
- Preserve REST API endpoints through presentation layer

### Day 08 Components Integration

- Import token analysis components as domain services
- Adapt compression strategies to domain layer
- Integrate ML engineering patterns into application layer

### Local Models Integration

- No changes required to local_models infrastructure
- Access through unified model client in infrastructure layer

## Migration Strategy

### Phase 1A: Foundation (This Phase)

- Create directory structure
- Implement core domain entities and services
- Set up basic infrastructure

### Phase 1B: Integration (Next)

- Build compatibility adapters
- Integrate existing components
- Validate all day_XX functionality works

### Phase 1C: Testing (Next)

- Comprehensive test coverage (80%+)
- Integration testing with existing projects
- Performance benchmarking

## Success Criteria

- [ ] All directory structure created with proper `__init__.py` files
- [ ] Core domain entities implemented with 100% type hints
- [ ] Repository interfaces defined following DIP
- [ ] At least 2 use cases implemented (GenerateCode, ReviewCode)
- [ ] Unified model client working with shared SDK
- [ ] Compatibility adapter for day_07 functional
- [ ] Basic CLI and API endpoints operational
- [ ] Unit tests for domain layer (80%+ coverage)
- [ ] Docker configuration working
- [ ] Documentation updated

## Dependencies

**Python Packages** (to add to pyproject.toml):

- Core: `python = "^3.10"`
- Web: `fastapi`, `uvicorn`, `pydantic`
- Async: `httpx`, `asyncio`
- Testing: `pytest`, `pytest-asyncio`, `pytest-cov`
- Quality: `black`, `mypy`, `flake8`, `bandit`
- Config: `pydantic-settings`, `python-dotenv`, `pyyaml`

**Existing Dependencies** (reuse):

- Shared SDK: Already installed
- Local models: Docker infrastructure

## Timeline Estimate

- **Directory structure setup**: 1 hour
- **Domain layer implementation**: 4-6 hours
- **Application layer**: 3-4 hours
- **Infrastructure layer**: 4-5 hours
- **Presentation layer**: 2-3 hours
- **Testing infrastructure**: 3-4 hours
- **Documentation**: 2-3 hours
- **Total**: ~20-30 hours of development

## Notes

- Follow strict layer dependency rules (domain ← application ← infrastructure)
- All domain code must be framework-agnostic
- Use dependency injection for all cross-layer dependencies
- Maintain 100% type hint coverage in core modules
- Every public function must have docstrings
- Follow PEP8 and project code standards
- All commits must pass linting and tests

### To-dos

- [ ] Create root directory structure (src/, config/, docs/, scripts/)
- [ ] Set up pyproject.toml, Makefile, docker-compose.yml, and root configuration files
- [ ] Implement domain entities (AgentTask, ModelConfig, ExperimentRun)
- [ ] Implement value objects (TokenInfo, QualityMetrics, CompressionResult)
- [ ] Define repository interfaces following DIP
- [ ] Implement domain services (TokenAnalyzer, CodeQualityChecker, ExperimentManager)
- [ ] Implement application use cases (GenerateCode, ReviewCode, AnalyzeTokens, RunExperiment)
- [ ] Create DTOs for layer communication (agent_dtos, model_dtos, experiment_dtos)
- [ ] Implement concrete repositories (JSON-based for agents and experiments)
- [ ] Create unified model client integrating shared SDK
- [ ] Build compatibility adapters for day_07 and day_08 components
- [ ] Create FastAPI application with agent and experiment routes
- [ ] Implement CLI interface for common operations
- [ ] Set up pytest configuration and test infrastructure (fixtures, mocks)
- [ ] Implement unit tests for domain layer (80%+ coverage target)
- [ ] Add integration tests for application layer use cases
- [ ] Create Dockerfile with multi-stage build and docker-compose configuration
- [ ] Update README, create architecture docs, and write migration guide