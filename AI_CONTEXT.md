# AI Challenge - Project Context for AI Assistants

## Project Overview

**AI Challenge** is a 14-day learning project exploring AI-powered systems with language models and multi-agent architectures. The project demonstrates Clean Architecture principles, Domain-Driven Design, and production-ready patterns for building AI applications.

**Current Status**: Day 14 complete - Multi-Pass Code Review & MCP Homework Review

## Architecture

### Clean Architecture Layers

The project follows strict Clean Architecture with 4 layers:

```
┌─────────────────────────────────────────┐
│  Presentation Layer                     │
│  - Telegram Bot (FSM-based)             │
│  - MCP HTTP Server                      │
│  - FastAPI REST API                     │
│  - CLI interfaces                       │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│  Application Layer                      │
│  - IntentOrchestrator                   │
│  - Use cases                            │
│  - Workflow orchestration               │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│  Domain Layer                           │
│  - Entities (AgentTask, Intent, etc.) │
│  - Value Objects                        │
│  - Business Logic                       │
│  - Interfaces (Protocols)              │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│  Infrastructure Layer                    │
│  - MongoDB repositories                  │
│  - LLM clients (UnifiedModelClient)     │
│  - MCP clients                          │
│  - HW Checker client                    │
└──────────────────────────────────────────┘
```

**Critical Rule**: Dependencies flow inward only. Domain layer has ZERO external dependencies.

## Key Technologies

### Core Stack
- **Python 3.10+** with type hints (100% coverage)
- **Poetry** for dependency management
- **FastAPI** for REST APIs
- **aiogram** for Telegram bot
- **Pyrogram** for Telegram channel access
- **MongoDB** with Motor (async driver)
- **MCP (Model Context Protocol)** for tool integration

### AI/ML Stack
- **Local Models**: Mistral-7B, Qwen-4B, TinyLlama, StarCoder
- **External APIs**: Perplexity, ChadGPT (optional)
- **UnifiedModelClient**: Abstraction over all model providers

### Infrastructure
- **Docker** & **Docker Compose** for deployment
- **Prometheus** & **Grafana** for monitoring
- **pytest** for testing (80%+ coverage required)

## Project Structure

```
AI_Challenge/
├── src/                          # Main source code
│   ├── domain/                  # Business logic (pure Python)
│   │   ├── agents/              # Agent implementations
│   │   │   ├── multi_pass_reviewer.py  # 3-pass code review
│   │   │   ├── butler_orchestrator.py  # Main bot orchestrator
│   │   │   ├── mcp_aware_agent.py      # MCP tool-aware agent
│   │   │   ├── handlers/        # Mode-specific handlers
│   │   │   └── passes/          # Review passes (arch, component, synthesis)
│   │   ├── intent/              # Intent classification
│   │   │   ├── hybrid_classifier.py    # Rule-based + LLM
│   │   │   ├── rule_based_classifier.py
│   │   │   └── llm_classifier.py
│   │   ├── entities/            # Domain entities
│   │   ├── value_objects/      # Immutable value objects
│   │   └── interfaces/         # Protocol definitions
│   ├── application/             # Use cases & orchestration
│   │   ├── orchestration/       # Intent orchestration
│   │   └── usecases/           # Specific use cases
│   ├── infrastructure/          # External integrations
│   │   ├── hw_checker/          # HW Checker API client
│   │   ├── linters/             # Code quality checkers
│   │   ├── reporting/           # Report generators
│   │   ├── repositories/        # MongoDB repositories
│   │   └── clients/             # External API clients
│   └── presentation/            # Interfaces
│       ├── bot/                  # Telegram bot
│       ├── mcp/                  # MCP server & tools
│       └── api/                  # FastAPI REST API
├── shared/                       # Shared SDK package
│   └── shared_package/
│       ├── clients/             # UnifiedModelClient
│       └── config/               # API key management
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/             # Integration tests
│   └── e2e/                      # End-to-end tests
├── config/                       # Configuration files
│   ├── models.yml                # Model configurations
│   └── agent_configs.yaml       # Agent settings
├── docs/                         # Documentation
└── tasks/                        # Daily challenge tasks
```

## Core Patterns

### 1. Multi-Pass Code Review

Three-pass architecture for comprehensive code analysis:

**Pass 1: Architecture Overview**
- Detects project structure
- Identifies components (Airflow, Spark, MLflow, Docker)
- High-level assessment

**Pass 2: Component Deep-Dive**
- Per-component analysis
- Technology-specific checks
- Detailed findings

**Pass 3: Synthesis**
- Integration analysis
- Overall assessment
- Recommendations

**Implementation**: `src/domain/agents/multi_pass_reviewer.py`

### 2. Hybrid Intent Classification

Two-layer approach for fast, accurate intent recognition:

**Layer 1: Rule-Based (Synchronous)**
- Fast pattern matching (<100ms)
- High-confidence results (threshold: 0.7)
- No LLM calls needed

**Layer 2: LLM Fallback (Async)**
- Cached results (5-minute TTL)
- Low-confidence fallback
- Entity extraction

**Implementation**: `src/domain/intent/hybrid_classifier.py`

### 3. Butler Agent FSM

Finite State Machine for Telegram bot dialog management:

**States**:
- `IDLE` - General conversation
- `TASK` - Task creation/management
- `DATA` - Data collection (digests, stats)
- `REMINDERS` - Reminder management
- `HOMEWORK_REVIEW` - Homework review

**Transitions**: Based on mode classification from `ModeClassifier`

**Implementation**: `src/domain/agents/state_machine.py`

### 4. MCP-Aware Agent

Agent that automatically discovers and uses MCP tools:

**Flow**:
1. Discover tools via `MCPToolsRegistry`
2. LLM decides which tool to use
3. Execute tool via `MCPClient`
4. Format result for user

**Implementation**: `src/domain/agents/mcp_aware_agent.py`

## Key Abstractions

### UnifiedModelClient

Single interface for all LLM providers:

```python
from shared_package.clients.unified_client import UnifiedModelClient

client = UnifiedModelClient()
response = await client.chat(
    model="mistral",
    messages=[{"role": "user", "content": "Hello"}]
)
```

**Supported Providers**:
- Local models (Mistral, Qwen, TinyLlama, StarCoder)
- External APIs (Perplexity, ChadGPT)

### ToolClientProtocol

Abstraction for MCP tool execution:

```python
from src.domain.interfaces.tool_client import ToolClientProtocol

result = await tool_client.call_tool("create_task", {"title": "Task"})
```

### LLMClientProtocol

Abstraction for LLM requests:

```python
from src.domain.interfaces.llm_client import LLMClientProtocol

response = await llm_client.make_request(
    model_name="mistral",
    prompt="Hello",
    max_tokens=256
)
```

## Common Workflows

### Homework Review Workflow

1. User sends: `"Сделай ревью abc123"`
2. `HomeworkHandler` parses commit hash
3. Downloads archive via `HWCheckerClient`
4. Extracts archive to temp directory
5. Calls `MultiPassReviewerAgent.process_multi_pass()`
6. Generates markdown report via `generate_detailed_markdown_report()`
7. Returns report as file to user

**Files**: 
- `src/domain/agents/handlers/homework_handler.py`
- `src/domain/agents/multi_pass_reviewer.py`
- `src/infrastructure/reporting/homework_report_generator.py`

### Task Creation Workflow

1. User sends: `"Create a task to buy milk"`
2. `ButlerOrchestrator` routes to `TaskHandler`
3. `IntentOrchestrator` parses task intent
4. `TaskHandler` calls MCP tool `create_task`
5. Task saved to MongoDB
6. Response sent to user

**Files**:
- `src/domain/agents/butler_orchestrator.py`
- `src/domain/agents/handlers/task_handler.py`
- `src/application/orchestration/intent_orchestrator.py`

### PDF Digest Generation Workflow

1. `PostFetcherWorker` collects posts hourly from Telegram channels
2. Posts stored in MongoDB with 7-day TTL
3. User requests digest via Telegram bot
4. `DataHandler` calls MCP tool `generate_pdf_digest`
5. PDF generated with WeasyPrint
6. Cached for 1 hour, then regenerated
7. PDF sent to user

**Files**:
- `src/workers/post_fetcher_worker.py`
- `src/domain/agents/handlers/data_handler.py`
- `src/presentation/mcp/tools/pdf_digest_tools.py`

## Testing Patterns

### Unit Tests

Test individual components in isolation:

```python
@pytest.mark.asyncio
async def test_task_handler():
    """Test task handler functionality."""
    # Arrange
    handler = TaskHandler(...)
    
    # Act
    result = await handler.handle(context, "Create task")
    
    # Assert
    assert "Task created" in result
```

**Location**: `tests/unit/`

### Integration Tests

Test component interactions:

```python
@pytest.mark.asyncio
async def test_homework_review_flow():
    """Test complete homework review flow."""
    # Test real MCP tool calls, database operations
```

**Location**: `tests/integration/`

### E2E Tests

Test complete user workflows:

```python
@pytest.mark.e2e
async def test_telegram_bot_homework_review():
    """Test homework review via Telegram bot."""
    # Test real Telegram bot interaction
```

**Location**: `tests/e2e/`

## Configuration

### Environment Variables

Key environment variables (see `.env.example`):

```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_SESSION_STRING=your_session_string

# MongoDB
MONGODB_URL=mongodb://localhost:27017
DB_NAME=butler

# LLM
MISTRAL_URL=http://localhost:8001
MCP_SERVER_URL=http://localhost:8004

# API Keys (optional)
PERPLEXITY_API_KEY=pplx-...
CHADGPT_API_KEY=chad-...
```

### Model Configuration

Models configured in `config/models.yml`:

```yaml
models:
  mistral:
    type: local
    port: 8001
    url: http://localhost:8001
```

## Docker Architecture

### Current Compose Files

- `docker-compose.yml` - Main/default services
- `docker-compose.day11.yml` - Butler Bot (Day 11)
- `docker-compose.day12.yml` - Post Fetcher & PDF (Day 12)
- `docker-compose.mcp-demo.yml` - MCP demo services

### Services

- **butler-bot**: Telegram bot with FSM
- **mcp-server**: MCP HTTP server
- **mistral-chat**: Local Mistral LLM
- **mongodb**: Database
- **post-fetcher-worker**: Hourly post collection
- **summary-worker**: Digest generation worker
- **prometheus**: Metrics collection
- **grafana**: Visualization

## Development Workflow

### Local Development

```bash
# Install dependencies
poetry install

# Run tests
make test

# Format code
make format

# Lint code
make lint

# Start services
make day-12-up
```

### Hot Reload

Development mode with hot reload:
- `docker-compose.day12.yml` includes volume mounts for source code
- Uvicorn `--reload` for MCP server
- Watchdog for bot auto-restart

### Adding New Features

1. **Start with Domain**: Define entities and value objects
2. **Add Application**: Create use cases and orchestrators
3. **Implement Infrastructure**: Add repositories and clients
4. **Add Presentation**: Create API endpoints or bot handlers
5. **Write Tests**: Unit → Integration → E2E
6. **Update Documentation**: README.md and docstrings

## Code Quality Standards

### Required

- ✅ Type hints on all functions (100%)
- ✅ Docstrings on all public functions/classes
- ✅ Functions max 15 lines (where possible)
- ✅ One responsibility per function
- ✅ 80%+ test coverage
- ✅ No magic numbers
- ✅ No hardcoded secrets

### Docstring Format

```python
def function_name(param: type) -> return_type:
    """Brief description.

    Purpose:
        Detailed explanation.

    Args:
        param: Parameter description.

    Returns:
        Return value description.

    Raises:
        ExceptionType: When raised.

    Example:
        >>> result = function_name("example")
        >>> result
        'expected'
    """
```

## Common Pitfalls

### ❌ Layer Violations

**Wrong**:
```python
# In domain layer
from src.infrastructure.database.mongo import get_db  # ❌
```

**Correct**:
```python
# In domain layer
from src.domain.interfaces.repository import Repository  # ✅ Protocol
```

### ❌ Missing Type Hints

**Wrong**:
```python
def process(data):  # ❌
    return data
```

**Correct**:
```python
def process(data: Dict[str, Any]) -> Dict[str, Any]:  # ✅
    return data
```

### ❌ Long Functions

**Wrong**:
```python
def handle_request():  # 50 lines ❌
    # ... many responsibilities
```

**Correct**:
```python
def handle_request():  # ✅
    intent = _parse_intent()
    result = _process_intent(intent)
    return _format_response(result)
```

## Useful Commands

```bash
# Testing
make test              # All tests
make test-unit         # Unit tests only
make test-integration  # Integration tests
make coverage          # With coverage report

# Code Quality
make lint              # Run linters
make format            # Format with Black

# Docker
make day-12-up         # Start Day 12 services
make day-12-down       # Stop services
make day-12-logs       # View logs

# MCP
make mcp-server-start  # Start MCP server
make mcp-demo          # Run MCP demo
```

## Key Files Reference

### Domain
- `src/domain/agents/multi_pass_reviewer.py` - Multi-pass code review
- `src/domain/agents/butler_orchestrator.py` - Main orchestrator
- `src/domain/intent/hybrid_classifier.py` - Intent classification
- `src/domain/agents/state_machine.py` - FSM implementation

### Infrastructure
- `src/infrastructure/hw_checker/client.py` - HW Checker API
- `src/infrastructure/reporting/homework_report_generator.py` - Report generation
- `src/infrastructure/linters/code_quality_checker.py` - Code quality

### Presentation
- `src/presentation/bot/butler_bot.py` - Telegram bot
- `src/presentation/mcp/server.py` - MCP HTTP server
- `src/presentation/mcp/tools/homework_review_tool.py` - Review tool

### Shared
- `shared/shared_package/clients/unified_client.py` - Unified LLM client

## When Working on This Codebase

1. **Always read existing code first** - Follow established patterns
2. **Respect layer boundaries** - Never import outward
3. **Write tests first** - TDD approach
4. **Update documentation** - README.md for API changes
5. **Check linting** - Run `make lint` before committing
6. **Keep functions small** - Max 15 lines where possible
7. **Use type hints** - 100% coverage required
8. **Add docstrings** - All public functions/classes

## Questions?

- See `docs/ARCHITECTURE.md` for detailed architecture
- See `docs/DEVELOPMENT.md` for setup instructions
- See `.cursorrules` for coding standards
- See `README.md` for project overview

