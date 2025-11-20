"""Integration tests for ButlerOrchestrator with DialogContextRepository.

Tests the full integration with MongoDB through repository implementations.
Uses in-memory mock MongoDB for isolated testing.

Epic 21 · Stage 21_01a · Dialog Context Repository
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.agents.butler_orchestrator import ButlerOrchestrator
from src.domain.agents.services.mode_classifier import DialogMode
from src.domain.agents.state_machine import DialogContext, DialogState
from src.infrastructure.di.container import LegacyDialogContextAdapter
from src.infrastructure.repositories.mongo_dialog_context_repository import (
    MongoDialogContextRepository,
)


@pytest.mark.epic21
@pytest.mark.stage_21_01
@pytest.mark.dialog_context
@pytest.mark.integration
class TestButlerOrchestratorWithRepositoryIntegration:
    """Integration tests for ButlerOrchestrator with repository implementations."""

    @pytest.fixture
    def mock_mongodb(self):
        """Create in-memory mock MongoDB for testing."""
        mock_db = MagicMock()
        _storage = {}

        # Mock dialog_contexts collection
        dialog_contexts = MagicMock()

        async def find_one_mock(filter):
            session_id = filter.get("session_id")
            if session_id and session_id in _storage:
                return _storage[session_id].copy()  # Return copy to avoid mutations
            return None

        async def update_one_mock(filter, update, **kwargs):
            session_id = filter.get("session_id")
            if session_id:
                if "$set" in update:
                    if session_id not in _storage:
                        _storage[session_id] = {}
                    _storage[session_id].update(update["$set"])

        async def delete_one_mock(filter):
            session_id = filter.get("session_id")
            if session_id and session_id in _storage:
                del _storage[session_id]

        dialog_contexts.find_one = find_one_mock
        dialog_contexts.update_one = update_one_mock
        dialog_contexts.delete_one = delete_one_mock

        mock_db.dialog_contexts = dialog_contexts
        return mock_db

    @pytest.fixture
    def mongo_repo(self, mock_mongodb):
        """Create MongoDB repository with mock database."""
        # Override collection methods with async versions for MongoDB repo
        collection = mock_mongodb.dialog_contexts

        async def async_find_one(filter):
            return collection.find_one(filter)

        async def async_update_one(filter, update, **kwargs):
            return collection.update_one(filter, update, **kwargs)

        collection.find_one = async_find_one
        collection.update_one = async_update_one

        return MongoDialogContextRepository(mock_mongodb)

    @pytest.fixture
    def legacy_adapter(self, mock_mongodb):
        """Create legacy adapter with mock database."""
        return LegacyDialogContextAdapter(mock_mongodb)

    @pytest.fixture
    def orchestrator_with_mongo(self, mongo_repo):
        """Create ButlerOrchestrator with MongoDB repository."""
        # Create mock handlers
        mode_classifier = AsyncMock()
        mode_classifier.classify.return_value = DialogMode.IDLE

        chat_handler = AsyncMock()
        chat_handler.handle.return_value = "Response from MongoDB integration!"

        task_handler = AsyncMock()
        data_handler = AsyncMock()
        homework_handler = AsyncMock()

        return ButlerOrchestrator(
            mode_classifier=mode_classifier,
            task_handler=task_handler,
            data_handler=data_handler,
            homework_handler=homework_handler,
            chat_handler=chat_handler,
            dialog_context_repository=mongo_repo,
        )

    async def test_integration_mongo_repository_new_session(
        self, orchestrator_with_mongo, mongo_repo
    ):
        """Integration: MongoDB repository works for new session."""
        # Act - Handle message for new session
        response = await orchestrator_with_mongo.handle_user_message(
            user_id="mongo_user",
            message="Hello MongoDB test",
            session_id="mongo_session_new",
        )

        # Assert
        assert response == "Response from MongoDB integration!"

        # Verify context was saved in repository
        saved_context = await mongo_repo.get_by_session("mongo_session_new")

        assert saved_context is not None
        assert saved_context.user_id == "mongo_user"
        assert saved_context.session_id == "mongo_session_new"
        assert saved_context.state == DialogState.IDLE
        assert saved_context.data == {}
        assert saved_context.step_count == 0

    async def test_integration_mongo_repository_existing_session(self, mongo_repo):
        """Integration: MongoDB repository works for existing session."""
        # Arrange - Pre-populate context
        existing_context = DialogContext(
            state=DialogState.TASK_CREATE_DESC,
            user_id="existing_mongo_user",
            session_id="existing_mongo_session",
            data={"title": "MongoDB integration task"},
            step_count=3,
        )
        await mongo_repo.save(existing_context)

        # Create orchestrator
        mode_classifier = AsyncMock()
        mode_classifier.classify.return_value = DialogMode.TASK

        task_handler = AsyncMock()
        task_handler.handle.return_value = "Task updated via MongoDB!"

        orchestrator = ButlerOrchestrator(
            mode_classifier=mode_classifier,
            task_handler=task_handler,
            data_handler=AsyncMock(),
            homework_handler=AsyncMock(),
            chat_handler=AsyncMock(),
            dialog_context_repository=mongo_repo,
        )

        # Act - Handle message for existing session
        response = await orchestrator.handle_user_message(
            user_id="existing_mongo_user",
            message="Update task description",
            session_id="existing_mongo_session",
        )

        # Assert
        assert response == "Task updated via MongoDB!"

        # Verify context was loaded and updated
        updated_context = await mongo_repo.get_by_session("existing_mongo_session")
        assert updated_context is not None
        assert updated_context.user_id == "existing_mongo_user"
        assert updated_context.session_id == "existing_mongo_session"
        assert updated_context.state == DialogState.TASK  # Updated by orchestrator
        assert updated_context.data == {"title": "MongoDB integration task"}
        assert updated_context.step_count == 3

    async def test_integration_legacy_adapter_compatibility(self, legacy_adapter):
        """Integration: Legacy adapter provides same interface."""
        # Test get_by_session (returns None for new session)
        context = await legacy_adapter.get_by_session("legacy_test_session")
        assert context is None

        # Test save
        test_context = DialogContext(
            state=DialogState.DATA_COLLECTING,
            user_id="legacy_test_user",
            session_id="legacy_test_session",
            data={"homework": "legacy adapter test"},
            step_count=5,
        )
        await legacy_adapter.save(test_context)

        # Test get_by_session (returns saved context)
        saved_context = await legacy_adapter.get_by_session("legacy_test_session")
        assert saved_context is not None
        assert saved_context.state == DialogState.DATA_COLLECTING
        assert saved_context.user_id == "legacy_test_user"
        assert saved_context.data == {"homework": "legacy adapter test"}
        assert saved_context.step_count == 5

        # Test delete
        await legacy_adapter.delete("legacy_test_session")
        deleted_context = await legacy_adapter.get_by_session("legacy_test_session")
        assert deleted_context is None
