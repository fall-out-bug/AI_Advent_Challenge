"""Unit tests for ButlerOrchestrator with DialogContextRepository interface.

Tests the new Clean Architecture implementation with dependency injection.
Uses mocks for all external dependencies.

Epic 21 · Stage 21_01a · Dialog Context Repository
"""

import pytest
from unittest.mock import AsyncMock

from src.domain.agents.butler_orchestrator import ButlerOrchestrator
from src.domain.agents.services.mode_classifier import DialogMode
from src.domain.agents.state_machine import DialogContext, DialogState
from src.domain.interfaces.dialog_context_repository import DialogContextRepository


@pytest.mark.epic21
@pytest.mark.stage_21_01
@pytest.mark.dialog_context
@pytest.mark.unit
class TestButlerOrchestratorWithRepository:
    """Unit tests for ButlerOrchestrator using DialogContextRepository interface."""

    @pytest.fixture
    def mock_repository(self):
        """Mock DialogContextRepository for testing."""
        return AsyncMock(spec=DialogContextRepository)

    @pytest.fixture
    def mock_handlers(self):
        """Mock handlers for testing."""
        return {
            "mode_classifier": AsyncMock(),
            "task_handler": AsyncMock(),
            "data_handler": AsyncMock(),
            "homework_handler": AsyncMock(),
            "chat_handler": AsyncMock(),
        }

    @pytest.fixture
    def orchestrator(self, mock_repository, mock_handlers):
        """Create ButlerOrchestrator with mocked dependencies."""
        return ButlerOrchestrator(
            mode_classifier=mock_handlers["mode_classifier"],
            task_handler=mock_handlers["task_handler"],
            data_handler=mock_handlers["data_handler"],
            homework_handler=mock_handlers["homework_handler"],
            chat_handler=mock_handlers["chat_handler"],
            dialog_context_repository=mock_repository,
        )

    async def test_get_or_create_context_creates_new_when_none_exists(
        self, orchestrator, mock_repository
    ):
        """Unit: Creates new context when repository returns None."""
        # Arrange
        mock_repository.get_by_session.return_value = None

        # Act
        context = await orchestrator._get_or_create_context("alice", "session_123")

        # Assert
        assert isinstance(context, DialogContext)
        assert context.user_id == "alice"
        assert context.session_id == "session_123"
        assert context.state == DialogState.IDLE
        assert context.data == {}
        assert context.step_count == 0

        mock_repository.get_by_session.assert_called_once_with("session_123")

    async def test_get_or_create_context_returns_existing_from_repository(
        self, orchestrator, mock_repository
    ):
        """Unit: Returns existing context from repository."""
        # Arrange
        existing_context = DialogContext(
            state=DialogState.TASK_CREATE_TITLE,
            user_id="bob",
            session_id="session_456",
            data={"task": "Buy milk"},
            step_count=2,
        )
        mock_repository.get_by_session.return_value = existing_context

        # Act
        context = await orchestrator._get_or_create_context("bob", "session_456")

        # Assert
        assert context is existing_context  # Should return exact same object
        mock_repository.get_by_session.assert_called_once_with("session_456")

    async def test_save_context_delegates_to_repository(
        self, orchestrator, mock_repository
    ):
        """Unit: Save context delegates to repository interface."""
        # Arrange
        context = DialogContext(
            state=DialogState.DATA_COLLECTING,
            user_id="charlie",
            session_id="session_789",
            data={"query": "weather"},
            step_count=1,
        )

        # Act
        await orchestrator._save_context(context)

        # Assert
        mock_repository.save.assert_called_once_with(context)

    async def test_handle_user_message_full_flow_with_new_session(
        self, orchestrator, mock_repository, mock_handlers
    ):
        """Unit: Full message handling flow for new session."""
        # Arrange
        mock_repository.get_by_session.return_value = None  # New session
        mock_handlers["mode_classifier"].classify.return_value = DialogMode.IDLE
        mock_handlers["chat_handler"].handle.return_value = "Hello! How can I help?"

        # Act
        response = await orchestrator.handle_user_message(
            user_id="diana", message="Hi there", session_id="session_new"
        )

        # Assert
        assert response == "Hello! How can I help?"

        # Verify repository calls
        mock_repository.get_by_session.assert_called_once_with("session_new")

        # Verify context was saved (should be called with new context)
        assert mock_repository.save.call_count == 1
        saved_context = mock_repository.save.call_args[0][0]
        assert saved_context.user_id == "diana"
        assert saved_context.session_id == "session_new"
        assert saved_context.state == DialogState.IDLE

        # Verify handlers were called
        mock_handlers["mode_classifier"].classify.assert_called_once_with("Hi there")
        mock_handlers["chat_handler"].handle.assert_called_once()

    async def test_handle_user_message_full_flow_with_existing_session(
        self, orchestrator, mock_repository, mock_handlers
    ):
        """Unit: Full message handling flow for existing session."""
        # Arrange
        existing_context = DialogContext(
            state=DialogState.TASK_CREATE_DESC,
            user_id="eve",
            session_id="session_existing",
            data={"title": "Buy groceries"},
            step_count=3,
        )
        mock_repository.get_by_session.return_value = existing_context
        mock_handlers["mode_classifier"].classify.return_value = DialogMode.TASK
        mock_handlers["task_handler"].handle.return_value = "Task updated successfully!"

        # Act
        response = await orchestrator.handle_user_message(
            user_id="eve", message="Add description", session_id="session_existing"
        )

        # Assert
        assert response == "Task updated successfully!"

        # Verify repository calls
        mock_repository.get_by_session.assert_called_once_with("session_existing")

        # Verify context was saved (updated existing)
        assert mock_repository.save.call_count == 1
        saved_context = mock_repository.save.call_args[0][0]
        assert saved_context is existing_context  # Same object

        # Verify handlers were called with existing context
        mock_handlers["mode_classifier"].classify.assert_called_once_with("Add description")
        mock_handlers["task_handler"].handle.assert_called_once()
        call_args = mock_handlers["task_handler"].handle.call_args
        assert call_args[0][0] is existing_context  # First arg is context
        assert call_args[0][1] == "Add description"  # Second arg is message

    async def test_handle_user_message_forces_mode_bypasses_classifier(
        self, orchestrator, mock_repository, mock_handlers
    ):
        """Unit: Forced mode bypasses classifier."""
        # Arrange
        mock_repository.get_by_session.return_value = None
        mock_handlers["data_handler"].handle.return_value = "Data collected!"

        # Act - Force DATA mode
        response = await orchestrator.handle_user_message(
            user_id="frank",
            message="Some message",
            session_id="session_force",
            force_mode=DialogMode.DATA
        )

        # Assert
        assert response == "Data collected!"

        # Verify classifier was NOT called
        mock_handlers["mode_classifier"].classify.assert_not_called()

        # Verify DATA handler was called (not IDLE/chat)
        mock_handlers["data_handler"].handle.assert_called_once()
        mock_handlers["chat_handler"].handle.assert_not_called()

    async def test_handle_user_message_unknown_mode_falls_back_to_chat(
        self, orchestrator, mock_repository, mock_handlers
    ):
        """Unit: Unknown mode falls back to chat handler."""
        # Arrange
        mock_repository.get_by_session.return_value = None
        mock_handlers["mode_classifier"].classify.return_value = "UNKNOWN_MODE"  # Invalid
        mock_handlers["chat_handler"].handle.return_value = "Fallback response"

        # Act
        response = await orchestrator.handle_user_message(
            user_id="grace", message="Hello", session_id="session_unknown"
        )

        # Assert
        assert response == "Fallback response"

        # Verify chat handler was used as fallback
        mock_handlers["chat_handler"].handle.assert_called_once()

    async def test_handle_user_message_error_returns_generic_message(
        self, orchestrator, mock_repository, mock_handlers
    ):
        """Unit: Errors during processing return generic error message."""
        # Arrange
        mock_repository.get_by_session.side_effect = Exception("Database error")

        # Act
        response = await orchestrator.handle_user_message(
            user_id="hank", message="Test", session_id="session_error"
        )

        # Assert
        assert response == "❌ Sorry, I encountered an error. Please try again."

        # Verify save was not called due to early error
        mock_repository.save.assert_not_called()
