"""Tests for presentation-layer homework handler."""

from __future__ import annotations

import base64
from unittest.mock import AsyncMock

import pytest

from src.application.dtos.butler_dialog_dtos import DialogContext, DialogState
from src.application.dtos.homework_dtos import (
    HomeworkListResult,
    HomeworkReviewResult,
    HomeworkSubmission,
)
from src.presentation.bot.handlers.homework import HomeworkHandler


@pytest.mark.asyncio
async def test_handle_list_homeworks_formats_response() -> None:
    """Should render homework list using list use case output."""
    list_use_case = AsyncMock()
    review_use_case = AsyncMock()

    list_use_case.execute.return_value = HomeworkListResult(
        total=1,
        submissions=[
            HomeworkSubmission(
                commit_hash="abc1234",
                archive_name="student_hw1.zip",
                assignment="HW1",
                commit_dttm="2025-11-09T12:00:00Z",
                status="passed",
            )
        ],
    )

    handler = HomeworkHandler(
        list_use_case=list_use_case,
        review_use_case=review_use_case,
    )
    context = DialogContext(
        state=DialogState.IDLE,
        user_id="42",
        session_id="sess-1",
    )

    response = await handler.handle(context, "Покажи домашки за 3 дня")

    list_use_case.execute.assert_awaited_once()
    assert "📚 Домашки за последние 3 дней" in response
    assert "student\\_hw1.zip" in response
    assert "Коммит: abc1234" in response


@pytest.mark.asyncio
async def test_handle_review_homework_returns_file_payload() -> None:
    """Should return file payload with encoded markdown."""
    list_use_case = AsyncMock()
    review_use_case = AsyncMock()
    review_use_case.execute.return_value = HomeworkReviewResult(
        success=True,
        markdown_report="# Report\nOK",
        total_findings=0,
        detected_components=[],
        pass_2_components=[],
        execution_time_seconds=1.2,
    )

    handler = HomeworkHandler(
        list_use_case=list_use_case,
        review_use_case=review_use_case,
    )
    context = DialogContext(
        state=DialogState.IDLE,
        user_id="42",
        session_id="sess-1",
    )

    response = await handler.handle(context, "Сделай ревью deadbeef")

    review_use_case.execute.assert_awaited_once_with(commit_hash="deadbeef")
    assert response.startswith("FILE:review_deadbeef")
    encoded = response.split(":")[2]
    decoded = base64.b64decode(encoded).decode("utf-8")
    assert "# Report" in decoded


@pytest.mark.asyncio
async def test_handle_unknown_command_returns_help() -> None:
    """Should return help message when command not recognized."""
    handler = HomeworkHandler(
        list_use_case=AsyncMock(),
        review_use_case=AsyncMock(),
    )
    context = DialogContext(
        state=DialogState.IDLE,
        user_id="42",
        session_id="sess-1",
    )

    response = await handler.handle(context, "непонятная команда")

    assert "Не понял команду" in response
