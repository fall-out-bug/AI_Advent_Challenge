"""E2E tests for memory compression."""

import pytest

from src.application.personalization.dtos import PersonalizedReplyInput
from src.infrastructure.config.settings import get_settings
from src.infrastructure.personalization.factory import (
    create_personalized_use_cases,
)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_memory_compression_trigger(
    real_mongodb, llm_client
):
    """Test that memory compression triggers at threshold.

    Purpose:
        Verify that:
        1. >50 events triggers compression
        2. Compression creates summary
        3. Old events are deleted, last 20 kept
        4. Profile is updated with summary
    """
    settings = get_settings()
    mongo_client = real_mongodb.client

    reply_use_case, _ = create_personalized_use_cases(
        settings, mongo_client, llm_client
    )

    user_id = "e2e_test_compression_123"

    # Send 51 messages to trigger compression (cap is 50)
    compressed_triggered = False
    for i in range(51):
        input_data = PersonalizedReplyInput(
            user_id=user_id,
            text=f"Message {i}",
            source="text",
        )
        output = await reply_use_case.execute(input_data)

        # Last message should trigger compression
        if output.compressed:
            compressed_triggered = True

    # Verify compression was triggered
    assert compressed_triggered is True

    # Verify compression result
    db = real_mongodb

    # Check event count (should be ≤22 after compression + last interaction)
    event_count = await db.user_memory.count_documents({"user_id": user_id})
    assert event_count <= 22  # 20 kept + 2 new from last interaction

    # Check profile has summary
    profile = await db.user_profiles.find_one({"user_id": user_id})
    assert profile is not None
    assert profile.get("memory_summary") is not None
    assert len(profile["memory_summary"]) > 0

