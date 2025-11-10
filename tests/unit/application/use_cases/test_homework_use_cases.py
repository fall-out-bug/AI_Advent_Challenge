"""Tests for homework-related application use cases."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from src.application.dtos.homework_dtos import (
    HomeworkListResult,
    HomeworkReviewResult,
    HomeworkSubmission,
)
from src.application.use_cases.list_homework_submissions import (
    ListHomeworkSubmissionsUseCase,
)
from src.application.use_cases.review_homework_use_case import ReviewHomeworkUseCase
from src.domain.interfaces.homework_checker import HomeworkCheckerProtocol
from src.domain.interfaces.tool_client import ToolClientProtocol


class DummyToolClient(ToolClientProtocol):
    """Simple test double for ToolClientProtocol."""

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:  # type: ignore[override]
        raise NotImplementedError("DummyToolClient should be mocked in tests")

    async def discover_tools(self) -> list[dict]:  # pragma: no cover - unused
        return []


class DummyHomeworkChecker(HomeworkCheckerProtocol):
    """Simple test double for HomeworkCheckerProtocol."""

    async def get_recent_commits(self, days: int) -> dict:  # type: ignore[override]
        raise NotImplementedError("DummyHomeworkChecker should be mocked in tests")

    async def download_archive(self, commit_hash: str) -> bytes:  # type: ignore[override]
        raise NotImplementedError("DummyHomeworkChecker should be mocked in tests")


@pytest.mark.asyncio
async def test_list_homework_submissions_success() -> None:
    """Should return structured submissions when checker responds."""
    checker = DummyHomeworkChecker()
    checker.get_recent_commits = AsyncMock(  # type: ignore[assignment]
        return_value={
            "total": 2,
            "commits": [
                {
                    "commit_hash": "abc1234",
                    "archive_name": "hw1.zip",
                    "assignment": "HW1",
                    "commit_dttm": "2025-11-09T10:00:00Z",
                    "status": "passed",
                },
                {
                    "commit_hash": "def5678",
                    "archive_name": "hw2.zip",
                    "assignment": "HW2",
                    "commit_dttm": "2025-11-08T12:00:00Z",
                    "status": "failed",
                },
            ],
        }
    )

    use_case = ListHomeworkSubmissionsUseCase(homework_checker=checker)

    result = await use_case.execute(days=3)

    checker.get_recent_commits.assert_awaited_once_with(days=3)
    assert isinstance(result, HomeworkListResult)
    assert result.total == 2
    assert len(result.submissions) == 2
    assert result.submissions[0] == HomeworkSubmission(
        commit_hash="abc1234",
        archive_name="hw1.zip",
        assignment="HW1",
        commit_dttm="2025-11-09T10:00:00Z",
        status="passed",
    )


@pytest.mark.asyncio
async def test_review_homework_success(tmp_path: Path) -> None:
    """Should call tool with downloaded archive and return structured result."""
    checker = DummyHomeworkChecker()
    checker.download_archive = AsyncMock(  # type: ignore[assignment]
        return_value=b"fake-zip-bytes"
    )

    tool_client = DummyToolClient()
    tool_client.call_tool = AsyncMock(  # type: ignore[assignment]
        return_value={
            "success": True,
            "markdown_report": "# Report\n\nAll good.",
            "total_findings": 1,
            "detected_components": ["spark"],
            "pass_2_components": ["pass_2_spark"],
            "execution_time_seconds": 3.5,
        }
    )

    use_case = ReviewHomeworkUseCase(
        homework_checker=checker,
        tool_client=tool_client,
        temp_directory=tmp_path,
    )

    result = await use_case.execute(commit_hash="abc1234")

    checker.download_archive.assert_awaited_once_with("abc1234")
    tool_client.call_tool.assert_awaited_once()

    assert isinstance(result, HomeworkReviewResult)
    assert result.success is True
    assert result.markdown_report.startswith("# Report")
    assert result.total_findings == 1
    assert result.detected_components == ["spark"]
    assert result.pass_2_components == ["pass_2_spark"]


@pytest.mark.asyncio
async def test_review_homework_failure_raises(tmp_path: Path) -> None:
    """Should raise error when tool reports failure."""
    checker = DummyHomeworkChecker()
    checker.download_archive = AsyncMock(  # type: ignore[assignment]
        return_value=b"fake-zip-bytes"
    )

    tool_client = DummyToolClient()
    tool_client.call_tool = AsyncMock(  # type: ignore[assignment]
        return_value={"success": False, "error": "timeout"}
    )

    use_case = ReviewHomeworkUseCase(
        homework_checker=checker,
        tool_client=tool_client,
        temp_directory=tmp_path,
    )

    with pytest.raises(RuntimeError) as exc:
        await use_case.execute(commit_hash="deadbeef")

    assert "Review tool returned failure" in str(exc.value)
    checker.download_archive.assert_awaited_once()
    tool_client.call_tool.assert_awaited_once()
