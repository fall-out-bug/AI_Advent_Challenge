"""Factory helpers for assembling benchmark evaluation components."""

from __future__ import annotations

from typing import Optional

from src.application.benchmarking.runner import BenchmarkEvaluationRunner
from src.infrastructure.benchmarking.jsonl_dataset_provider import (
    JsonlBenchmarkDatasetProvider,
)
from src.infrastructure.benchmarking.judge import SummarizationJudgeAdapter
from src.infrastructure.benchmarking.metrics_recorder import (
    PrometheusBenchmarkRecorder,
)
from src.infrastructure.config.settings import get_settings
from src.infrastructure.llm.clients.resilient_client import ResilientLLMClient
from src.infrastructure.llm.evaluation.summarization_evaluator import (
    SummarizationEvaluator,
)
from src.infrastructure.llm.token_counter import TokenCounter


def create_benchmark_runner(max_concurrency: Optional[int] = None) -> BenchmarkEvaluationRunner:
    """Build BenchmarkEvaluationRunner wired with production dependencies.

    Purpose:
        Centralise creation of the benchmarking runner so scripts and services
        can reuse consistent wiring without duplicating infrastructure setup.

    Args:
        max_concurrency: Optional override for LLM judge concurrency. When not
            provided, the value defaults to ``Settings.benchmark_max_concurrency``.

    Returns:
        Configured BenchmarkEvaluationRunner instance ready for execution.

    Raises:
        None.

    Example:
        >>> runner = create_benchmark_runner()
        >>> result = await runner.run(scenario)
    """

    settings = get_settings()
    concurrency = max_concurrency or settings.benchmark_max_concurrency

    llm_client = ResilientLLMClient(
        url=settings.llm_url,
        timeout=settings.benchmark_judge_timeout_seconds,
    )
    token_counter = TokenCounter(model_name=settings.llm_model)
    evaluator = SummarizationEvaluator(llm_client=llm_client, token_counter=token_counter)
    judge = SummarizationJudgeAdapter(evaluator=evaluator)
    dataset_provider = JsonlBenchmarkDatasetProvider()
    recorder = PrometheusBenchmarkRecorder()

    return BenchmarkEvaluationRunner(  # pragma: no cover - wiring integration
        dataset_provider=dataset_provider,
        judge=judge,
        metrics_recorder=recorder,
        max_concurrency=concurrency,
    )
