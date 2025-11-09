"""Unit tests for dialog state machine.

Following TDD principles and testing best practices.
"""

import pytest
from src.domain.agents.state_machine import DialogState, DialogContext


class TestDialogState:
    """Test DialogState enum."""

    def test_idle_state_exists(self):
        """Test IDLE state exists."""
        assert DialogState.IDLE == DialogState("idle")

    def test_task_create_title_state_exists(self):
        """Test TASK_CREATE_TITLE state exists."""
        assert DialogState.TASK_CREATE_TITLE == DialogState("task_create_title")

    def test_task_create_desc_state_exists(self):
        """Test TASK_CREATE_DESC state exists."""
        assert DialogState.TASK_CREATE_DESC == DialogState("task_create_desc")

    def test_task_confirm_state_exists(self):
        """Test TASK_CONFIRM state exists."""
        assert DialogState.TASK_CONFIRM == DialogState("task_confirm")

    def test_data_collecting_state_exists(self):
        """Test DATA_COLLECTING state exists."""
        assert DialogState.DATA_COLLECTING == DialogState("data_collecting")

    def test_reminders_listing_state_exists(self):
        """Test REMINDERS_LISTING state exists."""
        assert DialogState.REMINDERS_LISTING == DialogState("reminders_listing")


class TestDialogContext:
    """Test DialogContext dataclass."""

    def test_create_context_with_required_fields(self):
        """Test creating context with required fields."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="user123",
            session_id="session456",
        )
        assert context.state == DialogState.IDLE
        assert context.user_id == "user123"
        assert context.session_id == "session456"
        assert context.data == {}
        assert context.step_count == 0

    def test_create_context_with_initial_data(self):
        """Test creating context with initial data."""
        initial_data = {"key": "value"}
        context = DialogContext(
            state=DialogState.TASK_CREATE_TITLE,
            user_id="user123",
            session_id="session456",
            data=initial_data,
        )
        assert context.data == initial_data

    def test_transition_to_new_state(self):
        """Test transitioning to a new state."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="user123",
            session_id="session456",
        )
        context.transition_to(DialogState.TASK_CREATE_TITLE)
        assert context.state == DialogState.TASK_CREATE_TITLE
        assert context.step_count == 1

    def test_multiple_transitions(self):
        """Test multiple state transitions."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="user123",
            session_id="session456",
        )
        context.transition_to(DialogState.TASK_CREATE_TITLE)
        context.transition_to(DialogState.TASK_CREATE_DESC)
        assert context.state == DialogState.TASK_CREATE_DESC
        assert context.step_count == 2

    def test_reset_clears_state_and_data(self):
        """Test reset clears state and data."""
        context = DialogContext(
            state=DialogState.TASK_CREATE_TITLE,
            user_id="user123",
            session_id="session456",
        )
        context.data["title"] = "My task"
        context.step_count = 5
        context.reset()
        assert context.state == DialogState.IDLE
        assert context.data == {}
        assert context.step_count == 0

    def test_update_data(self):
        """Test updating context data."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="user123",
            session_id="session456",
        )
        context.update_data("title", "My task")
        assert context.data["title"] == "My task"

    def test_update_data_multiple_keys(self):
        """Test updating multiple data keys."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="user123",
            session_id="session456",
        )
        context.update_data("title", "My task")
        context.update_data("deadline", "2025-01-30")
        assert context.data["title"] == "My task"
        assert context.data["deadline"] == "2025-01-30"

    def test_update_data_overwrites_existing(self):
        """Test updating data overwrites existing value."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="user123",
            session_id="session456",
        )
        context.update_data("title", "Old title")
        context.update_data("title", "New title")
        assert context.data["title"] == "New title"
        assert len(context.data) == 1
