"""Unit tests for ReviewHomeworkCleanUseCase with domain services.

Tests the new Clean Architecture use case implementation.

Epic 21 · Stage 21_01d · Use Case Decomposition
"""

import pytest
from unittest.mock import AsyncMock

from src.application.dtos.homework_dtos import HomeworkReviewResult
from src.application.use_cases.review_homework_clean_use_case import ReviewHomeworkCleanUseCase


@pytest.mark.epic21
@pytest.mark.stage_21_01
@pytest.mark.use_case
@pytest.mark.unit
class TestReviewHomeworkCleanUseCaseUnit:
    """Unit tests for ReviewHomeworkCleanUseCase."""

    @pytest.fixture
    def mock_homework_review_service(self):
        """Mock HomeworkReviewService for testing."""
        mock_service = AsyncMock()

        # Default successful responses
        mock_service.review_homework.return_value = "FILE:review_abc123456.md:dGVzdCBtYXJrZG93biByZXBvcnQ="
        mock_service.list_homeworks.return_value = {
            "total": 2,
            "commits": [
                {
                    "commit_hash": "abc123",
                    "archive_name": "hw1.zip",
                    "assignment": "Python Basics",
                    "status": "passed"
                }
            ]
        }

        return mock_service

    @pytest.fixture
    def use_case(self, mock_homework_review_service):
        """Create ReviewHomeworkCleanUseCase with mocked service."""
        return ReviewHomeworkCleanUseCase(
            homework_review_service=mock_homework_review_service,
        )

    async def test_execute_successful_review(self, use_case, mock_homework_review_service):
        """Unit: execute handles successful review."""
        # Act
        result = await use_case.execute("abc123456789")

        # Assert
        assert isinstance(result, HomeworkReviewResult)
        assert result.success == True
        assert "Review completed" in result.markdown_report

        # Verify domain service was called
        mock_homework_review_service.review_homework.assert_called_once()
        call_args = mock_homework_review_service.review_homework.call_args

        # Verify context was created properly
        context = call_args[0][0]  # First positional argument
        assert context.state.value == "idle"
        assert context.user_id == "system"
        assert context.session_id == "review_abc12345"  # First 8 chars of commit

        # Verify commit hash was passed
        assert call_args[0][1] == "abc123456789"

    async def test_execute_with_invalid_commit_hash(self, use_case):
        """Unit: execute validates commit hash input."""
        # Test empty string
        with pytest.raises(ValueError) as exc_info:
            await use_case.execute("")
        assert "non-empty string" in str(exc_info.value)

        # Test None
        with pytest.raises(ValueError) as exc_info:
            await use_case.execute(None)
        assert "commit_hash must be a non-empty string" in str(exc_info.value)

        # Test whitespace only
        with pytest.raises(ValueError) as exc_info:
            await use_case.execute("   ")
        assert "cannot be empty or whitespace" in str(exc_info.value)

    async def test_execute_domain_service_failure(self, use_case, mock_homework_review_service):
        """Unit: execute handles domain service failures."""
        # Mock service failure
        mock_homework_review_service.review_homework.side_effect = Exception("Storage error")

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            await use_case.execute("failing_commit")

        assert "Homework review failed" in str(exc_info.value)
        assert "Storage error" in str(exc_info.value)

    async def test_execute_invalid_file_format(self, use_case, mock_homework_review_service):
        """Unit: execute handles invalid FILE format from service."""
        # Mock invalid FILE format
        mock_homework_review_service.review_homework.return_value = "INVALID_FORMAT"

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            await use_case.execute("bad_format_commit")

        assert "Review failed" in str(exc_info.value)

    async def test_execute_error_response_from_service(self, use_case, mock_homework_review_service):
        """Unit: execute handles error messages from service."""
        # Mock error response
        mock_homework_review_service.review_homework.return_value = "❌ Archive not found"

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            await use_case.execute("not_found_commit")

        assert "Review failed" in str(exc_info.value)
        assert "Archive not found" in str(exc_info.value)

    async def test_list_recent_homeworks_success(self, use_case, mock_homework_review_service):
        """Unit: list_recent_homeworks delegates to domain service."""
        # Act
        result = await use_case.list_recent_homeworks(days=3)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["commit_hash"] == "abc123"
        assert result[0]["assignment"] == "Python Basics"

        # Verify domain service was called
        mock_homework_review_service.list_homeworks.assert_called_once_with(3)

    async def test_list_recent_homeworks_default_days(self, use_case, mock_homework_review_service):
        """Unit: list_recent_homeworks uses default days parameter."""
        # Act
        result = await use_case.list_recent_homeworks()

        # Assert
        mock_homework_review_service.list_homeworks.assert_called_once_with(1)

    async def test_list_recent_homeworks_service_failure(self, use_case, mock_homework_review_service):
        """Unit: list_recent_homeworks handles service failures."""
        # Mock service failure
        mock_homework_review_service.list_homeworks.side_effect = Exception("Database connection failed")

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            await use_case.list_recent_homeworks(days=2)

        assert "Failed to list homeworks" in str(exc_info.value)
        assert "Database connection failed" in str(exc_info.value)

    async def test_list_recent_homeworks_malformed_response(self, use_case, mock_homework_review_service):
        """Unit: list_recent_homeworks handles malformed service responses."""
        # Mock malformed response
        mock_homework_review_service.list_homeworks.return_value = "not a dict"

        # Act
        result = await use_case.list_recent_homeworks()

        # Assert - should return empty list gracefully
        assert result == []

    async def test_list_recent_homeworks_missing_commits_key(self, use_case, mock_homework_review_service):
        """Unit: list_recent_homeworks handles missing commits key."""
        # Mock response without commits key
        mock_homework_review_service.list_homeworks.return_value = {"total": 5}

        # Act
        result = await use_case.list_recent_homeworks()

        # Assert - should return empty list
        assert result == []

    async def test_execute_preserves_exception_chain(self, use_case, mock_homework_review_service):
        """Unit: execute preserves exception chaining."""
        # Mock service with specific exception
        original_error = ValueError("Original domain error")
        mock_homework_review_service.review_homework.side_effect = original_error

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            await use_case.execute("test_commit")

        # Verify exception chaining
        assert exc_info.value.__cause__ is original_error

    async def test_execute_with_long_commit_hash(self, use_case, mock_homework_review_service):
        """Unit: execute handles long commit hashes."""
        long_commit = "a" * 64  # Max SHA-256 length

        # Act
        result = await use_case.execute(long_commit)

        # Assert
        assert result.success == True

        # Verify session ID uses first 8 chars
        call_args = mock_homework_review_service.review_homework.call_args
        context = call_args[0][0]
        assert context.session_id == "review_aaaaaaaa"  # First 8 'a's

    async def test_days_parameter_passed_through(self, use_case, mock_homework_review_service):
        """Unit: days parameter is passed to execute method."""
        # Act - call execute with days parameter (currently unused but validated)
        result = await use_case.execute("test_commit", days=5)

        # Assert - should work without issues
        assert result.success == True
        # Note: days parameter is currently not used in execute, but method accepts it
