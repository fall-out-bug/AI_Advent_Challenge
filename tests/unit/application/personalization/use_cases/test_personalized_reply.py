"""Tests for PersonalizedReplyUseCase."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.personalization.dtos import PersonalizedReplyInput
from src.application.personalization.use_cases.personalized_reply import (
    PersonalizedReplyUseCase,
)
from src.domain.personalization.personalized_prompt import PersonalizedPrompt
from src.domain.personalization.user_memory_event import UserMemoryEvent
from src.domain.personalization.user_profile import UserProfile


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
    mock_llm_client,
):
    """Create use case instance."""
    return PersonalizedReplyUseCase(
        mock_personalization_service,
        mock_memory_repo,
        mock_profile_repo,
        mock_llm_client,
    )


@pytest.mark.asyncio
async def test_execute_generates_reply(
    use_case, mock_personalization_service, mock_llm_client, mock_memory_repo
):
    """Test successful reply generation."""
    profile = UserProfile.create_default_profile("123")
    mock_personalization_service.load_profile.return_value = profile

    prompt = PersonalizedPrompt(
        persona_section="You are Alfred",
        memory_context="",
        new_message="Hello",
        full_prompt="You are Alfred\n\nUser: Hello\nButler:",
    )
    mock_personalization_service.build_personalized_prompt.return_value = prompt

    input_data = PersonalizedReplyInput(user_id="123", text="Hello")
    output = await use_case.execute(input_data)

    assert output.reply == "Good day, sir"
    assert output.used_persona is True
    assert output.memory_events_used == 0
    assert output.compressed is False
    mock_llm_client.generate.assert_called_once()
    mock_memory_repo.append_events.assert_called_once()


@pytest.mark.asyncio
async def test_execute_compresses_memory_when_exceeds_cap(
    use_case,
    mock_memory_repo,
    mock_profile_repo,
    mock_personalization_service,
    mock_llm_client,
):
    """Test memory compression when cap exceeded."""
    # Simulate 51 events (exceeds cap of 50)
    mock_memory_repo.count_events.return_value = 51
    mock_memory_repo.get_recent_events.return_value = []

    profile = UserProfile.create_default_profile("123")
    mock_personalization_service.load_profile.return_value = profile
    mock_profile_repo.get.return_value = profile

    prompt = PersonalizedPrompt("", "", "Hi", "Hi")
    mock_personalization_service.build_personalized_prompt.return_value = prompt

    # Mock compression summary generation
    mock_llm_client.generate.side_effect = [
        "Summary of conversation",  # For compression
        "Good day, sir",  # For reply
    ]

    input_data = PersonalizedReplyInput(user_id="123", text="Hi")
    output = await use_case.execute(input_data)

    # Verify compression was triggered
    assert output.compressed is True
    mock_memory_repo.compress.assert_called_once()
    mock_profile_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_execute_handles_errors_gracefully(
    use_case, mock_personalization_service
):
    """Test graceful error handling."""
    # Simulate error
    mock_personalization_service.load_profile.side_effect = Exception("DB error")

    input_data = PersonalizedReplyInput(user_id="123", text="Hello")
    output = await use_case.execute(input_data)

    # Should return fallback message
    assert "Извините" in output.reply
    assert output.used_persona is False
    assert output.memory_events_used == 0


@pytest.mark.asyncio
async def test_execute_saves_interaction_to_memory(
    use_case, mock_personalization_service, mock_memory_repo
):
    """Test that interaction is saved to memory."""
    profile = UserProfile.create_default_profile("123")
    mock_personalization_service.load_profile.return_value = profile

    prompt = PersonalizedPrompt("", "", "Test", "Test")
    mock_personalization_service.build_personalized_prompt.return_value = prompt

    input_data = PersonalizedReplyInput(user_id="123", text="Test message")
    await use_case.execute(input_data)

    # Verify events were appended
    mock_memory_repo.append_events.assert_called_once()
    call_args = mock_memory_repo.append_events.call_args[0][0]
    assert len(call_args) == 2
    assert call_args[0].role == "user"
    assert call_args[0].content == "Test message"
    assert call_args[1].role == "assistant"


@pytest.mark.asyncio
async def test_execute_with_voice_source(use_case, mock_personalization_service):
    """Test execution with voice source."""
    profile = UserProfile.create_default_profile("123")
    mock_personalization_service.load_profile.return_value = profile

    prompt = PersonalizedPrompt("", "", "Voice test", "Voice test")
    mock_personalization_service.build_personalized_prompt.return_value = prompt

    input_data = PersonalizedReplyInput(
        user_id="123", text="Voice message", source="voice"
    )
    output = await use_case.execute(input_data)

    assert output.used_persona is True
    assert output.reply == "Good day, sir"


@pytest.mark.asyncio
async def test_execute_with_memory_events(
    use_case, mock_personalization_service, mock_memory_repo
):
    """Test execution with existing memory events."""
    profile = UserProfile.create_default_profile("123")
    mock_personalization_service.load_profile.return_value = profile

    events = [
        UserMemoryEvent.create_user_event("123", "Previous message"),
        UserMemoryEvent.create_assistant_event("123", "Previous reply"),
    ]
    mock_memory_repo.get_recent_events.return_value = events

    prompt = PersonalizedPrompt("", "", "New message", "New message")
    mock_personalization_service.build_personalized_prompt.return_value = prompt

    input_data = PersonalizedReplyInput(user_id="123", text="New message")
    output = await use_case.execute(input_data)

    assert output.memory_events_used == 2
    assert output.used_persona is True


@pytest.mark.asyncio
async def test_compress_memory_handles_llm_failure(
    use_case,
    mock_memory_repo,
    mock_profile_repo,
    mock_personalization_service,
    mock_llm_client,
):
    """Test that compression failure doesn't break the request."""
    # Simulate 51 events
    mock_memory_repo.count_events.return_value = 51
    mock_memory_repo.get_recent_events.return_value = []

    profile = UserProfile.create_default_profile("123")
    mock_personalization_service.load_profile.return_value = profile
    mock_profile_repo.get.return_value = profile

    prompt = PersonalizedPrompt("", "", "Test", "Test")
    mock_personalization_service.build_personalized_prompt.return_value = prompt

    # Simulate LLM failure during compression
    mock_llm_client.generate.side_effect = [
        Exception("LLM error"),  # Compression fails
        "Good day, sir",  # Reply succeeds
    ]

    input_data = PersonalizedReplyInput(user_id="123", text="Test")
    # Should not raise, but compression should fail gracefully
    output = await use_case.execute(input_data)

    # Request should still succeed
    assert output.used_persona is True
    assert output.reply == "Good day, sir"
