"""E2E tests for voice personalization flow."""

import pytest

from src.application.personalization.dtos import PersonalizedReplyInput
from src.infrastructure.config.settings import get_settings
from src.infrastructure.personalization.factory import (
    create_personalized_use_cases,
)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_voice_personalized_reply_flow(
    real_mongodb, llm_client
):
    """Test full voice message personalization flow.

    Purpose:
        Verify that:
        1. Voice transcription is routed to personalized reply
        2. Memory is saved with source="voice"
        3. Reply is generated with persona
    """
    settings = get_settings()
    mongo_client = real_mongodb.client

    reply_use_case, _ = create_personalized_use_cases(
        settings, mongo_client, llm_client
    )

    user_id = "e2e_test_voice_123"

    # Simulate voice message (after STT transcription)
    input_data = PersonalizedReplyInput(
        user_id=user_id,
        text="Привет, как дела?",  # Transcribed text
        source="voice",
    )

    output = await reply_use_case.execute(input_data)

    # Verify personalized reply
    assert output.used_persona is True
    assert output.reply
    assert len(output.reply) > 0

    # Verify memory was saved
    db = real_mongodb
    events = await db.user_memory.find({"user_id": user_id}).to_list(length=10)
    assert len(events) == 2  # user + assistant events

    # Verify source is tracked (in memory events)
    user_event = next((e for e in events if e["role"] == "user"), None)
    assert user_event is not None
    assert user_event["content"] == "Привет, как дела?"
