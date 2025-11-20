"""CLI commands for RAG comparison."""

from __future__ import annotations

import asyncio
import dataclasses
import json
from pathlib import Path
from typing import Any, Tuple

import click
from pymongo import MongoClient

from src.application.rag import (
    CompareRagAnswersUseCase,
    PromptAssembler,
    RetrievalService,
)
from src.domain.rag import FilterConfig, Query
from src.infrastructure.clients.llm_client import ResilientLLMClient
from src.infrastructure.config.rag_rerank import (
    RagRerankConfig,
    load_rag_rerank_config,
)
from src.infrastructure.config.settings import get_settings
from src.infrastructure.embedding_index import (
    LocalEmbeddingGateway,
    MongoChunkRepository,
    MongoDocumentRepository,
)
from src.infrastructure.embeddings import LocalEmbeddingClient
from src.infrastructure.rag import (
    LLMRerankerAdapter,
    LLMServiceAdapter,
    ThresholdFilterAdapter,
    VectorSearchAdapter,
)

_DEFAULT_LLM_URL = "http://127.0.0.1:8000"


def _build_pipeline() -> Tuple[CompareRagAnswersUseCase, RagRerankConfig]:
    """Build CompareRagAnswersUseCase and return with rerank configuration."""
    settings = get_settings()
    rag_config = load_rag_rerank_config()

<<<<<<< HEAD
    # MongoDB connection
    mongo_client = MongoClient(settings.mongodb_url)
=======
    # MongoDB connection (using DI-based factory)
    from src.infrastructure.database.mongo_client_factory import MongoClientFactory

    factory = MongoClientFactory(settings)
    mongo_client = factory.create_sync_client(use_test_url=False)
>>>>>>> origin/master
    database = mongo_client[settings.embedding_mongo_database]
    chunk_collection = database[settings.embedding_mongo_chunks_collection]
    document_collection = database[settings.embedding_mongo_documents_collection]

    # Chunk repository
    chunk_repository = MongoChunkRepository(chunk_collection, ensure_indexes=False)
    document_repository = MongoDocumentRepository(document_collection)

    # Embedding gateway
    embedding_base_url = settings.embedding_api_url or _DEFAULT_LLM_URL
    embedding_client = LocalEmbeddingClient(
        base_url=embedding_base_url,
        model=settings.embedding_model,
        timeout=settings.embedding_api_timeout_seconds,
        use_ollama_format=True,  # Use Ollama /api/embeddings endpoint
    )
    embedding_gateway = LocalEmbeddingGateway(
        client=embedding_client,
        fallback_dimension=settings.embedding_vector_dimension,
    )

    # Vector search adapter
    fallback_index_path = Path("var/indices/embedding_index_v1.pkl")
    vector_search = VectorSearchAdapter(
        chunk_repository=chunk_repository,
        document_repository=document_repository,
        fallback_index_path=fallback_index_path,
    )

    reranker_llm_config = rag_config.reranker.llm
<<<<<<< HEAD
=======
    reranker_seed = rag_config.reranker.seed
>>>>>>> origin/master
    reranker_client = ResilientLLMClient(url=settings.llm_url or _DEFAULT_LLM_URL)
    reranker_adapter = LLMRerankerAdapter(
        llm_client=reranker_client,
        timeout_seconds=reranker_llm_config.timeout_seconds,
        temperature=reranker_llm_config.temperature,
        max_tokens=reranker_llm_config.max_tokens,
<<<<<<< HEAD
=======
        seed=reranker_seed,
>>>>>>> origin/master
    )

    # Retrieval service
    retrieval_service = RetrievalService(
        vector_search=vector_search,
        relevance_filter=ThresholdFilterAdapter(),
        reranker=reranker_adapter,
        headroom_multiplier=rag_config.retrieval.vector_search_headroom_multiplier,
    )

    # Prompt assembler
    prompt_assembler = PromptAssembler(
        max_context_tokens=settings.rag_max_context_tokens,
    )

    # LLM service
    llm_base_url = settings.llm_url or _DEFAULT_LLM_URL
    llm_service = LLMServiceAdapter(
        base_url=llm_base_url,
        model=settings.llm_model,
        timeout_seconds=settings.review_llm_timeout,
    )

    # Use case
    use_case = CompareRagAnswersUseCase(
        embedding_gateway=embedding_gateway,
        retrieval_service=retrieval_service,
        prompt_assembler=prompt_assembler,
        llm_service=llm_service,
        top_k=settings.rag_top_k,
        score_threshold=settings.rag_score_threshold,
        max_tokens=settings.llm_max_tokens,
        temperature=settings.llm_temperature,
    )

    return use_case, rag_config


def _compute_filter_config(
    config: RagRerankConfig,
    *,
    filter_override: bool | None,
    threshold_override: float | None,
    reranker_override: str | None,
) -> FilterConfig:
    """Build FilterConfig applying CLI overrides with precedence."""
    threshold = (
        threshold_override
        if threshold_override is not None
        else config.retrieval.score_threshold
    )
    top_k = config.retrieval.top_k

    filter_enabled = (
        filter_override
        if filter_override is not None
        else config.feature_flags.enable_rag_plus_plus
    )
    if not filter_enabled:
        threshold = 0.0

    reranker_strategy = (
        reranker_override if reranker_override is not None else config.reranker.strategy
    )
    reranker_enabled = (
        reranker_override != "off"
        if reranker_override is not None
        else config.reranker.enabled
    )
    strategy_value = reranker_strategy if reranker_enabled else "off"
    if strategy_value == "cross_encoder":
        click.echo(
            "cross_encoder reranker is not available yet; falling back to 'off'.",
            err=True,
        )
        strategy_value = "off"
        reranker_enabled = False

    return FilterConfig(
        score_threshold=threshold,
        top_k=top_k,
        reranker_enabled=reranker_enabled,
        reranker_strategy=strategy_value,
    )


def _serialize_result(result: Any) -> dict:
    """Serialize ComparisonResult to dict for JSON output.

    Purpose:
        Convert dataclass instances to JSON-serializable dicts.

    Args:
        result: ComparisonResult instance.

    Returns:
        Dict representation of the result.
    """
    return dataclasses.asdict(result)


@click.group(name="rag")
def rag_commands() -> None:
    """RAG comparison commands."""


@rag_commands.command(name="compare")
@click.option(
    "--question",
    required=True,
    help="Question to answer (supports RU/EN). See docs/specs/epic_21/OPERATIONS_RUNBOOK.md for tuning tips.",
)
@click.option(
    "--filter",
    "filter_enabled",
    flag_value=True,
    default=None,
    help="Enable threshold filtering (overrides config). Without this flag, all retrieved chunks are kept.",
)
@click.option(
    "--no-filter",
    "filter_enabled",
    flag_value=False,
    help="Disable threshold filtering (overrides config).",
)
@click.option(
    "--threshold",
    type=float,
    default=None,
    help="Override similarity score threshold (0.0-1.0). Example: --threshold 0.30",
)
@click.option(
    "--reranker",
    type=click.Choice(["off", "llm", "cross_encoder"]),
    default=None,
    help="Override reranker strategy (default inherits config). Example: --reranker llm",
)
def compare_command(
    question: str,
    filter_enabled: bool | None,
    threshold: float | None,
    reranker: str | None,
) -> None:
    """Compare RAG vs non-RAG for a single question.

    Purpose:
        Generate answers in both modes and display side-by-side comparison.

    Args:
        question: User question to answer.

    Example:
        >>> # poetry run cli rag:compare --question "Что такое MapReduce?"
        >>> # poetry run cli rag:compare --question "..." --filter --threshold 0.30
        >>> # poetry run cli rag:compare --question "..." --filter --threshold 0.30 --reranker llm
    """
    if threshold is not None and not 0.0 <= threshold <= 1.0:
        raise click.BadParameter("threshold must be between 0.0 and 1.0.")

    use_case, rag_config = _build_pipeline()
    filter_config = _compute_filter_config(
        rag_config,
        filter_override=filter_enabled,
        threshold_override=threshold,
        reranker_override=reranker,
    )

    query = Query(id="cli-query-1", question=question)
    result = asyncio.run(use_case.execute(query, filter_config=filter_config))

    result_dict = _serialize_result(result)
    click.echo(json.dumps(result_dict, ensure_ascii=False, indent=2))


@rag_commands.command(name="batch")
@click.option(
    "--queries",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to queries JSONL file",
)
@click.option(
    "--out",
    required=True,
    type=click.Path(path_type=Path),
    help="Path to output JSONL file",
)
@click.option(
    "--filter",
    "filter_enabled",
    flag_value=True,
    default=None,
    help="Enable threshold filtering for all queries.",
)
@click.option(
    "--no-filter",
    "filter_enabled",
    flag_value=False,
    help="Disable threshold filtering for all queries.",
)
@click.option(
    "--threshold",
    type=float,
    default=None,
    help="Override similarity score threshold (0.0-1.0).",
)
@click.option(
    "--reranker",
    type=click.Choice(["off", "llm", "cross_encoder"]),
    default=None,
    help="Override reranker strategy.",
)
def batch_command(
    queries: Path,
    out: Path,
    filter_enabled: bool | None,
    threshold: float | None,
    reranker: str | None,
) -> None:
    """Run batch comparison on queries.jsonl.

    Purpose:
        Process multiple queries and write results to JSONL file.

    Args:
        queries: Path to input queries JSONL file.
        out: Path to output results JSONL file.

    Example:
        >>> # poetry run cli rag:batch \
        ... #     --queries docs/specs/epic_20/queries.jsonl \
        ... #     --out results.jsonl
    """

    if threshold is not None and not 0.0 <= threshold <= 1.0:
        raise click.BadParameter("threshold must be between 0.0 and 1.0.")

    use_case, rag_config = _build_pipeline()
    filter_config = _compute_filter_config(
        rag_config,
        filter_override=filter_enabled,
        threshold_override=threshold,
        reranker_override=reranker,
    )

    asyncio.run(
        _run_batch(
            use_case=use_case,
            queries_path=queries,
            out_path=out,
            filter_config=filter_config,
        )
    )


async def _run_batch(
    *,
    use_case: CompareRagAnswersUseCase,
    queries_path: Path,
    out_path: Path,
    filter_config: FilterConfig,
) -> None:
    with queries_path.open("r", encoding="utf-8") as infile, out_path.open(
        "w", encoding="utf-8"
    ) as outfile:
        for line_num, line in enumerate(infile, start=1):
            if not line.strip():
                continue  # Skip empty lines

            try:
                query_data = json.loads(line)
                if "lang" in query_data and "language" not in query_data:
                    query_data["language"] = query_data.pop("lang")
                query = Query(**query_data)
            except (json.JSONDecodeError, TypeError, ValueError) as error:
                message = (
                    f"Warning: Skipping line {line_num} "
                    f"(invalid JSON or query): {error}"
                )
                click.echo(message, err=True)
                continue

            click.echo(f"Processing query {query.id}: {query.question[:50]}...")

            try:
                result = await use_case.execute(query, filter_config=filter_config)
            except Exception as error:  # noqa: BLE001
                click.echo(f"  ✗ Failed: {error}", err=True)
                continue

            result_dict = _serialize_result(result)
            outfile.write(json.dumps(result_dict, ensure_ascii=False))
            outfile.write("\n")
            click.echo(f"  ✓ Completed ({len(result.chunks_used)} chunks used)")

    click.echo(f"\nResults written to {out_path}")
