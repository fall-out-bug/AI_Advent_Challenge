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

### 4. Start Local Models (Legacy)

Local containers are deprecated; manifests remain in `archive/legacy/local_models/`
for reference only.

```bash
cd archive/legacy/local_models
docker-compose up -d mistral-chat

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

## Epic 21 Transition Guidance

Epic 21 introduces updated quality gates. While Stage 21_02 is in progress, please follow these interim instructions:

- **Docstring template**: Option B (pragmatic) is the required standard. See `docs/specs/epic_21/architect/docstring_faq.md` for complete guidance and examples.
- **Pre-commit hooks**:
  - Fast hooks (`black`, `isort`, `flake8`, `pydocstyle`) run automatically on commit.
  - Heavy hooks (`mypy`, `bandit`, `markdownlint`) run manually or in CI. Before pushing, execute:
    ```bash
    pre-commit run --hook-stage manual --all-files
    ```
  - Full configuration is documented in `docs/specs/epic_21/architect/pre_commit_strategy.md`.
- **Pytest markers**: New markers for Epic 21 reside in `docs/specs/epic_21/architect/pytest_markers.md`. Use them when adding tests to ensure proper tagging.

This placeholder will be replaced with finalized sections once Stage 21_02 lands.

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

## Butler Agent Development Guidelines

This section provides specific guidelines for developing Butler Agent components following Clean Architecture and SOLID principles.

### Architecture Principles

Butler Agent follows **Clean Architecture** with strict layer separation:

```
Presentation → Application → Domain ← Infrastructure
```

**Key Rules:**
- **Domain layer must NEVER import from infrastructure or presentation**
- Use protocols/interfaces for dependencies
- Dependencies point inward toward domain
- Infrastructure implements domain protocols

### Handler Development

**Creating a New Handler:**

1. **Implement Handler Interface:**
```python
from src.domain.agents.handlers.handler import Handler
from src.domain.agents.state_machine import DialogContext

class MyNewHandler(Handler):
    """Handler for specific mode/functionality."""

    def __init__(self, dependency: DependencyProtocol):
        """Initialize handler.

        Args:
            dependency: Dependency implementing protocol (not concrete class)
        """
        self.dependency = dependency

    async def handle(self, context: DialogContext, message: str) -> str:
        """Handle message in given context.

        Args:
            context: Dialog context with state and data
            message: User message text

        Returns:
            Response text to send to user
        """
        # Implementation
        pass
```

2. **Follow Handler Rules:**
   - Handlers are **stateless** - no instance variables for user data
   - Get `user_id` from `context.user_id`, not initialization
   - Use dependency injection, not global access
   - All functions <40 lines
   - Handle errors gracefully with user-friendly messages

3. **Register Handler:**
```python
# In butler_orchestrator.py
def _get_handler_for_mode(self, mode: DialogMode) -> Handler:
    if mode == DialogMode.MY_NEW_MODE:
        return self.my_new_handler
    # ...
```

### Use Case Development

**Creating a New Use Case:**

1. **Location:** `src/application/use_cases/`

2. **Structure:**
```python
from src.application.dtos.butler_use_case_dtos import TaskCreationResult
from src.domain.interfaces.tool_client import ToolClientProtocol

class MyNewUseCase:
    """Use case for specific business operation."""

    def __init__(self, tool_client: ToolClientProtocol):
        """Initialize use case.

        Args:
            tool_client: Tool client protocol (not concrete class)
        """
        self.tool_client = tool_client

    async def execute(self, message: str) -> TaskCreationResult:
        """Execute use case and return typed result."""
        # Implementation
        return TaskCreationResult(created=False, error="Not implemented")
```


3. **Use Case Rules:**
   - **Stateless**: No instance state for business data
   - **Single responsibility**: One use case = one operation
   - **Typed results**: Use Pydantic models, not raw dicts
   - **Error handling**: Return error in result, don't raise
   - **All functions ≤15 lines**

4. **Add Result Type:**
```python
# In result_types.py
class MyNewResult(BaseModel):
    """Result of new use case."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
```

### State Machine Development

**Adding New States:**

1. **Update DialogState Enum:**
```python
# In state_machine.py
class DialogState(Enum):
    # ... existing states
    MY_NEW_STATE = "my_new_state"
```

2. **Add State Transitions:**
   - Document transition rules
   - Update state diagram in documentation
   - Add transition logic in handlers

3. **Context Data:**
   - Use `context.data` dictionary for state-specific data
   - Document required keys in docstrings
   - Clear data on state reset

### Testing Butler Agent Components

#### Unit Test Structure for Handlers

```python
import pytest
from unittest.mock import AsyncMock
from src.domain.agents.handlers.task_handler import TaskHandler
from src.domain.agents.state_machine import DialogContext, DialogState

@pytest.mark.asyncio
async def test_task_handler_creates_task_successfully():
    """Test task handler creates task on valid input."""
    # Arrange
    mock_intent_orch = AsyncMock()
    mock_tool_client = AsyncMock()
    mock_intent_orch.parse_task_intent.return_value = IntentResult(...)
    mock_tool_client.call_tool.return_value = {"id": "123"}

    handler = TaskHandler(mock_intent_orch, mock_tool_client)
    context = DialogContext(
        state=DialogState.IDLE,
        user_id="123",
        session_id="456"
    )

    # Act
    result = await handler.handle(context, "Buy milk")

    # Assert
    assert "created" in result.lower()
    mock_tool_client.call_tool.assert_called_once()
```

#### Integration Test Setup for Orchestrator

```python
import pytest
from src.domain.agents.butler_orchestrator import ButlerOrchestrator
from tests.fixtures.butler_fixtures import butler_orchestrator

@pytest.mark.asyncio
async def test_orchestrator_routes_to_correct_handler(
    butler_orchestrator: ButlerOrchestrator
):
    """Test orchestrator routes messages to correct handler."""
    # Configure mode classifier
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value={"content": "TASK"}
    )

    # Execute
    response = await butler_orchestrator.handle_user_message(
        user_id="123",
        message="Buy milk",
        session_id="456"
    )

    # Verify
    assert response is not None
    # Verify handler was called (check mocks)
```

#### E2E Test Examples for Telegram Bot

```python
import pytest
from aiogram import Bot, Dispatcher
from aiogram.test import MockedClient
from src.presentation.bot.factory import create_butler_orchestrator

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_telegram_bot_task_creation():
    """E2E test for task creation via Telegram."""
    # Arrange
    orchestrator = await create_butler_orchestrator()
    bot = Bot(token="test")
    dp = Dispatcher()

    # Configure orchestrator mocks
    # ...

    # Act
    # Simulate user message
    # ...

    # Assert
    # Verify bot response
    # ...
```

#### Mock Fixtures Usage

```python
# Use existing fixtures from tests/fixtures/butler_fixtures.py
@pytest.mark.asyncio
async def test_with_fixtures(
    butler_orchestrator,
    mock_llm_client_protocol,
    mock_tool_client_protocol,
    sample_task_message
):
    """Test using provided fixtures."""
    # Configure fixtures
    mock_llm_client_protocol.make_request = AsyncMock(
        return_value="TASK"
    )

    # Execute test
    response = await butler_orchestrator.handle_user_message(
        user_id="123",
        message=sample_task_message,
        session_id="456"
    )

    # Verify
    assert response is not None
```

**Available Fixtures:**
- `butler_orchestrator`: Full orchestrator with mocks
- `mock_llm_client_protocol`: Mock LLM client
- `mock_tool_client_protocol`: Mock tool client
- `mock_mongodb`: Mock MongoDB
- `sample_task_message`, `sample_data_message`: Sample messages

### Code Review Checklist for Butler Agent

Before submitting PR for Butler Agent changes:

#### Protocol Compliance
- [ ] Uses `ToolClientProtocol` or `LLMClientProtocol` (not concrete classes)
- [ ] Domain layer has no imports from infrastructure/presentation
- [ ] All dependencies injected via `__init__`

#### Handler Checklist
- [ ] Handler implements `Handler` interface correctly
- [ ] Handler is stateless (no user data in instance vars)
- [ ] Gets `user_id` from `context.user_id`
- [ ] Error handling returns user-friendly messages
- [ ] All functions <40 lines

#### Use Case Checklist
- [ ] Use case is stateless
- [ ] Returns typed result (Pydantic model)
- [ ] Error handling in result, not exceptions
- [ ] All functions ≤15 lines
- [ ] Single responsibility

#### State Machine Checklist
- [ ] New states added to `DialogState` enum
- [ ] State transitions documented
- [ ] Context data keys documented
- [ ] No magic strings for states

#### Testing Checklist
- [ ] Unit tests for new components
- [ ] Integration tests for workflows
- [ ] E2E tests for user journeys (if applicable)
- [ ] Coverage ≥80% for new code
- [ ] Mocks used correctly (protocols, not concrete)

#### Documentation Checklist
- [ ] Docstrings in Google style
- [ ] Architecture diagram updated (if needed)
- [ ] API docs updated (if new modes/endpoints)
- [ ] Examples in docstrings

### Butler Agent Specific Rules

#### Mode Classification Guidelines

When adding new modes:
1. Update `DialogMode` enum in `mode_classifier.py`
2. Update classification prompt in `ModeClassifier.MODE_CLASSIFICATION_PROMPT`
3. Add handler for new mode
4. Register handler in `ButlerOrchestrator._get_handler_for_mode()`
5. Update documentation

#### Context Management Best Practices

```python
# Good: Clear context usage
async def handle(self, context: DialogContext, message: str) -> str:
    # Get user ID from context
    user_id = context.user_id

    # Update context data
    context.update_data("key", "value")

    # Transition state
    context.transition_to(DialogState.NEW_STATE)

    # Get existing data
    existing_value = context.get_data("key", default="default")
```

```python
# Bad: Using instance variables for user data
class BadHandler:
    def __init__(self):
        self.user_data = {}  # ❌ Stateless violation

    async def handle(self, context, message):
        self.user_data[context.user_id] = message  # ❌ Wrong
```

#### MCP Tool Integration Patterns

```python
# Good: Using protocol
from src.domain.interfaces.tool_client import ToolClientProtocol

class MyHandler(Handler):
    def __init__(self, tool_client: ToolClientProtocol):
        self.tool_client = tool_client  # ✅ Protocol, not concrete

    async def handle(self, context, message):
        result = await self.tool_client.call_tool(
            "tool_name",
            {"param": "value"}
        )
```

```python
# Bad: Direct MCP client usage
from src.presentation.mcp.client import MCPClient  # ❌ Domain imports presentation

class BadHandler:
    def __init__(self):
        self.client = MCPClient()  # ❌ Concrete class, not protocol
```

### Testing Patterns

**Handler Testing:**
- Mock all dependencies (LLM, MCP, MongoDB)
- Test happy path and error cases
- Verify context state transitions
- Check user-facing error messages

**Use Case Testing:**
- Test with mock tool client
- Verify result types
- Test error scenarios
- Check clarification flow (if applicable)

**Integration Testing:**
- Use real orchestrator with mocked dependencies
- Test full message flows
- Verify mode transitions
- Test error recovery

**E2E Testing:**
- Use aiogram test client
- Test complete user journeys
- Verify Telegram message format
- Test error scenarios

## Getting Help

- **Documentation**: See [docs/](docs/)
  - [Architecture Documentation](docs/reference/en/ARCHITECTURE.md)
  - [API Documentation](docs/reference/en/API.md)
  - [Deployment Guide](docs/guides/en/DEPLOYMENT.md)
- **Questions**: Open an issue
- **Bugs**: Report in issues
- **Features**: Discuss in issues first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
