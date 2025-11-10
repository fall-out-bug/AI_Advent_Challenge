"""Adapter turning summarization evaluator into benchmark judge."""

from __future__ import annotations

from typing import Any

from src.application.benchmarking.models import (
    BenchmarkJudgeResult,
    BenchmarkSample,
    BenchmarkScenarioConfig,
)
from src.application.benchmarking.protocols import BenchmarkJudge
from src.domain.value_objects.summarization_context import SummarizationContext
from src.infrastructure.llm.evaluation.summarization_evaluator import (
    SummarizationEvaluator,
)


class SummarizationJudgeAdapter(BenchmarkJudge):
    """Leverage SummarizationEvaluator for benchmark judging.

    Purpose:
        Provide a benchmarking-compatible adapter that reuses the existing
        summarisation evaluation service to obtain coverage, accuracy,
        coherence, and informativeness scores for each sample.

    Args:
        evaluator: SummarizationEvaluator instance performing LLM-as-judge
            requests.

    Returns:
        Adapter ready to evaluate benchmark samples with the configured
        evaluator.

    Raises:
        None.

    Example:
        >>> judge = SummarizationJudgeAdapter(evaluator)
        >>> result = await judge.evaluate(sample, scenario)
    """

    def __init__(self, evaluator: SummarizationEvaluator) -> None:
        self._evaluator = evaluator

    async def evaluate(
        self, sample: BenchmarkSample, scenario: BenchmarkScenarioConfig
    ) -> BenchmarkJudgeResult:
        """Execute LLM-as-judge for the provided sample.

        Purpose:
            Convert benchmark samples into summarisation evaluation calls and
            adapt the results into BenchmarkJudgeResult objects.

        Args:
            sample: Benchmark sample with source and summary text.
            scenario: Scenario metadata (used to derive language context).

        Returns:
            BenchmarkJudgeResult capturing numeric scores and verdict text.

        Raises:
            RuntimeError: When the evaluator fails to return valid scores.

        Example:
            >>> await judge.evaluate(sample, scenario)
            BenchmarkJudgeResult(...)
        """

        context = self._build_context(sample)
        evaluation = await self._evaluator.evaluate(  # type: ignore[misc]
            original_text=sample.source_text,
            summary_text=sample.summary_text,
            context=context,
            summary_metadata=self._build_summary_metadata(sample, scenario),
        )
        scores = {
            "coverage": evaluation.coverage_score,
            "accuracy": evaluation.accuracy_score,
            "coherence": evaluation.coherence_score,
            "informativeness": evaluation.informativeness_score,
        }
        if latency := sample.metadata.get("latency_seconds"):
            scores["latency_seconds"] = float(latency)
        return BenchmarkJudgeResult(
            scores=scores,
            verdict=evaluation.summary_metadata.get("llm_verdict"),
            notes=evaluation.summary_metadata.get("llm_notes"),
            metadata={
                "evaluator_model": evaluation.evaluator_model,
                "prompt_version": scenario.prompt_version,
            },
        )

    def _build_context(self, sample: BenchmarkSample) -> SummarizationContext:
        metadata = sample.metadata
        return SummarizationContext(
            language=str(metadata.get("language", "ru")),
            time_period_hours=self._int_or_none(metadata.get("time_range_hours")),
            channel_username=metadata.get("channel"),
            user_preferences=metadata.get("user_preferences", {}),
            additional_metadata={
                "feature_flags": metadata.get("feature_flags", {}),
            },
        )

    def _build_summary_metadata(
        self,
        sample: BenchmarkSample,
        scenario: BenchmarkScenarioConfig,
    ) -> dict[str, Any]:
        metadata = dict(sample.metadata)
        metadata.setdefault("scenario_id", scenario.scenario_id)
        metadata.setdefault("dataset_id", scenario.dataset_id)
        metadata.setdefault("prompt_version", scenario.prompt_version)
        return metadata

    @staticmethod
    def _int_or_none(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
