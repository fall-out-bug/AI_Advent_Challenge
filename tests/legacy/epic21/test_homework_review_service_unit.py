"""Unit tests for HomeworkReviewService with dependency injection.

Tests the new Clean Architecture implementation with mocked dependencies.

Epic 21 · Stage 21_01b · Homework Review Service
"""

import pytest
from unittest.mock import AsyncMock

from src.domain.agents.state_machine import DialogContext, DialogState
from src.domain.interfaces.homework_review_service import HomeworkReviewService
from src.infrastructure.services.homework_review_service_impl import HomeworkReviewServiceImpl


@pytest.mark.epic21
@pytest.mark.stage_21_01
@pytest.mark.homework_service
@pytest.mark.unit
class TestHomeworkReviewServiceUnit:
    """Unit tests for HomeworkReviewService implementation."""

    @pytest.fixture
    def mock_hw_checker(self):
        """Mock HomeworkCheckerProtocol for testing."""
        mock_client = AsyncMock()
        mock_client.get_recent_commits.return_value = {
            "total": 2,
            "commits": [
                {
                    "commit_hash": "abc123456789",
                    "archive_name": "student_homework_1.zip",
                    "assignment": "Python Basics",
                    "commit_dttm": "2025-01-15 10:30:00",
                    "status": "passed"
                }
            ]
        }
        mock_client.download_archive.return_value = b"fake_zip_content"
        return mock_client

    @pytest.fixture
    def mock_tool_client(self):
        """Mock ToolClientProtocol for testing."""
        mock_client = AsyncMock()
        mock_client.call_tool.return_value = {
            "success": True,
            "total_findings": 3,
            "markdown_report": "# Homework Review\n\nGood work!\n",
            "execution_time_seconds": 2.5,
            "detected_components": ["main.py", "utils.py"]
        }
        return mock_client

    @pytest.fixture
    def mock_storage_service(self):
        """Mock StorageService for testing."""
        from unittest.mock import MagicMock
        mock_service = MagicMock()
        mock_file = MagicMock()
        mock_file.name = "/tmp/test_homework.zip"
        mock_file.close = MagicMock()
        mock_service.create_temp_file.return_value = mock_file
        mock_service.cleanup_temp_file = MagicMock()
        return mock_service

    @pytest.fixture
    def homework_review_service(self, mock_hw_checker, mock_tool_client, mock_storage_service) -> HomeworkReviewService:
        """Create HomeworkReviewService with mocked dependencies."""
        return HomeworkReviewServiceImpl(
            hw_checker=mock_hw_checker,
            tool_client=mock_tool_client,
            storage_service=mock_storage_service,
        )

    async def test_list_homeworks_delegates_to_hw_checker(self, homework_review_service, mock_hw_checker):
        """Unit: list_homeworks delegates to HW checker."""
        # Act
        result = await homework_review_service.list_homeworks(days=3)

        # Assert
        mock_hw_checker.get_recent_commits.assert_called_once_with(days=3)
        assert result == mock_hw_checker.get_recent_commits.return_value

    async def test_list_homeworks_handles_hw_checker_error(self, homework_review_service, mock_hw_checker):
        """Unit: list_homeworks handles HW checker errors."""
        # Arrange
        mock_hw_checker.get_recent_commits.side_effect = Exception("HW checker failed")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await homework_review_service.list_homeworks(days=1)

        assert "HW checker failed" in str(exc_info.value)

    async def test_review_homework_successful_flow(self, homework_review_service, mock_hw_checker, mock_tool_client):
        """Unit: review_homework handles successful review."""
        # Arrange
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )

        # Act
        result = await homework_review_service.review_homework(context, "abc123456789")

        # Assert
        # Should download archive
        mock_hw_checker.download_archive.assert_called_once_with("abc123456789")

        # Should call review tool
        mock_tool_client.call_tool.assert_called_once()
        call_args = mock_tool_client.call_tool.call_args
        assert call_args[0][0] == "review_homework_archive"
        # archive_path contains temp file path, not commit hash
        archive_path = call_args[0][1]["archive_path"]
        assert str(archive_path).endswith(".zip")

        # Should return file format
        assert result.startswith("FILE:")
        assert "review_abc123456789.md" in result

    async def test_review_homework_no_findings_success(self, homework_review_service, mock_tool_client):
        """Unit: review_homework handles successful review with no findings."""
        # Arrange
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )
        mock_tool_client.call_tool.return_value = {
            "success": True,
            "total_findings": 0,
            "markdown_report": "",
            "execution_time_seconds": 1.5,
            "detected_components": ["main.py"]
        }

        # Act
        result = await homework_review_service.review_homework(context, "clean123456789")

        # Assert
        assert "✅ Ревью выполнено успешно, но не найдено проблем" in result
        assert "Компонентов обнаружено: 1" in result

    async def test_review_homework_tool_failure(self, homework_review_service, mock_tool_client):
        """Unit: review_homework handles tool execution failure."""
        # Arrange
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )
        mock_tool_client.call_tool.return_value = {
            "success": False,
            "total_findings": 0,
            "markdown_report": "",
            "error": "Tool execution failed"
        }

        # Act
        result = await homework_review_service.review_homework(context, "error123456789")

        # Assert
        assert "❌ Ошибка при выполнении ревью" in result

    async def test_review_homework_empty_report(self, homework_review_service, mock_tool_client):
        """Unit: review_homework handles empty report from tool."""
        # Arrange
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )
        mock_tool_client.call_tool.return_value = {
            "success": True,
            "total_findings": 5,
            "markdown_report": "",  # Empty report
            "execution_time_seconds": 3.0,
            "detected_components": ["main.py", "utils.py"]
        }

        # Act
        result = await homework_review_service.review_homework(context, "empty123456789")

        # Assert
        assert "❌ Ревью не вернуло отчет" in result

    async def test_review_homework_download_404_error(self, homework_review_service, mock_hw_checker):
        """Unit: review_homework handles 404 download error."""
        # Arrange
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )
        mock_hw_checker.download_archive.side_effect = Exception("404 Not Found")

        # Act
        result = await homework_review_service.review_homework(context, "notfound123456789")

        # Assert
        assert "❌ Архив с коммитом notfound123456789 не найден на сервере" in result

    async def test_review_homework_download_connection_error(self, homework_review_service, mock_hw_checker):
        """Unit: review_homework handles connection error."""
        # Arrange
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )
        mock_hw_checker.download_archive.side_effect = Exception("Connection timeout")

        # Act
        result = await homework_review_service.review_homework(context, "timeout123456789")

        # Assert
        assert "❌ Не удалось подключиться к серверу проверки домашних работ" in result

    async def test_review_homework_download_timeout_error(self, homework_review_service, mock_hw_checker):
        """Unit: review_homework handles timeout error."""
        # Arrange
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )
        mock_hw_checker.download_archive.side_effect = Exception("Request timeout")

        # Act
        result = await homework_review_service.review_homework(context, "timeout123456789")

        # Assert
        assert "❌ Превышено время ожидания ответа от сервера" in result

    async def test_review_homework_generic_download_error(self, homework_review_service, mock_hw_checker):
        """Unit: review_homework handles generic download error."""
        # Arrange
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )
        mock_hw_checker.download_archive.side_effect = Exception("Some unexpected error")

        # Act
        result = await homework_review_service.review_homework(context, "error123456789")

        # Assert
        assert "❌ Ошибка при ревью домашней работы" in result
        assert "Some unexpected error" in result
