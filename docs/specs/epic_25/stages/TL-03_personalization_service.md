# Stage TL-03: Personalization Service & Prompt Assembly

**Epic**: EP25 - Personalised Butler  
**Stage**: TL-03  
**Duration**: 1.5 days  
**Owner**: Dev A  
**Dependencies**: TL-01, TL-02  
**Status**: Pending

---

## Goal

Implement PersonalizationServiceImpl that builds personalized LLM prompts from profile + memory context.

---

## Objectives

1. Define prompt templates (persona, memory, full prompt)
2. Implement PersonalizationServiceImpl
3. Add token estimation and truncation logic
4. Write comprehensive unit tests

---

## File Structure

```
src/application/personalization/
├── __init__.py
├── templates.py               # Prompt templates
└── personalization_service.py # PersonalizationServiceImpl

tests/unit/application/personalization/
├── __init__.py
├── test_templates.py
└── test_personalization_service.py
```

---

## Implementation Details

### 1. Prompt Templates

**File**: `src/application/personalization/templates.py`

**Requirements**:
- Template for persona section
- Template for memory context
- Template for full prompt assembly
- Russian language support

**Implementation**:

```python
"""Prompt templates for personalized interactions."""

# Persona template with Alfred-style дворецкий character
PERSONA_TEMPLATE = """Ты — {persona}. Твой тон: {tone}. Язык ответа: {language}.

Instructions:
- Отвечай как Alfred из Batman (вежливый, ироничный, заботливый).
- Используй английский юмор, но говори на русском языке.
- Будь полезным и информативным, но добавляй лёгкую иронию где уместно.
- Preferred topics: {preferred_topics}.
- Обращайся к пользователю на "вы" или "сэр" для поддержания стиля Alfred.

Примеры стиля:
- "Добрый день, сэр. Надеюсь, день проходит без излишней драмы?"
- "Ах, вечный вопрос. Позвольте проверить свои архивы..."
- "Конечно, сэр. Хотя я бы рекомендовал немного больше внимания к деталям в будущем."
"""

# Memory context template
MEMORY_CONTEXT_TEMPLATE = """Контекст предыдущих взаимодействий:

{summary_section}
{events_section}
"""

# Full prompt template
FULL_PROMPT_TEMPLATE = """{persona_section}

---

{memory_context}

---

User: {new_message}
Butler:"""

# Summary section template
SUMMARY_SECTION_TEMPLATE = """Summary of earlier interactions:
{summary}
"""

# Events section template
EVENTS_SECTION_TEMPLATE = """Recent conversation:
{events}"""


def format_persona_section(
    persona: str,
    tone: str,
    language: str,
    preferred_topics: list[str]
) -> str:
    """Format persona section from profile.
    
    Purpose:
        Build persona instructions from user profile.
    
    Args:
        persona: Persona name.
        tone: Conversation tone.
        language: Response language.
        preferred_topics: List of user's preferred topics.
    
    Returns:
        Formatted persona section.
    
    Example:
        >>> section = format_persona_section(
        ...     "Alfred-style дворецкий", "witty", "ru", ["Python"]
        ... )
        >>> "Alfred" in section
        True
    """
    topics_str = ", ".join(preferred_topics) if preferred_topics else "general topics"
    
    return PERSONA_TEMPLATE.format(
        persona=persona,
        tone=tone,
        language=language,
        preferred_topics=topics_str,
    )


def format_memory_context(
    summary: str | None,
    events: list[str]
) -> str:
    """Format memory context from summary and events.
    
    Purpose:
        Build memory context section for LLM prompt.
    
    Args:
        summary: Optional summary of older interactions.
        events: List of formatted event strings.
    
    Returns:
        Formatted memory context.
    
    Example:
        >>> context = format_memory_context(
        ...     "User likes Python",
        ...     ["- User: Hello", "- Butler: Good day, sir"]
        ... )
        >>> "Summary" in context
        True
    """
    sections = []
    
    if summary:
        summary_section = SUMMARY_SECTION_TEMPLATE.format(summary=summary)
        sections.append(summary_section)
    
    if events:
        events_text = "\n".join(events)
        events_section = EVENTS_SECTION_TEMPLATE.format(events=events_text)
        sections.append(events_section)
    
    if not sections:
        return ""
    
    return MEMORY_CONTEXT_TEMPLATE.format(
        summary_section=sections[0] if summary else "",
        events_section=sections[1] if len(sections) > 1 else sections[0] if not summary else "",
    )


def format_full_prompt(
    persona_section: str,
    memory_context: str,
    new_message: str
) -> str:
    """Format complete personalized prompt.
    
    Purpose:
        Assemble all sections into final LLM prompt.
    
    Args:
        persona_section: Formatted persona instructions.
        memory_context: Formatted memory context.
        new_message: Current user message.
    
    Returns:
        Complete personalized prompt.
    
    Example:
        >>> prompt = format_full_prompt("You are Alfred", "Previous: ...", "Hello")
        >>> "Alfred" in prompt and "Hello" in prompt
        True
    """
    return FULL_PROMPT_TEMPLATE.format(
        persona_section=persona_section,
        memory_context=memory_context if memory_context else "(No previous context)",
        new_message=new_message,
    )
```

**Tests** (`tests/unit/application/personalization/test_templates.py`):

```python
"""Tests for prompt templates."""

import pytest

from src.application.personalization.templates import (
    format_persona_section,
    format_memory_context,
    format_full_prompt,
)


def test_format_persona_section():
    """Test persona section formatting."""
    section = format_persona_section(
        "Alfred-style дворецкий",
        "witty",
        "ru",
        ["Python", "AI"]
    )
    
    assert "Alfred" in section
    assert "witty" in section
    assert "ru" in section
    assert "Python" in section
    assert "AI" in section


def test_format_memory_context_with_summary():
    """Test memory context with summary."""
    context = format_memory_context(
        "User asked about Python",
        ["- User: Hello", "- Butler: Good day"]
    )
    
    assert "Summary" in context
    assert "Python" in context
    assert "Recent conversation" in context


def test_format_memory_context_without_summary():
    """Test memory context without summary."""
    context = format_memory_context(
        None,
        ["- User: Hello"]
    )
    
    assert "Summary" not in context
    assert "Hello" in context


def test_format_full_prompt():
    """Test full prompt assembly."""
    prompt = format_full_prompt(
        "You are Alfred",
        "Previous context",
        "Hello"
    )
    
    assert "Alfred" in prompt
    assert "Previous context" in prompt
    assert "User: Hello" in prompt
    assert "Butler:" in prompt
```

---

### 2. PersonalizationServiceImpl

**File**: `src/application/personalization/personalization_service.py`

**Requirements**:
- Load profile (create if missing)
- Build personalized prompts
- Token estimation and truncation
- Logging and error handling

**Implementation**:

```python
"""Personalization service implementation."""

from src.domain.interfaces.personalization import (
    PersonalizationService,
    UserProfileRepository,
)
from src.domain.personalization.memory_slice import MemorySlice
from src.domain.personalization.personalized_prompt import PersonalizedPrompt
from src.domain.personalization.user_profile import UserProfile
from src.application.personalization.templates import (
    format_persona_section,
    format_memory_context,
    format_full_prompt,
)
from src.infrastructure.logging import get_logger

logger = get_logger("personalization_service")

# Token limits for prompt sections
TOKEN_LIMIT_TOTAL = 2000
TOKEN_LIMIT_PERSONA = 200
TOKEN_LIMIT_MEMORY = 800
TOKEN_LIMIT_MESSAGE = 200


class PersonalizationServiceImpl:
    """Service for building personalized prompts.
    
    Purpose:
        Implements PersonalizationService protocol.
        Loads profiles and assembles prompts with token limits.
    
    Attributes:
        profile_repo: Repository for user profiles.
    
    Example:
        >>> service = PersonalizationServiceImpl(profile_repo)
        >>> profile = await service.load_profile("123")
        >>> prompt = await service.build_personalized_prompt(profile, memory, "Hi")
    """
    
    def __init__(self, profile_repo: UserProfileRepository) -> None:
        """Initialize service with profile repository.
        
        Args:
            profile_repo: Repository for user profiles.
        """
        self.profile_repo = profile_repo
        logger.info("PersonalizationServiceImpl initialized")
    
    async def load_profile(self, user_id: str) -> UserProfile:
        """Load user profile (create default if missing).
        
        Purpose:
            Get or create user profile with default Alfred persona.
        
        Args:
            user_id: User identifier.
        
        Returns:
            UserProfile (newly created if didn't exist).
        
        Example:
            >>> profile = await service.load_profile("123")
            >>> profile.persona
            'Alfred-style дворецкий'
        """
        profile = await self.profile_repo.get(user_id)
        
        logger.info(
            "Profile loaded",
            extra={
                "user_id": user_id,
                "persona": profile.persona,
                "language": profile.language,
                "has_summary": profile.memory_summary is not None,
            }
        )
        
        return profile
    
    async def build_personalized_prompt(
        self,
        profile: UserProfile,
        memory_slice: MemorySlice,
        new_message: str,
    ) -> PersonalizedPrompt:
        """Build personalized prompt for LLM.
        
        Purpose:
            Assemble persona + memory + message into complete prompt.
            Applies token limits and truncation if needed.
        
        Args:
            profile: User profile with persona settings.
            memory_slice: Memory context (events + summary).
            new_message: Current user message.
        
        Returns:
            PersonalizedPrompt ready for LLM generation.
        
        Example:
            >>> prompt = await service.build_personalized_prompt(
            ...     profile, memory_slice, "Hello"
            ... )
            >>> prompt.estimate_tokens() <= 2000
            True
        """
        # Build persona section
        persona_section = format_persona_section(
            persona=profile.persona,
            tone=profile.tone,
            language=profile.language,
            preferred_topics=profile.preferred_topics,
        )
        
        # Build memory context (initial attempt with all events)
        memory_context = self._build_memory_context(memory_slice, max_events=20)
        
        # Build full prompt
        full_prompt = format_full_prompt(
            persona_section=persona_section,
            memory_context=memory_context,
            new_message=new_message,
        )
        
        # Check token limit
        estimated_tokens = len(full_prompt) // 4
        
        if estimated_tokens > TOKEN_LIMIT_TOTAL:
            logger.warning(
                "Prompt exceeds token limit, truncating",
                extra={
                    "user_id": profile.user_id,
                    "estimated_tokens": estimated_tokens,
                    "limit": TOKEN_LIMIT_TOTAL,
                }
            )
            
            # Truncate: keep summary + last 5 events
            memory_context = self._build_memory_context(memory_slice, max_events=5)
            full_prompt = format_full_prompt(
                persona_section=persona_section,
                memory_context=memory_context,
                new_message=new_message,
            )
            estimated_tokens = len(full_prompt) // 4
        
        prompt = PersonalizedPrompt(
            persona_section=persona_section,
            memory_context=memory_context,
            new_message=new_message,
            full_prompt=full_prompt,
        )
        
        logger.info(
            "Personalized prompt built",
            extra={
                "user_id": profile.user_id,
                "persona": profile.persona,
                "memory_events_used": len(memory_slice.events),
                "has_summary": memory_slice.summary is not None,
                "estimated_tokens": estimated_tokens,
            }
        )
        
        return prompt
    
    def _build_memory_context(
        self,
        memory_slice: MemorySlice,
        max_events: int
    ) -> str:
        """Build memory context with event limit.
        
        Args:
            memory_slice: Memory slice with events and summary.
            max_events: Maximum events to include.
        
        Returns:
            Formatted memory context string.
        """
        # Format events
        event_strings = []
        for event in memory_slice.events[-max_events:]:
            role_label = "User" if event.role == "user" else "Butler"
            content_preview = event.content[:200]
            if len(event.content) > 200:
                content_preview += "..."
            event_strings.append(f"- {role_label}: {content_preview}")
        
        # Format context
        return format_memory_context(
            summary=memory_slice.summary,
            events=event_strings,
        )
```

**Tests** (`tests/unit/application/personalization/test_personalization_service.py`):

```python
"""Tests for PersonalizationServiceImpl."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.application.personalization.personalization_service import (
    PersonalizationServiceImpl
)
from src.domain.personalization.user_profile import UserProfile
from src.domain.personalization.user_memory_event import UserMemoryEvent
from src.domain.personalization.memory_slice import MemorySlice


@pytest.fixture
def mock_profile_repo():
    """Mock profile repository."""
    repo = MagicMock()
    repo.get = AsyncMock()
    return repo


@pytest.fixture
def service(mock_profile_repo):
    """Create service instance."""
    return PersonalizationServiceImpl(mock_profile_repo)


@pytest.mark.asyncio
async def test_load_profile_creates_default(service, mock_profile_repo):
    """Test load_profile creates default if missing."""
    user_id = "test_user_123"
    profile = UserProfile.create_default_profile(user_id)
    mock_profile_repo.get.return_value = profile
    
    result = await service.load_profile(user_id)
    
    assert result.user_id == user_id
    assert result.persona == "Alfred-style дворецкий"
    mock_profile_repo.get.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_build_prompt_with_memory(service):
    """Test building prompt with memory."""
    profile = UserProfile.create_default_profile("123")
    
    events = [
        UserMemoryEvent.create_user_event("123", "Hello"),
        UserMemoryEvent.create_assistant_event("123", "Good day, sir"),
    ]
    
    memory_slice = MemorySlice(
        events=events,
        summary="Previous conversation",
        total_events=2,
    )
    
    prompt = await service.build_personalized_prompt(
        profile, memory_slice, "Tell me more"
    )
    
    assert "Alfred" in prompt.persona_section
    assert "Hello" in prompt.memory_context or "Good day" in prompt.memory_context
    assert "Tell me more" in prompt.new_message
    assert prompt.estimate_tokens() > 0


@pytest.mark.asyncio
async def test_build_prompt_truncates_long_context(service):
    """Test prompt truncation for long context."""
    profile = UserProfile.create_default_profile("123")
    
    # Create many events (simulate >50 events)
    events = [
        UserMemoryEvent.create_user_event("123", "Message" * 100)
        for _ in range(50)
    ]
    
    memory_slice = MemorySlice(
        events=events,
        summary="Long conversation",
        total_events=50,
    )
    
    prompt = await service.build_personalized_prompt(
        profile, memory_slice, "Hi"
    )
    
    # Should truncate to keep under 2000 tokens
    assert prompt.estimate_tokens() <= 2000


@pytest.mark.asyncio
async def test_build_prompt_without_memory(service):
    """Test building prompt without memory."""
    profile = UserProfile.create_default_profile("123")
    
    memory_slice = MemorySlice(events=[], summary=None, total_events=0)
    
    prompt = await service.build_personalized_prompt(
        profile, memory_slice, "Hello"
    )
    
    assert "Alfred" in prompt.persona_section
    assert "Hello" in prompt.new_message
    assert prompt.full_prompt
```

---

## Testing Requirements

### Unit Tests Coverage

- **Templates**: 100%
  - Persona section formatting
  - Memory context formatting
  - Full prompt assembly
  - Edge cases (empty topics, no summary)

- **PersonalizationServiceImpl**: ≥80%
  - Load profile
  - Build prompt (with/without memory)
  - Token truncation
  - Error handling

### Test Execution

```bash
# Run unit tests
pytest tests/unit/application/personalization/ -v --cov=src/application/personalization --cov-report=term-missing

# Type checking
mypy src/application/personalization/ --strict
```

---

## Acceptance Criteria

- [ ] Prompt templates implemented
- [ ] PersonalizationServiceImpl implemented
- [ ] Token estimation and truncation working
- [ ] Unit tests with ≥80% coverage
- [ ] All docstrings complete
- [ ] Logging for prompt assembly
- [ ] Mypy strict mode passes

---

## Dependencies

- **Upstream**: TL-01 (domain models), TL-02 (repositories)
- **Downstream**: TL-04 (use cases)

---

## Deliverables

- [ ] `src/application/personalization/templates.py`
- [ ] `src/application/personalization/personalization_service.py`
- [ ] `tests/unit/application/personalization/test_templates.py`
- [ ] `tests/unit/application/personalization/test_personalization_service.py`
- [ ] Test coverage report

---

## Next Steps

After completion:
1. Code review with Tech Lead
2. Merge to main branch
3. Begin TL-04 (Personalized Reply Use Case)

---

**Status**: Pending  
**Estimated Effort**: 1.5 days  
**Priority**: High

