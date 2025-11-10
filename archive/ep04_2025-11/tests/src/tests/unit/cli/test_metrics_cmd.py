"""Tests for metrics command.

Following the Zen of Python:
- Simple is better than complex
- Flat is better than nested
"""

import json

from src.presentation.cli.commands.metrics_cmd import (
    display_metrics_summary,
    export_metrics_csv,
    export_metrics_json,
    reset_metrics,
)


def test_display_metrics_summary(capsys) -> None:
    """Test metrics summary display."""
    display_metrics_summary()

    captured = capsys.readouterr()
    assert "Metrics Summary" in captured.out


def test_export_metrics_json(tmp_path) -> None:
    """Test JSON export functionality."""
    output_file = tmp_path / "test_metrics.json"

    export_metrics_json(str(output_file))

    assert output_file.exists()

    with output_file.open() as f:
        data = json.load(f)

    assert "request_count" in data
    assert "total_tokens_used" in data


def test_export_metrics_csv(tmp_path) -> None:
    """Test CSV export functionality."""
    output_file = tmp_path / "test_metrics.csv"

    export_metrics_csv(str(output_file))

    assert output_file.exists()

    content = output_file.read_text()
    assert "Metric,Value" in content
    assert "Total Requests" in content


def test_reset_metrics(capsys) -> None:
    """Test metrics reset."""
    from src.infrastructure.monitoring.metrics import get_metrics

    # Set some initial state
    collector = get_metrics()
    collector.record_request(success=True, tokens_used=100)

    initial_count = collector.get_metrics()["request_count"]
    assert initial_count > 0

    # Reset
    reset_metrics()

    # Verify reset
    reset_count = collector.get_metrics()["request_count"]
    assert reset_count == 0

    captured = capsys.readouterr()
    assert "reset" in captured.out.lower()
