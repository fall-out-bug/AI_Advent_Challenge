"""Tests for metrics exporter."""

import csv
import json
import tempfile
from pathlib import Path

import pytest

from src.infrastructure.monitoring.exporter import MetricsExporter
from src.infrastructure.monitoring.metrics import MetricsCollector


class TestMetricsExporter:
    """Test metrics export functionality."""

    @pytest.fixture
    def metrics(self) -> MetricsCollector:
        """Create metrics collector for testing."""
        collector = MetricsCollector()

        # Record some sample data
        for i in range(10):
            collector.record_request(
                success=i < 8,  # 80% success rate
                response_time_ms=float(i * 10),
                tokens_used=i * 100,
                operation=f"test_op_{i % 3}",
                error="Test error" if i >= 8 else None,
            )

        return collector

    def test_export_to_json(self, metrics: MetricsCollector) -> None:
        """Test JSON export."""
        exporter = MetricsExporter(metrics)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            exporter.export_to_json(filepath)

            # Verify file was created
            assert Path(filepath).exists()

            # Verify JSON is valid
            with Path(filepath).open() as f:
                data = json.load(f)

            assert "request_count" in data
            assert data["request_count"] == 10

            assert "success_rate" in data
            assert data["success_rate"] == 0.8

            assert "token_usage_by_operation" in data
            assert len(data["token_usage_by_operation"]) > 0

        finally:
            Path(filepath).unlink()

    def test_export_to_json_with_history(self, metrics: MetricsCollector) -> None:
        """Test JSON export with operation history."""
        exporter = MetricsExporter(metrics)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            exporter.export_to_json(filepath, include_history=True)

            with Path(filepath).open() as f:
                data = json.load(f)

            assert "recent_operations" in data
            assert len(data["recent_operations"]) > 0

        finally:
            Path(filepath).unlink()

    def test_export_to_csv(self, metrics: MetricsCollector) -> None:
        """Test CSV export."""
        exporter = MetricsExporter(metrics)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            filepath = f.name

        try:
            exporter.export_to_csv(filepath)

            # Verify file was created
            assert Path(filepath).exists()

            # Verify CSV is valid
            with Path(filepath).open() as f:
                reader = csv.reader(f)
                rows = list(reader)

            assert len(rows) > 5  # Should have several rows
            assert rows[0][0] == "Metric"  # Header row

        finally:
            Path(filepath).unlink()

    def test_export_to_markdown(self, metrics: MetricsCollector) -> None:
        """Test Markdown export."""
        exporter = MetricsExporter(metrics)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            filepath = f.name

        try:
            exporter.export_to_markdown(filepath)

            # Verify file was created
            assert Path(filepath).exists()

            # Verify Markdown content
            with Path(filepath).open() as f:
                content = f.read()

            assert "# Metrics Report" in content
            assert "Total Requests" in content
            assert "Success Rate" in content

        finally:
            Path(filepath).unlink()

    def test_export_to_markdown_with_history(self, metrics: MetricsCollector) -> None:
        """Test Markdown export with operation history."""
        exporter = MetricsExporter(metrics)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            filepath = f.name

        try:
            exporter.export_to_markdown(filepath, include_history=True)

            with Path(filepath).open() as f:
                content = f.read()

            assert "Recent Operations" in content
            assert "| Timestamp" in content  # Table header

        finally:
            Path(filepath).unlink()

    def test_export_handles_empty_metrics(self) -> None:
        """Test export handles empty metrics gracefully."""
        metrics = MetricsCollector()
        exporter = MetricsExporter(metrics)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            exporter.export_to_json(filepath)

            with Path(filepath).open() as f:
                data = json.load(f)

            assert data["request_count"] == 0
            assert data["success_rate"] == 0.0

        finally:
            Path(filepath).unlink()
