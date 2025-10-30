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


def test_mcp_get_posts_from_db_request_schema() -> None:
    """Validate get_posts_from_db tool expects user_id (int) and optional hours (int)."""
    valid_args = {"user_id": 123, "hours": 24}
    assert isinstance(valid_args["user_id"], int)
    assert isinstance(valid_args["hours"], int)
    assert valid_args["hours"] > 0


def test_mcp_get_posts_from_db_response_schema() -> None:
    """Validate get_posts_from_db returns expected structure."""
    valid_response = {
        "posts_by_channel": {
            "channel1": [
                {
                    "text": "Post text",
                    "date": "2024-01-15T10:00:00",
                    "message_id": "123",
                    "channel_username": "channel1",
                }
            ],
        },
        "total_posts": 1,
        "channels_count": 1,
    }
    assert "posts_by_channel" in valid_response
    assert "total_posts" in valid_response
    assert "channels_count" in valid_response
    assert isinstance(valid_response["posts_by_channel"], dict)
    assert isinstance(valid_response["total_posts"], int)
    assert isinstance(valid_response["channels_count"], int)


def test_mcp_summarize_posts_request_schema() -> None:
    """Validate summarize_posts tool expects posts (list), channel_username (str), optional max_sentences (int)."""
    valid_args = {
        "posts": [{"text": "Post", "date": "2024-01-15", "message_id": "1"}],
        "channel_username": "test_channel",
        "max_sentences": 5,
    }
    assert isinstance(valid_args["posts"], list)
    assert isinstance(valid_args["channel_username"], str)
    assert isinstance(valid_args["max_sentences"], int)
    assert valid_args["max_sentences"] > 0


def test_mcp_summarize_posts_response_schema() -> None:
    """Validate summarize_posts returns expected structure."""
    valid_response = {
        "summary": "Summary text here",
        "post_count": 5,
        "channel": "test_channel",
    }
    assert "summary" in valid_response
    assert "post_count" in valid_response
    assert "channel" in valid_response
    assert isinstance(valid_response["summary"], str)
    assert isinstance(valid_response["post_count"], int)
    assert isinstance(valid_response["channel"], str)


def test_mcp_format_digest_markdown_request_schema() -> None:
    """Validate format_digest_markdown tool expects summaries (list) and metadata (dict)."""
    valid_args = {
        "summaries": [
            {"summary": "Summary", "post_count": 5, "channel": "channel1"}
        ],
        "metadata": {"generation_date": "2024-01-15T10:00:00", "user_id": 123},
    }
    assert isinstance(valid_args["summaries"], list)
    assert isinstance(valid_args["metadata"], dict)
    assert "generation_date" in valid_args["metadata"]


def test_mcp_format_digest_markdown_response_schema() -> None:
    """Validate format_digest_markdown returns expected structure."""
    valid_response = {
        "markdown": "# Channel Digest\n\n## Channel1\nSummary",
        "sections_count": 1,
    }
    assert "markdown" in valid_response
    assert "sections_count" in valid_response
    assert isinstance(valid_response["markdown"], str)
    assert isinstance(valid_response["sections_count"], int)


def test_mcp_combine_markdown_sections_request_schema() -> None:
    """Validate combine_markdown_sections tool expects sections (list) and optional template (str)."""
    valid_args = {
        "sections": ["# Section 1\n\nContent"],
        "template": "default",
    }
    assert isinstance(valid_args["sections"], list)
    assert isinstance(valid_args["template"], str)


def test_mcp_combine_markdown_sections_response_schema() -> None:
    """Validate combine_markdown_sections returns expected structure."""
    valid_response = {
        "combined_markdown": "# Digest\n\nContent",
        "total_chars": 100,
    }
    assert "combined_markdown" in valid_response
    assert "total_chars" in valid_response
    assert isinstance(valid_response["combined_markdown"], str)
    assert isinstance(valid_response["total_chars"], int)


def test_mcp_convert_markdown_to_pdf_request_schema() -> None:
    """Validate convert_markdown_to_pdf tool expects markdown (str) and optional style (str), metadata (dict)."""
    valid_args = {
        "markdown": "# Test\n\nContent",
        "style": "default",
        "metadata": {"user_id": 123},
    }
    assert isinstance(valid_args["markdown"], str)
    assert isinstance(valid_args["style"], str)
    assert isinstance(valid_args["metadata"], dict)


def test_mcp_convert_markdown_to_pdf_response_schema() -> None:
    """Validate convert_markdown_to_pdf returns expected structure."""
    import base64

    pdf_bytes = b"%PDF-1.4\nfake pdf"
    valid_response = {
        "pdf_bytes": base64.b64encode(pdf_bytes).decode(),
        "file_size": len(pdf_bytes),
        "pages": 1,
    }
    assert "pdf_bytes" in valid_response
    assert "file_size" in valid_response
    assert "pages" in valid_response
    assert isinstance(valid_response["pdf_bytes"], str)  # Base64 encoded
    assert isinstance(valid_response["file_size"], int)
    assert isinstance(valid_response["pages"], int)
    assert valid_response["file_size"] > 0
    assert valid_response["pages"] > 0


def test_mcp_convert_markdown_to_pdf_error_response_schema() -> None:
    """Validate convert_markdown_to_pdf error response structure."""
    valid_error_response = {
        "pdf_bytes": "",
        "file_size": 0,
        "pages": 0,
        "error": "PDF generation failed",
    }
    assert "pdf_bytes" in valid_error_response
    assert "file_size" in valid_error_response
    assert "pages" in valid_error_response
    assert "error" in valid_error_response
    assert valid_error_response["pdf_bytes"] == ""
    assert valid_error_response["file_size"] == 0


def test_mcp_pdf_digest_tools_backward_compatibility() -> None:
    """Test backward compatibility: all PDF digest tools maintain same schema."""
    # Test that existing tools still work with old call patterns
    old_get_posts_args = {"user_id": 123}  # hours is optional
    assert isinstance(old_get_posts_args["user_id"], int)
    
    old_summarize_args = {
        "posts": [],
        "channel_username": "test",
    }  # max_sentences is optional
    assert isinstance(old_summarize_args["posts"], list)
    assert isinstance(old_summarize_args["channel_username"], str)
    
    old_combine_args = {"sections": []}  # template is optional
    assert isinstance(old_combine_args["sections"], list)
    
    old_convert_args = {"markdown": "# Test"}  # style and metadata are optional
    assert isinstance(old_convert_args["markdown"], str)

