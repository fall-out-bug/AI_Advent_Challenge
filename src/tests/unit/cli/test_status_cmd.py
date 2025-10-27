"""Tests for status command.

Following TDD principles:
- Write tests first
- Test behavior, not implementation
- One test per assertion where possible
"""

import pytest
from unittest.mock import patch, MagicMock
from rich.console import Console

from src.presentation.cli.commands.status_cmd import (
    display_status,
    _display_recent_operations,
    _display_token_usage,
)


def test_display_status(capsys) -> None:
    """Test status display."""
    display_status()

    captured = capsys.readouterr()
    output = captured.out

    assert "System Status" in output


@patch("src.presentation.cli.commands.status_cmd.get_metrics")
def test_display_recent_operations_empty(mock_get_metrics, capsys) -> None:
    """Test display of empty recent operations."""
    mock_metrics = MagicMock()
    mock_metrics.get_recent_operations.return_value = []
    mock_get_metrics.return_value = mock_metrics

    console = Console()
    _display_recent_operations(console)

    captured = capsys.readouterr()
    assert "No recent operations" in captured.out


@patch("src.presentation.cli.commands.status_cmd.get_metrics")
def test_display_recent_operations_with_data(mock_get_metrics, capsys) -> None:
    """Test display with recent operations data."""
    mock_metrics = MagicMock()
    mock_metrics.get_recent_operations.return_value = [
        {
            "timestamp": "2024-01-01T12:00:00",
            "operation": "test_op",
            "response_time_ms": 100.0,
            "success": True,
        }
    ]
    mock_get_metrics.return_value = mock_metrics

    console = Console()
    _display_recent_operations(console, limit=1)

    captured = capsys.readouterr()
    assert "test_op" in captured.out


def test_display_token_usage_empty(capsys) -> None:
    """Test display with no token usage."""
    console = Console()
    metrics = {"token_usage_by_operation": {}}

    _display_token_usage(console, metrics)

    # Should not crash with empty token usage


def test_display_token_usage_with_data(capsys) -> None:
    """Test display with token usage data."""
    console = Console()
    metrics = {
        "token_usage_by_operation": {
            "operation1": 100,
            "operation2": 200,
        }
    }

    _display_token_usage(console, metrics)

    captured = capsys.readouterr()
    assert "operation1" in captured.out
    assert "operation2" in captured.out
