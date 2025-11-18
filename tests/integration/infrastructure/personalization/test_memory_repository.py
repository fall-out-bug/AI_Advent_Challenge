"""Integration tests for MongoUserMemoryRepository."""

import pytest

from src.domain.personalization.user_memory_event import UserMemoryEvent


@pytest.mark.asyncio
async def test_append_and_get_events(memory_repo):
    """Test appending and retrieving events."""
    user_id = "test_user_123"

    # Create events
    events = [
        UserMemoryEvent.create_user_event(user_id, "Hello"),
        UserMemoryEvent.create_assistant_event(user_id, "Hi there!"),
    ]

    # Append
    await memory_repo.append_events(events)

    # Retrieve
    retrieved = await memory_repo.get_recent_events(user_id, limit=10)

    assert len(retrieved) == 2
    assert retrieved[0].role == "user"
    assert retrieved[0].content == "Hello"
    assert retrieved[1].role == "assistant"
    assert retrieved[1].content == "Hi there!"


@pytest.mark.asyncio
async def test_get_recent_events_chronological_order(memory_repo):
    """Test that events are returned in chronological order."""
    user_id = "test_user_order"

    # Create events with delays to ensure different timestamps
    events = [
        UserMemoryEvent.create_user_event(user_id, f"Message {i}") for i in range(5)
    ]

    await memory_repo.append_events(events)

    # Retrieve
    retrieved = await memory_repo.get_recent_events(user_id, limit=10)

    # Verify chronological order (oldest first)
    assert len(retrieved) == 5
    for i, event in enumerate(retrieved):
        assert f"Message {i}" in event.content


@pytest.mark.asyncio
async def test_get_recent_events_respects_limit(memory_repo):
    """Test that get_recent_events respects limit parameter."""
    user_id = "test_user_limit"

    # Create 10 events
    events = [
        UserMemoryEvent.create_user_event(user_id, f"Message {i}") for i in range(10)
    ]

    await memory_repo.append_events(events)

    # Retrieve with limit 5
    retrieved = await memory_repo.get_recent_events(user_id, limit=5)

    # Should return only 5 most recent
    assert len(retrieved) == 5
    # Should be the last 5 messages
    assert "Message 5" in retrieved[0].content
    assert "Message 9" in retrieved[4].content


@pytest.mark.asyncio
async def test_count_events(memory_repo):
    """Test counting events."""
    user_id = "test_user_count"

    # Initial count should be 0
    count = await memory_repo.count_events(user_id)
    assert count == 0

    # Add events
    events = [
        UserMemoryEvent.create_user_event(user_id, f"Message {i}") for i in range(5)
    ]
    await memory_repo.append_events(events)

    # Count should be 5
    count = await memory_repo.count_events(user_id)
    assert count == 5


@pytest.mark.asyncio
async def test_compress_memory(memory_repo):
    """Test memory compression."""
    user_id = "test_user_compress"

    # Create 30 events
    events = [
        UserMemoryEvent.create_user_event(user_id, f"Message {i}") for i in range(30)
    ]
    await memory_repo.append_events(events)

    # Compress: keep last 10
    await memory_repo.compress(user_id, "Summary of old messages", keep_last_n=10)

    # Verify only 10 remain
    count = await memory_repo.count_events(user_id)
    assert count == 10

    # Verify recent events are kept
    recent = await memory_repo.get_recent_events(user_id, limit=20)
    assert len(recent) == 10
    # Should be messages 20-29
    assert "Message 20" in recent[0].content
    assert "Message 29" in recent[9].content


@pytest.mark.asyncio
async def test_compress_no_compression_needed(memory_repo):
    """Test compression when event count is below threshold."""
    user_id = "test_user_no_compress"

    # Create 5 events (below keep_last_n=10)
    events = [
        UserMemoryEvent.create_user_event(user_id, f"Message {i}") for i in range(5)
    ]
    await memory_repo.append_events(events)

    # Compress: keep last 10 (more than we have)
    await memory_repo.compress(user_id, "Summary", keep_last_n=10)

    # All events should remain
    count = await memory_repo.count_events(user_id)
    assert count == 5


@pytest.mark.asyncio
async def test_append_empty_events_list(memory_repo):
    """Test that appending empty list does nothing."""
    user_id = "test_user_empty"

    # Append empty list
    await memory_repo.append_events([])

    # Count should still be 0
    count = await memory_repo.count_events(user_id)
    assert count == 0


@pytest.mark.asyncio
async def test_multiple_users_isolated(memory_repo):
    """Test that events from different users are isolated."""
    user_id_1 = "test_user_1"
    user_id_2 = "test_user_2"

    # Create events for user 1
    events_1 = [UserMemoryEvent.create_user_event(user_id_1, "User 1 message")]
    await memory_repo.append_events(events_1)

    # Create events for user 2
    events_2 = [UserMemoryEvent.create_user_event(user_id_2, "User 2 message")]
    await memory_repo.append_events(events_2)

    # Retrieve for user 1
    retrieved_1 = await memory_repo.get_recent_events(user_id_1, limit=10)
    assert len(retrieved_1) == 1
    assert retrieved_1[0].content == "User 1 message"

    # Retrieve for user 2
    retrieved_2 = await memory_repo.get_recent_events(user_id_2, limit=10)
    assert len(retrieved_2) == 1
    assert retrieved_2[0].content == "User 2 message"
