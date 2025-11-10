"""Tests for LLM-driven MCP publishing in ReviewSubmissionUseCase."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from shared.shared_package.clients.base_client import ModelResponse

from src.application.use_cases.review_submission_use_case import (
    ReviewSubmissionUseCase,
)
from src.domain.value_objects.long_summarization_task import LongTask
from src.domain.value_objects.task_status import TaskStatus
from src.domain.value_objects.task_type import TaskType
from src.domain.services.diff_analyzer import DiffAnalyzer
from src.infrastructure.archive.archive_service import ZipArchiveService
from src.infrastructure.config.settings import Settings


@pytest.fixture
def review_use_case_with_mcp() -> ReviewSubmissionUseCase:
    """Create use case instance with MCP client and fallback publisher mocks."""

    settings = Settings()
    archive_service = ZipArchiveService(settings)
    unified_client = MagicMock()
    unified_client.make_request = AsyncMock()
    tasks_repository = MagicMock()
    tasks_repository.count_reviews_in_window = AsyncMock(return_value=0)

    use_case = ReviewSubmissionUseCase(
        archive_reader=archive_service,
        diff_analyzer=DiffAnalyzer(),
        unified_client=unified_client,
        review_repository=MagicMock(),
        tasks_repository=tasks_repository,
        publisher=AsyncMock(),
        log_parser=MagicMock(),
        log_normalizer=MagicMock(),
        log_analyzer=MagicMock(),
        settings=settings,
        mcp_client=AsyncMock(),
        fallback_publisher=AsyncMock(),
    )

    return use_case


@pytest.mark.asyncio
async def test_publish_review_via_mcp_success(
    review_use_case_with_mcp: ReviewSubmissionUseCase,
) -> None:
    """Use case should call MCP tool when LLM returns valid JSON payload."""

    use_case = review_use_case_with_mcp
    assert use_case.mcp_client is not None
    assert use_case.fallback_publisher is not None

    use_case.unified_client.make_request.return_value = ModelResponse(  # type: ignore[attr-defined]
        response=(
            '{"tool": "submit_review_result", "arguments": '
            '{"student_id": "Ivanov Ivan", "submission_hash": "abc123", '
            '"review_content": "# Review", "session_id": "session-1", '
            '"overall_score": 90}}'
        ),
        response_tokens=10,
        input_tokens=10,
        total_tokens=20,
        model_name="mistral",
        response_time=1.0,
    )

    use_case.mcp_client.discover_tools.return_value = [  # type: ignore[union-attr]
        {
            "name": "submit_review_result",
            "description": "Submit review",
            "input_schema": {"type": "object"},
        }
    ]

    published = await use_case._publish_review_via_mcp(  # type: ignore[attr-defined]
        student_id="Ivanov Ivan",
        assignment_id="HW1",
        submission_hash="abc123",
        review_markdown="# Review",
        session_id="session-1",
        overall_score=90,
        task_id="task-1",
    )

    assert published is True
    use_case.mcp_client.call_tool.assert_awaited_once_with(  # type: ignore[union-attr]
        "submit_review_result",
        {
            "student_id": "Ivanov Ivan",
            "submission_hash": "abc123",
            "review_content": "# Review",
            "session_id": "session-1",
            "overall_score": 90,
        },
    )
    use_case.fallback_publisher.publish_review.assert_not_called()  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_publish_review_via_mcp_invalid_llm_response_triggers_fallback(
    review_use_case_with_mcp: ReviewSubmissionUseCase,
) -> None:
    """Fallback publisher should be used when LLM response is invalid."""

    use_case = review_use_case_with_mcp
    use_case.unified_client.make_request.return_value = ModelResponse(  # type: ignore[attr-defined]
        response="Not a JSON payload",
        response_tokens=5,
        input_tokens=5,
        total_tokens=10,
        model_name="mistral",
        response_time=0.5,
    )

    use_case.mcp_client.discover_tools.return_value = [  # type: ignore[union-attr]
        {"name": "submit_review_result", "description": "", "input_schema": {}}
    ]

    published = await use_case._publish_review_via_mcp(  # type: ignore[attr-defined]
        student_id="Ivanov Ivan",
        assignment_id="HW1",
        submission_hash="abc123",
        review_markdown="# Review",
        session_id="session-1",
        overall_score=90,
        task_id="task-1",
    )

    assert published is False
    use_case.fallback_publisher.publish_review.assert_awaited_once_with(  # type: ignore[union-attr]
        {
            "task_id": "task-1",
            "student_id": "Ivanov Ivan",
            "assignment_id": "HW1",
            "session_id": "session-1",
            "overall_score": 90,
            "new_commit": "abc123",
        }
    )


@pytest.mark.asyncio
async def test_publish_review_via_mcp_call_failure_triggers_fallback(
    review_use_case_with_mcp: ReviewSubmissionUseCase,
) -> None:
    """Fallback publisher should run when MCP tool execution fails."""

    use_case = review_use_case_with_mcp
    use_case.unified_client.make_request.return_value = ModelResponse(  # type: ignore[attr-defined]
        response=(
            '{"tool": "submit_review_result", "arguments": '
            '{"student_id": "Ivanov Ivan", "submission_hash": "abc123", '
            '"review_content": "# Review", "session_id": "session-1"}}'
        ),
        response_tokens=10,
        input_tokens=10,
        total_tokens=20,
        model_name="mistral",
        response_time=1.0,
    )

    use_case.mcp_client.discover_tools.return_value = [  # type: ignore[union-attr]
        {
            "name": "submit_review_result",
            "description": "Submit review",
            "input_schema": {"type": "object"},
        }
    ]
    use_case.mcp_client.call_tool.side_effect = RuntimeError(  # type: ignore[union-attr]
        "Tool failed"
    )

    published = await use_case._publish_review_via_mcp(  # type: ignore[attr-defined]
        student_id="Ivanov Ivan",
        assignment_id="HW1",
        submission_hash="abc123",
        review_markdown="# Review",
        session_id="session-1",
        overall_score=None,
        task_id="task-1",
    )

    assert published is False
    use_case.fallback_publisher.publish_review.assert_awaited_once()  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_publish_review_via_mcp_without_client_uses_fallback() -> None:
    """If MCP client is missing, the fallback publisher should handle output."""

    settings = Settings()
    archive_service = ZipArchiveService(settings)
    unified_client = MagicMock()
    unified_client.make_request = AsyncMock()
    fallback = AsyncMock()
    use_case = ReviewSubmissionUseCase(
        archive_reader=archive_service,
        diff_analyzer=DiffAnalyzer(),
        unified_client=unified_client,
        review_repository=MagicMock(),
        tasks_repository=MagicMock(),
        publisher=fallback,
        log_parser=MagicMock(),
        log_normalizer=MagicMock(),
        log_analyzer=MagicMock(),
        settings=settings,
        mcp_client=None,
        fallback_publisher=fallback,
    )

    published = await use_case._publish_review_via_mcp(  # type: ignore[attr-defined]
        student_id="Ivanov Ivan",
        assignment_id="HW1",
        submission_hash="abc123",
        review_markdown="# Review",
        session_id="session-1",
        overall_score=75,
        task_id="task-1",
    )

    assert published is False
    fallback.publish_review.assert_awaited_once()  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_execute_publishes_via_mcp_successfully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end check: execute() publishes via MCP with valid data."""

    unified_client = AsyncMock()
    unified_client.make_request.return_value = ModelResponse(
        response=(
            '{"tool": "submit_review_result", "arguments": '
            '{"student_id": "Ivanov Ivan", "submission_hash": "commit123", '
            '"review_content": "# Review", "session_id": "session-42", '
            '"overall_score": 88}}'
        ),
        response_tokens=10,
        input_tokens=10,
        total_tokens=20,
        model_name="mistral",
        response_time=1.0,
    )

    mcp_client = AsyncMock()
    mcp_client.discover_tools.return_value = [
        {
            "name": "submit_review_result",
            "description": "Submit review",
            "input_schema": {"type": "object"},
        }
    ]

    fallback_publisher = AsyncMock()
    review_repository = AsyncMock()
    tasks_repository = AsyncMock()
    tasks_repository.complete = AsyncMock()
    tasks_repository.fail = AsyncMock()
    tasks_repository.count_reviews_in_window = AsyncMock(return_value=0)

    report = MagicMock()
    report.session_id = "session-42"
    report.to_dict.return_value = {}
    report.to_markdown.return_value = "# Review"
    report.pass_1 = MagicMock(metadata={"overall_score": 88}, findings=[])
    report.pass_4_logs = None
    report.total_findings = 0
    report.critical_count = 0
    report.major_count = 0
    report.detected_components = []

    monkeypatch.setattr(
        "src.application.use_cases.review_submission_use_case.ModularReviewService",
        lambda **kwargs: MagicMock(review_submission=AsyncMock(return_value=report)),
    )

    use_case = ReviewSubmissionUseCase(
        archive_reader=ZipArchiveService(Settings()),
        diff_analyzer=DiffAnalyzer(),
        unified_client=unified_client,
        review_repository=review_repository,
        tasks_repository=tasks_repository,
        publisher=fallback_publisher,
        log_parser=MagicMock(),
        log_normalizer=MagicMock(),
        log_analyzer=AsyncMock(),
        settings=Settings(),
        mcp_client=mcp_client,
        fallback_publisher=fallback_publisher,
    )

    task = LongTask(
        task_id="task-commit123",
        task_type=TaskType.CODE_REVIEW,
        user_id=2001,
        status=TaskStatus.QUEUED,
        metadata={
            "new_submission_path": "/tmp/new.zip",
            "new_commit": "commit123",
        },
    )

    session_id = await use_case.execute(task)

    assert session_id == "session-42"
    mcp_client.call_tool.assert_awaited_once()  # type: ignore[attr-defined]
    fallback_publisher.publish_review.assert_not_awaited()  # type: ignore[attr-defined]
    review_repository.save_review_session.assert_awaited_once()  # type: ignore[attr-defined]
    tasks_repository.complete.assert_awaited_once()  # type: ignore[attr-defined]
