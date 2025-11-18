# Stage TL-05: Telegram Bot Integration

**Epic**: EP25 - Personalised Butler
**Stage**: TL-05
**Duration**: 2 days
**Owner**: Dev C
**Dependencies**: TL-04
**Status**: Pending

---

## Goal

Integrate PersonalizedReplyUseCase into Telegram bot handlers (text and voice messages) with feature flag control.

---

## Objectives

1. Update text message handler to route through PersonalizedReplyUseCase
2. Update voice handler to route STT output through PersonalizedReplyUseCase
3. Create factory for dependency injection
4. Add feature flag PERSONALIZATION_ENABLED (default: false)
5. Update bot initialization
6. Write integration tests

---

## File Structure

```
src/infrastructure/personalization/
└── factory.py                # DI factory

src/infrastructure/config/
└── settings.py               # Add PERSONALIZATION_ENABLED

src/presentation/bot/handlers/
├── butler_handler.py         # Updated for personalization
└── voice_handler.py          # Updated for personalization

src/presentation/bot/
└── butler_bot.py             # Update initialization

tests/integration/bot/
├── test_personalized_text_handler.py
└── test_personalized_voice_handler.py
```

---

## Implementation Details

### 1. Feature Flag Configuration

**File**: `src/infrastructure/config/settings.py`

**Add**:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Personalization settings
    personalization_enabled: bool = Field(
        default=False,  # Opt-in for gradual rollout
        description="Enable personalized replies with Alfred persona"
    )
```

---

### 2. Dependency Injection Factory

**File**: `src/infrastructure/personalization/factory.py`

**Requirements**:
- Create all dependencies (repos, service, use cases)
- Return use cases for bot integration
- Handle errors gracefully

**Implementation**:

```python
"""Factory for creating personalization use cases."""

from typing import Tuple

from motor.motor_asyncio import AsyncIOMotorClient

from src.application.personalization.personalization_service import (
    PersonalizationServiceImpl
)
from src.application/personalization.use_cases.personalized_reply import (
    PersonalizedReplyUseCase
)
from src.application.personalization.use_cases.reset_personalization import (
    ResetPersonalizationUseCase
)
from src.infrastructure.config.settings import Settings
from src.infrastructure.personalization.memory_repository import (
    MongoUserMemoryRepository
)
from src.infrastructure.personalization.profile_repository import (
    MongoUserProfileRepository
)
from src.infrastructure.logging import get_logger

logger = get_logger("personalization_factory")


def create_personalized_use_cases(
    settings: Settings,
    mongo_client: AsyncIOMotorClient,
    llm_client: "LLMClient",
) -> Tuple[PersonalizedReplyUseCase, ResetPersonalizationUseCase]:
    """Create personalization use cases with dependencies.

    Purpose:
        Factory function for dependency injection.
        Creates all required repositories, services, and use cases.

    Args:
        settings: Application settings.
        mongo_client: MongoDB async client.
        llm_client: LLM client for generation.

    Returns:
        Tuple of (PersonalizedReplyUseCase, ResetPersonalizationUseCase).

    Example:
        >>> from motor.motor_asyncio import AsyncIOMotorClient
        >>> client = AsyncIOMotorClient("mongodb://localhost")
        >>> reply_uc, reset_uc = create_personalized_use_cases(
        ...     settings, client, llm_client
        ... )

    Raises:
        Exception: If initialization fails.
    """
    try:
        logger.info("Creating personalization use cases...")

        # Create repositories
        profile_repo = MongoUserProfileRepository(
            mongo_client, settings.db_name
        )
        memory_repo = MongoUserMemoryRepository(
            mongo_client, settings.db_name
        )

        logger.info("Repositories created")

        # Create service
        personalization_service = PersonalizationServiceImpl(profile_repo)

        logger.info("PersonalizationService created")

        # Create use cases
        personalized_reply_use_case = PersonalizedReplyUseCase(
            personalization_service=personalization_service,
            memory_repo=memory_repo,
            profile_repo=profile_repo,
            llm_client=llm_client,
        )

        reset_use_case = ResetPersonalizationUseCase(
            profile_repo=profile_repo,
            memory_repo=memory_repo,
        )

        logger.info("Personalization use cases created successfully")

        return personalized_reply_use_case, reset_use_case

    except Exception as e:
        logger.error(
            "Failed to create personalization use cases",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise
```

---

### 3. Updated Butler Handler

**File**: `src/presentation/bot/handlers/butler_handler.py`

**Changes**:
- Add feature flag check
- Route through PersonalizedReplyUseCase if enabled
- Fallback to ButlerOrchestrator if disabled

**Implementation**:

```python
# ... existing imports ...
from src.infrastructure.config.settings import get_settings

# Add global use case instance
_personalized_reply_use_case: Optional["PersonalizedReplyUseCase"] = None

def setup_butler_handler(
    orchestrator: ButlerOrchestrator,
    personalized_reply_use_case: Optional["PersonalizedReplyUseCase"] = None,
) -> Router:
    """Setup butler handler with orchestrator dependency.

    Args:
        orchestrator: ButlerOrchestrator instance for message processing.
        personalized_reply_use_case: Optional personalized reply use case.

    Returns:
        Configured aiogram Router.
    """
    global _orchestrator, _personalized_reply_use_case
    _orchestrator = orchestrator
    _personalized_reply_use_case = personalized_reply_use_case

    router = Router()
    router.message.register(handle_any_message, F.text)
    return router


async def handle_any_message(message: Message, state: FSMContext | None = None) -> None:
    """Handle any text message using ButlerOrchestrator or PersonalizedReplyUseCase.

    Purpose:
        Main entry point for processing user messages.
        Routes through personalization if enabled, otherwise uses Butler.

    Args:
        message: Telegram message object.
        state: Optional FSM context for state management.
    """
    if not message.text or not message.from_user:
        logger.warning("Received message without text or user")
        return

    if _orchestrator is None:
        logger.error("ButlerOrchestrator not initialized")
        await _handle_error(message, RuntimeError("Orchestrator not initialized"))
        return

    user_id = str(message.from_user.id)
    text = message.text
    settings = get_settings()

    # Check if personalization is enabled and use case is available
    if settings.personalization_enabled and _personalized_reply_use_case is not None:
        logger.info(
            "Routing through personalized reply",
            extra={"user_id": user_id, "text_preview": text[:50]}
        )

        try:
            from src.application.personalization.dtos import PersonalizedReplyInput

            input_data = PersonalizedReplyInput(
                user_id=user_id,
                text=text,
                source="text"
            )

            output = await _personalized_reply_use_case.execute(input_data)

            await message.answer(output.reply)

            logger.info(
                "Personalized reply sent",
                extra={
                    "user_id": user_id,
                    "used_persona": output.used_persona,
                    "memory_events_used": output.memory_events_used,
                    "compressed": output.compressed,
                }
            )
            return

        except Exception as e:
            logger.error(
                "Personalized reply failed, falling back to Butler",
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True,
            )
            # Fall through to Butler fallback

    # Fallback to Butler orchestrator
    session_id = f"telegram_{user_id}_{message.message_id}"

    # ... rest of existing Butler handler logic ...
```

---

### 4. Updated Voice Handler

**File**: `src/presentation/bot/handlers/voice_handler.py`

**Changes**:
- After STT transcription, route through PersonalizedReplyUseCase
- Keep feature flag check
- Send transcription + personalized reply

**Implementation**:

```python
# ... existing imports ...
from src.infrastructure.config.settings import get_settings

# Add global use case
_personalized_reply_use_case: Optional["PersonalizedReplyUseCase"] = None

def setup_voice_handler(
    process_voice_command_use_case: ProcessVoiceCommandUseCase,
    personalized_reply_use_case: Optional["PersonalizedReplyUseCase"] = None,
) -> Router:
    """Setup voice handler with use case dependencies.

    Args:
        process_voice_command_use_case: Use case for voice processing.
        personalized_reply_use_case: Optional personalized reply use case.

    Returns:
        Configured aiogram Router.
    """
    global _process_voice_command_use_case, _personalized_reply_use_case
    _process_voice_command_use_case = process_voice_command_use_case
    _personalized_reply_use_case = personalized_reply_use_case

    router = Router()
    router.message.register(handle_voice_message, F.content_type.in_({"voice", "audio"}))
    return router


async def handle_voice_message(message: Message) -> None:
    """Handle voice/audio messages with STT and personalization.

    Purpose:
        Process voice messages through:
        1. STT (Whisper) for transcription
        2. PersonalizedReplyUseCase for reply (if enabled)
        3. Send transcription + reply to user
    """
    # ... existing STT logic ...

    # After transcription:
    user_id = str(message.from_user.id)
    settings = get_settings()

    if settings.personalization_enabled and _personalized_reply_use_case is not None:
        logger.info(
            "Routing voice transcription through personalized reply",
            extra={"user_id": user_id, "transcription": transcription.text[:50]}
        )

        try:
            from src.application.personalization.dtos import PersonalizedReplyInput

            input_data = PersonalizedReplyInput(
                user_id=user_id,
                text=transcription.text,
                source="voice"
            )

            output = await _personalized_reply_use_case.execute(input_data)

            # Send transcription + personalized reply
            await message.answer(
                f"🎤 Распознала: «{transcription.text[:500]}{'...' if len(transcription.text) > 500 else ''}»\n\n"
                f"{output.reply}"
            )

            logger.info(
                "Voice command processed with personalization",
                extra={
                    "user_id": user_id,
                    "used_persona": output.used_persona,
                }
            )
            return

        except Exception as e:
            logger.error(
                "Personalized voice reply failed",
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True,
            )
            # Fall through to fallback

    # Fallback: send transcription only
    await message.answer(f"🎤 Распознала: «{transcription.text}»")
```

---

### 5. Bot Initialization Update

**File**: `src/presentation/bot/butler_bot.py`

**Changes**:
- Create personalization use cases if enabled
- Pass to handler setup functions

**Implementation**:

```python
class ButlerBot:
    def __init__(
        self,
        token: str,
        orchestrator: ButlerOrchestrator,
        llm_client: "LLMClient",
        mongo_client: AsyncIOMotorClient,
    ) -> None:
        """Initialize Butler bot.

        Args:
            token: Telegram bot token.
            orchestrator: ButlerOrchestrator instance (injected via DI).
            llm_client: LLM client for personalization.
            mongo_client: MongoDB client for personalization.
        """
        self.bot = Bot(token=token)
        self.storage = MemoryStorage()
        self.dp = Dispatcher(storage=self.storage)
        self.router = Router()
        self.orchestrator = orchestrator
        self._setup_handlers(llm_client, mongo_client)
        self.dp.include_router(self.router)

        # ... rest of initialization ...

    def _setup_handlers(
        self,
        llm_client: "LLMClient",
        mongo_client: AsyncIOMotorClient,
    ) -> None:
        """Setup all bot handlers with personalization support."""
        from src.infrastructure.config.settings import get_settings

        settings = get_settings()

        # Create personalization use cases if enabled
        personalized_reply_use_case = None
        if settings.personalization_enabled:
            logger.info("Personalization enabled, creating use cases")
            try:
                from src.infrastructure.personalization.factory import (
                    create_personalized_use_cases
                )

                personalized_reply_use_case, reset_use_case = (
                    create_personalized_use_cases(
                        settings, mongo_client, llm_client
                    )
                )

                logger.info("Personalization use cases created")
            except Exception as e:
                logger.error(
                    "Failed to create personalization use cases",
                    extra={"error": str(e)},
                    exc_info=True,
                )
        else:
            logger.info("Personalization disabled")

        # ... existing command handlers ...

        # Include butler handler with personalization
        butler_router = setup_butler_handler(
            self.orchestrator,
            personalized_reply_use_case=personalized_reply_use_case,
        )
        self.dp.include_router(butler_router)
```

---

## Testing Requirements

### Integration Tests

**File**: `tests/integration/bot/test_personalized_text_handler.py`

```python
"""Integration tests for personalized text handler."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from aiogram import Bot
from aiogram.types import Message, User


@pytest.mark.asyncio
async def test_text_message_with_personalization_enabled(mocker):
    """Test text message routes through personalization when enabled."""
    # Mock settings
    mocker.patch(
        "src.infrastructure.config.settings.get_settings",
        return_value=MagicMock(personalization_enabled=True)
    )

    # Mock use case
    mock_use_case = MagicMock()
    from src.application.personalization.dtos import PersonalizedReplyOutput
    mock_use_case.execute = AsyncMock(
        return_value=PersonalizedReplyOutput(
            reply="Good day, sir",
            used_persona=True,
            memory_events_used=5,
            compressed=False,
        )
    )

    # Setup handler
    from src.presentation.bot.handlers.butler_handler import (
        setup_butler_handler,
        handle_any_message,
    )

    # ... test implementation ...


@pytest.mark.asyncio
async def test_text_message_with_personalization_disabled(mocker):
    """Test text message routes through Butler when personalization disabled."""
    mocker.patch(
        "src.infrastructure.config.settings.get_settings",
        return_value=MagicMock(personalization_enabled=False)
    )

    # ... test implementation ...
```

**File**: `tests/integration/bot/test_personalized_voice_handler.py`

```python
"""Integration tests for personalized voice handler."""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_voice_message_with_personalization_enabled(mocker):
    """Test voice message routes through personalization after STT."""
    # ... test implementation ...


@pytest.mark.asyncio
async def test_voice_message_with_personalization_disabled(mocker):
    """Test voice message sends transcription only when personalization disabled."""
    # ... test implementation ...
```

### Manual Testing

1. **Feature Flag Off** (PERSONALIZATION_ENABLED=false):
   - Send text message → verify Butler response (no persona)
   - Send voice message → verify transcription only

2. **Feature Flag On** (PERSONALIZATION_ENABLED=true):
   - Send text message → verify Alfred-style response
   - Send voice message → verify transcription + Alfred-style response
   - Send 51 messages → verify compression triggered

### Test Execution

```bash
# Integration tests
pytest tests/integration/bot/ -v

# Manual testing
docker compose -f docker-compose.butler.yml up -d butler-bot
# Send messages via Telegram
# Check logs: docker compose -f docker-compose.butler.yml logs -f butler-bot
```

---

## Acceptance Criteria

- [ ] Feature flag PERSONALIZATION_ENABLED added (default: false)
- [ ] Dependency injection factory implemented
- [ ] Text handler routes through PersonalizedReplyUseCase when enabled
- [ ] Voice handler routes through PersonalizedReplyUseCase when enabled
- [ ] Bot initialization updated to create use cases
- [ ] Integration tests for text and voice handlers
- [ ] Graceful fallback when personalization disabled or fails
- [ ] Logging for personalization routing

---

## Dependencies

- **Upstream**: TL-04 (use cases)
- **Downstream**: TL-06 (admin tools), TL-07 (testing & docs)

---

## Deliverables

- [ ] `src/infrastructure/personalization/factory.py`
- [ ] Updated `src/infrastructure/config/settings.py`
- [ ] Updated `src/presentation/bot/handlers/butler_handler.py`
- [ ] Updated `src/presentation/bot/handlers/voice_handler.py`
- [ ] Updated `src/presentation/bot/butler_bot.py`
- [ ] `tests/integration/bot/test_personalized_text_handler.py`
- [ ] `tests/integration/bot/test_personalized_voice_handler.py`

---

## Rollout Plan

1. **Phase 1 (Internal Testing)**:
   - Deploy with PERSONALIZATION_ENABLED=false
   - Enable for specific test users via manual config
   - Monitor logs and metrics

2. **Phase 2 (Beta)**:
   - Enable for beta user group (10-20 users)
   - Collect feedback
   - Iterate on persona if needed

3. **Phase 3 (Full Rollout)**:
   - Enable PERSONALIZATION_ENABLED=true by default
   - Monitor error rates and performance
   - Quick rollback plan if issues arise

---

## Next Steps

After completion:
1. Manual testing with feature flag on/off
2. Code review with Tech Lead
3. Merge to main branch
4. Begin TL-06 (Admin Tools)

---

**Status**: Pending
**Estimated Effort**: 2 days
**Priority**: High
