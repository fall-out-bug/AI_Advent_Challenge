# Stage TL-04: Personalized Reply Use Case

**Epic**: EP25 - Personalised Butler  
**Stage**: TL-04  
**Duration**: 2 days  
**Owner**: Dev A  
**Dependencies**: TL-01, TL-02, TL-03  
**Status**: Pending

---

## Goal

Implement PersonalizedReplyUseCase that orchestrates profile loading, memory management, prompt assembly, and LLM generation.

---

## Objectives

1. Define input/output DTOs
2. Implement PersonalizedReplyUseCase with inline memory compression
3. Implement ResetPersonalizationUseCase
4. Add comprehensive logging and metrics
5. Write unit and integration tests

---

## File Structure

```
src/application/personalization/
├── __init__.py
├── dtos.py                   # DTOs for use cases
└── use_cases/
    ├── __init__.py
    ├── personalized_reply.py  # PersonalizedReplyUseCase
    └── reset_personalization.py # ResetPersonalizationUseCase

tests/unit/application/personalization/use_cases/
├── __init__.py
├── test_personalized_reply.py
└── test_reset_personalization.py

tests/integration/application/personalization/
├── __init__.py
└── test_personalized_reply_flow.py
```

---

## Implementation Details

### 1. DTOs

**File**: `src/application/personalization/dtos.py`

**Requirements**:
- Input/Output DTOs for use cases
- Type hints and validation
- Dataclass frozen for immutability

**Implementation**:

```python
"""DTOs for personalization use cases."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PersonalizedReplyInput:
    """Input DTO for personalized reply use case.
    
    Purpose:
        Encapsulates input data for generating personalized replies.
    
    Attributes:
        user_id: User identifier (Telegram user ID).
        text: User message text to respond to.
        source: Message source ("text" or "voice").
    
    Example:
        >>> input_data = PersonalizedReplyInput(
        ...     user_id="123",
        ...     text="Hello",
        ...     source="text"
        ... )
    """
    
    user_id: str
    text: str
    source: Literal["text", "voice"] = "text"


@dataclass(frozen=True)
class PersonalizedReplyOutput:
    """Output DTO for personalized reply use case.
    
    Purpose:
        Encapsulates result of personalized reply generation.
    
    Attributes:
        reply: Generated reply text from LLM.
        used_persona: Whether personalization was applied.
        memory_events_used: Number of memory events used for context.
        compressed: Whether memory was compressed during this request.
    
    Example:
        >>> output = PersonalizedReplyOutput(
        ...     reply="Good day, sir",
        ...     used_persona=True,
        ...     memory_events_used=10,
        ...     compressed=False
        ... )
    """
    
    reply: str
    used_persona: bool
    memory_events_used: int
    compressed: bool = False


@dataclass(frozen=True)
class ResetPersonalizationInput:
    """Input DTO for reset personalization use case.
    
    Purpose:
        Encapsulates input for resetting user profile and memory.
    
    Attributes:
        user_id: User identifier.
    
    Example:
        >>> input_data = ResetPersonalizationInput(user_id="123")
    """
    
    user_id: str


@dataclass(frozen=True)
class ResetPersonalizationOutput:
    """Output DTO for reset personalization use case.
    
    Purpose:
        Encapsulates result of reset operation.
    
    Attributes:
        success: Whether reset was successful.
        profile_reset: Whether profile was reset.
        memory_deleted_count: Number of memory events deleted.
    
    Example:
        >>> output = ResetPersonalizationOutput(
        ...     success=True,
        ...     profile_reset=True,
        ...     memory_deleted_count=50
        ... )
    """
    
    success: bool
    profile_reset: bool
    memory_deleted_count: int
```

---

### 2. PersonalizedReplyUseCase

**File**: `src/application/personalization/use_cases/personalized_reply.py`

**Requirements**:
- Load profile and memory
- Check memory count and compress if needed
- Build personalized prompt
- Call LLM
- Save interaction to memory
- Comprehensive logging and metrics
- Graceful error handling with fallback

**Implementation**:

```python
"""Personalized reply use case."""

import time
from typing import Protocol

from src.application.personalization.dtos import (
    PersonalizedReplyInput,
    PersonalizedReplyOutput,
)
from src.domain.interfaces.personalization import (
    PersonalizationService,
    UserMemoryRepository,
    UserProfileRepository,
)
from src.domain.personalization.memory_slice import MemorySlice
from src.domain.personalization.user_memory_event import UserMemoryEvent
from src.infrastructure.logging import get_logger
from src.infrastructure.personalization.metrics import (
    user_memory_compression_duration_seconds,
)

logger = get_logger("personalized_reply_use_case")

# Memory cap: compress when exceeds this threshold
MEMORY_CAP = 50
# Keep this many events after compression
KEEP_AFTER_COMPRESSION = 20
# Max events to load for context
MAX_CONTEXT_EVENTS = 20


class LLMClient(Protocol):
    """Protocol for LLM client."""
    
    async def generate(self, prompt: str) -> str:
        """Generate text from prompt."""
        ...


class PersonalizedReplyUseCase:
    """Use case for generating personalized replies.
    
    Purpose:
        Orchestrates profile loading, memory management, prompt assembly,
        and LLM generation for personalized interactions.
    
    Attributes:
        personalization_service: Service for profile and prompt operations.
        memory_repo: Repository for user memory.
        profile_repo: Repository for user profiles.
        llm_client: Client for LLM generation.
    
    Example:
        >>> use_case = PersonalizedReplyUseCase(
        ...     personalization_service,
        ...     memory_repo,
        ...     profile_repo,
        ...     llm_client
        ... )
        >>> input_data = PersonalizedReplyInput(user_id="123", text="Hello")
        >>> output = await use_case.execute(input_data)
    """
    
    def __init__(
        self,
        personalization_service: PersonalizationService,
        memory_repo: UserMemoryRepository,
        profile_repo: UserProfileRepository,
        llm_client: LLMClient,
    ) -> None:
        """Initialize use case with dependencies.
        
        Args:
            personalization_service: Service for personalization operations.
            memory_repo: Repository for user memory.
            profile_repo: Repository for user profiles.
            llm_client: Client for LLM generation.
        """
        self.personalization_service = personalization_service
        self.memory_repo = memory_repo
        self.profile_repo = profile_repo
        self.llm_client = llm_client
        logger.info("PersonalizedReplyUseCase initialized")
    
    async def execute(
        self, input_data: PersonalizedReplyInput
    ) -> PersonalizedReplyOutput:
        """Execute personalized reply generation.
        
        Purpose:
            Main orchestration method that:
            1. Loads profile (auto-create if missing)
            2. Checks memory count and compresses if needed
            3. Loads recent memory
            4. Builds personalized prompt
            5. Calls LLM
            6. Saves interaction to memory
        
        Args:
            input_data: Input DTO with user_id, text, source.
        
        Returns:
            PersonalizedReplyOutput with reply and metadata.
        
        Example:
            >>> input_data = PersonalizedReplyInput("123", "Hello")
            >>> output = await use_case.execute(input_data)
            >>> output.reply
            'Good day, sir. How may I assist you?'
        """
        try:
            start_time = time.time()
            
            # 1. Load profile (auto-create if missing)
            profile = await self.personalization_service.load_profile(
                input_data.user_id
            )
            
            # 2. Check memory count and compress if needed
            event_count = await self.memory_repo.count_events(input_data.user_id)
            compressed = False
            
            if event_count > MEMORY_CAP:
                logger.info(
                    "Memory exceeds cap, triggering compression",
                    extra={
                        "user_id": input_data.user_id,
                        "event_count": event_count,
                        "cap": MEMORY_CAP,
                    }
                )
                await self._compress_memory(input_data.user_id, profile)
                compressed = True
                # Reload profile with updated summary
                profile = await self.profile_repo.get(input_data.user_id)
            
            # 3. Load recent memory
            recent_events = await self.memory_repo.get_recent_events(
                input_data.user_id, limit=MAX_CONTEXT_EVENTS
            )
            
            memory_slice = MemorySlice(
                events=recent_events,
                summary=profile.memory_summary,
                total_events=event_count,
            )
            
            # 4. Build personalized prompt
            prompt = await self.personalization_service.build_personalized_prompt(
                profile=profile,
                memory_slice=memory_slice,
                new_message=input_data.text,
            )
            
            logger.info(
                "Built personalized prompt",
                extra={
                    "user_id": input_data.user_id,
                    "persona": profile.persona,
                    "memory_events_used": len(recent_events),
                    "prompt_tokens": prompt.estimate_tokens(),
                    "source": input_data.source,
                }
            )
            
            # 5. Call LLM
            reply = await self.llm_client.generate(prompt.full_prompt)
            
            # 6. Save interaction to memory
            user_event = UserMemoryEvent.create_user_event(
                input_data.user_id, input_data.text
            )
            assistant_event = UserMemoryEvent.create_assistant_event(
                input_data.user_id, reply
            )
            await self.memory_repo.append_events([user_event, assistant_event])
            
            elapsed = time.time() - start_time
            
            logger.info(
                "Personalized reply generated",
                extra={
                    "user_id": input_data.user_id,
                    "reply_length": len(reply),
                    "source": input_data.source,
                    "compressed": compressed,
                    "elapsed_seconds": round(elapsed, 2),
                }
            )
            
            return PersonalizedReplyOutput(
                reply=reply,
                used_persona=True,
                memory_events_used=len(recent_events),
                compressed=compressed,
            )
            
        except Exception as e:
            logger.error(
                "Failed to generate personalized reply",
                extra={
                    "user_id": input_data.user_id,
                    "error": str(e),
                    "source": input_data.source,
                },
                exc_info=True,
            )
            
            # Graceful fallback
            return PersonalizedReplyOutput(
                reply="Извините, временные технические проблемы. Попробуйте позже.",
                used_persona=False,
                memory_events_used=0,
                compressed=False,
            )
    
    async def _compress_memory(
        self, user_id: str, profile: "UserProfile"
    ) -> None:
        """Compress user memory inline.
        
        Purpose:
            Summarize old events and keep only recent ones.
            Updates profile with summary.
        
        Args:
            user_id: User identifier.
            profile: Current user profile.
        """
        start_time = time.time()
        
        try:
            logger.info(
                "Starting memory compression",
                extra={"user_id": user_id}
            )
            
            # Load all events for summarization
            all_events = await self.memory_repo.get_recent_events(
                user_id, limit=1000
            )
            
            # Build events text for LLM summarization
            events_text = "\n".join([
                f"{e.role}: {e.content[:200]}" for e in all_events
            ])
            
            # Summarize via LLM (simple implementation)
            summary_prompt = (
                f"Summarise the following conversation history in Russian "
                f"(max 300 tokens):\n\n{events_text}"
            )
            summary = await self.llm_client.generate(summary_prompt)
            
            # Compress: keep last N events
            await self.memory_repo.compress(
                user_id, summary, keep_last_n=KEEP_AFTER_COMPRESSION
            )
            
            # Update profile with summary
            updated_profile = profile.with_summary(summary)
            await self.profile_repo.save(updated_profile)
            
            elapsed = time.time() - start_time
            user_memory_compression_duration_seconds.observe(elapsed)
            
            logger.info(
                "Memory compressed successfully",
                extra={
                    "user_id": user_id,
                    "total_events_before": len(all_events),
                    "kept_events": KEEP_AFTER_COMPRESSION,
                    "summary_length": len(summary),
                    "elapsed_seconds": round(elapsed, 2),
                }
            )
            
        except Exception as e:
            logger.error(
                "Memory compression failed",
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True
            )
            # Don't fail the whole request on compression failure
```

**Tests** (`tests/unit/application/personalization/use_cases/test_personalized_reply.py`):

```python
"""Tests for PersonalizedReplyUseCase."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.application.personalization.dtos import PersonalizedReplyInput
from src.application.personalization.use_cases.personalized_reply import (
    PersonalizedReplyUseCase
)
from src.domain.personalization.user_profile import UserProfile
from src.domain.personalization.user_memory_event import UserMemoryEvent


@pytest.fixture
def mock_personalization_service():
    """Mock personalization service."""
    service = MagicMock()
    service.load_profile = AsyncMock()
    service.build_personalized_prompt = AsyncMock()
    return service


@pytest.fixture
def mock_memory_repo():
    """Mock memory repository."""
    repo = MagicMock()
    repo.count_events = AsyncMock(return_value=10)
    repo.get_recent_events = AsyncMock(return_value=[])
    repo.append_events = AsyncMock()
    repo.compress = AsyncMock()
    return repo


@pytest.fixture
def mock_profile_repo():
    """Mock profile repository."""
    repo = MagicMock()
    repo.get = AsyncMock()
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    client = MagicMock()
    client.generate = AsyncMock(return_value="Good day, sir")
    return client


@pytest.fixture
def use_case(
    mock_personalization_service,
    mock_memory_repo,
    mock_profile_repo,
    mock_llm_client
):
    """Create use case instance."""
    return PersonalizedReplyUseCase(
        mock_personalization_service,
        mock_memory_repo,
        mock_profile_repo,
        mock_llm_client,
    )


@pytest.mark.asyncio
async def test_execute_generates_reply(use_case, mock_personalization_service, mock_llm_client):
    """Test successful reply generation."""
    profile = UserProfile.create_default_profile("123")
    mock_personalization_service.load_profile.return_value = profile
    
    from src.domain.personalization.personalized_prompt import PersonalizedPrompt
    prompt = PersonalizedPrompt(
        persona_section="You are Alfred",
        memory_context="",
        new_message="Hello",
        full_prompt="You are Alfred\n\nUser: Hello\nButler:"
    )
    mock_personalization_service.build_personalized_prompt.return_value = prompt
    
    input_data = PersonalizedReplyInput(user_id="123", text="Hello")
    output = await use_case.execute(input_data)
    
    assert output.reply == "Good day, sir"
    assert output.used_persona is True
    mock_llm_client.generate.assert_called_once()


@pytest.mark.asyncio
async def test_execute_compresses_memory_when_exceeds_cap(
    use_case,
    mock_memory_repo,
    mock_profile_repo,
    mock_personalization_service
):
    """Test memory compression when cap exceeded."""
    # Simulate 51 events (exceeds cap of 50)
    mock_memory_repo.count_events.return_value = 51
    mock_memory_repo.get_recent_events.return_value = []
    
    profile = UserProfile.create_default_profile("123")
    mock_personalization_service.load_profile.return_value = profile
    mock_profile_repo.get.return_value = profile
    
    from src.domain.personalization.personalized_prompt import PersonalizedPrompt
    prompt = PersonalizedPrompt("", "", "Hi", "Hi")
    mock_personalization_service.build_personalized_prompt.return_value = prompt
    
    input_data = PersonalizedReplyInput(user_id="123", text="Hi")
    output = await use_case.execute(input_data)
    
    # Verify compression was triggered
    assert output.compressed is True
    mock_memory_repo.compress.assert_called_once()


@pytest.mark.asyncio
async def test_execute_handles_errors_gracefully(
    use_case,
    mock_personalization_service
):
    """Test graceful error handling."""
    # Simulate error
    mock_personalization_service.load_profile.side_effect = Exception("DB error")
    
    input_data = PersonalizedReplyInput(user_id="123", text="Hello")
    output = await use_case.execute(input_data)
    
    # Should return fallback message
    assert "Извините" in output.reply
    assert output.used_persona is False
```

---

### 3. ResetPersonalizationUseCase

**File**: `src/application/personalization/use_cases/reset_personalization.py`

**Requirements**:
- Reset profile to defaults
- Delete all memory events
- Return success status and counts

**Implementation**:

```python
"""Reset personalization use case."""

from src.application.personalization.dtos import (
    ResetPersonalizationInput,
    ResetPersonalizationOutput,
)
from src.domain.interfaces.personalization import (
    UserMemoryRepository,
    UserProfileRepository,
)
from src.infrastructure.logging import get_logger

logger = get_logger("reset_personalization_use_case")


class ResetPersonalizationUseCase:
    """Use case for resetting user personalization.
    
    Purpose:
        Reset user profile to defaults and delete all memory events.
        Used for "start fresh" functionality.
    
    Attributes:
        profile_repo: Repository for user profiles.
        memory_repo: Repository for user memory.
    
    Example:
        >>> use_case = ResetPersonalizationUseCase(profile_repo, memory_repo)
        >>> input_data = ResetPersonalizationInput(user_id="123")
        >>> output = await use_case.execute(input_data)
    """
    
    def __init__(
        self,
        profile_repo: UserProfileRepository,
        memory_repo: UserMemoryRepository,
    ) -> None:
        """Initialize use case with repositories.
        
        Args:
            profile_repo: Repository for user profiles.
            memory_repo: Repository for user memory.
        """
        self.profile_repo = profile_repo
        self.memory_repo = memory_repo
        logger.info("ResetPersonalizationUseCase initialized")
    
    async def execute(
        self, input_data: ResetPersonalizationInput
    ) -> ResetPersonalizationOutput:
        """Execute personalization reset.
        
        Purpose:
            Reset profile and delete memory for user.
        
        Args:
            input_data: Input DTO with user_id.
        
        Returns:
            ResetPersonalizationOutput with success status.
        
        Example:
            >>> input_data = ResetPersonalizationInput(user_id="123")
            >>> output = await use_case.execute(input_data)
            >>> output.success
            True
        """
        try:
            # Count events before deletion
            event_count = await self.memory_repo.count_events(input_data.user_id)
            
            # Reset profile (delete and recreate with defaults)
            await self.profile_repo.reset(input_data.user_id)
            
            # Delete all memory events (via compression with keep_last_n=0)
            await self.memory_repo.compress(
                input_data.user_id, "", keep_last_n=0
            )
            
            logger.info(
                "Personalization reset successfully",
                extra={
                    "user_id": input_data.user_id,
                    "memory_deleted_count": event_count,
                }
            )
            
            return ResetPersonalizationOutput(
                success=True,
                profile_reset=True,
                memory_deleted_count=event_count,
            )
            
        except Exception as e:
            logger.error(
                "Failed to reset personalization",
                extra={"user_id": input_data.user_id, "error": str(e)},
                exc_info=True,
            )
            
            return ResetPersonalizationOutput(
                success=False,
                profile_reset=False,
                memory_deleted_count=0,
            )
```

---

## Testing Requirements

### Unit Tests Coverage

- **PersonalizedReplyUseCase**: ≥80%
  - Successful reply generation
  - Memory compression trigger
  - Error handling with fallback
  - Logging and metrics

- **ResetPersonalizationUseCase**: ≥80%
  - Successful reset
  - Error handling

### Integration Tests

Test full flow with real MongoDB (testcontainers):
- Text message → personalized reply → memory stored
- >50 messages → compression triggered
- Reset → profile/memory cleared

### Test Execution

```bash
# Unit tests
pytest tests/unit/application/personalization/use_cases/ -v

# Integration tests
pytest tests/integration/application/personalization/ -v

# Coverage
pytest tests/unit/application/personalization/ tests/integration/application/personalization/ --cov=src/application/personalization --cov-report=term-missing
```

---

## Acceptance Criteria

- [ ] PersonalizedReplyUseCase implemented with inline compression
- [ ] ResetPersonalizationUseCase implemented
- [ ] DTOs defined with type hints
- [ ] Unit tests with ≥80% coverage
- [ ] Integration tests for full flow
- [ ] Comprehensive logging with structured data
- [ ] Metrics instrumentation
- [ ] Graceful error handling with fallback

---

## Dependencies

- **Upstream**: TL-01 (domain), TL-02 (repos), TL-03 (service)
- **Downstream**: TL-05 (bot integration)

---

## Deliverables

- [ ] `src/application/personalization/dtos.py`
- [ ] `src/application/personalization/use_cases/personalized_reply.py`
- [ ] `src/application/personalization/use_cases/reset_personalization.py`
- [ ] `tests/unit/application/personalization/use_cases/*.py`
- [ ] `tests/integration/application/personalization/*.py`
- [ ] Test coverage report

---

## Next Steps

After completion:
1. Code review with Tech Lead
2. Merge to main branch
3. Begin TL-05 (Telegram Bot Integration)

---

**Status**: Pending  
**Estimated Effort**: 2 days  
**Priority**: High

