"""Integration tests for homework review workflow.

Testing full flow: message → orchestrator → handler → MCP tools → response.
"""

import base64
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
from pathlib import Path

from src.presentation.bot.orchestrator import ButlerOrchestrator
from src.application.dtos.butler_dialog_dtos import DialogContext, DialogMode, DialogState
from src.application.services.mode_classifier import ModeClassifier
from src.infrastructure.hw_checker.client import HWCheckerClient
from src.application.use_cases.list_homework_submissions import (
    ListHomeworkSubmissionsUseCase,
)
from src.application.use_cases.review_homework_use_case import ReviewHomeworkUseCase
from src.presentation.bot.handlers.homework import HomeworkHandler


@pytest.fixture
def mock_hw_checker_client():
    """Create mock HW Checker client."""
    client = MagicMock(spec=HWCheckerClient)
    return client


@pytest.fixture
def mock_tool_client():
    """Create mock MCP tool client."""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    client = AsyncMock()
    return client


@pytest.fixture
def homework_handler(mock_hw_checker_client, mock_tool_client):
    """Create HomeworkHandler instance."""
    list_uc = ListHomeworkSubmissionsUseCase(homework_checker=mock_hw_checker_client)
    review_uc = ReviewHomeworkUseCase(
        homework_checker=mock_hw_checker_client,
        tool_client=mock_tool_client,
    )
    return HomeworkHandler(list_use_case=list_uc, review_use_case=review_uc)


@pytest.fixture
def mode_classifier(mock_llm_client):
    """Create ModeClassifier instance."""
    return ModeClassifier(llm_client=mock_llm_client, default_model="mistral")


@pytest.fixture
def orchestrator(mode_classifier, homework_handler):
    """Create ButlerOrchestrator with mocked dependencies."""
    from src.presentation.bot.handlers.chat import ChatHandler
    from src.presentation.bot.handlers.data import DataHandler
    from src.presentation.bot.handlers.task import TaskHandler
    from motor.motor_asyncio import AsyncIOMotorDatabase

    # Create minimal mocks for other handlers
    mock_chat = MagicMock(spec=ChatHandler)
    mock_chat.handle = AsyncMock(return_value="Chat response")

    mock_data = MagicMock(spec=DataHandler)
    mock_data.handle = AsyncMock(return_value="Data response")

    mock_task = MagicMock(spec=TaskHandler)
    mock_task.handle = AsyncMock(return_value="Task response")

    mock_db = MagicMock(spec=AsyncIOMotorDatabase)
    mock_db.dialog_contexts = MagicMock()
    mock_db.dialog_contexts.find_one = AsyncMock(return_value=None)
    mock_db.dialog_contexts.update_one = AsyncMock()

    return ButlerOrchestrator(
        mode_classifier=mode_classifier,
        task_handler=mock_task,
        data_handler=mock_data,
        homework_handler=homework_handler,
        chat_handler=mock_chat,
        mongodb=mock_db,
    )


@pytest.mark.asyncio
class TestHomeworkReviewFlow:
    """Test suite for full homework review workflow."""

    async def test_list_homeworks_flow(
        self, orchestrator, mode_classifier, mock_hw_checker_client
    ):
        """Test full flow for listing homeworks."""
        # Arrange
        mock_response = {
            "commits": [
                {
                    "commit_hash": "abc123def456",
                    "archive_name": "Иванов_Иван_hw2.zip",
                    "commit_dttm": "2024-11-02T16:00:00",
                    "assignment": "HW2",
                    "status": "passed",
                }
            ],
            "total": 1,
        }
        mock_hw_checker_client.get_recent_commits = AsyncMock(
            return_value=mock_response
        )
        mode_classifier.classify = AsyncMock(return_value=DialogMode.HOMEWORK_REVIEW)

        # Act
        response = await orchestrator.handle_user_message(
            user_id="123", message="Покажи домашки", session_id="test_session"
        )

        # Assert
        assert "📚 Домашки" in response
        assert "Иванов\\_Иван\\_hw2.zip" in response
        mock_hw_checker_client.get_recent_commits.assert_called_once()

    async def test_review_homework_flow(
        self, orchestrator, mode_classifier, mock_hw_checker_client, mock_tool_client
    ):
        """Test full flow for reviewing homework."""
        # Arrange
        commit_hash = "abc123def456"
        archive_content = b"PK\x03\x04fake zip content"
        markdown_report = "# Code Review Report\n\n## Summary\n\nTest review content."

        mock_hw_checker_client.download_archive = AsyncMock(
            return_value=archive_content
        )
        mock_tool_client.call_tool = AsyncMock(
            return_value={
                "success": True,
                "markdown_report": markdown_report,
                "session_id": "test_session",
                "total_findings": 5,
                "detected_components": [],
                "pass_2_components": [],
                "execution_time_seconds": 2.1,
            }
        )
        mode_classifier.classify = AsyncMock(return_value=DialogMode.HOMEWORK_REVIEW)

        # Act
        response = await orchestrator.handle_user_message(
            user_id="123",
            message=f"Сделай ревью {commit_hash}",
            session_id="test_session",
        )

        # Assert
        assert response.startswith("FILE:")
        assert "review_" in response
        assert commit_hash[:12] in response

        # Verify file content
        parts = response[5:].split(":", 1)
        assert len(parts) == 2
        filename = parts[0]
        content_b64 = parts[1]
        decoded_content = base64.b64decode(content_b64).decode("utf-8")
        assert decoded_content == markdown_report
        assert filename.endswith(".md")

        mock_hw_checker_client.download_archive.assert_called_once_with(commit_hash)
        mock_tool_client.call_tool.assert_called_once()

    async def test_review_homework_mode_classification(
        self, orchestrator, mode_classifier
    ):
        """Test that review command is classified as HOMEWORK_REVIEW mode."""
        # Arrange
        test_messages = [
            "Сделай ревью abc123",
            "Покажи домашки",
            "ревью def456",
            "Покажи домашк",
        ]

        # Act & Assert
        for message in test_messages:
            mode = await mode_classifier.classify(message)
            assert mode == DialogMode.HOMEWORK_REVIEW, f"Failed for: {message}"

    async def test_review_homework_error_handling(
        self, orchestrator, mode_classifier, mock_hw_checker_client
    ):
        """Test error handling in review flow."""
        # Arrange
        commit_hash = "abc1234"
        from httpx import HTTPStatusError, Response

        mock_response = MagicMock(spec=Response)
        error = HTTPStatusError("404", request=MagicMock(), response=mock_response)
        mock_hw_checker_client.download_archive = AsyncMock(side_effect=error)
        mode_classifier.classify = AsyncMock(return_value=DialogMode.HOMEWORK_REVIEW)

        # Act
        response = await orchestrator.handle_user_message(
            user_id="123",
            message=f"Сделай ревью {commit_hash}",
            session_id="test_session",
        )

        # Assert
        assert "❌" in response
        assert "ошибка при ревью" in response.lower()

    async def test_list_homeworks_with_assignment_filter(
        self, orchestrator, mode_classifier, mock_hw_checker_client
    ):
        """Test listing homeworks with assignment filter."""
        # Arrange
        mock_response = {
            "commits": [
                {
                    "commit_hash": "abc123",
                    "archive_name": "test_hw2.zip",
                    "commit_dttm": "2024-11-02T16:00:00",
                    "assignment": "HW2",
                    "status": "passed",
                }
            ],
            "total": 1,
        }
        mock_hw_checker_client.get_recent_commits = AsyncMock(
            return_value=mock_response
        )
        mode_classifier.classify = AsyncMock(return_value=DialogMode.HOMEWORK_REVIEW)

        # Act
        response = await orchestrator.handle_user_message(
            user_id="123",
            message="Покажи домашки за 3 дня",
            session_id="test_session",
        )

        # Assert
        assert "3 дней" in response
        # Verify days parameter was passed
        call_args = mock_hw_checker_client.get_recent_commits.call_args
        assert call_args[1]["days"] == 3

    async def test_review_homework_temp_file_cleanup(
        self,
        orchestrator,
        mode_classifier,
        mock_hw_checker_client,
        mock_tool_client,
        homework_handler,
    ):
        """Test that temp file is properly cleaned up."""
        # Arrange
        commit_hash = "abc1234"
        archive_content = b"PK\x03\x04fake zip"
        markdown_report = "# Review Report\n\nTest"

        mock_hw_checker_client.download_archive = AsyncMock(
            return_value=archive_content
        )
        mock_tool_client.call_tool = AsyncMock(
            return_value={
                "success": True,
                "markdown_report": markdown_report,
                "detected_components": [],
                "pass_2_components": [],
                "execution_time_seconds": 1.0,
                "total_findings": 0,
            }
        )
        mode_classifier.classify = AsyncMock(return_value=DialogMode.HOMEWORK_REVIEW)

        # Act
        cleanup_spy = AsyncMock()
        with patch.object(
            homework_handler._review_use_case, "_cleanup_file", cleanup_spy
        ):
            response = await orchestrator.handle_user_message(
                user_id="123",
                message=f"Сделай ревью {commit_hash}",
                session_id="test_session",
            )

        # Assert
        assert response.startswith("FILE:")
        cleanup_spy.assert_awaited_once()
