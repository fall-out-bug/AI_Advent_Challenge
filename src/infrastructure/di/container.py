"""Dependency injection container for summarization system."""

from __future__ import annotations

from dependency_injector import containers, providers

from src.application.use_cases.generate_channel_digest import (
    GenerateChannelDigestUseCase,
)
from src.application.use_cases.generate_channel_digest_by_name import (
    GenerateChannelDigestByNameUseCase,
)
from src.application.use_cases.generate_task_summary import (
    GenerateTaskSummaryUseCase,
)
from src.domain.services.summary_quality_checker import SummaryQualityChecker
from src.domain.services.text_cleaner import TextCleanerService
from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.mongo import get_db
from src.infrastructure.llm.chunking.semantic_chunker import SemanticChunker
from src.infrastructure.llm.clients.resilient_client import ResilientLLMClient
from src.infrastructure.llm.summarizers.adaptive_summarizer import (
    AdaptiveSummarizer,
)
from src.infrastructure.llm.summarizers.llm_summarizer import LLMSummarizer
from src.infrastructure.llm.summarizers.map_reduce_summarizer import (
    MapReduceSummarizer,
)
from src.infrastructure.llm.token_counter import TokenCounter
from src.infrastructure.repositories.post_repository import PostRepository
from src.infrastructure.repositories.task_repository import TaskRepository


class SummarizationContainer(containers.DeclarativeContainer):
    """Dependency injection container for summarization components.

    Purpose:
        Provides dependency injection for all summarization-related components
        following Clean Architecture principles.

    Usage:
        container = SummarizationContainer()
        container.config.from_dict({"llm_url": "http://localhost:8001"})
        use_case = container.generate_task_summary()
    """

    config = providers.Configuration()

    # Settings
    settings = providers.Singleton(get_settings)

    # Database
    database = providers.Resource(get_db)

    # Repositories
    task_repository = providers.Factory(
        TaskRepository,
        db=database,
    )

    post_repository = providers.Factory(
        PostRepository,
        db=database,
    )

    # Infrastructure: LLM Client
    llm_client = providers.Singleton(
        ResilientLLMClient,
        url=settings.provided.llm_url,
        timeout=settings.provided.summarizer_timeout_seconds,
    )

    # Infrastructure: Token Counter
    token_counter = providers.Singleton(
        TokenCounter,
        model_name=settings.provided.llm_model,
    )

    # Domain Services
    text_cleaner = providers.Singleton(TextCleanerService)

    quality_checker = providers.Singleton(SummaryQualityChecker)

    # Infrastructure: Chunker
    semantic_chunker = providers.Factory(
        SemanticChunker,
        token_counter=token_counter,
        max_tokens=3000,
        overlap_tokens=200,
    )

    # Infrastructure: Summarizers
    llm_summarizer = providers.Factory(
        LLMSummarizer,
        llm_client=llm_client,
        token_counter=token_counter,
        text_cleaner=text_cleaner,
        quality_checker=quality_checker,
        temperature=settings.provided.summarizer_temperature,
        max_tokens=settings.provided.summarizer_max_tokens,
        max_retries=2,
    )

    map_reduce_summarizer = providers.Factory(
        MapReduceSummarizer,
        llm_client=llm_client,
        chunker=semantic_chunker,
        token_counter=token_counter,
        text_cleaner=text_cleaner,
        quality_checker=quality_checker,
        temperature=settings.provided.summarizer_temperature,
        map_max_tokens=600,
        reduce_max_tokens=2000,
    )

    adaptive_summarizer = providers.Factory(
        AdaptiveSummarizer,
        direct_summarizer=llm_summarizer,
        map_reduce_summarizer=map_reduce_summarizer,
        token_counter=token_counter,
        threshold_tokens=3000,
    )

    # Application: Use Cases
    generate_task_summary = providers.Factory(
        GenerateTaskSummaryUseCase,
        task_repository=task_repository,
    )

    generate_channel_digest = providers.Factory(
        GenerateChannelDigestUseCase,
        post_repository=post_repository,
        summarizer=adaptive_summarizer,
        settings=settings,
    )

    generate_channel_digest_by_name = providers.Factory(
        GenerateChannelDigestByNameUseCase,
        post_repository=post_repository,
        summarizer=adaptive_summarizer,
        settings=settings,
    )
