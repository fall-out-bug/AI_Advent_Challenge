# Stage TL-01: Domain Models & Interfaces

**Epic**: EP25 - Personalised Butler  
**Stage**: TL-01  
**Duration**: 1.5 days  
**Owner**: Dev A  
**Dependencies**: TL-00  
**Status**: Pending

---

## Goal

Define domain layer foundation with value objects and protocols following Clean Architecture principles.

---

## Objectives

1. Create domain value objects (UserProfile, UserMemoryEvent, MemorySlice, PersonalizedPrompt)
2. Define repository and service protocols
3. Implement comprehensive unit tests
4. Ensure 100% type coverage and documentation

---

## File Structure

```
src/domain/personalization/
├── __init__.py
├── user_profile.py          # UserProfile value object
├── user_memory_event.py     # UserMemoryEvent value object
├── memory_slice.py          # MemorySlice value object
└── personalized_prompt.py   # PersonalizedPrompt value object

src/domain/interfaces/personalization.py  # Protocols

tests/unit/domain/personalization/
├── __init__.py
├── test_user_profile.py
├── test_user_memory_event.py
├── test_memory_slice.py
└── test_personalized_prompt.py
```

---

## Implementation Details

### 1. UserProfile Value Object

**File**: `src/domain/personalization/user_profile.py`

**Requirements**:
- Immutable dataclass (frozen=True)
- All fields typed with type hints
- Factory method for default profile creation
- Validation logic

**Implementation**:

```python
"""User profile value object for personalization."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class UserProfile:
    """User profile with personalization preferences.
    
    Purpose:
        Stores user preferences for personalized interactions including
        language, persona, tone, and memory summary.
    
    Attributes:
        user_id: Unique user identifier (Telegram user ID as string).
        language: ISO 639-1 language code (e.g., "ru", "en").
        persona: Persona name (e.g., "Alfred-style дворецкий").
        tone: Conversation tone (e.g., "witty", "formal", "casual").
        preferred_topics: List of user's preferred topics.
        memory_summary: Compressed summary of past interactions.
        created_at: Profile creation timestamp.
        updated_at: Last profile update timestamp.
    
    Example:
        >>> profile = UserProfile.create_default_profile("123456789")
        >>> profile.persona
        'Alfred-style дворецкий'
        >>> profile.language
        'ru'
    """
    
    user_id: str
    language: str
    persona: str
    tone: str
    preferred_topics: List[str] = field(default_factory=list)
    memory_summary: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self) -> None:
        """Validate profile data.
        
        Raises:
            ValueError: If user_id is empty or language is invalid.
        """
        if not self.user_id:
            raise ValueError("user_id cannot be empty")
        
        if not self.language:
            raise ValueError("language cannot be empty")
        
        # Valid ISO 639-1 codes (extend as needed)
        valid_languages = {"ru", "en", "es", "de", "fr"}
        if self.language not in valid_languages:
            raise ValueError(f"language must be one of {valid_languages}")
    
    @staticmethod
    def create_default_profile(user_id: str) -> "UserProfile":
        """Create default profile with Alfred persona and Russian language.
        
        Purpose:
            Factory method to create new user profiles with sensible defaults.
            All users start with "Alfred-style дворецкий" persona.
        
        Args:
            user_id: Unique user identifier.
        
        Returns:
            UserProfile with default settings.
        
        Example:
            >>> profile = UserProfile.create_default_profile("123")
            >>> profile.persona
            'Alfred-style дворецкий'
        """
        now = datetime.utcnow()
        return UserProfile(
            user_id=user_id,
            language="ru",
            persona="Alfred-style дворецкий",
            tone="witty",
            preferred_topics=[],
            memory_summary=None,
            created_at=now,
            updated_at=now,
        )
    
    def with_summary(self, summary: str) -> "UserProfile":
        """Create new profile with updated memory summary.
        
        Purpose:
            Immutable update pattern for memory summary.
        
        Args:
            summary: New memory summary text.
        
        Returns:
            New UserProfile with updated summary and timestamp.
        
        Example:
            >>> profile = UserProfile.create_default_profile("123")
            >>> updated = profile.with_summary("User asked about Python")
            >>> updated.memory_summary
            'User asked about Python'
        """
        return UserProfile(
            user_id=self.user_id,
            language=self.language,
            persona=self.persona,
            tone=self.tone,
            preferred_topics=self.preferred_topics,
            memory_summary=summary,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )
```

**Tests** (`tests/unit/domain/personalization/test_user_profile.py`):
- Test default profile creation
- Test validation (empty user_id, invalid language)
- Test `with_summary()` immutability
- Test serialization (if needed for JSON)

---

### 2. UserMemoryEvent Value Object

**File**: `src/domain/personalization/user_memory_event.py`

**Requirements**:
- Immutable dataclass
- UUID for event_id
- Role validation (user/assistant only)
- Factory methods for each role

**Implementation**:

```python
"""User memory event value object."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal
from uuid import UUID, uuid4


@dataclass(frozen=True)
class UserMemoryEvent:
    """Single interaction event in user memory.
    
    Purpose:
        Represents one message in conversation history (user or assistant).
        Events are stored chronologically and used to build context for LLM.
    
    Attributes:
        event_id: Unique event identifier (UUID).
        user_id: User this event belongs to.
        role: Message role ("user" or "assistant").
        content: Message text content.
        created_at: Event timestamp.
        tags: Optional tags for categorization.
    
    Example:
        >>> event = UserMemoryEvent.create_user_event("123", "Hello!")
        >>> event.role
        'user'
        >>> event.content
        'Hello!'
    """
    
    event_id: UUID
    user_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate event data.
        
        Raises:
            ValueError: If required fields are invalid.
        """
        if not self.user_id:
            raise ValueError("user_id cannot be empty")
        
        if not self.content:
            raise ValueError("content cannot be empty")
        
        if self.role not in ("user", "assistant"):
            raise ValueError("role must be 'user' or 'assistant'")
    
    @staticmethod
    def create_user_event(user_id: str, content: str) -> "UserMemoryEvent":
        """Create user message event.
        
        Args:
            user_id: User identifier.
            content: Message text.
        
        Returns:
            UserMemoryEvent with role="user".
        
        Example:
            >>> event = UserMemoryEvent.create_user_event("123", "Hello")
            >>> event.role
            'user'
        """
        return UserMemoryEvent(
            event_id=uuid4(),
            user_id=user_id,
            role="user",
            content=content,
            created_at=datetime.utcnow(),
            tags=[],
        )
    
    @staticmethod
    def create_assistant_event(user_id: str, content: str) -> "UserMemoryEvent":
        """Create assistant reply event.
        
        Args:
            user_id: User identifier.
            content: Reply text.
        
        Returns:
            UserMemoryEvent with role="assistant".
        
        Example:
            >>> event = UserMemoryEvent.create_assistant_event("123", "Hi!")
            >>> event.role
            'assistant'
        """
        return UserMemoryEvent(
            event_id=uuid4(),
            user_id=user_id,
            role="assistant",
            content=content,
            created_at=datetime.utcnow(),
            tags=[],
        )
```

**Tests** (`tests/unit/domain/personalization/test_user_memory_event.py`):
- Test factory methods (user/assistant events)
- Test validation (empty content, invalid role)
- Test UUID generation uniqueness
- Test immutability

---

### 3. MemorySlice Value Object

**File**: `src/domain/personalization/memory_slice.py`

**Requirements**:
- Container for events + summary
- Method to format for prompt context
- Truncation logic for large event lists

**Implementation**:

```python
"""Memory slice value object."""

from dataclasses import dataclass
from typing import List, Optional

from src.domain.personalization.user_memory_event import UserMemoryEvent


@dataclass
class MemorySlice:
    """Slice of user memory for prompt context.
    
    Purpose:
        Bundles recent events with optional summary for LLM prompts.
        Provides formatting method to convert events to prompt text.
    
    Attributes:
        events: List of recent memory events (chronological order).
        summary: Optional compressed summary of older interactions.
        total_events: Total number of events in full memory (for metrics).
    
    Example:
        >>> events = [UserMemoryEvent.create_user_event("123", "Hi")]
        >>> slice = MemorySlice(events=events, summary="Previous chat")
        >>> context = slice.to_prompt_context()
        >>> "Recent interactions" in context
        True
    """
    
    events: List[UserMemoryEvent]
    summary: Optional[str] = None
    total_events: int = 0
    
    def to_prompt_context(self, max_events: int = 10) -> str:
        """Format memory slice as LLM prompt context.
        
        Purpose:
            Convert events and summary into formatted text for injection
            into personalized prompts.
        
        Args:
            max_events: Maximum events to include (default: 10).
        
        Returns:
            Formatted context string with summary and recent events.
        
        Example:
            >>> slice = MemorySlice(events=[...], summary="User likes Python")
            >>> context = slice.to_prompt_context(max_events=5)
            >>> "Summary: User likes Python" in context
            True
        """
        lines = []
        
        # Add summary if available
        if self.summary:
            lines.append(f"Summary: {self.summary}\n")
        
        # Add recent events
        if self.events:
            lines.append("Recent interactions:")
            # Take last N events
            recent_events = self.events[-max_events:]
            for event in recent_events:
                role_label = "User" if event.role == "user" else "Butler"
                # Truncate long messages
                content_preview = event.content[:200]
                if len(event.content) > 200:
                    content_preview += "..."
                lines.append(f"- {role_label}: {content_preview}")
        
        return "\n".join(lines) if lines else ""
```

**Tests** (`tests/unit/domain/personalization/test_memory_slice.py`):
- Test `to_prompt_context()` formatting
- Test truncation of long messages
- Test with/without summary
- Test empty events list
- Test max_events parameter

---

### 4. PersonalizedPrompt Value Object

**File**: `src/domain/personalization/personalized_prompt.py`

**Requirements**:
- Container for prompt sections
- Token estimation method
- Full prompt assembly

**Implementation**:

```python
"""Personalized prompt value object."""

from dataclasses import dataclass


@dataclass
class PersonalizedPrompt:
    """Personalized LLM prompt with persona and memory context.
    
    Purpose:
        Assembles persona instructions, memory context, and new message
        into a complete prompt for LLM generation.
    
    Attributes:
        persona_section: Persona instructions and tone.
        memory_context: Formatted memory events and summary.
        new_message: Current user message to respond to.
        full_prompt: Complete assembled prompt.
    
    Example:
        >>> prompt = PersonalizedPrompt(
        ...     persona_section="You are Alfred",
        ...     memory_context="Previous: User asked about Python",
        ...     new_message="Tell me more",
        ...     full_prompt="You are Alfred\\n\\nPrevious...\\n\\nUser: Tell me more"
        ... )
        >>> prompt.estimate_tokens()
        25
    """
    
    persona_section: str
    memory_context: str
    new_message: str
    full_prompt: str
    
    def estimate_tokens(self) -> int:
        """Estimate token count for full prompt.
        
        Purpose:
            Simple heuristic for token estimation to enforce limits.
            Uses 4 characters ≈ 1 token approximation.
        
        Returns:
            Estimated token count.
        
        Example:
            >>> prompt = PersonalizedPrompt(..., full_prompt="Hello world")
            >>> prompt.estimate_tokens()
            2
        """
        return len(self.full_prompt) // 4
    
    def is_within_limit(self, token_limit: int = 2000) -> bool:
        """Check if prompt is within token limit.
        
        Args:
            token_limit: Maximum allowed tokens (default: 2000).
        
        Returns:
            True if prompt is within limit.
        
        Example:
            >>> prompt = PersonalizedPrompt(..., full_prompt="short")
            >>> prompt.is_within_limit(2000)
            True
        """
        return self.estimate_tokens() <= token_limit
```

**Tests** (`tests/unit/domain/personalization/test_personalized_prompt.py`):
- Test `estimate_tokens()` calculation
- Test `is_within_limit()` boundary conditions
- Test with various prompt lengths

---

### 5. Repository Protocols

**File**: `src/domain/interfaces/personalization.py`

**Requirements**:
- Protocol definitions for repositories and service
- Async methods
- Type hints for all parameters and returns

**Implementation**:

```python
"""Personalization domain protocols."""

from typing import List, Optional, Protocol

from src.domain.personalization.memory_slice import MemorySlice
from src.domain.personalization.personalized_prompt import PersonalizedPrompt
from src.domain.personalization.user_memory_event import UserMemoryEvent
from src.domain.personalization.user_profile import UserProfile


class UserProfileRepository(Protocol):
    """Repository for user profiles.
    
    Purpose:
        Persistence interface for UserProfile value objects.
        Implementations handle storage details (Mongo, etc.).
    """
    
    async def get(self, user_id: str) -> Optional[UserProfile]:
        """Get profile by user ID.
        
        Args:
            user_id: User identifier.
        
        Returns:
            UserProfile if found, None otherwise.
        """
        ...
    
    async def save(self, profile: UserProfile) -> None:
        """Save (upsert) user profile.
        
        Args:
            profile: Profile to save.
        """
        ...
    
    async def reset(self, user_id: str) -> None:
        """Delete profile and recreate with defaults.
        
        Args:
            user_id: User identifier.
        """
        ...


class UserMemoryRepository(Protocol):
    """Repository for user memory events.
    
    Purpose:
        Persistence interface for UserMemoryEvent value objects.
        Supports chronological queries and memory compression.
    """
    
    async def append_events(self, events: List[UserMemoryEvent]) -> None:
        """Append new memory events.
        
        Args:
            events: List of events to append.
        """
        ...
    
    async def get_recent_events(
        self, user_id: str, limit: int
    ) -> List[UserMemoryEvent]:
        """Get recent events in chronological order.
        
        Args:
            user_id: User identifier.
            limit: Maximum events to return.
        
        Returns:
            List of recent events (oldest first).
        """
        ...
    
    async def compress(
        self, user_id: str, summary: str, keep_last_n: int
    ) -> None:
        """Compress memory by deleting old events.
        
        Args:
            user_id: User identifier.
            summary: Summary of deleted events (stored in profile).
            keep_last_n: Number of recent events to retain.
        """
        ...
    
    async def count_events(self, user_id: str) -> int:
        """Count total events for user.
        
        Args:
            user_id: User identifier.
        
        Returns:
            Total event count.
        """
        ...


class PersonalizationService(Protocol):
    """Service for building personalized prompts.
    
    Purpose:
        Domain service for loading profiles and assembling prompts.
        Orchestrates profile + memory into LLM-ready prompts.
    """
    
    async def load_profile(self, user_id: str) -> UserProfile:
        """Load user profile (create default if missing).
        
        Args:
            user_id: User identifier.
        
        Returns:
            UserProfile (newly created if didn't exist).
        """
        ...
    
    async def build_personalized_prompt(
        self,
        profile: UserProfile,
        memory_slice: MemorySlice,
        new_message: str,
    ) -> PersonalizedPrompt:
        """Build personalized prompt for LLM.
        
        Args:
            profile: User profile with persona settings.
            memory_slice: Memory context (events + summary).
            new_message: Current user message.
        
        Returns:
            PersonalizedPrompt ready for LLM generation.
        """
        ...
```

**Tests**: Protocol compliance verified by mypy strict mode

---

## Testing Requirements

### Unit Tests Coverage

- **UserProfile**: 100%
  - Default creation
  - Validation (empty user_id, invalid language)
  - `with_summary()` immutability
  - Factory method

- **UserMemoryEvent**: 100%
  - User event creation
  - Assistant event creation
  - Validation (empty content, invalid role)
  - UUID uniqueness

- **MemorySlice**: 100%
  - `to_prompt_context()` formatting
  - Truncation logic
  - With/without summary
  - Empty events

- **PersonalizedPrompt**: 100%
  - Token estimation
  - Limit checking
  - Boundary conditions

### Test Execution

```bash
# Run domain layer tests
pytest tests/unit/domain/personalization/ -v --cov=src/domain/personalization --cov-report=term-missing

# Type checking
mypy src/domain/personalization/ --strict

# Linting
flake8 src/domain/personalization/
black --check src/domain/personalization/
```

---

## Acceptance Criteria

- [ ] All value objects implemented with frozen dataclasses
- [ ] 100% type hints coverage (mypy strict mode passes)
- [ ] All protocols defined in `personalization.py`
- [ ] Factory methods for default creation
- [ ] Validation logic for all value objects
- [ ] Unit tests with 100% coverage
- [ ] All docstrings complete (Google style)
- [ ] Code passes linting (flake8, black)

---

## Dependencies

- **Upstream**: TL-00 (decisions confirmed)
- **Downstream**: TL-02 (repositories need these protocols)

---

## Deliverables

- [ ] `src/domain/personalization/*.py` - All value objects
- [ ] `src/domain/interfaces/personalization.py` - Protocols
- [ ] `tests/unit/domain/personalization/*.py` - Unit tests
- [ ] Test coverage report (≥100% for domain layer)

---

## Next Steps

After completion:
1. Code review with Tech Lead
2. Merge to main branch
3. Begin TL-02 (Infrastructure Repositories)

---

**Status**: Pending  
**Estimated Effort**: 1.5 days  
**Priority**: High

