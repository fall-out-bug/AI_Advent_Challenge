"""Tests for enhanced metrics with percentile calculations."""

import pytest

from src.infrastructure.monitoring.metrics import MetricsCollector


class TestMetricsPercentiles:
    """Test percentile calculations in metrics."""

    def test_percentiles_empty(self) -> None:
        """Test percentiles when no data."""
        metrics = MetricsCollector()
        percentiles = metrics.get_percentiles()

        assert percentiles["p50"] == 0.0
        assert percentiles["p95"] == 0.0
        assert percentiles["p99"] == 0.0

    def test_percentiles_single_value(self) -> None:
        """Test percentiles with single value."""
        metrics = MetricsCollector()
        metrics.record_request(
            success=True,
            response_time_ms=100.0,
            operation="test",
        )

        percentiles = metrics.get_percentiles()

        assert percentiles["p50"] == 100.0
        assert percentiles["p95"] == 100.0
        assert percentiles["p99"] == 100.0

    def test_percentiles_multiple_values(self) -> None:
        """Test percentiles with multiple values."""
        metrics = MetricsCollector()

        # Record 100 requests with varying response times
        for i in range(100):
            metrics.record_request(
                success=True,
                response_time_ms=float(i),
                operation="test",
            )

        percentiles = metrics.get_percentiles()

        assert percentiles["p50"] == pytest.approx(50.0, rel=1.0)
        assert percentiles["p95"] == pytest.approx(95.0, rel=1.0)
        assert percentiles["p99"] == pytest.approx(99.0, rel=1.0)

    def test_percentiles_in_metrics(self) -> None:
        """Test that percentiles are included in get_metrics."""
        metrics = MetricsCollector()

        # Record some requests
        for i in range(50):
            metrics.record_request(
                success=True,
                response_time_ms=float(i * 10),
                operation="test",
            )

        metrics_data = metrics.get_metrics()

        assert "response_time_percentiles" in metrics_data
        percentiles = metrics_data["response_time_percentiles"]

        assert "p50" in percentiles
        assert "p95" in percentiles
        assert "p99" in percentiles
        assert percentiles["p50"] > 0
        assert percentiles["p99"] > percentiles["p50"]

    def test_rolling_window(self) -> None:
        """Test rolling window limits data size."""
        metrics = MetricsCollector(rolling_window_size=10)

        # Record more requests than window size
        for i in range(100):
            metrics.record_request(
                success=True,
                response_time_ms=float(i),
                operation="test",
            )

        # Should only have last 10 values
        percentiles = metrics.get_percentiles()

        # Should not include early values
        assert percentiles["p99"] < 100.0

    def test_zero_response_time(self) -> None:
        """Test that zero response times are handled."""
        metrics = MetricsCollector()

        metrics.record_request(
            success=True,
            response_time_ms=0.0,
            operation="test",
        )

        percentiles = metrics.get_percentiles()

        assert percentiles["p50"] == 0.0
