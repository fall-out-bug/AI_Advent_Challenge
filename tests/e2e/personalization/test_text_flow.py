"""E2E tests for text personalization flow."""

import pytest

from src.application.personalization.dtos import PersonalizedReplyInput
from src.infrastructure.config.settings import get_settings
from src.infrastructure.personalization.factory import create_personalized_use_cases


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_text_personalized_reply_flow(real_mongodb, llm_client):
    """Test full text message personalization flow.

    Purpose:
        Verify that:
        1. User profile is auto-created with Alfred persona
        2. LLM generates reply with persona
        3. Interaction is saved to memory
        4. Subsequent request uses memory context
    """
    settings = get_settings()
    mongo_client = real_mongodb.client

    # Create use cases
    reply_use_case, _ = create_personalized_use_cases(
        settings, mongo_client, llm_client
    )

    user_id = "e2e_test_text_123"

    # First interaction
    input_data1 = PersonalizedReplyInput(
        user_id=user_id,
        text="Hello, who are you?",
        source="text",
    )

    output1 = await reply_use_case.execute(input_data1)

    # Verify reply has Alfred characteristics
    assert output1.used_persona is True
    assert output1.reply
    assert len(output1.reply) > 0

    # Verify memory was saved
    assert output1.memory_events_used == 0  # First interaction

    # Second interaction (should use memory from first)
    input_data2 = PersonalizedReplyInput(
        user_id=user_id,
        text="What did I just ask you?",
        source="text",
    )

    output2 = await reply_use_case.execute(input_data2)

    # Verify memory context used
    assert output2.used_persona is True
    assert output2.memory_events_used >= 2  # User + assistant from first

    # Verify profile exists in MongoDB
    db = real_mongodb
    profile = await db.user_profiles.find_one({"user_id": user_id})

    assert profile is not None
    assert profile["persona"] == "Alfred-style дворецкий"
    assert profile["language"] == "ru"

    # Verify memory events exist
    event_count = await db.user_memory.count_documents({"user_id": user_id})
    assert event_count >= 4  # 2 interactions × 2 events (user + assistant)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_personalization_profile_auto_creation(real_mongodb, llm_client):
    """Test that profile is auto-created on first interaction."""
    settings = get_settings()
    mongo_client = real_mongodb.client

    reply_use_case, _ = create_personalized_use_cases(
        settings, mongo_client, llm_client
    )

    user_id = "e2e_test_auto_create_456"

    # Verify profile doesn't exist yet
    db = real_mongodb
    profile_before = await db.user_profiles.find_one({"user_id": user_id})
    assert profile_before is None

    # First interaction (should auto-create profile)
    input_data = PersonalizedReplyInput(
        user_id=user_id,
        text="Test message",
        source="text",
    )

    output = await reply_use_case.execute(input_data)

    # Verify profile was created
    profile_after = await db.user_profiles.find_one({"user_id": user_id})
    assert profile_after is not None
    assert profile_after["persona"] == "Alfred-style дворецкий"
    assert profile_after["language"] == "ru"
    assert output.used_persona is True
