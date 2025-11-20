"""Unit tests for UserMemoryEvent value object."""

from datetime import datetime
from uuid import UUID

import pytest

from src.domain.personalization.user_memory_event import UserMemoryEvent


def test_create_user_event():
    """Test user event creation."""
    event = UserMemoryEvent.create_user_event("123", "Hello!")

    assert event.user_id == "123"
    assert event.role == "user"
    assert event.content == "Hello!"
    assert isinstance(event.event_id, UUID)
    assert isinstance(event.created_at, datetime)
    assert event.tags == []


def test_create_assistant_event():
    """Test assistant event creation."""
    event = UserMemoryEvent.create_assistant_event("123", "Hi there!")

    assert event.user_id == "123"
    assert event.role == "assistant"
    assert event.content == "Hi there!"
    assert isinstance(event.event_id, UUID)
    assert isinstance(event.created_at, datetime)
    assert event.tags == []


def test_event_immutability():
    """Test that events are immutable."""
    event = UserMemoryEvent.create_user_event("123", "Hello")

    # Attempting to modify should raise AttributeError
    with pytest.raises(AttributeError):
        event.content = "Modified"  # type: ignore


def test_event_validation_empty_user_id():
    """Test validation fails with empty user_id."""
    with pytest.raises(ValueError, match="user_id cannot be empty"):
        UserMemoryEvent(
            event_id=UUID("00000000-0000-0000-0000-000000000001"),
            user_id="",
            role="user",
            content="Hello",
            created_at=datetime.utcnow(),
        )


def test_event_validation_empty_content():
    """Test validation fails with empty content."""
    with pytest.raises(ValueError, match="content cannot be empty"):
        UserMemoryEvent(
            event_id=UUID("00000000-0000-0000-0000-000000000001"),
            user_id="123",
            role="user",
            content="",
            created_at=datetime.utcnow(),
        )


def test_event_validation_invalid_role():
    """Test validation fails with invalid role."""
    with pytest.raises(ValueError, match="role must be 'user' or 'assistant'"):
        UserMemoryEvent(
            event_id=UUID("00000000-0000-0000-0000-000000000001"),
            user_id="123",
            role="invalid",  # type: ignore
            content="Hello",
            created_at=datetime.utcnow(),
        )


def test_event_uuid_uniqueness():
    """Test that factory methods generate unique UUIDs."""
    event1 = UserMemoryEvent.create_user_event("123", "Message 1")
    event2 = UserMemoryEvent.create_user_event("123", "Message 2")

    assert event1.event_id != event2.event_id


def test_event_with_tags():
    """Test event with tags."""
    event = UserMemoryEvent(
        event_id=UUID("00000000-0000-0000-0000-000000000001"),
        user_id="123",
        role="user",
        content="Hello",
        created_at=datetime.utcnow(),
        tags=["greeting", "test"],
    )

    assert event.tags == ["greeting", "test"]


def test_user_and_assistant_events_different():
    """Test that user and assistant events are distinct."""
    user_event = UserMemoryEvent.create_user_event("123", "Hello")
    assistant_event = UserMemoryEvent.create_assistant_event("123", "Hi")

    assert user_event.role == "user"
    assert assistant_event.role == "assistant"
    assert user_event.event_id != assistant_event.event_id


def test_event_timestamps():
    """Test that events have valid timestamps."""
    event = UserMemoryEvent.create_user_event("123", "Hello")

    assert isinstance(event.created_at, datetime)
    # Timestamp should be recent (within last minute)
    now = datetime.utcnow()
    time_diff = abs((now - event.created_at).total_seconds())
    assert time_diff < 60  # Less than 1 minute
