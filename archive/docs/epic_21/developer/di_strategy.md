# Epic 21 · Dependency Injection Strategy

**Decision**: Manual DI with lightweight container pattern

**Rationale**: Simple, explicit, testable - matches project size and complexity

---

## Strategy Overview

### Chosen Approach: Manual DI
- **Why**: Explicit control, easy debugging, no magic
- **Why not dependency-injector**: Overkill for current project size
- **Why not manual factories everywhere**: Too verbose, hard to test

### Container Pattern
- **Lightweight container class** with `@cached_property`
- **Feature flags** control implementation selection
- **Test doubles** override via container injection

---

## Container Implementation

### Core Container Class

```python
# src/infrastructure/di/container.py
from functools import cached_property
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings with feature flags."""
    # Database
    mongodb_url: str

    # External services
    hw_checker_base_url: str
    hw_checker_api_key: str

    # Feature flags (Epic 21)
    use_new_dialog_context_repo: bool = False
    use_new_homework_review_service: bool = False
    use_new_storage_adapter: bool = False
    use_decomposed_use_case: bool = False

    class Config:
        env_file = ".env.infra"


class DIContainer:
    """Dependency injection container.

    Purpose:
        Centralizes dependency wiring and enables feature flag control.
        Provides lazy initialization of services via cached_property.

    Usage:
        container = DIContainer(settings)
        orchestrator = container.butler_orchestrator
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._instances: dict[str, Any] = {}  # For test overrides

    # --- Infrastructure Layer ---

    @cached_property
    def mongo_client(self):
        """MongoDB client."""
        from infrastructure.database.mongo import MongoClient
        return MongoClient(self.settings.mongodb_url)

    @cached_property
    def http_client(self):
        """Shared HTTP client for external APIs."""
        import httpx
        return httpx.AsyncClient(timeout=30.0)

    # --- Domain Interfaces (Feature Flag Controlled) ---

    @cached_property
    def dialog_context_repo(self):
        """Dialog context repository (domain interface)."""
        if self.settings.use_new_dialog_context_repo:
            return self._create_new_dialog_repo()
        else:
            return self._create_legacy_dialog_adapter()

    def _create_new_dialog_repo(self):
        """Create new MongoDB-based repository."""
        from infrastructure.repositories.mongo_dialog_context_repository import MongoDialogContextRepository
        return MongoDialogContextRepository(self.mongo_client)

    def _create_legacy_dialog_adapter(self):
        """Create legacy adapter for backward compatibility."""
        from infrastructure.adapters.legacy_dialog_context_adapter import LegacyDialogContextAdapter
        return LegacyDialogContextAdapter(self.mongo_client)

    @cached_property
    def homework_review_service(self):
        """Homework review service (domain interface)."""
        if self.settings.use_new_homework_review_service:
            return self._create_new_homework_service()
        else:
            return self._create_legacy_homework_adapter()

    def _create_new_homework_service(self):
        """Create new HTTP-based service."""
        from infrastructure.clients.http_homework_review_service import HttpHomeworkReviewService
        return HttpHomeworkReviewService(
            base_url=self.settings.hw_checker_base_url,
            api_key=self.settings.hw_checker_api_key,
            http_client=self.http_client
        )

    def _create_legacy_homework_adapter(self):
        """Create legacy adapter for backward compatibility."""
        from infrastructure.adapters.legacy_homework_review_adapter import LegacyHomeworkReviewAdapter
        return LegacyHomeworkReviewAdapter(
            base_url=self.settings.hw_checker_base_url,
            api_key=self.settings.hw_checker_api_key
        )

    @cached_property
    def review_archive_storage(self):
        """Review archive storage (domain interface)."""
        if self.settings.use_new_storage_adapter:
            return self._create_new_storage_adapter()
        else:
            return self._create_legacy_storage_adapter()

    def _create_new_storage_adapter(self):
        """Create new secure storage adapter."""
        from infrastructure.storage.local_file_review_archive_storage import LocalFileReviewArchiveStorage
        return LocalFileReviewArchiveStorage(
            base_path="/var/review-archives",
            max_file_size=100 * 1024 * 1024  # 100MB
        )

    def _create_legacy_storage_adapter(self):
        """Create legacy adapter for backward compatibility."""
        from infrastructure.adapters.legacy_review_archive_storage import LegacyReviewArchiveStorage
        return LegacyReviewArchiveStorage(temp_dir="/tmp")

    # --- Application Layer ---

    @cached_property
    def butler_orchestrator(self):
        """Butler orchestrator (application service)."""
        from domain.agents.butler_orchestrator import ButlerOrchestrator
        from domain.agents.intent_processor import IntentProcessor
        from domain.agents.response_generator import ResponseGenerator

        return ButlerOrchestrator(
            session_manager=self.session_manager,
            dialog_context_repo=self.dialog_context_repo,  # ← Injected interface
            intent_processor=self.intent_processor,
            response_generator=self.response_generator
        )

    @cached_property
    def homework_handler(self):
        """Homework handler (presentation service)."""
        from presentation.bot.handlers.homework import HomeworkHandler

        return HomeworkHandler(
            bot=self.telegram_bot,
            homework_service=self.homework_review_service  # ← Injected interface
        )

    @cached_property
    def review_submission_use_case(self):
        """Review submission use case (application service)."""
        from application.use_cases.review_submission_use_case import ReviewSubmissionUseCase

        if self.settings.use_decomposed_use_case:
            return self._create_decomposed_use_case()
        else:
            return self._create_legacy_use_case()

    def _create_decomposed_use_case(self):
        """Create use case with focused collaborators."""
        from application.use_cases.review_submission_use_case import ReviewSubmissionUseCase
        return ReviewSubmissionUseCase(
            storage=self.review_archive_storage,
            rate_limiter=self.review_rate_limiter,
            log_analyzer=self.log_analyzer,
            publisher=self.review_publisher
        )

    def _create_legacy_use_case(self):
        """Create legacy monolithic use case."""
        from application.use_cases.legacy_review_submission_use_case import LegacyReviewSubmissionUseCase
        return LegacyReviewSubmissionUseCase(
            storage_adapter=self.review_archive_storage
        )

    # --- Supporting Services ---

    @cached_property
    def session_manager(self):
        """Session manager."""
        from domain.agents.session_manager import SessionManager
        return SessionManager()

    @cached_property
    def intent_processor(self):
        """Intent processor."""
        from domain.agents.intent_processor import IntentProcessor
        return IntentProcessor()

    @cached_property
    def response_generator(self):
        """Response generator."""
        from domain.agents.response_generator import ResponseGenerator
        return ResponseGenerator()

    @cached_property
    def telegram_bot(self):
        """Telegram bot instance."""
        # Would be initialized with bot token, etc.
        return None  # Placeholder

    @cached_property
    def review_rate_limiter(self):
        """Review rate limiter."""
        from application.services.review_rate_limiter import ReviewRateLimiter
        return ReviewRateLimiter()

    @cached_property
    def log_analyzer(self):
        """Log analyzer."""
        from application.services.log_analyzer import LogAnalyzer
        return LogAnalyzer()

    @cached_property
    def review_publisher(self):
        """Review publisher."""
        from application.services.review_publisher import ReviewPublisher
        return ReviewPublisher()

    # --- Test Support ---

    def override_for_testing(self, **overrides):
        """Override services for testing.

        Usage:
            container = DIContainer(settings)
            container.override_for_testing(
                dialog_context_repo=mock_repo,
                homework_service=fake_service
            )
        """
        self._instances.update(overrides)

    def get_for_testing(self, service_name: str):
        """Get service instance (with test overrides)."""
        if service_name in self._instances:
            return self._instances[service_name]

        # Fall back to cached property
        return getattr(self, service_name)
```

### Presentation Layer Wiring

#### FastAPI Dependency Injection

```python
# src/presentation/api/dependencies.py
from infrastructure.di.container import DIContainer, Settings

# Global container instance
_container: DIContainer | None = None

def get_container() -> DIContainer:
    """Get the global DI container."""
    if _container is None:
        raise RuntimeError("DI container not initialized")
    return _container

def init_container(settings: Settings) -> DIContainer:
    """Initialize global DI container."""
    global _container
    _container = DIContainer(settings)
    return _container

# Dependency functions for FastAPI
def get_butler_orchestrator():
    """FastAPI dependency for butler orchestrator."""
    return get_container().butler_orchestrator

def get_review_submission_use_case():
    """FastAPI dependency for review use case."""
    return get_container().review_submission_use_case
```

```python
# src/presentation/api/review_routes.py
from presentation.api.dependencies import get_review_submission_use_case
from domain.interfaces.review_archive_storage import ReviewArchiveStorage

@router.post("/reviews")
async def submit_review(
    request: ReviewSubmissionRequest,
    use_case = Depends(get_review_submission_use_case),  # ← Injected via DI
    storage: ReviewArchiveStorage = Depends(lambda: get_container().review_archive_storage)
):
    """Submit code review request.

    Purpose:
        Accept review submission, store archive securely,
        and queue processing in background.
    """
    # Use injected services
    result = await use_case.submit_review(
        student_id=request.student_id,
        assignment_id=request.assignment_id,
        archive_url=request.archive_url,
        storage=storage  # ← Pass storage interface
    )

    return result
```

#### Telegram Bot Wiring

```python
# src/presentation/bot/butler_bot.py
from infrastructure.di.container import DIContainer

class ButlerBot:
    """Telegram bot with dependency injection."""

    def __init__(self, container: DIContainer):
        self.container = container
        self.homework_handler = container.homework_handler  # ← Injected

    async def handle_homework_command(self, message):
        """Handle /homework command."""
        await self.homework_handler.handle_list_homeworks(message)  # ← Uses injected service
```

### Test Wiring

#### Unit Test Fixtures

```python
# tests/conftest.py
import pytest
from infrastructure.di.container import DIContainer, Settings
from unittest.mock import AsyncMock

@pytest.fixture
def test_settings():
    """Test settings."""
    return Settings(
        mongodb_url="mongodb://test",
        hw_checker_base_url="https://test.hw",
        hw_checker_api_key="test_key",
        use_new_dialog_context_repo=True,
        use_new_homework_review_service=True,
        use_new_storage_adapter=True,
        use_decomposed_use_case=True
    )

@pytest.fixture
def test_container(test_settings):
    """DI container with test settings."""
    return DIContainer(test_settings)

@pytest.fixture
def mock_dialog_repo():
    """Mock dialog context repository."""
    return AsyncMock()

@pytest.fixture
def mock_homework_service():
    """Mock homework review service."""
    return AsyncMock()

@pytest.fixture
def mock_storage():
    """Mock review archive storage."""
    return AsyncMock()

@pytest.fixture
def container_with_mocks(test_container, mock_dialog_repo, mock_homework_service, mock_storage):
    """DI container with all services mocked."""
    test_container.override_for_testing(
        dialog_context_repo=mock_dialog_repo,
        homework_review_service=mock_homework_service,
        review_archive_storage=mock_storage
    )
    return test_container
```

#### Unit Test Example

```python
# tests/unit/domain/test_butler_orchestrator.py
import pytest
from domain.agents.butler_orchestrator import ButlerOrchestrator

@pytest.mark.asyncio
async def test_butler_saves_context(container_with_mocks, mock_dialog_repo):
    """Unit: ButlerOrchestrator saves context via repository interface."""

    # Arrange
    orchestrator = container_with_mocks.butler_orchestrator  # ← Uses mocked container

    # Act
    await orchestrator.handle_message("alice", "Hello world")

    # Assert
    mock_dialog_repo.save.assert_called_once()
    saved_context = mock_dialog_repo.save.call_args[0][0]
    assert saved_context.user_id == "alice"
    assert "Hello world" in saved_context.messages
```

#### Integration Test Example

```python
# tests/integration/test_butler_workflow.py
@pytest.mark.asyncio
async def test_full_butler_workflow(container_with_mocks, mock_dialog_repo, mock_homework_service):
    """Integration: Full butler workflow with DI."""

    # Arrange
    bot = ButlerBot(container_with_mocks)
    mock_message = MockMessage(chat_id=123, text="/homework")

    # Mock external dependencies
    mock_homework_service.list_recent_homeworks.return_value = [
        HomeworkStatus(commit="abc123", student="alice", status="pending")
    ]

    # Act
    await bot.handle_homework_command(mock_message)

    # Assert
    mock_homework_service.list_recent_homeworks.assert_called_once()
    # Verify bot sent correct message
    bot.bot.send_message.assert_called_once()
```

---

## Migration Strategy

### Phase 1: Container Setup (No Behavior Changes)

1. **Create container class** with all current dependencies
2. **Add feature flags** (all `false` initially)
3. **Wire existing code** to use container (no interface changes yet)
4. **Verify all tests pass**

### Phase 2: Interface Introduction (Stage 21_01)

1. **Add interfaces** to domain layer
2. **Implement adapters** in infrastructure
3. **Update container** with feature flag logic
4. **Gradually enable** flags in staging

### Phase 3: Legacy Cleanup (Post-Epic 21)

1. **Remove legacy adapters** after full rollout
2. **Simplify container** (remove feature flags)
3. **Clean up** deprecated code paths

---

## Benefits of This Approach

### ✅ Advantages
- **Explicit**: Clear where dependencies come from
- **Testable**: Easy to mock any service via `override_for_testing`
- **Flexible**: Feature flags enable gradual rollout
- **Maintainable**: Single place to see all dependencies
- **Type Safe**: Full type hints and validation

### ⚠️ Trade-offs
- **Manual**: No auto-wiring magic
- **Verbose**: More code than library solutions
- **Discipline**: Team must use container consistently

### 📊 Comparison with Alternatives

| Approach | Pros | Cons | Suitability |
|----------|------|------|-------------|
| **Manual DI (Chosen)** | Explicit, testable, no magic | Verbose, manual | ✅ Best for this project |
| **dependency-injector** | Powerful, auto-wiring | Complex, steep learning curve | ❌ Overkill |
| **Factory Functions** | Simple, no container | Hard to test, scattered | ❌ Not scalable |
| **Service Locator** | Simple | Hidden dependencies, hard to test | ❌ Anti-pattern |

---

## Implementation Checklist

- [ ] Create `DIContainer` class with all services
- [ ] Add feature flags to settings
- [ ] Create legacy adapters for backward compatibility
- [ ] Update FastAPI dependencies to use container
- [ ] Update bot initialization to use container
- [ ] Add test fixtures with mocked container
- [ ] Create migration scripts for gradual rollout
- [ ] Update documentation with wiring examples
- [ ] Add container health checks and validation</contents>

