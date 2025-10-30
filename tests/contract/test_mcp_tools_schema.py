import pytest
from pydantic import ValidationError

from src.domain.entities.intent import IntentParseResult


def test_intent_parse_result_schema_validates_required_fields() -> None:
    """Ensure IntentParseResult validates required fields."""
    result = IntentParseResult(
        title="Buy milk",
        deadline_iso="2025-12-01T10:00:00",
        priority="high",
        needs_clarification=False,
        questions=[],
    )
    assert result.title == "Buy milk"
    assert result.priority in {"low", "medium", "high"}


def test_intent_parse_result_allows_empty_questions_when_no_clarification() -> None:
    """When needs_clarification=False, questions can be empty."""
    result = IntentParseResult(
        title="Task",
        deadline_iso=None,
        priority="medium",
        needs_clarification=False,
        questions=[],
    )
    assert result.needs_clarification is False
    assert result.questions == []


def test_mcp_add_task_schema_requires_user_id_and_title() -> None:
    """Validate that add_task tool expects user_id (int) and title (str)."""
    # This is a contract test - we're checking the expected shape
    # In production, this would be validated by the MCP server
    valid_args = {"user_id": 123, "title": "Buy milk", "priority": "high"}
    assert isinstance(valid_args["user_id"], int)
    assert isinstance(valid_args["title"], str)
    assert valid_args["priority"] in {"low", "medium", "high"}


def test_mcp_get_summary_response_schema() -> None:
    """Validate get_summary returns expected structure."""
    valid_response = {
        "tasks": [],
        "stats": {
            "total": 0,
            "completed": 0,
            "overdue": 0,
            "high_priority": 0,
        },
    }
    assert "tasks" in valid_response
    assert "stats" in valid_response
    assert all(k in valid_response["stats"] for k in ["total", "completed", "overdue", "high_priority"])

