"""Unit tests for MemorySlice value object."""

from src.domain.personalization.memory_slice import MemorySlice
from src.domain.personalization.user_memory_event import UserMemoryEvent


def test_memory_slice_with_events():
    """Test memory slice with events."""
    events = [
        UserMemoryEvent.create_user_event("123", "Hello"),
        UserMemoryEvent.create_assistant_event("123", "Hi there!"),
    ]

    slice_obj = MemorySlice(events=events)

    assert len(slice_obj.events) == 2
    assert slice_obj.summary is None
    assert slice_obj.total_events == 0


def test_memory_slice_with_summary():
    """Test memory slice with summary."""
    events = [UserMemoryEvent.create_user_event("123", "Hello")]
    summary = "Previous conversation about Python"

    slice_obj = MemorySlice(events=events, summary=summary, total_events=10)

    assert slice_obj.summary == summary
    assert slice_obj.total_events == 10


def test_to_prompt_context_with_events():
    """Test to_prompt_context() formatting with events."""
    events = [
        UserMemoryEvent.create_user_event("123", "Hello"),
        UserMemoryEvent.create_assistant_event("123", "Hi there!"),
    ]

    slice_obj = MemorySlice(events=events)
    context = slice_obj.to_prompt_context()

    assert "Recent interactions:" in context
    assert "User: Hello" in context
    assert "Butler: Hi there!" in context


def test_to_prompt_context_with_summary():
    """Test to_prompt_context() includes summary."""
    events = [UserMemoryEvent.create_user_event("123", "Hello")]
    summary = "Previous conversation about Python"

    slice_obj = MemorySlice(events=events, summary=summary)
    context = slice_obj.to_prompt_context()

    assert "Summary: Previous conversation about Python" in context
    assert "Recent interactions:" in context


def test_to_prompt_context_empty_events():
    """Test to_prompt_context() with empty events list."""
    slice_obj = MemorySlice(events=[])
    context = slice_obj.to_prompt_context()

    assert context == ""


def test_to_prompt_context_empty_with_summary():
    """Test to_prompt_context() with only summary, no events."""
    slice_obj = MemorySlice(events=[], summary="Previous chat")
    context = slice_obj.to_prompt_context()

    assert "Summary: Previous chat" in context
    assert "Recent interactions:" not in context


def test_to_prompt_context_max_events():
    """Test to_prompt_context() respects max_events parameter."""
    # Create 15 events
    events = [
        UserMemoryEvent.create_user_event("123", f"Message {i}") for i in range(15)
    ]

    slice_obj = MemorySlice(events=events)
    context = slice_obj.to_prompt_context(max_events=5)

    # Should only include last 5 events
    assert "Message 10" in context
    assert "Message 14" in context
    assert "Message 0" not in context
    assert "Message 5" not in context


def test_to_prompt_context_truncates_long_messages():
    """Test to_prompt_context() truncates long message content."""
    long_message = "A" * 300  # 300 characters
    events = [UserMemoryEvent.create_user_event("123", long_message)]

    slice_obj = MemorySlice(events=events)
    context = slice_obj.to_prompt_context()

    # Should truncate to 200 chars + "..."
    assert len([line for line in context.split("\n") if "User:" in line][0]) < 250
    assert "..." in context


def test_to_prompt_context_role_labels():
    """Test to_prompt_context() uses correct role labels."""
    events = [
        UserMemoryEvent.create_user_event("123", "User message"),
        UserMemoryEvent.create_assistant_event("123", "Assistant reply"),
    ]

    slice_obj = MemorySlice(events=events)
    context = slice_obj.to_prompt_context()

    assert "User: User message" in context
    assert "Butler: Assistant reply" in context


def test_memory_slice_total_events():
    """Test total_events field for metrics."""
    events = [UserMemoryEvent.create_user_event("123", "Hello")]
    slice_obj = MemorySlice(events=events, total_events=50)

    assert slice_obj.total_events == 50
    assert len(slice_obj.events) == 1  # Only recent events in slice
