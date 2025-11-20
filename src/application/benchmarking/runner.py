"""Benchmark evaluation orchestration logic."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from statistics import mean
from time import perf_counter
from typing import Iterable, Sequence

from src.application.benchmarking.models import (
    BenchmarkDirection,
    BenchmarkJudgeResult,
    BenchmarkMetricResult,
    BenchmarkMetricRule,
    BenchmarkOutcome,
    BenchmarkRunResult,
    BenchmarkSample,
    BenchmarkSampleResult,
    BenchmarkScenarioConfig,
)
from src.application.benchmarking.protocols import (
    BenchmarkDatasetProvider,
    BenchmarkJudge,
    BenchmarkMetricsRecorder,
)


class BenchmarkEvaluationRunner:
    """Coordinate dataset loading, judge calls, and metric recording.

    Purpose:
        Execute configured benchmark scenarios end-to-end by loading samples,
        invoking the LLM-as-judge, applying thresholds, and exporting metrics.

    Args:
        dataset_provider: Loader supplying benchmark samples.
        judge: Component executing LLM-as-judge evaluations.
        metrics_recorder: Publisher for metric exports (e.g., Prometheus).
        max_concurrency: Maximum number of concurrent judge calls.

    Returns:
        None.

    Raises:
        ValueError: If no samples are found for a scenario.

    Example:
        >>> runner = BenchmarkEvaluationRunner(provider, judge, recorder, 4)
        >>> result = await runner.run(scenario)
        >>> result.overall.value
        'pass'
    """

    def __init__(
        self,
        dataset_provider: BenchmarkDatasetProvider,
        judge: BenchmarkJudge,
        metrics_recorder: BenchmarkMetricsRecorder,
        max_concurrency: int = 4,
    ) -> None:
        self._dataset_provider = dataset_provider
        self._judge = judge
        self._metrics_recorder = metrics_recorder
        self._max_concurrency = max_concurrency

    async def run(self, scenario: BenchmarkScenarioConfig) -> BenchmarkRunResult:
        """Execute a benchmark scenario.

        Purpose:
            Load samples, evaluate them, aggregate metrics, and publish results.

        Args:
            scenario: Scenario configuration describing dataset and thresholds.

        Returns:
            BenchmarkRunResult with per-sample and aggregate metrics.

        Raises:
            ValueError: When the dataset contains no samples.

        Example:
            >>> result = await runner.run(scenario)
            >>> result.scenario_id == scenario.scenario_id
            True
        """

        start_time = perf_counter()
        samples = await self._load_samples(scenario)
        sample_results = await self._evaluate_samples(scenario, samples)
        aggregate_metrics = self._aggregate(sample_results, scenario.metrics)
        run_result = self._assemble_result(
            scenario=scenario,
            sample_results=sample_results,
            aggregate_metrics=aggregate_metrics,
            duration=perf_counter() - start_time,
        )
        self._metrics_recorder.record_run(run_result)
        return run_result

    async def _load_samples(
        self, scenario: BenchmarkScenarioConfig
    ) -> Sequence[BenchmarkSample]:
        samples = await self._dataset_provider.load_samples(scenario)
        if not samples:
            raise ValueError(
                f"No samples loaded for scenario '{scenario.scenario_id}'."
            )
        return samples

    async def _evaluate_samples(
        self,
        scenario: BenchmarkScenarioConfig,
        samples: Sequence[BenchmarkSample],
    ) -> tuple[BenchmarkSampleResult, ...]:
        semaphore = asyncio.Semaphore(self._max_concurrency)

        async def _evaluate(sample: BenchmarkSample) -> BenchmarkSampleResult:
            async with semaphore:
                judge_result = await self._judge.evaluate(sample, scenario)
                return self._build_sample_result(
                    sample=sample,
                    judge_result=judge_result,
                    metric_rules=scenario.metrics,
                )

        tasks = [_evaluate(sample) for sample in samples]
        results = await asyncio.gather(*tasks)
        return tuple(results)

    def _build_sample_result(
        self,
        sample: BenchmarkSample,
        judge_result: BenchmarkJudgeResult,
        metric_rules: Sequence[BenchmarkMetricRule],
    ) -> BenchmarkSampleResult:
        metric_results = [
            self._evaluate_metric(rule, judge_result.scores.get(rule.name, 0.0))
            for rule in metric_rules
        ]
        return BenchmarkSampleResult(
            sample_id=sample.sample_id,
            metrics=tuple(metric_results),
            verdict=judge_result.verdict,
            notes=judge_result.notes,
        )

    def _evaluate_metric(
        self,
        rule: BenchmarkMetricRule,
        observed: float,
    ) -> BenchmarkMetricResult:
        if rule.direction is BenchmarkDirection.HIGHER_IS_BETTER:
            if observed >= rule.pass_value:
                outcome = BenchmarkOutcome.PASS
            elif observed >= rule.warn_value:
                outcome = BenchmarkOutcome.WARN
            else:
                outcome = BenchmarkOutcome.FAIL
        else:
            if observed <= rule.pass_value:
                outcome = BenchmarkOutcome.PASS
            elif observed <= rule.warn_value:
                outcome = BenchmarkOutcome.WARN
            else:
                outcome = BenchmarkOutcome.FAIL
        return BenchmarkMetricResult(name=rule.name, value=observed, outcome=outcome)

    def _aggregate(
        self,
        samples: Iterable[BenchmarkSampleResult],
        rules: Sequence[BenchmarkMetricRule],
    ) -> tuple[BenchmarkMetricResult, ...]:
        values: dict[str, list[float]] = defaultdict(list)
        outcomes: dict[str, BenchmarkOutcome] = {}
        for sample in samples:
            for metric in sample.metrics:
                values[metric.name].append(metric.value)
                outcomes[metric.name] = self._worst_outcome(
                    outcomes.get(metric.name, BenchmarkOutcome.PASS),
                    metric.outcome,
                )

        aggregated = []
        for rule in rules:
            metric_values = values.get(rule.name, [0.0])
            aggregated.append(
                BenchmarkMetricResult(
                    name=rule.name,
                    value=mean(metric_values),
                    outcome=outcomes.get(rule.name, BenchmarkOutcome.FAIL),
                )
            )
        return tuple(aggregated)

    @staticmethod
    def _worst_outcome(
        current: BenchmarkOutcome, contender: BenchmarkOutcome
    ) -> BenchmarkOutcome:
        order = {
            BenchmarkOutcome.PASS: 0,
            BenchmarkOutcome.WARN: 1,
            BenchmarkOutcome.FAIL: 2,
        }
        return contender if order[contender] > order[current] else current

    def _overall_outcome(
        self, metrics: Sequence[BenchmarkMetricResult]
    ) -> BenchmarkOutcome:
        outcome = BenchmarkOutcome.PASS
        for metric in metrics:
            outcome = self._worst_outcome(outcome, metric.outcome)
        return outcome

    def _assemble_result(
        self,
        scenario: BenchmarkScenarioConfig,
        sample_results: Sequence[BenchmarkSampleResult],
        aggregate_metrics: Sequence[BenchmarkMetricResult],
        duration: float,
    ) -> BenchmarkRunResult:
        metadata = {
            "model_name": scenario.model_name,
            "prompt_version": scenario.prompt_version,
            "sample_count": len(sample_results),
            "duration_seconds": duration,
        }
        metadata.update(scenario.extra_metadata)
        return BenchmarkRunResult(
            scenario_id=scenario.scenario_id,
            dataset_id=scenario.dataset_id,
            overall=self._overall_outcome(aggregate_metrics),
            metrics=tuple(aggregate_metrics),
            samples=tuple(sample_results),
            metadata=metadata,
        )
