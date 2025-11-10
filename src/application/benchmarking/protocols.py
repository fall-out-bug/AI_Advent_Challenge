"""Protocols describing benchmarking dependencies."""

from __future__ import annotations

from typing import Protocol, Sequence

from src.application.benchmarking.models import (
    BenchmarkJudgeResult,
    BenchmarkRunResult,
    BenchmarkSample,
    BenchmarkScenarioConfig,
)


class BenchmarkDatasetProvider(Protocol):
    """Protocol for loading benchmark samples.

    Purpose:
        Ensure dataset loading can be implemented by various infrastructure
        adapters (JSON, Mongo, S3) without coupling the application layer to
        specific storage solutions.

    Args:
        scenario: Scenario configuration describing dataset path and metadata.

    Returns:
        Sequence of `BenchmarkSample` objects ready for evaluation.

    Raises:
        RuntimeError: When the dataset cannot be loaded.

    Example:
        >>> provider: BenchmarkDatasetProvider
        >>> scenario = BenchmarkScenarioConfig(...)
        >>> samples = await provider.load_samples(scenario)
        >>> len(samples) > 0
        True
    """

    async def load_samples(
        self, scenario: BenchmarkScenarioConfig
    ) -> Sequence[BenchmarkSample]:
        ...


class BenchmarkJudge(Protocol):
    """Protocol for executing LLM-as-judge evaluations.

    Purpose:
        Abstract judge execution so the benchmarking runner can orchestrate
        any backend implementation (OpenAI, local models, test doubles).

    Args:
        sample: Sample to evaluate.
        scenario: Scenario configuration to supply prompt version metadata.

    Returns:
        BenchmarkJudgeResult containing metric scores and optional verdict text.

    Raises:
        RuntimeError: If the judge cannot return a valid response.

    Example:
        >>> judge: BenchmarkJudge
        >>> sample = BenchmarkSample(...)
        >>> scenario = BenchmarkScenarioConfig(...)
        >>> result = await judge.evaluate(sample, scenario)
        >>> "coverage" in result.scores
        True
    """

    async def evaluate(
        self, sample: BenchmarkSample, scenario: BenchmarkScenarioConfig
    ) -> BenchmarkJudgeResult:
        ...


class BenchmarkMetricsRecorder(Protocol):
    """Protocol for exporting benchmark run metrics to observability backends.

    Purpose:
        Allow Prometheus, logging, or alternative recorders to share the same
        runner implementation without tight coupling.

    Args:
        run_result: Benchmark run result to publish.

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> recorder: BenchmarkMetricsRecorder
        >>> recorder.record_run(run_result)
    """

    def record_run(self, run_result: BenchmarkRunResult) -> None:
        ...
