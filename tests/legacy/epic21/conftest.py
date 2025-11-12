"""Test configuration for Epic 21 characterization tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any

from src.domain.agents.handlers.chat_handler import ChatHandler
from src.domain.agents.handlers.data_handler import DataHandler
from src.domain.agents.handlers.homework_handler import HomeworkHandler
from src.domain.agents.handlers.task_handler import TaskHandler
from src.domain.agents.services.mode_classifier import DialogMode, ModeClassifier


@pytest.fixture
async def butler_mock_mongodb():
    """Create in-memory mock MongoDB database for Epic 21 testing.

    This fixture maintains state between test operations, allowing
    characterization tests to verify actual persistence behavior.

    Returns:
        Mock AsyncIOMotorDatabase with in-memory dialog_contexts collection.
    """
    from unittest.mock import AsyncMock

    db = MagicMock()

    # In-memory storage for documents
    _storage: Dict[str, Dict[str, Any]] = {}

    # Mock dialog_contexts collection using AsyncMock for all methods
    dialog_contexts = MagicMock()

    async def find_one_mock(filter: Dict[str, Any]) -> Dict[str, Any] | None:
        """Find one document by session_id."""
        session_id = filter.get("session_id")
        if session_id and session_id in _storage:
            return _storage[session_id]
        return None

    async def insert_one_mock(doc: Dict[str, Any]) -> MagicMock:
        """Insert new document."""
        session_id = doc.get("session_id")
        if session_id:
            _storage[session_id] = doc.copy()
        result = MagicMock()
        result.inserted_id = f"mock_id_{session_id}"
        return result

    async def update_one_mock(filter: Dict[str, Any], update: Dict[str, Any], **kwargs) -> MagicMock:
        """Update existing document with upsert support."""
        session_id = filter.get("session_id")
        if session_id:
            # Handle upsert=True case (create if doesn't exist)
            if kwargs.get("upsert", False) or session_id in _storage:
                if "$set" in update:
                    if session_id not in _storage:
                        _storage[session_id] = {}
                    _storage[session_id].update(update["$set"])

        result = MagicMock()
        result.modified_count = 1 if session_id in _storage else 0
        return result

    async def count_documents_mock(filter: Dict[str, Any]) -> int:
        """Count documents matching filter."""
        session_id = filter.get("session_id")
        if session_id:
            return 1 if session_id in _storage else 0
        return len(_storage)

    async def delete_one_mock(filter: Dict[str, Any]) -> MagicMock:
        """Delete one document."""
        session_id = filter.get("session_id")
        if session_id and session_id in _storage:
            del _storage[session_id]

        result = MagicMock()
        result.deleted_count = 1 if session_id in _storage else 0
        return result

    # Configure the mock to use async methods
    dialog_contexts.configure_mock(**{
        'find_one': AsyncMock(side_effect=find_one_mock),
        'insert_one': AsyncMock(side_effect=insert_one_mock),
        'update_one': AsyncMock(side_effect=update_one_mock),
        'delete_one': AsyncMock(side_effect=delete_one_mock),
        'count_documents': AsyncMock(side_effect=count_documents_mock),
    })

    db.dialog_contexts = dialog_contexts

    # Clear storage between tests
    _storage.clear()

    return db


@pytest.fixture
def sample_handlers():
    """Provide mock handlers for ButlerOrchestrator tests.

    Returns:
        Dict with mock instances of all required handlers and classifier.
    """
    return {
        "mode_classifier": AsyncMock(spec=ModeClassifier),
        "task_handler": AsyncMock(spec=TaskHandler),
        "data_handler": AsyncMock(spec=DataHandler),
        "homework_handler": AsyncMock(spec=HomeworkHandler),
        "chat_handler": AsyncMock(spec=ChatHandler),
    }


@pytest.fixture
def mock_mode_classifier():
    """Mock mode classifier for testing."""
    classifier = AsyncMock(spec=ModeClassifier)
    classifier.classify.return_value = DialogMode.IDLE
    return classifier


@pytest.fixture
def mock_chat_handler():
    """Mock chat handler for testing."""
    handler = AsyncMock(spec=ChatHandler)
    handler.handle.return_value = "Mock chat response"
    return handler


@pytest.fixture
def mock_task_handler():
    """Mock task handler for testing."""
    handler = AsyncMock(spec=TaskHandler)
    handler.handle.return_value = "Mock task response"
    return handler


@pytest.fixture
def mock_data_handler():
    """Mock data handler for testing."""
    handler = AsyncMock(spec=DataHandler)
    handler.handle.return_value = "Mock data response"
    return handler


@pytest.fixture
def mock_homework_handler():
    """Mock homework handler for testing."""
    handler = AsyncMock(spec=HomeworkHandler)
    handler.handle.return_value = "Mock homework response"
    return handler
