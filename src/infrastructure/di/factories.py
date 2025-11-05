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
        Creates use case directly without using container to avoid async Resource issues.

    Returns:
        Configured GenerateChannelDigestUseCase instance.
    """
    from src.infrastructure.config.settings import get_settings
    from src.infrastructure.di.container import SummarizationContainer
    
    # Create dependencies directly
    settings = get_settings()
    container = SummarizationContainer()
    container.config.from_dict({})
    
    # Get summarizer from container (doesn't depend on async resources directly)
    summarizer = container.adaptive_summarizer()
    
    # Create use case directly with dependencies
    # post_repository=None means it will be created lazily in async context when needed
    use_case = GenerateChannelDigestUseCase(
        post_repository=None,  # Will be created in execute() method when needed
        summarizer=summarizer,
        settings=settings,
    )
    
    return use_case


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
        Creates use case directly without using container to avoid async Resource issues.

    Returns:
        Configured GenerateChannelDigestByNameUseCase instance.
    """
    from src.infrastructure.config.settings import get_settings
    from src.infrastructure.di.container import SummarizationContainer
    
    # Create dependencies directly
    settings = get_settings()
    container = SummarizationContainer()
    container.config.from_dict({})
    
    # Get summarizer from container (doesn't depend on async resources directly)
    summarizer = container.adaptive_summarizer()
    
    # Create use case directly with dependencies
    # post_repository=None means it will be created lazily in async context when needed
    use_case = GenerateChannelDigestByNameUseCase(
        post_repository=None,  # Will be created in execute() method when needed
        summarizer=summarizer,
        settings=settings,
    )
    
    return use_case


def create_adaptive_summarizer_with_long_timeout() -> AdaptiveSummarizer:
    """Create AdaptiveSummarizer instance with extended timeout for long tasks.

    Purpose:
        Factory function for creating AdaptiveSummarizer with long timeout
        for async long summarization tasks.

    Returns:
        Configured AdaptiveSummarizer instance with extended timeout.
    """
    from src.infrastructure.config.settings import get_settings
    from src.infrastructure.llm.clients.resilient_client import ResilientLLMClient
    from src.infrastructure.llm.summarizers.llm_summarizer import LLMSummarizer
    from src.infrastructure.llm.summarizers.map_reduce_summarizer import MapReduceSummarizer
    from src.infrastructure.llm.token_counter import TokenCounter
    from src.domain.services.text_cleaner import TextCleanerService
    from src.domain.services.summary_quality_checker import SummaryQualityChecker

    settings = get_settings()

    # Create LLM client with long timeout
    llm_client = ResilientLLMClient(
        url=settings.llm_url or None,
        timeout=settings.summarizer_timeout_seconds_long,
    )

    token_counter = TokenCounter(model_name=settings.llm_model)
    text_cleaner = TextCleanerService()
    quality_checker = SummaryQualityChecker()

    # Create summarizers with long timeout client
    direct_summarizer = LLMSummarizer(
        llm_client=llm_client,
        token_counter=token_counter,
        text_cleaner=text_cleaner,
        quality_checker=quality_checker,
        temperature=settings.summarizer_temperature,
        max_tokens=settings.summarizer_max_tokens,
    )

    # Create chunker and map-reduce summarizer
    from src.infrastructure.llm.chunking.semantic_chunker import SemanticChunker
    semantic_chunker = SemanticChunker(
        token_counter=token_counter,
        max_tokens=3000,
    )

    map_reduce_summarizer = MapReduceSummarizer(
        llm_client=llm_client,
        chunker=semantic_chunker,
        token_counter=token_counter,
        text_cleaner=text_cleaner,
        quality_checker=quality_checker,
        temperature=settings.summarizer_temperature,
        map_max_tokens=600,
        reduce_max_tokens=2000,
    )

    return AdaptiveSummarizer(
        direct_summarizer=direct_summarizer,
        map_reduce_summarizer=map_reduce_summarizer,
        token_counter=token_counter,
        threshold_tokens=3000,
    )
