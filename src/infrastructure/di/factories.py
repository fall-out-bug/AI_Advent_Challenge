"""Factory functions for creating summarization components."""

from __future__ import annotations

from src.application.use_cases.generate_channel_digest import GenerateChannelDigestUseCase
from src.application.use_cases.generate_channel_digest_by_name import (
    GenerateChannelDigestByNameUseCase,
)
from src.application.use_cases.generate_task_summary import GenerateTaskSummaryUseCase
from src.infrastructure.di.container import SummarizationContainer
from src.infrastructure.llm.summarizers.adaptive_summarizer import AdaptiveSummarizer


def create_adaptive_summarizer() -> AdaptiveSummarizer:
    """Create AdaptiveSummarizer instance.

    Purpose:
        Factory function for creating AdaptiveSummarizer with all dependencies.

    Returns:
        Configured AdaptiveSummarizer instance.
    """
    container = SummarizationContainer()
    container.config.from_dict({})
    return container.adaptive_summarizer()


def create_task_summary_use_case() -> GenerateTaskSummaryUseCase:
    """Create GenerateTaskSummaryUseCase instance.

    Purpose:
        Factory function for creating task summary use case with dependencies.

    Returns:
        Configured GenerateTaskSummaryUseCase instance.
    """
    container = SummarizationContainer()
    container.config.from_dict({})
    return container.generate_task_summary()


def create_channel_digest_use_case() -> GenerateChannelDigestUseCase:
    """Create GenerateChannelDigestUseCase instance.

    Purpose:
        Factory function for creating channel digest use case with dependencies.

    Returns:
        Configured GenerateChannelDigestUseCase instance.
    """
    container = SummarizationContainer()
    container.config.from_dict({})
    return container.generate_channel_digest()


def create_summarization_evaluator():
    """Create SummarizationEvaluator instance."""
    from src.infrastructure.llm.evaluation.summarization_evaluator import (
        SummarizationEvaluator,
    )

    container = SummarizationContainer()

    return SummarizationEvaluator(
        llm_client=container.llm_client(),
        token_counter=container.token_counter(),
    )


def create_channel_digest_by_name_use_case() -> GenerateChannelDigestByNameUseCase:
    """Create GenerateChannelDigestByNameUseCase instance.

    Purpose:
        Factory function for creating channel digest by name use case.

    Returns:
        Configured GenerateChannelDigestByNameUseCase instance.
    """
    container = SummarizationContainer()
    container.config.from_dict({})
    return container.generate_channel_digest_by_name()
