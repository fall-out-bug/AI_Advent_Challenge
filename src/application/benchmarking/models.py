"""Benchmarking data models used by the application layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, MutableMapping


class BenchmarkDirection(str, Enum):
    """Enumerate metric directionality semantics.

    Purpose:
        Distinguish metrics where higher values indicate success from those
        where lower values are preferred (e.g., latency).

    Args:
        value: Enumerated value (automatically provided by Enum).

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> BenchmarkDirection.HIGHER_IS_BETTER.value
        'higher_is_better'
    """

    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


@dataclass(frozen=True)
class BenchmarkMetricRule:
    """Describe quality thresholds for a single metric.

    Purpose:
        Capture pass, warning, and failure boundaries so the benchmarking
        runner can classify results consistently for any metric direction.

    Args:
        name: Metric identifier aligned with dataset schema (e.g., coverage).
        direction: Whether higher or lower values indicate better outcomes.
        pass_value: Value at which the metric is considered fully passing.
        warn_value: Inclusive boundary for warning state. The interpretation
            depends on the direction (lower bound for HIGHER_IS_BETTER,
            upper bound for LOWER_IS_BETTER).

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> BenchmarkMetricRule(
        ...     name="coverage",
        ...     direction=BenchmarkDirection.HIGHER_IS_BETTER,
        ...     pass_value=0.9,
        ...     warn_value=0.85,
        ... )
        BenchmarkMetricRule(name='coverage', direction=<BenchmarkDirection.HIGHER_IS_BETTER: 'higher_is_better'>, pass_value=0.9, warn_value=0.85)
    """

    name: str
    direction: BenchmarkDirection
    pass_value: float
    warn_value: float


@dataclass(frozen=True)
class BenchmarkScenarioConfig:
    """Configuration that defines a benchmark execution.

    Purpose:
        Provide the runner with dataset metadata, model configuration, and
        metric thresholds for a single scenario (e.g., RU channel digest run).

    Args:
        scenario_id: Unique identifier for the scenario (slug form).
        dataset_path: Path to the dataset (JSONL) used for the run.
        dataset_id: Logical dataset identifier stored with results.
        model_name: Model that should perform summarisation or judging.
        prompt_version: Prompt version to pass to the LLM-as-judge.
        metrics: Threshold definitions for metrics to validate.
        extra_metadata: Optional immutable metadata attached to run records.

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> BenchmarkScenarioConfig(
        ...     scenario_id="digest_ru",
        ...     dataset_path=Path("data/benchmarks/digest.jsonl"),
        ...     dataset_id="benchmark_digest_ru_v1",
        ...     model_name="gpt-4o",
        ...     prompt_version="benchmark-2025-11-v1",
        ...     metrics=(
        ...         BenchmarkMetricRule(
        ...             name="coverage",
        ...             direction=BenchmarkDirection.HIGHER_IS_BETTER,
        ...             pass_value=0.9,
        ...             warn_value=0.85,
        ...         ),
        ...     ),
        ... )
        BenchmarkScenarioConfig(scenario_id='digest_ru', dataset_path=PosixPath('data/benchmarks/digest.jsonl'), dataset_id='benchmark_digest_ru_v1', model_name='gpt-4o', prompt_version='benchmark-2025-11-v1', metrics=(BenchmarkMetricRule(name='coverage', direction=<BenchmarkDirection.HIGHER_IS_BETTER: 'higher_is_better'>, pass_value=0.9, warn_value=0.85),), extra_metadata={})
    """

    scenario_id: str
    dataset_path: Path
    dataset_id: str
    model_name: str
    prompt_version: str
    metrics: tuple[BenchmarkMetricRule, ...]
    extra_metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BenchmarkSample:
    """Represent a single benchmark sample ready for evaluation.

    Purpose:
        Encapsulate source material, generated summary, and contextual metadata
        so the runner can execute LLM-as-judge calls without additional lookups.

    Args:
        sample_id: Unique identifier within the dataset.
        source_text: Full source content used to validate the summary.
        summary_text: Generated summary to evaluate.
        metadata: Additional context (channel, timestamps, feature flags).
        baseline_scores: Optional pre-existing scores for drift comparison.

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> BenchmarkSample(
        ...     sample_id="digest-001",
        ...     source_text="Original content...",
        ...     summary_text="Summary...",
        ...     metadata={"channel": "@example"},
        ... )
        BenchmarkSample(sample_id='digest-001', source_text='Original content...', summary_text='Summary...', metadata={'channel': '@example'}, baseline_scores=None)
    """

    sample_id: str
    source_text: str
    summary_text: str
    metadata: Mapping[str, Any]
    baseline_scores: Mapping[str, float] | None = None


class BenchmarkOutcome(str, Enum):
    """Outcome classification for a metric or overall run.

    Purpose:
        Provide consistent labels for metric statuses recorded to Prometheus
        and persisted in run manifests.

    Args:
        value: Enumerated value managed by Enum.

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> BenchmarkOutcome.PASS.value
        'pass'
    """

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True)
class BenchmarkMetricResult:
    """Hold metric value and outcome for a sample or aggregate run.

    Purpose:
        Express both the measured value and the threshold evaluation so
        downstream reporting can display precise numbers with status badges.

    Args:
        name: Metric name.
        value: Observed metric value.
        outcome: Classification relative to thresholds.

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> BenchmarkMetricResult(
        ...     name="coverage",
        ...     value=0.92,
        ...     outcome=BenchmarkOutcome.PASS,
        ... )
        BenchmarkMetricResult(name='coverage', value=0.92, outcome=<BenchmarkOutcome.PASS: 'pass'>)
    """

    name: str
    value: float
    outcome: BenchmarkOutcome


@dataclass(frozen=True)
class BenchmarkSampleResult:
    """Capture per-sample evaluation outcomes.

    Purpose:
        Preserve metric results per sample to support later drill-down and
        regression analysis.

    Args:
        sample_id: Identifier of the evaluated sample.
        metrics: Collection of metric results for the sample.
        verdict: Optional textual verdict returned by LLM judge.
        notes: Optional judge notes.

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> BenchmarkSampleResult(
        ...     sample_id="digest-001",
        ...     metrics=(
        ...         BenchmarkMetricResult(
        ...             name="coverage",
        ...             value=0.9,
        ...             outcome=BenchmarkOutcome.PASS,
        ...         ),
        ...     ),
        ... )
        BenchmarkSampleResult(sample_id='digest-001', metrics=(BenchmarkMetricResult(name='coverage', value=0.9, outcome=<BenchmarkOutcome.PASS: 'pass'>),), verdict=None, notes=None)
    """

    sample_id: str
    metrics: tuple[BenchmarkMetricResult, ...]
    verdict: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class BenchmarkJudgeResult:
    """Container for raw judge output per sample.

    Purpose:
        Carry numeric scores and optional textual verdicts from the LLM judge
        so the runner can transform them into metric results.

    Args:
        scores: Mapping of metric names to numeric values in [0.0, 1.0] or
            other appropriate ranges (latency is supported as absolute value).
        verdict: Optional textual verdict from the judge.
        notes: Optional additional notes or rationale.
        metadata: Additional judge metadata (model identifiers, prompt hashes).

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> BenchmarkJudgeResult(
        ...     scores={"coverage": 0.9},
        ...     verdict="MEETS_EXPECTATIONS",
        ... )
        BenchmarkJudgeResult(scores={'coverage': 0.9}, verdict='MEETS_EXPECTATIONS', notes=None, metadata={})
    """

    scores: Mapping[str, float]
    verdict: str | None = None
    notes: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BenchmarkRunResult:
    """Aggregate outcome for a benchmark scenario run.

    Purpose:
        Summarise per-sample evaluations and overall status to feed reporting,
        CI workflows, and Prometheus metrics.

    Args:
        scenario_id: Scenario identifier.
        dataset_id: Dataset used for the run.
        overall: Overall outcome (worst metric classification).
        metrics: Aggregate metric results calculated over samples.
        samples: Detailed sample results in evaluation order.
        metadata: Arbitrary metadata persisted alongside run records.

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> BenchmarkRunResult(
        ...     scenario_id="digest_ru",
        ...     dataset_id="benchmark_digest_ru_v1",
        ...     overall=BenchmarkOutcome.PASS,
        ...     metrics=(
        ...         BenchmarkMetricResult(
        ...             name="coverage",
        ...             value=0.91,
        ...             outcome=BenchmarkOutcome.PASS,
        ...         ),
        ...     ),
        ...     samples=(),
        ...     metadata={},
        ... )
        BenchmarkRunResult(scenario_id='digest_ru', dataset_id='benchmark_digest_ru_v1', overall=<BenchmarkOutcome.PASS: 'pass'>, metrics=(BenchmarkMetricResult(name='coverage', value=0.91, outcome=<BenchmarkOutcome.PASS: 'pass'>),), samples=(), metadata={})
    """

    scenario_id: str
    dataset_id: str
    overall: BenchmarkOutcome
    metrics: tuple[BenchmarkMetricResult, ...]
    samples: tuple[BenchmarkSampleResult, ...]
    metadata: MutableMapping[str, Any] = field(default_factory=dict)
