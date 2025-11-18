"""Tests for PersonalizationServiceImpl."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.application.personalization.personalization_service import (
    PersonalizationServiceImpl,
)
from src.domain.personalization.memory_slice import MemorySlice
from src.domain.personalization.user_memory_event import UserMemoryEvent
from src.domain.personalization.user_profile import UserProfile


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
        events=events, summary="Previous conversation", total_events=2
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
        UserMemoryEvent.create_user_event("123", "Message" * 100) for _ in range(50)
    ]

    memory_slice = MemorySlice(
        events=events, summary="Long conversation", total_events=50
    )

    prompt = await service.build_personalized_prompt(profile, memory_slice, "Hi")

    # Should truncate to keep under 2000 tokens
    assert prompt.estimate_tokens() <= 2000


@pytest.mark.asyncio
async def test_build_prompt_without_memory(service):
    """Test building prompt without memory."""
    profile = UserProfile.create_default_profile("123")

    memory_slice = MemorySlice(events=[], summary=None, total_events=0)

    prompt = await service.build_personalized_prompt(profile, memory_slice, "Hello")

    assert "Alfred" in prompt.persona_section
    assert "Hello" in prompt.new_message
    assert prompt.full_prompt


@pytest.mark.asyncio
async def test_build_prompt_with_summary_only(service):
    """Test building prompt with summary but no events."""
    profile = UserProfile.create_default_profile("123")

    memory_slice = MemorySlice(
        events=[], summary="User asked about Python", total_events=10
    )

    prompt = await service.build_personalized_prompt(
        profile, memory_slice, "Tell me more"
    )

    assert "Alfred" in prompt.persona_section
    assert "Python" in prompt.memory_context
    assert "Tell me more" in prompt.new_message


@pytest.mark.asyncio
async def test_build_prompt_with_preferred_topics(service):
    """Test building prompt with preferred topics."""
    profile = UserProfile(
        user_id="123",
        language="ru",
        persona="Alfred-style дворецкий",
        tone="witty",
        preferred_topics=["Python", "AI", "Machine Learning"],
    )

    memory_slice = MemorySlice(events=[], summary=None, total_events=0)

    prompt = await service.build_personalized_prompt(profile, memory_slice, "Hello")

    assert "Python" in prompt.persona_section
    assert "AI" in prompt.persona_section
    assert "Machine Learning" in prompt.persona_section


@pytest.mark.asyncio
async def test_build_prompt_event_truncation(service):
    """Test that long event content is truncated."""
    profile = UserProfile.create_default_profile("123")

    # Create event with very long content
    long_content = "A" * 500
    events = [
        UserMemoryEvent.create_user_event("123", long_content),
    ]

    memory_slice = MemorySlice(events=events, summary=None, total_events=1)

    prompt = await service.build_personalized_prompt(profile, memory_slice, "Hello")

    # Content should be truncated to 200 chars + "..."
    assert "..." in prompt.memory_context
    # Should not contain full 500 chars
    assert long_content not in prompt.memory_context


@pytest.mark.asyncio
async def test_load_profile_handles_none(service, mock_profile_repo):
    """Test load_profile handles None from repository (defensive)."""
    user_id = "test_user_none"
    # Simulate repository returning None (shouldn't happen with auto-creation)
    mock_profile_repo.get.return_value = None
    mock_profile_repo.save = AsyncMock()

    result = await service.load_profile(user_id)

    # Should create default profile
    assert result is not None
    assert result.user_id == user_id
    assert result.persona == "Alfred-style дворецкий"
    mock_profile_repo.save.assert_called_once()
