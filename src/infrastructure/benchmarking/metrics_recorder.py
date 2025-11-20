"""Prometheus metrics recorder for benchmark runs."""

from __future__ import annotations

from typing import Protocol

from src.application.benchmarking.models import (
    BenchmarkMetricResult,
    BenchmarkOutcome,
    BenchmarkRunResult,
)
from src.application.benchmarking.protocols import BenchmarkMetricsRecorder

try:
    from prometheus_client import Gauge, Histogram  # type: ignore
except ImportError:  # pragma: no cover
    # Fallback no-op metrics when Prometheus client is unavailable
    class _DummyMetric:  # type: ignore
        def labels(self, *args, **kwargs):  # type: ignore
            return self

        def observe(self, *args, **kwargs):  # type: ignore
            return None

        def set(self, *args, **kwargs):  # type: ignore
            return None

    Gauge = Histogram = _DummyMetric  # type: ignore

benchmark_run_duration = Histogram(
    "benchmark_run_duration_seconds",
    "Duration of benchmark scenario executions",
    labelnames=("scenario", "dataset"),
)
benchmark_run_outcome = Gauge(
    "benchmark_run_outcome",
    "Outcome of the latest benchmark run (0=pass, 1=warn, 2=fail)",
    labelnames=("scenario", "dataset"),
)
benchmark_metric_value = Gauge(
    "benchmark_metric_value",
    "Aggregate metric value for benchmark runs",
    labelnames=("scenario", "dataset", "metric"),
)
benchmark_metric_outcome = Gauge(
    "benchmark_metric_outcome",
    "Outcome of benchmark metrics (0=pass, 1=warn, 2=fail)",
    labelnames=("scenario", "dataset", "metric"),
)


class OutcomeToFloat(Protocol):
    """Protocol describing conversion to numeric status.

    Purpose:
        Allow dependency injection for mapping outcomes in testing.

    Args:
        outcome: Benchmark outcome.

    Returns:
        Float representation of the outcome.

    Raises:
        None.

    Example:
        >>> converter(BenchmarkOutcome.PASS)
        0.0
    """

    def __call__(self, outcome: BenchmarkOutcome) -> float:
        ...


def default_outcome_mapper(outcome: BenchmarkOutcome) -> float:
    """Map BenchmarkOutcome to numeric representation.

    Purpose:
        Provide Prometheus-friendly encoding for outcome gauges.

    Args:
        outcome: Outcome enumeration value.

    Returns:
        Float value (0.0 pass, 1.0 warn, 2.0 fail).

    Raises:
        None.

    Example:
        >>> default_outcome_mapper(BenchmarkOutcome.WARN)
        1.0
    """

    mapping = {
        BenchmarkOutcome.PASS: 0.0,
        BenchmarkOutcome.WARN: 1.0,
        BenchmarkOutcome.FAIL: 2.0,
    }
    return mapping[outcome]


class PrometheusBenchmarkRecorder(BenchmarkMetricsRecorder):
    """Record benchmark results using Prometheus metrics.

    Purpose:
        Persist run-level and metric-level status information for dashboards
        and alerting pipelines aligned with Stage 05 requirements.

    Args:
        outcome_mapper: Optional custom mapping for numeric outcome encoding.

    Returns:
        Recorder instance ready for use by BenchmarkEvaluationRunner.

    Raises:
        None.

    Example:
        >>> recorder = PrometheusBenchmarkRecorder()
        >>> recorder.record_run(run_result)
    """

    def __init__(self, outcome_mapper: OutcomeToFloat = default_outcome_mapper) -> None:
        self._outcome_mapper = outcome_mapper

    def record_run(self, run_result: BenchmarkRunResult) -> None:
        """Publish benchmark run metrics to Prometheus.

        Purpose:
            Emit duration, outcome, and metric gauges so dashboards can display
            Stage 05 benchmark health.

        Args:
            run_result: Benchmark run result to export.

        Returns:
            None.

        Raises:
            None.

        Example:
            >>> recorder.record_run(run_result)
        """

        duration = float(run_result.metadata.get("duration_seconds", 0.0))
        scenario = run_result.scenario_id
        dataset = run_result.dataset_id
        benchmark_run_duration.labels(scenario, dataset).observe(duration)
        benchmark_run_outcome.labels(scenario, dataset).set(
            self._outcome_mapper(run_result.overall)
        )
        for metric in run_result.metrics:
            self._record_metric(scenario, dataset, metric)

    def _record_metric(
        self,
        scenario: str,
        dataset: str,
        metric: BenchmarkMetricResult,
    ) -> None:
        benchmark_metric_value.labels(scenario, dataset, metric.name).set(metric.value)
        benchmark_metric_outcome.labels(scenario, dataset, metric.name).set(
            self._outcome_mapper(metric.outcome)
        )
