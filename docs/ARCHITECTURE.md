# Architecture Documentation

## Overview

This document describes the Clean Architecture implementation of the AI Challenge project, following SOLID principles and the Zen of Python.

## Architecture Principles

### Clean Architecture Layers

The application is organized into four distinct layers:

1. **Domain Layer** - Core business logic
2. **Application Layer** - Use cases and orchestration
3. **Infrastructure Layer** - External integrations
4. **Presentation Layer** - API and CLI interfaces

### Dependency Flow

```
┌─────────────────────┐
│  Presentation       │  ← User Interface
│  (API, CLI)        │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Application        │  ← Use Cases & Orchestrators
│  (Orchestrators)   │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Domain             │  ← Business Logic
│  (Entities, VO)    │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Infrastructure     │  ← External Services
│  (Clients, Repos)  │
└─────────────────────┘
```

## Domain Layer

### Purpose
Contains the core business logic and entities, independent of external frameworks.

### Components

#### Entities
- `AgentTask` - Task lifecycle management
- `ModelConfig` - Model configuration with validation
- `TokenInfo` - Token counting and analysis

#### Value Objects
- `TaskMetadata` - Immutable task metadata
- `CodeQualityMetrics` - Code quality assessment
- `TokenCount` - Token usage information

#### Services
- `CodeGeneratorAgent` - Code generation logic
- `CodeReviewerAgent` - Code review logic
- `TokenAnalyzer` - Token analysis and compression
- `RiddleEvaluator` - Riddle testing and evaluation

## Application Layer

### Purpose
Implements use cases and orchestrates workflows between domain entities.

### Components

#### Orchestrators
- `MultiAgentOrchestrator` - Sequential multi-agent workflows
- `ParallelOrchestrator` - Concurrent agent execution

#### Use Cases
- `GenerateCodeUseCase` - Code generation workflow
- `ReviewCodeUseCase` - Code review workflow

## Infrastructure Layer

### Purpose
Handles external integrations and implementation details.

### Components

#### Clients
- `SimpleModelClient` - Model API client
- `MultiModelSupport` - Multi-model management

#### Repositories
- `JsonAgentRepository` - JSON-based task storage
- `InMemoryModelRepository` - In-memory model storage

#### Configuration
- `ModelSelector` - YAML-based model selection
- `ExperimentTemplate` - Experiment template loading

## Presentation Layer

### Purpose
Provides user interfaces (API and CLI).

### Components

#### API
- FastAPI endpoints for agent interactions
- RESTful API for workflow management

#### CLI
- Command-line interface for local development
- Interactive mode for testing

## Workers Layer

### Purpose
Background workers for scheduled tasks and notifications.

### Components

#### Summary Worker
Coordinates scheduled notifications for task summaries and channel digests.

**Modular Structure:**
```
src/workers/
├── summary_worker.py    # Main coordinator (258 lines)
├── formatters.py         # Message formatting
├── message_sender.py     # Message sending with retry
└── data_fetchers.py      # Data fetching from MCP/DB
```

**Responsibilities:**
- `summary_worker.py`: Main loop, scheduling, coordination
- `formatters.py`: Format messages (summary, digest, markdown cleanup)
- `message_sender.py`: Send messages with exponential backoff retry
- `data_fetchers.py`: Fetch data from MCP tools or database

**Features:**
- Scheduled morning task summaries
- Scheduled evening channel digests
- Debug mode with configurable intervals
- Quiet hours support
- Graceful shutdown handling

## Design Patterns

### Strategy Pattern
Used in compression algorithms and model selection strategies.

### Factory Pattern
Used for creating agents and orchestrators with different configurations.

### Repository Pattern
Used for data persistence abstraction.

### Observer Pattern
Used for workflow event handling and metrics collection.

## SOLID Principles

### Single Responsibility
Each class has one clear responsibility.

### Open/Closed
Open for extension, closed for modification.

### Liskov Substitution
Subclasses can replace parent classes without breaking functionality.

### Interface Segregation
Small, focused interfaces rather than large monolithic ones.

### Dependency Inversion
High-level modules depend on abstractions, not implementations.

## Architecture Benefits

### Testability
- Each layer can be tested independently
- Dependency injection enables easy mocking
- High test coverage (70%+)

### Maintainability
- Clear separation of concerns
- Easy to understand and modify
- Reduced coupling between components

### Scalability
- Easy to add new agents
- Plug-and-play architecture
- Configuration-driven behavior

### Portability
- Domain layer is framework-agnostic
- Easy to swap infrastructure components
- Platform-independent business logic

## Phase 2 Enhancements

### Multi-Agent Orchestration
- Sequential workflow coordination
- Error handling and recovery
- Statistics tracking

### Parallel Execution
- Concurrent agent execution using asyncio.gather()
- Partial failure handling
- Result aggregation strategies

### Token Management
- Automatic token counting
- Model-specific limit checking
- Auto-compression when limits exceeded

### Configuration-Driven Features
- YAML-based model selection
- Experiment templates
- Flexible configuration management

## Future Enhancements

### Planned Features
- Database persistence layer
- Real-time monitoring and metrics
- Message queue for reliability
- Advanced compression strategies
- Multi-region deployment support

### Performance Optimization
- Caching layer for model responses
- Request batching
- Connection pooling
- Async/await throughout

## References

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Zen of Python](https://www.python.org/dev/peps/pep-0020/)

