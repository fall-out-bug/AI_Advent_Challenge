"""Tests for ReviewSubmissionUseCase with Pass 4 (log analysis).

Following TDD principles.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shared.shared_package.clients.base_client import ModelResponse
from src.application.use_cases.review_submission_use_case import ReviewSubmissionUseCase
from src.domain.services.diff_analyzer import DiffAnalyzer
from src.domain.value_objects.long_summarization_task import LongTask
from src.domain.value_objects.task_status import TaskStatus
from src.domain.value_objects.task_type import TaskType
from src.infrastructure.archive.archive_service import ZipArchiveService
from src.infrastructure.config.settings import Settings
from src.infrastructure.repositories.homework_review_repository import (
    HomeworkReviewRepository,
)


class TestReviewSubmissionPass4:
    """Test Pass 4 integration in ReviewSubmissionUseCase."""

    @pytest.mark.asyncio
    async def test_pass_4_executed_when_logs_provided(self) -> None:
        """Test Pass 4 is executed when logs_zip_path is in metadata."""
        # Mock dependencies
        mock_unified_client = MagicMock()
        mock_unified_client.make_request = AsyncMock(
            return_value=ModelResponse(
                response='{"haiku": "test"}',
                response_tokens=5,
                input_tokens=5,
                total_tokens=10,
                model_name="mistral",
                response_time=0.1,
            )
        )

        settings = Settings(enable_log_analysis=True)
        archive_service = ZipArchiveService(settings)
        archive_service.extract_logs = MagicMock(
            return_value={
                "run_stdout.txt": "stdout content",
                "checker.log": "2025-11-03 | ERROR | test | Error message",
            }
        )

        mock_log_parser = MagicMock()
        mock_log_parser.parse = MagicMock(return_value=[])

        mock_log_normalizer = MagicMock()
        mock_log_normalizer.filter_by_severity = MagicMock(return_value=[])
        mock_log_normalizer.group_by_component_and_severity = MagicMock(return_value={})
        mock_log_normalizer.create_log_groups = MagicMock(return_value=[])

        mock_log_analyzer = AsyncMock()
        mock_log_analyzer.analyze_log_group = AsyncMock(return_value=None)

        mock_repository = AsyncMock()
        mock_repository.complete = AsyncMock()
        mock_repository.count_reviews_in_window = AsyncMock(return_value=0)

        mock_publisher = AsyncMock()
        mock_publisher.publish_review = AsyncMock()

        review_report = MagicMock(
            session_id="test-session",
            to_dict=lambda: {},
            to_markdown=lambda: "# Report",
            pass_1=MagicMock(metadata={}),
            pass_4_logs=None,
        )

        with patch(
            "src.application.use_cases.review_submission_use_case.ModularReviewService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service.review_submission = AsyncMock(return_value=review_report)
            mock_service_cls.return_value = mock_service

            use_case = ReviewSubmissionUseCase(
                archive_reader=archive_service,
                diff_analyzer=DiffAnalyzer(),
                unified_client=mock_unified_client,
                review_repository=AsyncMock(),
                tasks_repository=mock_repository,
                publisher=mock_publisher,
                log_parser=mock_log_parser,
                log_normalizer=mock_log_normalizer,
                log_analyzer=mock_log_analyzer,
                settings=settings,
            )

            task = LongTask(
                task_id="test-123",
                task_type=TaskType.CODE_REVIEW,
                user_id=2001,
                status=TaskStatus.RUNNING,
                metadata={
                    "new_submission_path": "/path/to/new.zip",
                    "new_commit": "commit123",
                    "logs_zip_path": "/path/to/logs.zip",
                },
            )

            await use_case.execute(task)

            # Verify logs were extracted
            archive_service.extract_logs.assert_called_once_with("/path/to/logs.zip")

    @pytest.mark.asyncio
    async def test_pass_4_skipped_when_no_logs(self) -> None:
        """Test Pass 4 is skipped when logs_zip_path is not provided."""
        mock_unified_client = MagicMock()
        mock_unified_client.make_request = AsyncMock(
            return_value=ModelResponse(
                response='{"haiku": "test"}',
                response_tokens=5,
                input_tokens=5,
                total_tokens=10,
                model_name="mistral",
                response_time=0.1,
            )
        )
        settings = Settings(enable_log_analysis=True)
        archive_service = ZipArchiveService(settings)
        archive_service.extract_logs = MagicMock()

        review_report = MagicMock(
            session_id="test-session",
            to_dict=lambda: {},
            to_markdown=lambda: "# Report",
            pass_1=MagicMock(metadata={}),
        )

        with patch(
            "src.application.use_cases.review_submission_use_case.ModularReviewService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service.review_submission = AsyncMock(return_value=review_report)
            mock_service_cls.return_value = mock_service

            tasks_repository = AsyncMock()
            tasks_repository.count_reviews_in_window = AsyncMock(return_value=0)

            use_case = ReviewSubmissionUseCase(
                archive_reader=archive_service,
                diff_analyzer=DiffAnalyzer(),
                unified_client=mock_unified_client,
                review_repository=AsyncMock(),
                tasks_repository=tasks_repository,
                publisher=AsyncMock(),
                log_parser=MagicMock(),
                log_normalizer=MagicMock(),
                log_analyzer=AsyncMock(),
                settings=settings,
            )

            task = LongTask(
                task_id="test-123",
                task_type=TaskType.CODE_REVIEW,
                user_id=2001,
                status=TaskStatus.RUNNING,
                metadata={
                    "new_submission_path": "/path/to/new.zip",
                    "new_commit": "commit123",
                },
            )

            await use_case.execute(task)

            # Verify logs were NOT extracted
            archive_service.extract_logs.assert_not_called()

    @pytest.mark.asyncio
    async def test_pass_4_skipped_when_disabled(self) -> None:
        """Test Pass 4 is skipped when enable_log_analysis is False."""
        mock_unified_client = MagicMock()
        mock_unified_client.make_request = AsyncMock(
            return_value=ModelResponse(
                response='{"haiku": "test"}',
                response_tokens=5,
                input_tokens=5,
                total_tokens=10,
                model_name="mistral",
                response_time=0.1,
            )
        )
        settings = Settings(enable_log_analysis=False)
        archive_service = ZipArchiveService(settings)
        archive_service.extract_logs = MagicMock()

        review_report = MagicMock(
            session_id="test-session",
            to_dict=lambda: {},
            to_markdown=lambda: "# Report",
            pass_1=MagicMock(metadata={}),
        )

        with patch(
            "src.application.use_cases.review_submission_use_case.ModularReviewService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service.review_submission = AsyncMock(return_value=review_report)
            mock_service_cls.return_value = mock_service

            tasks_repository = AsyncMock()
            tasks_repository.count_reviews_in_window = AsyncMock(return_value=0)

            use_case = ReviewSubmissionUseCase(
                archive_reader=archive_service,
                diff_analyzer=DiffAnalyzer(),
                unified_client=mock_unified_client,
                review_repository=AsyncMock(),
                tasks_repository=tasks_repository,
                publisher=AsyncMock(),
                log_parser=MagicMock(),
                log_normalizer=MagicMock(),
                log_analyzer=AsyncMock(),
                settings=settings,
            )

            task = LongTask(
                task_id="test-123",
                task_type=TaskType.CODE_REVIEW,
                user_id=2001,
                status=TaskStatus.RUNNING,
                metadata={
                    "new_submission_path": "/path/to/new.zip",
                    "new_commit": "commit123",
                    "logs_zip_path": "/path/to/logs.zip",
                },
            )

            await use_case.execute(task)

            # Verify logs were NOT extracted
            archive_service.extract_logs.assert_not_called()
