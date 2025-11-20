"""Integration tests for personalized reply flow."""

import pytest

from src.application.personalization.dtos import PersonalizedReplyInput
from src.domain.personalization.user_memory_event import UserMemoryEvent


@pytest.mark.asyncio
async def test_personalized_reply_flow(
    personalized_reply_use_case, memory_repo, profile_repo
):
    """Test full flow: text message → personalized reply → memory stored."""
    user_id = "test_user_integration_123"
    message_text = "Привет, как дела?"

    input_data = PersonalizedReplyInput(
        user_id=user_id, text=message_text, source="text"
    )

    output = await personalized_reply_use_case.execute(input_data)

    # Verify reply was generated
    assert output.reply is not None
    assert len(output.reply) > 0
    assert output.used_persona is True
    assert output.memory_events_used == 0  # First message, no history

    # Verify memory was stored
    events = await memory_repo.get_recent_events(user_id, limit=10)
    assert len(events) == 2  # user + assistant events
    assert events[0].role == "user"
    assert events[0].content == message_text
    assert events[1].role == "assistant"
    assert events[1].content == output.reply


@pytest.mark.asyncio
async def test_personalized_reply_with_memory_context(
    personalized_reply_use_case, memory_repo, profile_repo
):
    """Test personalized reply uses previous memory context."""
    user_id = "test_user_memory_456"

    # Add some previous events
    previous_events = [
        UserMemoryEvent.create_user_event(user_id, "Я люблю Python"),
        UserMemoryEvent.create_assistant_event(
            user_id, "Отлично, Python - замечательный язык!"
        ),
    ]
    await memory_repo.append_events(previous_events)

    # Send new message
    input_data = PersonalizedReplyInput(
        user_id=user_id, text="Расскажи про асинхронность", source="text"
    )

    output = await personalized_reply_use_case.execute(input_data)

    # Verify reply was generated with context
    assert output.used_persona is True
    assert output.memory_events_used == 2  # Previous events used

    # Verify new interaction was stored
    events = await memory_repo.get_recent_events(user_id, limit=10)
    assert len(events) == 4  # 2 previous + 2 new


@pytest.mark.asyncio
async def test_memory_compression_triggered(
    personalized_reply_use_case, memory_repo, profile_repo, mock_llm_client
):
    """Test memory compression when threshold exceeded."""
    user_id = "test_user_compression_789"

    # Create 51 events (exceeds cap of 50)
    events = []
    for i in range(51):
        events.append(UserMemoryEvent.create_user_event(user_id, f"Message {i}"))
        events.append(UserMemoryEvent.create_assistant_event(user_id, f"Reply {i}"))
    await memory_repo.append_events(events)

    # Mock LLM for compression summary
    mock_llm_client.generate.side_effect = [
        "Сводка предыдущих разговоров",  # Compression summary
        "Добрый день, сэр. Чем могу быть полезен?",  # Reply
    ]

    # Send new message (should trigger compression)
    input_data = PersonalizedReplyInput(
        user_id=user_id, text="Новое сообщение", source="text"
    )

    output = await personalized_reply_use_case.execute(input_data)

    # Verify compression was triggered
    assert output.compressed is True

    # Verify memory was compressed (should have ~20 events + 2 new)
    event_count = await memory_repo.count_events(user_id)
    assert event_count <= 22  # 20 kept + 2 new

    # Verify profile has summary
    profile = await profile_repo.get(user_id)
    assert profile.memory_summary is not None
    assert len(profile.memory_summary) > 0


@pytest.mark.asyncio
async def test_voice_source_handled(personalized_reply_use_case, memory_repo):
    """Test voice source is handled correctly."""
    user_id = "test_user_voice_999"
    message_text = "Голосовое сообщение"

    input_data = PersonalizedReplyInput(
        user_id=user_id, text=message_text, source="voice"
    )

    output = await personalized_reply_use_case.execute(input_data)

    assert output.used_persona is True
    assert output.reply is not None

    # Verify events stored
    events = await memory_repo.get_recent_events(user_id, limit=5)
    assert len(events) == 2
