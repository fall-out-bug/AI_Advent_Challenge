"""Unit tests for benchmark evaluation runner."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Sequence

import pytest

from src.application.benchmarking.models import (
    BenchmarkDirection,
    BenchmarkJudgeResult,
    BenchmarkMetricRule,
    BenchmarkOutcome,
    BenchmarkSample,
    BenchmarkScenarioConfig,
)
from src.application.benchmarking.runner import BenchmarkEvaluationRunner
from src.application.benchmarking.protocols import (
    BenchmarkDatasetProvider,
    BenchmarkJudge,
    BenchmarkMetricsRecorder,
)


class _StubDatasetProvider(BenchmarkDatasetProvider):
    def __init__(self, samples: Sequence[BenchmarkSample]) -> None:
        self._samples = samples

    async def load_samples(
        self, scenario: BenchmarkScenarioConfig
    ) -> Sequence[BenchmarkSample]:
        return self._samples


class _StubJudge(BenchmarkJudge):
    def __init__(self, results: Sequence[BenchmarkJudgeResult]) -> None:
        self._results = results
        self._index = 0

    async def evaluate(
        self, sample: BenchmarkSample, scenario: BenchmarkScenarioConfig
    ) -> BenchmarkJudgeResult:
        result = self._results[self._index]
        self._index += 1
        return result


class _Recorder(BenchmarkMetricsRecorder):
    def __init__(self) -> None:
        self.run_result = None

    def record_run(self, run_result):
        self.run_result = run_result


@pytest.mark.asyncio
async def test_runner_aggregates_metrics() -> None:
    """Runner aggregates sample metrics and records overall outcome."""

    scenario = BenchmarkScenarioConfig(
        scenario_id="digest_ru",
        dataset_path=Path("data/benchmarks/benchmark_digest_ru_v1/placeholder.jsonl"),
        dataset_id="benchmark_digest_ru_v1",
        model_name="gpt-4o",
        prompt_version="benchmark-2025-11-v1",
        metrics=(
            BenchmarkMetricRule(
                name="coverage",
                direction=BenchmarkDirection.HIGHER_IS_BETTER,
                pass_value=0.9,
                warn_value=0.85,
            ),
            BenchmarkMetricRule(
                name="latency_seconds",
                direction=BenchmarkDirection.LOWER_IS_BETTER,
                pass_value=210.0,
                warn_value=240.0,
            ),
        ),
    )
    samples = (
        BenchmarkSample(
            sample_id="sample-1",
            source_text="Original text A",
            summary_text="Summary A",
            metadata={"language": "ru"},
        ),
        BenchmarkSample(
            sample_id="sample-2",
            source_text="Original text B",
            summary_text="Summary B",
            metadata={"language": "ru"},
        ),
    )
    judge_results = (
        BenchmarkJudgeResult(
            scores={"coverage": 0.92, "latency_seconds": 205.0},
            verdict="MEETS_EXPECTATIONS",
        ),
        BenchmarkJudgeResult(
            scores={"coverage": 0.83, "latency_seconds": 230.0},
            verdict="WARN",
        ),
    )

    recorder = _Recorder()
    runner = BenchmarkEvaluationRunner(
        dataset_provider=_StubDatasetProvider(samples),
        judge=_StubJudge(judge_results),
        metrics_recorder=recorder,
        max_concurrency=2,
    )

    result = await runner.run(scenario)

    assert result.overall is BenchmarkOutcome.FAIL
    assert len(result.samples) == 2
    coverage_metric = next(m for m in result.metrics if m.name == "coverage")
    latency_metric = next(m for m in result.metrics if m.name == "latency_seconds")
    assert coverage_metric.outcome is BenchmarkOutcome.FAIL
    assert pytest.approx(coverage_metric.value, 0.01) == 0.875
    assert latency_metric.outcome is BenchmarkOutcome.WARN
    assert pytest.approx(latency_metric.value, 0.01) == 217.5
    assert recorder.run_result is result


@pytest.mark.asyncio
async def test_runner_raises_on_empty_dataset() -> None:
    """Runner fails fast when dataset provider returns no samples."""

    scenario = BenchmarkScenarioConfig(
        scenario_id="empty",
        dataset_path=Path("data/benchmarks/empty.jsonl"),
        dataset_id="empty",
        model_name="gpt-4o",
        prompt_version="benchmark-2025-11-v1",
        metrics=(
            BenchmarkMetricRule(
                name="coverage",
                direction=BenchmarkDirection.HIGHER_IS_BETTER,
                pass_value=0.9,
                warn_value=0.85,
            ),
        ),
    )

    runner = BenchmarkEvaluationRunner(
        dataset_provider=_StubDatasetProvider(tuple()),
        judge=_StubJudge(tuple()),
        metrics_recorder=_Recorder(),
    )

    with pytest.raises(ValueError):
        await runner.run(scenario)
