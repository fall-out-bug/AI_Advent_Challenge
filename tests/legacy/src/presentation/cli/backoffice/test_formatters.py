"""Tests for backoffice CLI output formatters."""

from __future__ import annotations

import json

import pytest

from src.presentation.cli.backoffice.formatters import OutputFormat, format_output


def test_format_output_json() -> None:
    """Formatter should return valid JSON string."""
    payload = {
        "channel": "tech_news",
        "status": "active",
        "tags": ["analytics", "news"],
    }

    result = format_output(payload, OutputFormat.JSON)

    parsed = json.loads(result)
    assert parsed["channel"] == "tech_news"
    assert parsed["tags"] == ["analytics", "news"]


@pytest.mark.parametrize(
    "payload,expected_fragments",
    [
        (
            [
                {"name": "channel_a", "status": "active"},
                {"name": "channel_b", "status": "archived"},
            ],
            ["channel_a", "channel_b", "status"],
        ),
        (
            {"name": "channel_a", "status": "active"},
            ["channel_a", "active"],
        ),
        (
            "plain-string",
            ["plain-string"],
        ),
    ],
)
def test_format_output_table(payload: object, expected_fragments: list[str]) -> None:
    """Formatter should produce readable table output."""
    result = format_output(payload, OutputFormat.TABLE)

    assert result  # non-empty
    for fragment in expected_fragments:
        assert fragment in result
