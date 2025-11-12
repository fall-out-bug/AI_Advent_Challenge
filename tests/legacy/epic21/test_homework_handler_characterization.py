"""Characterization tests for HomeworkHandler behavior.

Tests capture current behavior BEFORE refactoring to HomeworkReviewService.
These tests ensure we don't break existing functionality.

Epic 21 · Stage 21_01b · Homework Review Service
"""

import pytest
from unittest.mock import AsyncMock

from src.domain.agents.handlers.homework_handler import HomeworkHandler
from src.domain.agents.state_machine import DialogContext, DialogState
from src.domain.interfaces.tool_client import ToolClientProtocol


@pytest.mark.epic21
@pytest.mark.stage_21_01
@pytest.mark.homework_service
@pytest.mark.characterization
class TestHomeworkHandlerCharacterization:
    """Characterization tests for HomeworkHandler behavior.

    These tests capture the current behavior of HomeworkHandler
    BEFORE any refactoring. They ensure we don't break existing functionality.

    Epic 21 · Stage 21_01b · Homework Review Service
    """

    @pytest.fixture
    def mock_hw_checker_client(self):
        """Mock HWCheckerClient for testing."""
        mock_client = AsyncMock()
        # Default successful responses
        mock_client.get_recent_commits.return_value = {
            "total": 2,
            "commits": [
                {
                    "commit_hash": "abc123456789",
                    "archive_name": "student_homework_1.zip",
                    "assignment": "Python Basics",
                    "commit_dttm": "2025-01-15 10:30:00",
                    "status": "passed"
                },
                {
                    "commit_hash": "def789012345",
                    "archive_name": "student_homework_2.zip",
                    "assignment": "Data Structures",
                    "commit_dttm": "2025-01-14 15:45:00",
                    "status": "failed"
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
    def handler(self, mock_hw_checker_client, mock_tool_client):
        """Create HomeworkHandler with mocked dependencies."""
        # Create a mock homework review service that delegates to the original logic
        class MockHomeworkReviewService:
            def __init__(self, hw_checker, tool_client):
                self.hw_checker = hw_checker
                self.tool_client = tool_client

            async def list_homeworks(self, days: int):
                return await self.hw_checker.get_recent_commits(days=days)

            async def review_homework(self, context, commit_hash: str):
                # Import here to avoid circular dependency
                from src.infrastructure.services.homework_review_service_impl import HomeworkReviewServiceImpl
                # Create a mock storage service for testing
                class MockStorageService:
                    def create_temp_file(self, suffix='', prefix='temp_', content=None):
                        import tempfile
                        import os
                        from unittest.mock import MagicMock
                        temp_dir = '/tmp' if os.path.exists('/tmp') else tempfile.gettempdir()
                        mock_file = MagicMock()
                        mock_file.name = f"{temp_dir}/homework_review_test{suffix}"
                        if content:
                            mock_file.write = lambda c: None
                            mock_file.flush = lambda: None
                        mock_file.close = lambda: None
                        return mock_file

                    def cleanup_temp_file(self, path, missing_ok=True):
                        pass

                service = HomeworkReviewServiceImpl(self.hw_checker, self.tool_client, MockStorageService())
                return await service.review_homework(context, commit_hash)

        mock_service = MockHomeworkReviewService(mock_hw_checker_client, mock_tool_client)
        return HomeworkHandler(homework_review_service=mock_service)

    async def test_list_homeworks_command_recognition(self, handler):
        """Characterization: Recognizes various 'list homeworks' commands."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )

        test_commands = [
            "покажи домашки",
            "Покажи домашки",
            "покажи домашк",
            "покажи домашние работы",
            "show homework",
            "homework list",
            "список домашек",
            "список домашних работ",
            "list homework",
            "домашки",
            "homework"
        ]

        for command in test_commands:
            result = await handler.handle(context, command)
            assert "📚 Домашки за последние 1 дней" in result
            assert "Python Basics" in result
            assert "Data Structures" in result

    async def test_list_homeworks_with_days_parameter(self, handler):
        """Characterization: Parses days parameter from message."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )

        # Test various day patterns
        test_cases = [
            ("покажи домашки за 3 дня", 3),
            ("покажи домашки за 7 дней", 7),
            ("homework list for 5 days", 5),
            ("домашки за 2 дня", 2),
        ]

        for message, expected_days in test_cases:
            result = await handler.handle(context, message)
            assert f"📚 Домашки за последние {expected_days} дней" in result

    async def test_list_homeworks_empty_result(self, handler, mock_hw_checker_client):
        """Characterization: Handles empty homework list."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )

        # Mock empty result
        mock_hw_checker_client.get_recent_commits.return_value = {
            "total": 0,
            "commits": []
        }

        result = await handler.handle(context, "покажи домашки")
        assert "📚 Нет домашних работ за последние 1 дней" in result
        assert "Сделай ревью {commit_hash}" in result

    async def test_list_homeworks_error_handling(self, handler, mock_hw_checker_client):
        """Characterization: Handles HW checker client errors."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )

        # Mock connection error
        mock_hw_checker_client.get_recent_commits.side_effect = Exception("Connection failed")

        result = await handler.handle(context, "покажи домашки")
        assert "❌ Не удалось подключиться к серверу проверки домашних работ" in result

    async def test_review_homework_command_recognition(self, handler, mock_hw_checker_client, mock_tool_client):
        """Characterization: Recognizes various 'review homework' commands."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )

        test_cases = [
            ("сделай ревью abc123456789", "abc123456789"),
            ("Сделай ревью abc123456789", "abc123456789"),
            ("ревью abc123456789", "abc123456789"),
            ("review abc123456789", "abc123456789"),
            ("проверь коммит abc123456789", "abc123456789"),
            ("check commit abc123456789", "abc123456789"),
            ("сделай ревью abcdef123456789", "abcdef123456789"),
        ]

        for command, expected_commit in test_cases:
            mock_tool_client.call_tool.reset_mock()
            mock_hw_checker_client.download_archive.reset_mock()
            result = await handler.handle(context, command)

            # Should return file format
            assert result.startswith("FILE:")
            assert f"review_{expected_commit[:12]}.md" in result

            # Should call download and review tool
            mock_hw_checker_client.download_archive.assert_called_once_with(expected_commit)
            mock_tool_client.call_tool.assert_called_once()
            call_args = mock_tool_client.call_tool.call_args
            assert call_args[0][0] == "review_homework_archive"
            # archive_path contains temp file path, not commit hash
            assert call_args[0][1]["archive_path"].endswith(".zip")

    async def test_review_homework_commit_not_found(self, handler, mock_hw_checker_client):
        """Characterization: Handles commit not found error."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )

        # Mock 404 error
        mock_hw_checker_client.download_archive.side_effect = Exception("404 Not Found")

        result = await handler.handle(context, "сделай ревью nonexistent123456789")
        assert "❌ Архив с коммитом nonexistent123456789 не найден на сервере" in result

    async def test_review_homework_download_error(self, handler, mock_hw_checker_client):
        """Characterization: Handles download errors."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )

        # Mock download error
        mock_hw_checker_client.download_archive.side_effect = Exception("Network timeout")

        result = await handler.handle(context, "сделай ревью timeout123456789")
        assert "❌ Не удалось подключиться к серверу проверки домашних работ" in result

    async def test_review_homework_review_tool_error(self, handler, mock_tool_client):
        """Characterization: Handles review tool errors."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )

        # Mock review tool failure
        mock_tool_client.call_tool.return_value = {
            "success": False,
            "total_findings": 0,
            "markdown_report": "",
            "error": "Tool execution failed"
        }

        result = await handler.handle(context, "сделай ревью error123456789")
        assert "❌ Ошибка при выполнении ревью" in result

    async def test_review_homework_no_findings_success(self, handler, mock_tool_client):
        """Characterization: Handles successful review with no findings."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )

        # Mock successful review with no findings
        mock_tool_client.call_tool.return_value = {
            "success": True,
            "total_findings": 0,
            "markdown_report": "",
            "execution_time_seconds": 1.5,
            "detected_components": ["main.py"]
        }

        result = await handler.handle(context, "сделай ревью clean123456789")
        assert "✅ Ревью выполнено успешно, но не найдено проблем" in result
        assert "Компонентов обнаружено: 1" in result

    async def test_unknown_command(self, handler):
        """Characterization: Handles unknown commands."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )

        result = await handler.handle(context, "random message")
        assert "❌ Не понял команду" in result
        assert "Покажи домашки" in result
        assert "Сделай ревью {commit_hash}" in result

    async def test_no_hw_checker_client_configured(self, handler):
        """Characterization: Handles missing HW checker client."""
        # Create handler without HW checker client
        handler_no_client = HomeworkHandler(
            hw_checker_client=None,
            tool_client=AsyncMock(),
        )

        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )

        result = await handler_no_client.handle(context, "покажи домашки")
        assert "❌ HW Checker client не настроен" in result

    async def test_no_hw_checker_client_configured_for_list(self):
        """Characterization: Handles missing HW checker client for list command."""
        # Create handler without HW checker client
        from unittest.mock import AsyncMock
        handler_no_hw = HomeworkHandler(
            hw_checker_client=None,
            tool_client=AsyncMock(),
        )

        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )

        result = await handler_no_hw.handle(context, "покажи домашки")
        assert "❌ HW Checker client не настроен" in result

    async def test_markdown_escaping_in_homework_list(self, handler, mock_hw_checker_client):
        """Characterization: Escapes markdown in homework list output."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="test_user",
            session_id="test_session"
        )

        # Mock homework with markdown characters
        mock_hw_checker_client.get_recent_commits.return_value = {
            "total": 1,
            "commits": [
                {
                    "commit_hash": "abc123",
                    "archive_name": "test[with]brackets_homework.zip",
                    "assignment": "Python_Basics_With*Stars",
                    "commit_dttm": "2025-01-15 10:30:00",
                    "status": "passed"
                }
            ]
        }

        result = await handler.handle(context, "покажи домашки")
        # Should contain escaped markdown characters
        # Stars are removed, not escaped
        assert "*" not in result  # Stars should be removed
        assert "\\[" in result  # Brackets should be escaped
        assert "\\]" in result  # Brackets should be escaped
        assert "\\_" in result  # Underscores should be escaped
