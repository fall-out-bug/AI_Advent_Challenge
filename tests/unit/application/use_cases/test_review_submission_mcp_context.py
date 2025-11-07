"""Tests for MCP publish context preparation in ReviewSubmissionUseCase."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.use_cases.review_submission_use_case import (
    ReviewSubmissionUseCase,
)
from src.infrastructure.config.settings import Settings
from src.presentation.mcp.http_client import MCPHTTPClient


@pytest.fixture
def review_use_case(monkeypatch: pytest.MonkeyPatch) -> ReviewSubmissionUseCase:
    """Create ReviewSubmissionUseCase with patched reviewer agent."""

    class _DummyAgent:
        def __init__(self, *args, **kwargs) -> None:
            return

    monkeypatch.setattr(
        "src.application.use_cases.review_submission_use_case.MultiPassReviewerAgent",
        _DummyAgent,
    )

    return ReviewSubmissionUseCase(
        archive_reader=MagicMock(),
        diff_analyzer=MagicMock(),
        unified_client=MagicMock(),
        review_repository=MagicMock(),
        tasks_repository=MagicMock(),
        publisher=MagicMock(),
        log_parser=MagicMock(),
        log_normalizer=MagicMock(),
        log_analyzer=MagicMock(),
        settings=Settings(),
    )


@pytest.mark.asyncio
async def test_prepare_mcp_publish_context_returns_prompt_and_tool(
    review_use_case: ReviewSubmissionUseCase,
) -> None:
    """Ensure prompt includes required details and tool list is filtered."""

    mcp_client = AsyncMock(spec=MCPHTTPClient)
    mcp_client.discover_tools.return_value = [
        {
            "name": "submit_review_result",
            "description": "Submit review result to HW checker",
            "input_schema": {"type": "object"},
        },
        {
            "name": "unused_tool",
            "description": "Irrelevant",
            "input_schema": {},
        },
    ]

    prompt, tools = await review_use_case._prepare_mcp_publish_context(  # type: ignore[attr-defined]
        mcp_client=mcp_client,
        student_id="Ivanov Ivan",
        submission_hash="abc123",
        review_markdown="# Review\nEverything looks good.",
        session_id="session-1",
        overall_score=92,
    )

    mcp_client.discover_tools.assert_awaited_once()
    assert len(tools) == 1
    assert tools[0]["name"] == "submit_review_result"
    assert "Ivanov Ivan" in prompt
    assert "abc123" in prompt
    assert "submit_review_result" in prompt


@pytest.mark.asyncio
async def test_prepare_mcp_publish_context_raises_when_tool_missing(
    review_use_case: ReviewSubmissionUseCase,
) -> None:
    """Raise error when required MCP tool is not available."""

    mcp_client = AsyncMock(spec=MCPHTTPClient)
    mcp_client.discover_tools.return_value = [
        {
            "name": "other_tool",
            "description": "Not the expected one",
            "input_schema": {},
        }
    ]

    with pytest.raises(RuntimeError, match="submit_review_result tool not available"):
        await review_use_case._prepare_mcp_publish_context(  # type: ignore[attr-defined]
            mcp_client=mcp_client,
            student_id="Ivanov Ivan",
            submission_hash="abc123",
            review_markdown="# Review",
            session_id="session-1",
            overall_score=90,
        )

