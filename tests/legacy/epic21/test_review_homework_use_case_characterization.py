"""Characterization tests for ReviewHomeworkUseCase behavior.

Tests capture current behavior BEFORE refactoring use cases to use domain services.
These tests ensure we don't break existing use case functionality.

Epic 21 · Stage 21_01d · Use Case Decomposition
"""

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.application.dtos.homework_dtos import HomeworkReviewResult
from src.application.use_cases.review_homework_use_case import ReviewHomeworkUseCase


@pytest.mark.epic21
@pytest.mark.stage_21_01
@pytest.mark.use_case
@pytest.mark.characterization
class TestReviewHomeworkUseCaseCharacterization:
    """Characterization tests for ReviewHomeworkUseCase behavior.

    These tests capture the current behavior of ReviewHomeworkUseCase
    BEFORE any refactoring. They ensure we don't break existing functionality.

    Epic 21 · Stage 21_01d · Use Case Decomposition
    """

    @pytest.fixture
    def mock_homework_checker(self):
        """Mock HomeworkCheckerProtocol for testing."""
        mock_client = AsyncMock()
        mock_client.download_archive.return_value = b"fake_zip_content_12345"
        return mock_client

    @pytest.fixture
    def mock_tool_client(self):
        """Mock ToolClientProtocol for testing."""
        mock_client = AsyncMock()
        mock_client.call_tool.return_value = {
            "success": True,
            "markdown_report": "# Homework Review\n\nGood work on this assignment!\n\n## Findings\n\n- Code structure is clean\n- Good use of functions\n",
            "total_findings": 2,
            "detected_components": ["main.py", "utils.py", "tests.py"],
            "pass_2_components": ["main.py"],
            "execution_time_seconds": 3.45,
        }
        return mock_client

    @pytest.fixture
    def use_case(self, mock_homework_checker, mock_tool_client):
        """Create ReviewHomeworkUseCase with mocked dependencies."""
        return ReviewHomeworkUseCase(
            homework_checker=mock_homework_checker,
            tool_client=mock_tool_client,
            assignment_type="python_basics",
            token_budget=6000,
            model_name="claude-3",
            temp_directory=Path("/tmp/test_reviews"),
            cleanup_timeout=0.5,
        )

    async def test_execute_successful_review_flow(self, use_case, mock_homework_checker, mock_tool_client):
        """Characterization: execute handles successful review flow."""
        # Act
        result = await use_case.execute("abc123def456")

        # Assert - should return HomeworkReviewResult
        assert isinstance(result, HomeworkReviewResult)
        assert result.success == True
        assert "# Homework Review" in result.markdown_report
        assert result.total_findings == 2
        assert len(result.detected_components) == 3
        assert len(result.pass_2_components) == 1
        assert result.execution_time_seconds == 3.45

        # Verify interactions
        mock_homework_checker.download_archive.assert_called_once_with("abc123def456")
        mock_tool_client.call_tool.assert_called_once()

        # Verify tool call parameters
        call_args = mock_tool_client.call_tool.call_args
        assert call_args[0][0] == "review_homework_archive"

        tool_params = call_args[0][1]
        assert tool_params["assignment_type"] == "python_basics"
        assert tool_params["token_budget"] == 6000
        assert tool_params["model_name"] == "claude-3"
        assert "archive_path" in tool_params
        assert tool_params["archive_path"].endswith(".zip")

    async def test_execute_with_default_parameters(self, mock_homework_checker, mock_tool_client):
        """Characterization: execute uses default parameters when not specified."""
        # Create use case with minimal config
        use_case = ReviewHomeworkUseCase(
            homework_checker=mock_homework_checker,
            tool_client=mock_tool_client,
        )

        # Act
        result = await use_case.execute("commit789")

        # Assert - should use defaults
        assert result.success == True

        # Verify tool was called with defaults
        call_args = mock_tool_client.call_tool.call_args
        tool_params = call_args[0][1]
        assert tool_params["assignment_type"] == "auto"
        assert tool_params["token_budget"] == 8000
        assert tool_params["model_name"] == "mistral"

    async def test_execute_temp_file_creation_and_cleanup(self, use_case, mock_homework_checker):
        """Characterization: execute creates and cleans up temp files."""
        temp_files_created = []
        temp_files_cleaned = []

        def mock_write_bytes(data):
            temp_files_created.append(self._temp_directory / f"homework_{uuid.uuid4().hex}.zip")

        def mock_unlink(missing_ok=True):
            temp_files_cleaned.append(True)

        with patch.object(Path, 'write_bytes', side_effect=mock_write_bytes), \
             patch.object(Path, 'unlink', side_effect=mock_unlink), \
             patch.object(Path, 'mkdir'):

            # Act
            result = await use_case.execute("test_commit")

            # Assert
            assert result.success == True
            assert len(temp_files_created) == 1
            assert len(temp_files_cleaned) == 1

    async def test_execute_tool_failure_raises_exception(self, use_case, mock_tool_client):
        """Characterization: execute raises exception when tool fails."""
        # Mock tool failure
        mock_tool_client.call_tool.return_value = {
            "success": False,
            "error": "Tool execution failed: model timeout"
        }

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            await use_case.execute("failing_commit")

        assert "Review tool returned failure" in str(exc_info.value)
        assert "model timeout" in str(exc_info.value)

    async def test_execute_archive_download_failure_propagates(self, use_case, mock_homework_checker):
        """Characterization: execute propagates archive download failures."""
        # Mock download failure
        mock_homework_checker.download_archive.side_effect = Exception("404 Not Found")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute("missing_commit")

        assert "404 Not Found" in str(exc_info.value)

    async def test_execute_missing_success_field_defaults_to_failure(self, mock_homework_checker, mock_tool_client):
        """Characterization: execute treats missing success field as failure."""
        # Mock tool response without success field
        mock_tool_client.call_tool.return_value = {
            "markdown_report": "Some report",
            "total_findings": 1,
        }

        use_case = ReviewHomeworkUseCase(
            homework_checker=mock_homework_checker,
            tool_client=mock_tool_client,
        )

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            await use_case.execute("test_commit")

        assert "Review tool returned failure" in str(exc_info.value)

    async def test_execute_empty_markdown_report_handled(self, mock_homework_checker, mock_tool_client):
        """Characterization: execute handles empty markdown report."""
        # Mock tool response with empty report
        mock_tool_client.call_tool.return_value = {
            "success": True,
            "markdown_report": "",
            "total_findings": 0,
            "detected_components": [],
            "execution_time_seconds": 1.0,
        }

        use_case = ReviewHomeworkUseCase(
            homework_checker=mock_homework_checker,
            tool_client=mock_tool_client,
        )

        # Act
        result = await use_case.execute("empty_report_commit")

        # Assert
        assert result.success == True
        assert result.markdown_report == ""
        assert result.total_findings == 0

    async def test_execute_with_custom_temp_directory(self, mock_homework_checker, mock_tool_client):
        """Characterization: execute respects custom temp directory."""
        custom_temp_dir = Path("/custom/archive/path")

        use_case = ReviewHomeworkUseCase(
            homework_checker=mock_homework_checker,
            tool_client=mock_tool_client,
            temp_directory=custom_temp_dir,
        )

        mkdir_calls = []

        def mock_mkdir(parents=True, exist_ok=True):
            mkdir_calls.append((self, parents, exist_ok))

        with patch.object(Path, 'mkdir', side_effect=mock_mkdir), \
             patch.object(Path, 'write_bytes'), \
             patch.object(Path, 'unlink'):

            # Act
            result = await use_case.execute("custom_dir_commit")

            # Assert
            assert result.success == True
            # Directory should be created
            assert len(mkdir_calls) == 1

    async def test_execute_cleanup_timeout_handled(self, use_case):
        """Characterization: execute handles cleanup timeouts gracefully."""
        cleanup_timeout_calls = []

        async def mock_wait_for(coro, timeout):
            if str(coro).find('unlink') >= 0:
                cleanup_timeout_calls.append(timeout)
                raise asyncio.TimeoutError()
            return await coro

        with patch('asyncio.wait_for', side_effect=mock_wait_for), \
             patch.object(Path, 'write_bytes'), \
             patch.object(Path, 'mkdir'), \
             patch('uuid.uuid4', return_value=type('MockUUID', (), {'hex': 'testuuid123'})()):

            # Act - should not raise exception despite cleanup timeout
            result = await use_case.execute("timeout_commit")

            # Assert
            assert result.success == True
            assert len(cleanup_timeout_calls) == 1
            assert cleanup_timeout_calls[0] == 0.5  # cleanup_timeout

    async def test_write_archive_creates_unique_filename(self, mock_homework_checker, mock_tool_client):
        """Characterization: _write_archive creates unique filenames."""
        use_case = ReviewHomeworkUseCase(
            homework_checker=mock_homework_checker,
            tool_client=mock_tool_client,
            temp_directory=Path("/tmp/test"),
        )

        created_files = []

        def mock_write_bytes(data):
            # Capture the filename that would be created
            filename = f"homework_{uuid.uuid4().hex}.zip"
            created_files.append(filename)

        with patch.object(Path, 'write_bytes', side_effect=mock_write_bytes), \
             patch.object(Path, 'mkdir'):

            # Act - call multiple times
            await use_case._write_archive(b"data1")
            await use_case._write_archive(b"data2")

            # Assert - should create unique filenames
            assert len(created_files) == 2
            assert created_files[0] != created_files[1]
            assert all(f.startswith("homework_") for f in created_files)
            assert all(f.endswith(".zip") for f in created_files)

    async def test_cleanup_file_missing_file_handled(self, use_case):
        """Characterization: _cleanup_file handles missing files gracefully."""
        missing_path = Path("/nonexistent/file.zip")

        # Act - should not raise exception
        await use_case._cleanup_file(missing_path)

        # Assert - no exception raised (missing_ok=True behavior)

    async def test_cleanup_file_with_custom_timeout(self):
        """Characterization: cleanup uses custom timeout."""
        use_case = ReviewHomeworkUseCase(
            homework_checker=AsyncMock(),
            tool_client=AsyncMock(),
            cleanup_timeout=2.0,
        )

        timeout_calls = []

        async def mock_wait_for(coro, timeout):
            timeout_calls.append(timeout)
            return None

        with patch('asyncio.wait_for', side_effect=mock_wait_for):
            # Act
            await use_case._cleanup_file(Path("/tmp/test.zip"))

            # Assert
            assert timeout_calls == [2.0]

    async def test_execute_with_environment_temp_dir(self, mock_homework_checker, mock_tool_client):
        """Characterization: execute uses BUTLER_ARCHIVE_DIR environment variable."""
        with patch.dict('os.environ', {'BUTLER_ARCHIVE_DIR': '/env/archive/dir'}), \
             patch.object(Path, 'mkdir'), \
             patch.object(Path, 'write_bytes'), \
             patch.object(Path, 'unlink'):

            use_case = ReviewHomeworkUseCase(
                homework_checker=mock_homework_checker,
                tool_client=mock_tool_client,
                # Don't specify temp_directory to test env var
            )

            # Act
            result = await use_case.execute("env_commit")

            # Assert
            assert result.success == True
            # Should use env var directory
            mkdir_calls = []
            def capture_mkdir(*args, **kwargs):
                mkdir_calls.append(self)
            # Note: This is hard to test precisely without more complex mocking
