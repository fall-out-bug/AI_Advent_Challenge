"""Integration tests for reset personalization flow."""

import pytest

from src.application.personalization.dtos import ResetPersonalizationInput
from src.domain.personalization.user_memory_event import UserMemoryEvent


@pytest.mark.asyncio
async def test_reset_personalization_flow(
    reset_use_case, profile_repo, memory_repo
):
    """Test reset clears profile and memory."""
    user_id = "test_user_reset_123"

    # Create profile and memory
    profile = await profile_repo.get(user_id)
    events = [
        UserMemoryEvent.create_user_event(user_id, "Message 1"),
        UserMemoryEvent.create_assistant_event(user_id, "Reply 1"),
    ]
    await memory_repo.append_events(events)

    # Verify data exists
    event_count_before = await memory_repo.count_events(user_id)
    assert event_count_before == 2

    # Reset
    input_data = ResetPersonalizationInput(user_id=user_id)
    output = await reset_use_case.execute(input_data)

    # Verify reset succeeded
    assert output.success is True
    assert output.profile_reset is True
    assert output.memory_deleted_count == 2

    # Verify memory is cleared
    event_count_after = await memory_repo.count_events(user_id)
    assert event_count_after == 0

    # Verify profile is reset to defaults
    reset_profile = await profile_repo.get(user_id)
    assert reset_profile.user_id == user_id
    assert reset_profile.persona == "Alfred-style дворецкий"
    assert reset_profile.memory_summary is None


@pytest.mark.asyncio
async def test_reset_with_no_memory(reset_use_case, profile_repo):
    """Test reset when user has no memory."""
    user_id = "test_user_reset_empty_456"

    # Create profile only
    await profile_repo.get(user_id)

    # Reset
    input_data = ResetPersonalizationInput(user_id=user_id)
    output = await reset_use_case.execute(input_data)

    # Verify reset succeeded
    assert output.success is True
    assert output.memory_deleted_count == 0
