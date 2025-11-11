"""CLI commands for RAG comparison."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

import click
from pymongo import MongoClient

from src.application.rag import (
    CompareRagAnswersUseCase,
    PromptAssembler,
    RetrievalService,
)
from src.domain.rag import Query
from src.infrastructure.config.settings import get_settings
from src.infrastructure.embedding_index import (
    LocalEmbeddingGateway,
    MongoChunkRepository,
    MongoDocumentRepository,
)
from src.infrastructure.embeddings import LocalEmbeddingClient
from src.infrastructure.rag import LLMServiceAdapter, VectorSearchAdapter

_DEFAULT_LLM_URL = "http://127.0.0.1:8000"


def _build_use_case() -> CompareRagAnswersUseCase:
    """Build CompareRagAnswersUseCase with dependencies.

    Purpose:
        Factory function to wire all dependencies for the use case.

    Returns:
        Fully initialized use case instance.
    """
    settings = get_settings()

    # MongoDB connection
    mongo_client = MongoClient(settings.mongodb_url)
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

    # Retrieval service
    retrieval_service = RetrievalService(
        vector_search=vector_search,
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

    return use_case


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
@click.option("--question", required=True, help="Question to answer (Russian)")
def compare_command(question: str) -> None:
    """Compare RAG vs non-RAG for a single question.

    Purpose:
        Generate answers in both modes and display side-by-side comparison.

    Args:
        question: User question to answer.

    Example:
        >>> # poetry run cli rag:compare --question "Что такое MapReduce?"
    """
    use_case = _build_use_case()

    query = Query(id="cli-query-1", question=question)
    result = use_case.execute(query)

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
def batch_command(queries: Path, out: Path) -> None:
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
    use_case = _build_use_case()

    with queries.open("r") as infile, out.open("w") as outfile:
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
                result = use_case.execute(query)
                result_dict = _serialize_result(result)
                outfile.write(json.dumps(result_dict, ensure_ascii=False))
                outfile.write("\n")
                click.echo(f"  ✓ Completed ({len(result.chunks_used)} chunks used)")
            except Exception as error:
                click.echo(f"  ✗ Failed: {error}", err=True)
                continue

    click.echo(f"\nResults written to {out}")
