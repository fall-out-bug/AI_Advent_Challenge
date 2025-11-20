"""Tests for Dialog Manager.

Following TDD approach: tests written BEFORE implementation (Red phase).
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.infrastructure.dialogs.dialog_manager import DialogManager
from src.infrastructure.dialogs.schemas import DialogMessage


@pytest.mark.asyncio
class TestDialogManager:
    """Test suite for DialogManager."""

    async def test_add_message_success(self, mock_mongodb):
        """Test adding message successfully.

        Args:
            mock_mongodb: Mock MongoDB fixture
        """
        # Arrange
        session_id = "test_session_123"
        role = "user"
        content = "Test message"

        # Act
        manager = DialogManager(mongodb=mock_mongodb)
        await manager.add_message(session_id, role, content)

        # Assert
        assert mock_mongodb.dialogs.update_one.called

    async def test_get_context_empty_history(self, mock_mongodb):
        """Test getting context from empty history.

        Args:
            mock_mongodb: Mock MongoDB fixture
        """
        # Arrange
        session_id = "test_session_123"
        mock_mongodb.dialogs.find_one.return_value = None

        # Act
        manager = DialogManager(mongodb=mock_mongodb)
        context = await manager.get_context(session_id)

        # Assert
        assert context == ""

    async def test_get_context_with_messages(self, mock_mongodb, sample_dialog_history):
        """Test getting context with existing messages.

        Args:
            mock_mongodb: Mock MongoDB fixture
            sample_dialog_history: Sample dialog history fixture
        """
        # Arrange
        session_id = "test_session_123"
        mock_mongodb.dialogs.find_one = AsyncMock(
            return_value={
                "session_id": session_id,
                "messages": sample_dialog_history,
                "token_count": 29,
            }
        )

        # Act
        manager = DialogManager(mongodb=mock_mongodb)
        context = await manager.get_context(session_id)

        # Assert
        assert len(context) > 0
        assert "user" in context.lower() or "assistant" in context.lower()

    async def test_should_compress_under_limit(self, mock_mongodb):
        """Test compression check when under token limit.

        Args:
            mock_mongodb: Mock MongoDB fixture
        """
        # Arrange
        session_id = "test_session_123"
        mock_mongodb.dialogs.find_one = AsyncMock(
            return_value={"session_id": session_id, "token_count": 5000}
        )

        # Act
        manager = DialogManager(mongodb=mock_mongodb)
        should_compress = await manager._should_compress(session_id)

        # Assert
        assert should_compress is False

    async def test_should_compress_over_limit(self, mock_mongodb):
        """Test compression check when over token limit.

        Args:
            mock_mongodb: Mock MongoDB fixture
        """
        # Arrange
        session_id = "test_session_123"
        mock_mongodb.dialogs.find_one = AsyncMock(
            return_value={"session_id": session_id, "token_count": 9000}
        )

        # Act
        manager = DialogManager(mongodb=mock_mongodb)
        should_compress = await manager._should_compress(session_id)

        # Assert
        assert should_compress is True

    async def test_compress_history(
        self, mock_mongodb, mock_llm_client, sample_dialog_history
    ):
        """Test history compression.

        Args:
            mock_mongodb: Mock MongoDB fixture
            mock_llm_client: Mock LLM client fixture
            sample_dialog_history: Sample dialog history fixture
        """
        # Arrange
        from shared_package.clients.base_client import ModelResponse

        session_id = "test_session_123"
        mock_llm_client.make_request = AsyncMock(
            return_value=ModelResponse(
                response="Summary: User asked for digest, agent provided it",
                response_tokens=20,
                input_tokens=50,
                total_tokens=70,
                model_name="mistral",
                response_time=1.0,
            )
        )

        # Setup mocks for compression flow
        async def fetch_messages(*args, **kwargs):
            return [
                DialogMessage(**msg) for msg in sample_dialog_history * 15
            ]  # 45 messages

        manager = DialogManager(mongodb=mock_mongodb, llm_client=mock_llm_client)
        manager._fetch_from_mongo = AsyncMock(side_effect=fetch_messages)

        # Act
        await manager._compress_history(session_id)

        # Assert
        assert mock_mongodb.dialogs.update_one.called
        update_call = mock_mongodb.dialogs.update_one.call_args
        assert "$set" in update_call[0][1]

    async def test_get_context_respects_token_limit(
        self, mock_mongodb, sample_dialog_history
    ):
        """Test that context respects token limit.

        Args:
            mock_mongodb: Mock MongoDB fixture
            sample_dialog_history: Sample dialog history fixture
        """
        # Arrange
        session_id = "test_session_123"
        # Create history with many messages exceeding limit
        large_history = sample_dialog_history * 100  # 300 messages
        mock_mongodb.dialogs.find_one = AsyncMock(
            return_value={
                "session_id": session_id,
                "messages": large_history,
                "token_count": 2900,
            }
        )

        # Act
        manager = DialogManager(mongodb=mock_mongodb)
        context = await manager.get_context(session_id, max_tokens=1000)

        # Assert
        # Estimate tokens in context
        estimated_tokens = manager._estimate_tokens(context)
        assert estimated_tokens <= 1000
