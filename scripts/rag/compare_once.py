#!/usr/bin/env python3
"""Prototype: Single RAG vs non-RAG comparison.

Purpose:
    Validate retrieval + prompting + answer generation for a single query.

Usage:
    python scripts/rag/compare_once.py --question "Что такое MapReduce?"

Requirements:
    - Shared infra running (Mongo, Redis, LLM API)
    - EP19 index available (minimal demo index)
"""

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import click
from pymongo import MongoClient
from redis import Redis

# Add project root to path
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from src.infrastructure.config.settings import get_settings  # noqa: E402


def embed_query_text(question: str, settings: Any) -> List[float]:
    """Embed query text using the embedding API.

    Purpose:
        Generate embedding vector for the query to enable similarity search.

    Args:
        question: Query text to embed.
        settings: Application settings with embedding API config.

    Returns:
        List of floats representing the embedding vector.

    Raises:
        RuntimeError: If embedding API is unavailable.
    """
    import httpx

    try:
        response = httpx.post(
            f"{settings.embedding_api_url}/v1/embeddings",
            json={"input": question, "model": settings.embedding_model},
            timeout=settings.embedding_api_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]
    except Exception as error:
        raise RuntimeError(f"Embedding API failed: {error}") from error


def search_redis_vectors(
    query_vector: List[float],
    top_k: int,
    redis_client: Redis,
    index_name: str,
) -> List[str]:
    """Search for similar vectors in Redis (simplified).

    Purpose:
        Perform KNN search using RediSearch (if available).

    Args:
        query_vector: Query embedding vector.
        top_k: Number of results to return.
        redis_client: Redis client connection.
        index_name: RediSearch index name.

    Returns:
        List of chunk IDs ordered by similarity.

    Raises:
        RuntimeError: If RediSearch is unavailable.

    Note:
        This is a simplified prototype. Full implementation requires
        RediSearch FT.SEARCH with KNN query syntax.
    """
    # TODO: Implement RediSearch KNN query
    # For now, return empty list (will trigger fallback behavior)
    return []


def fetch_chunks_from_mongo(
    chunk_ids: List[str],
    mongo_client: MongoClient,
    db_name: str,
    collection_name: str,
) -> List[Dict[str, Any]]:
    """Fetch chunk metadata from MongoDB.

    Purpose:
        Retrieve full chunk documents by their IDs.

    Args:
        chunk_ids: List of chunk IDs to fetch.
        mongo_client: MongoDB client connection.
        db_name: Database name.
        collection_name: Collection name.

    Returns:
        List of chunk documents (dicts).
    """
    db = mongo_client[db_name]
    collection = db[collection_name]
    cursor = collection.find({"chunk_id": {"$in": chunk_ids}})
    return list(cursor)


def build_non_rag_prompt(question: str) -> str:
    """Build non-RAG prompt (baseline).

    Purpose:
        Format question without any retrieved context.

    Args:
        question: User question.

    Returns:
        Formatted prompt string.
    """
    system_prompt = "\n".join(
        [
            "Ты — помощник, отвечающий на вопросы по курсам Big Data и"
            " Machine Learning.",
            "",
            "Инструкции:",
            "- Отвечай на русском языке, если вопрос задан на русском.",
            "- Если не знаешь точного ответа, честно скажи об этом.",
            "- Будь кратким и конкретным (2-4 абзаца максимум).",
            "- Не выдумывай факты и не галлюцинируй.",
            "",
            "Вопрос:",
            "{question}",
        ]
    )
    return system_prompt.format(question=question)


def build_rag_prompt(question: str, chunks: List[Dict[str, Any]]) -> str:
    """Build RAG prompt with retrieved context.

    Purpose:
        Format question with retrieved document chunks as context.

    Args:
        question: User question.
        chunks: Retrieved chunk documents from MongoDB.

    Returns:
        Formatted prompt string with context.
    """
    context_parts = []
    for idx, chunk in enumerate(chunks[:5]):  # Top 5 chunks
        metadata = chunk.get("metadata", {}) or {}
        source_path = metadata.get("source_path", "unknown")
        chunk_text = "\n".join(
            [
                f"[Фрагмент {idx + 1}]",
                f"Источник: {source_path}",
                "",
                chunk.get("text", ""),
                "",
                "---",
            ]
        )
        context_parts.append(chunk_text)

    context = "\n".join(context_parts)

    system_prompt = "\n".join(
        [
            "Ты — помощник, отвечающий на вопросы по курсам Big Data и"
            " Machine Learning.",
            "",
            "Инструкции:",
            "- Используй ТОЛЬКО информацию из предоставленного контекста для"
            " ответа.",
            "- Если в контексте нет ответа, скажи:",
            '  "В предоставленных документах информация не найдена."',
            "- Отвечай на русском языке, если вопрос задан на русском.",
            "- Будь кратким и конкретным (2-4 абзаца максимум).",
            "",
            "Контекст (релевантные фрагменты документов):",
            "",
            "{context}",
            "",
            "---",
            "",
            "Вопрос:",
            "{question}",
        ]
    )
    return system_prompt.format(context=context, question=question)


def generate_answer(prompt: str, settings: Any) -> Dict[str, Any]:
    """Generate LLM answer from prompt.

    Purpose:
        Call LLM API and return answer with metadata.

    Args:
        prompt: Formatted prompt string.
        settings: Application settings with LLM config.

    Returns:
        Dict with answer text, model, latency, tokens.

    Raises:
        RuntimeError: If LLM API is unavailable.
    """
    import httpx

    start_time = time.time()

    try:
        response = httpx.post(
            f"{settings.llm_url}/v1/chat/completions",
            json={
                "model": settings.llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.7,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()

        latency_ms = int((time.time() - start_time) * 1000)

        usage_data = data.get("usage", {}) or {}
        return {
            "text": data["choices"][0]["message"]["content"],
            "model": data.get("model", settings.llm_model),
            "latency_ms": latency_ms,
            "tokens_generated": usage_data.get("completion_tokens", 0),
        }
    except Exception as error:
        raise RuntimeError(f"LLM API failed: {error}") from error


@click.command()
@click.option(
    "--question",
    required=True,
    help="Question to answer (Russian language recommended)",
)
def main(question: str) -> None:
    """Compare RAG vs non-RAG for a single question.

    Purpose:
        Prototype script to validate retrieval and answer generation.

    Args:
        question: User question to answer.

    Example:
        >>> # python scripts/rag/compare_once.py \
        ... #     --question "Что такое MapReduce?"
    """
    settings = get_settings()

    click.echo(f"Question: {question}\n")

    # 1. Generate non-RAG answer (baseline)
    click.echo("Generating non-RAG answer...")
    non_rag_prompt = build_non_rag_prompt(question)
    without_rag = generate_answer(non_rag_prompt, settings)
    latency_plain = without_rag["latency_ms"]
    click.echo(f"✓ Non-RAG answer generated ({latency_plain}ms)\n")

    # 2. Embed query
    click.echo("Embedding query...")
    try:
        query_vector = embed_query_text(question, settings)
        dimension = len(query_vector)
        click.echo(f"✓ Query embedded (dimension: {dimension})\n")
    except RuntimeError as error:
        click.echo(f"✗ Embedding failed: {error}")
        click.echo("Falling back to non-RAG mode only.\n")
        query_vector = None

    # 3. Retrieve chunks
    chunks = []
    if query_vector:
        click.echo("Searching for relevant chunks...")
        try:
            redis_client = Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,  # pragma: allowlist secret
                decode_responses=False,
            )
            chunk_ids = search_redis_vectors(
                query_vector,
                top_k=5,
                redis_client=redis_client,
                index_name=settings.embedding_redis_index_name,
            )
            redis_client.close()

            if chunk_ids:
                click.echo(f"✓ Found {len(chunk_ids)} chunk(s)\n")
                mongo_client = MongoClient(settings.mongodb_url)
                chunks = fetch_chunks_from_mongo(
                    chunk_ids,
                    mongo_client,
                    settings.embedding_mongo_database,
                    settings.embedding_mongo_chunks_collection,
                )
                mongo_client.close()
            else:
                # fmt: off
                empty_index_msg = (
                    "✗ No chunks found (empty index or RediSearch unavailable)"
                )
                # fmt: on
                click.echo(empty_index_msg)
                # fmt: off
                redis_hint = (
                    "Note: Run EP19 indexer first "
                    "or check Redis setup.\n"
                )
                # fmt: on
                click.echo(redis_hint)
        except Exception as error:
            click.echo(f"✗ Retrieval failed: {error}\n")

    # 4. Generate RAG answer
    if chunks:
        click.echo("Generating RAG answer with context...")
        rag_prompt = build_rag_prompt(question, chunks)
        with_rag = generate_answer(rag_prompt, settings)
        rag_latency = with_rag["latency_ms"]
        click.echo(f"✓ RAG answer generated ({rag_latency}ms)\n")
    else:
        click.echo("Skipping RAG answer (no chunks retrieved)\n")
        with_rag = None

    # 5. Display results
    result = {
        "query": question,
        "without_rag": without_rag,
        "with_rag": with_rag,
        "chunks_used": len(chunks),
    }

    click.echo("=" * 80)
    click.echo("COMPARISON RESULT")
    click.echo("=" * 80)
    click.echo(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
