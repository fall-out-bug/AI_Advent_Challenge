"""Unit tests for Homework Handler.

Following TDD principles and testing best practices.
"""

import base64
import pytest
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from pathlib import Path
import tempfile

from src.domain.agents.handlers.homework_handler import HomeworkHandler
from src.domain.agents.state_machine import DialogContext, DialogState


@pytest.fixture
def mock_hw_checker_client():
    """Create mock HW Checker client."""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_tool_client():
    """Create mock tool client."""
    client = AsyncMock()
    return client


@pytest.fixture
def handler(mock_hw_checker_client, mock_tool_client):
    """Create HomeworkHandler instance."""
    return HomeworkHandler(
        hw_checker_client=mock_hw_checker_client,
        tool_client=mock_tool_client,
    )


@pytest.fixture
def context():
    """Create dialog context."""
    return DialogContext(
        state=DialogState.IDLE,
        user_id="123",
        session_id="test_session",
    )


@pytest.mark.asyncio
class TestHomeworkHandlerListHomeworks:
    """Test suite for list homeworks functionality."""

    async def test_list_homeworks_success(self, handler, context, mock_hw_checker_client):
        """Test successful list homeworks."""
        # Arrange
        mock_response = {
            "commits": [
                {
                    "commit_hash": "abc123def456",
                    "archive_name": "Иванов_Иван_hw2.zip",
                    "commit_dttm": "2024-11-02T16:00:00",
                    "assignment": "HW2",
                    "status": "passed",
                },
                {
                    "commit_hash": "def456ghi789",
                    "archive_name": "Петров_Петр_hw3.zip",
                    "commit_dttm": "2024-11-03T10:00:00",
                    "assignment": "HW3",
                    "status": "running",
                },
            ],
            "total": 2,
        }
        mock_hw_checker_client.get_recent_commits = AsyncMock(return_value=mock_response)

        # Act
        result = await handler.handle(context, "Покажи домашки")

        # Assert
        assert "📚 Домашки" in result
        assert "Иванов_Иван_hw2.zip" in result
        assert "Петров_Петр_hw3.zip" in result
        assert "HW2" in result
        assert "HW3" in result
        mock_hw_checker_client.get_recent_commits.assert_called_once_with(days=1)

    async def test_list_homeworks_empty(self, handler, context, mock_hw_checker_client):
        """Test list homeworks when no commits found."""
        # Arrange
        mock_response = {"commits": [], "total": 0}
        mock_hw_checker_client.get_recent_commits = AsyncMock(return_value=mock_response)

        # Act
        result = await handler.handle(context, "Покажи домашки")

        # Assert
        assert "Нет домашних работ" in result
        mock_hw_checker_client.get_recent_commits.assert_called_once()

    async def test_list_homeworks_with_days(self, handler, context, mock_hw_checker_client):
        """Test list homeworks with days parameter."""
        # Arrange
        mock_response = {"commits": [], "total": 0}
        mock_hw_checker_client.get_recent_commits = AsyncMock(return_value=mock_response)

        # Act
        result = await handler.handle(context, "Покажи домашки за 7 дней")

        # Assert
        assert "7 дней" in result
        mock_hw_checker_client.get_recent_commits.assert_called_once_with(days=7)

    async def test_list_homeworks_connection_error(
        self, handler, context, mock_hw_checker_client
    ):
        """Test list homeworks with connection error."""
        # Arrange
        mock_hw_checker_client.get_recent_commits = AsyncMock(
            side_effect=Exception("Connection failed")
        )

        # Act
        result = await handler.handle(context, "Покажи домашки")

        # Assert
        assert "❌" in result
        assert "не удалось подключиться" in result.lower()


@pytest.mark.asyncio
class TestHomeworkHandlerReview:
    """Test suite for review homework functionality."""

    async def test_review_homework_success(self, handler, context, mock_hw_checker_client, mock_tool_client):
        """Test successful homework review."""
        # Arrange
        commit_hash = "abc123def456"
        archive_content = b"PK\x03\x04fake zip"
        markdown_report = "# Review Report\n\nTest review content"
        
        mock_hw_checker_client.download_archive = AsyncMock(return_value=archive_content)
        mock_tool_client.call_tool = AsyncMock(
            return_value={"markdown_report": markdown_report}
        )

        # Act
        result = await handler.handle(context, f"Сделай ревью {commit_hash}")

        # Assert
        assert result.startswith("FILE:")
        assert "review_" in result
        assert commit_hash[:12] in result
        
        # Verify file format
        parts = result[5:].split(":", 1)
        assert len(parts) == 2
        filename = parts[0]
        content_b64 = parts[1]
        decoded_content = base64.b64decode(content_b64).decode("utf-8")
        assert decoded_content == markdown_report
        assert filename.endswith(".md")
        
        mock_hw_checker_client.download_archive.assert_called_once_with(commit_hash, assignment=None)
        mock_tool_client.call_tool.assert_called_once()

    async def test_review_homework_parse_commit_hash(self, handler, context):
        """Test parsing commit hash from message."""
        # Arrange
        commit_hash = "abc123def456"
        
        # Act
        parsed = handler._parse_commit_hash_from_message(f"Сделай ревью {commit_hash}")
        
        # Assert
        assert parsed == commit_hash

    async def test_review_homework_multiple_formats(self, handler, context):
        """Test parsing commit hash from different message formats."""
        # Arrange
        commit_hash = "abc123def456"
        
        test_cases = [
            f"сделай ревью {commit_hash}",
            f"do review {commit_hash}",
            f"ревью {commit_hash}",
            f"review {commit_hash}",
            f"проверь коммит {commit_hash}",
            f"check commit {commit_hash}",
        ]
        
        # Act & Assert
        for message in test_cases:
            parsed = handler._parse_commit_hash_from_message(message)
            assert parsed == commit_hash, f"Failed for: {message}"

    async def test_review_homework_no_markdown_report(
        self, handler, context, mock_hw_checker_client, mock_tool_client
    ):
        """Test review when no markdown report returned."""
        # Arrange
        commit_hash = "abc123"
        archive_content = b"PK\x03\x04fake zip"
        
        mock_hw_checker_client.download_archive = AsyncMock(return_value=archive_content)
        mock_tool_client.call_tool = AsyncMock(return_value={})

        # Act
        result = await handler.handle(context, f"Сделай ревью {commit_hash}")

        # Assert
        assert "❌" in result
        assert "не вернуло результат" in result

    async def test_review_homework_archive_not_found(
        self, handler, context, mock_hw_checker_client
    ):
        """Test review when archive not found."""
        # Arrange
        commit_hash = "abc123"
        from httpx import HTTPStatusError, Response
        
        mock_response = MagicMock(spec=Response)
        error = HTTPStatusError("404", request=MagicMock(), response=mock_response)
        mock_hw_checker_client.download_archive = AsyncMock(side_effect=error)

        # Act
        result = await handler.handle(context, f"Сделай ревью {commit_hash}")

        # Assert
        assert "❌" in result
        assert "не найден" in result.lower() or "404" in result

    async def test_review_homework_cleanup_temp_file(
        self, handler, context, mock_hw_checker_client, mock_tool_client
    ):
        """Test that temp file is cleaned up after review."""
        # Arrange
        commit_hash = "abc123"
        archive_content = b"PK\x03\x04fake zip"
        markdown_report = "# Review Report\n\nTest"
        
        mock_hw_checker_client.download_archive = AsyncMock(return_value=archive_content)
        mock_tool_client.call_tool = AsyncMock(
            return_value={"markdown_report": markdown_report}
        )

        # Act
        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_file = MagicMock()
            mock_file.name = "/tmp/test.zip"
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=None)
            mock_temp.return_value = mock_file
            
            result = await handler.handle(context, f"Сделай ревью {commit_hash}")

        # Assert
        assert result.startswith("FILE:")
        # Verify temp file was written to
        mock_file.write.assert_called_once_with(archive_content)

    async def test_review_homework_unknown_command(self, handler, context):
        """Test handler with unknown command."""
        # Act
        result = await handler.handle(context, "Неизвестная команда")

        # Assert
        assert "❌" in result
        assert "Не понял команду" in result


@pytest.mark.asyncio
class TestHomeworkHandlerParseDays:
    """Test suite for parsing days from message."""

    async def test_parse_days_russian(self, handler):
        """Test parsing days from Russian message."""
        test_cases = [
            ("за 3 дня", 3),
            ("3 дня", 3),
            ("за 7 дней", 7),
            ("7 дней", 7),
            ("за 1 день", 1),
        ]
        
        for message, expected in test_cases:
            result = handler._parse_days_from_message(f"Покажи домашки {message}")
            assert result == expected, f"Failed for: {message}"

    async def test_parse_days_english(self, handler):
        """Test parsing days from English message."""
        test_cases = [
            ("for 3 days", 3),
            ("3 days", 3),
            ("for 7 days", 7),
            ("7 days", 7),
        ]
        
        for message, expected in test_cases:
            result = handler._parse_days_from_message(f"Show homework {message}")
            assert result == expected, f"Failed for: {message}"

    async def test_parse_days_default(self, handler):
        """Test default days when not specified."""
        result = handler._parse_days_from_message("Покажи домашки")
        assert result == 1

