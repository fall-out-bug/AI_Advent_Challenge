"""Unit tests for Butler Orchestrator.

Following TDD principles and testing best practices.
"""

import pytest
from unittest.mock import AsyncMock, Mock

from src.domain.agents.butler_orchestrator import ButlerOrchestrator
from src.domain.agents.handlers.chat_handler import ChatHandler
from src.domain.agents.handlers.data_handler import DataHandler
from src.domain.agents.handlers.reminders_handler import RemindersHandler
from src.domain.agents.handlers.task_handler import TaskHandler
from src.domain.agents.services.mode_classifier import DialogMode, ModeClassifier
from src.domain.agents.state_machine import DialogContext, DialogState


class MockMongoDB:
    """Mock MongoDB database."""

    def __init__(self):
        self.dialog_contexts = MockCollection()
        self.dialogs = MockCollection()


class MockCollection:
    """Mock MongoDB collection."""

    def __init__(self):
        self._data = {}

    async def find_one(self, query: dict):
        """Mock find_one."""
        session_id = query.get("session_id")
        return self._data.get(session_id)

    async def update_one(self, query: dict, update: dict, upsert: bool = False):
        """Mock update_one."""
        session_id = query.get("session_id")
        doc = update.get("$set", {})
        if upsert or session_id in self._data:
            self._data[session_id] = doc


class TestButlerOrchestrator:
    """Test ButlerOrchestrator."""

    @pytest.fixture
    def mock_mode_classifier(self):
        """Create mock mode classifier."""
        classifier = Mock(spec=ModeClassifier)
        classifier.classify = AsyncMock(return_value=DialogMode.IDLE)
        return classifier

    @pytest.fixture
    def mock_handlers(self):
        """Create mock handlers."""
        return {
            "task": Mock(spec=TaskHandler),
            "data": Mock(spec=DataHandler),
            "reminders": Mock(spec=RemindersHandler),
            "chat": Mock(spec=ChatHandler),
        }

    @pytest.fixture
    def orchestrator(self, mock_mode_classifier, mock_handlers):
        """Create orchestrator instance."""
        mongodb = MockMongoDB()
        return ButlerOrchestrator(
            mode_classifier=mock_mode_classifier,
            task_handler=mock_handlers["task"],
            data_handler=mock_handlers["data"],
            reminders_handler=mock_handlers["reminders"],
            chat_handler=mock_handlers["chat"],
            mongodb=mongodb,
        )

    @pytest.mark.asyncio
    async def test_handle_user_message_creates_new_context(
        self, orchestrator, mock_mode_classifier, mock_handlers
    ):
        """Test handling message creates new context."""
        mock_mode_classifier.classify = AsyncMock(return_value=DialogMode.IDLE)
        mock_handlers["chat"].handle = AsyncMock(return_value="Hello!")
        response = await orchestrator.handle_user_message(
            user_id="123", message="Hi", session_id="456"
        )
        assert response == "Hello!"
        mock_handlers["chat"].handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_user_message_routes_to_task_handler(
        self, orchestrator, mock_mode_classifier, mock_handlers
    ):
        """Test routing to task handler."""
        mock_mode_classifier.classify = AsyncMock(return_value=DialogMode.TASK)
        mock_handlers["task"].handle = AsyncMock(return_value="Task created")
        response = await orchestrator.handle_user_message(
            user_id="123", message="Create task", session_id="456"
        )
        assert response == "Task created"
        mock_handlers["task"].handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_user_message_routes_to_data_handler(
        self, orchestrator, mock_mode_classifier, mock_handlers
    ):
        """Test routing to data handler."""
        mock_mode_classifier.classify = AsyncMock(return_value=DialogMode.DATA)
        mock_handlers["data"].handle = AsyncMock(return_value="Data here")
        response = await orchestrator.handle_user_message(
            user_id="123", message="Show data", session_id="456"
        )
        assert response == "Data here"
        mock_handlers["data"].handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_user_message_routes_to_reminders_handler(
        self, orchestrator, mock_mode_classifier, mock_handlers
    ):
        """Test routing to reminders handler."""
        mock_mode_classifier.classify = AsyncMock(return_value=DialogMode.REMINDERS)
        mock_handlers["reminders"].handle = AsyncMock(return_value="Reminders")
        response = await orchestrator.handle_user_message(
            user_id="123", message="Show reminders", session_id="456"
        )
        assert response == "Reminders"
        mock_handlers["reminders"].handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_user_message_saves_context(
        self, orchestrator, mock_mode_classifier, mock_handlers
    ):
        """Test context is saved after handling."""
        mock_mode_classifier.classify = AsyncMock(return_value=DialogMode.IDLE)
        mock_handlers["chat"].handle = AsyncMock(return_value="Hello!")
        await orchestrator.handle_user_message(
            user_id="123", message="Hi", session_id="456"
        )
        saved = await orchestrator.context_collection.find_one({"session_id": "456"})
        assert saved is not None
        assert saved["user_id"] == "123"

    @pytest.mark.asyncio
    async def test_handle_user_message_handles_exception(
        self, orchestrator, mock_mode_classifier
    ):
        """Test exception handling."""
        mock_mode_classifier.classify = AsyncMock(side_effect=Exception("Error"))
        response = await orchestrator.handle_user_message(
            user_id="123", message="Hi", session_id="456"
        )
        assert "error" in response.lower() or "sorry" in response.lower()

