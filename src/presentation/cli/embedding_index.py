"""CLI commands for the embedding index pipeline."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Sequence, Tuple

import click
from pymongo import MongoClient
from redis import Redis
from redis.exceptions import ResponseError

from src.application.embedding_index import BuildEmbeddingIndexUseCase, IndexingRequest
from src.domain.embedding_index import ChunkingSettings
from src.infrastructure.config.settings import get_settings
from src.infrastructure.embedding_index import (
    FilesystemDocumentCollector,
    LocalEmbeddingGateway,
    MongoChunkRepository,
    MongoDocumentRepository,
    SlidingWindowChunker,
    TextPreprocessor,
)
from src.infrastructure.embeddings import LocalEmbeddingClient
from src.infrastructure.vector_store import RedisSchemaManager, RedisVectorStore


_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_SOURCES: Tuple[str, ...] = (
    str((_REPO_ROOT / "docs").resolve()),
    "/home/fall_out_bug/rework-branch/mlsd/lections",
    "/home/fall_out_bug/rework-branch/bigdata/lections",
)


@click.group(name="index")
def embedding_index() -> None:
    """Document embedding index commands."""


@embedding_index.command(name="run")
@click.option(
    "--source",
    "sources",
    multiple=True,
    help="Override default indexing sources (can be supplied multiple times).",
)
@click.option(
    "--replace-fallback",
    is_flag=True,
    help="Remove existing fallback embeddings before running the indexer.",
)
def run_command(sources: Sequence[str], replace_fallback: bool) -> None:
    """Run the embedding index pipeline for configured sources."""
    settings = _load_settings()
    resolved_sources = _resolve_sources(settings.embedding_sources, sources)
    use_case, mongo_client, redis_client = _build_pipeline(settings)
    fallback_index_path = _fallback_index_path()
    try:
        if replace_fallback:
            _cleanup_fallback_entries(
                settings=settings,
                mongo_client=mongo_client,
                redis_client=redis_client,
                fallback_path=fallback_index_path,
            )
        request = _build_request(settings, resolved_sources)
        result = use_case.execute(request)
    finally:
        mongo_client.close()
        redis_client.close()
    click.echo(f"documents_indexed={result.documents_indexed}")
    click.echo(f"chunks_indexed={result.chunks_indexed}")
    click.echo(f"embeddings_indexed={result.embeddings_indexed}")


@embedding_index.command(name="inspect")
@click.option(
    "--show-fallback",
    is_flag=True,
    help="Display count of chunks indexed with fallback embeddings.",
)
def inspect_command(show_fallback: bool) -> None:
    """Inspect existing embedding index metadata."""
    settings = _load_settings()
    _, mongo_client, redis_client = _build_pipeline(settings)
    try:
        stats = _gather_stats(settings, mongo_client, redis_client, show_fallback=show_fallback)
    finally:
        mongo_client.close()
        redis_client.close()
    for key, value in stats.items():
        click.echo(f"{key}={value}")


def _resolve_sources(
    configured: Iterable[str],
    overrides: Sequence[str],
) -> Tuple[str, ...]:
    """Resolve source directories from overrides or settings."""
    if overrides:
        return tuple(str(Path(path).expanduser()) for path in overrides)
    if configured:
        return tuple(str(Path(path).expanduser()) for path in configured)
    return _DEFAULT_SOURCES


def _build_pipeline(settings):
    """Create use case and backing clients."""
    mongo_client = _create_mongo_client(settings.mongodb_url, settings.mongo_timeout_ms)
    document_repo, chunk_repo = _create_mongo_repositories(settings, mongo_client)
    redis_client = _create_redis_client(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
    )
    vector_store = _create_vector_store(settings, redis_client)
    use_case = _create_use_case(settings, document_repo, chunk_repo, vector_store)
    return use_case, mongo_client, redis_client


def _create_mongo_client(url: str, timeout_ms: int) -> MongoClient:
    """Create MongoDB client."""
    sanitized_url = _resolve_mongo_url(url)
    return MongoClient(sanitized_url, serverSelectionTimeoutMS=timeout_ms)


def _create_mongo_repositories(settings, mongo_client: MongoClient):
    """Create Mongo repositories for documents and chunks."""
    database = mongo_client[settings.embedding_mongo_database]
    documents = database[settings.embedding_mongo_documents_collection]
    chunks = database[settings.embedding_mongo_chunks_collection]
    return MongoDocumentRepository(documents), MongoChunkRepository(chunks)


def _create_redis_client(
    host: str,
    port: int,
    password: str | None,
) -> Redis:
    """Create Redis client."""
    sanitized_password = _sanitize_password(password)
    return Redis(host=host, port=port, password=sanitized_password, decode_responses=False)


def _create_vector_store(settings, redis_client: Redis) -> RedisVectorStore:
    """Create Redis vector store and ensure schema exists."""
    schema_manager = RedisSchemaManager(
        index_name=settings.embedding_redis_index_name,
        key_prefix=settings.embedding_redis_key_prefix,
        dimension=settings.embedding_vector_dimension,
    )
    return RedisVectorStore(
        client=redis_client,
        schema_manager=schema_manager,
        key_prefix=settings.embedding_redis_key_prefix,
        fallback_index_path=_fallback_index_path(),
        dimension=settings.embedding_vector_dimension,
    )


def _create_use_case(settings, document_repo, chunk_repo, vector_store) -> BuildEmbeddingIndexUseCase:
    """Assemble embedding index use case."""
    client = LocalEmbeddingClient(
        base_url=settings.embedding_api_url or settings.llm_url or "http://127.0.0.1:8000",
        model=settings.embedding_model,
    )
    return BuildEmbeddingIndexUseCase(
        collector=FilesystemDocumentCollector(preprocessor=TextPreprocessor()),
        chunker=SlidingWindowChunker(),
        embedding_gateway=LocalEmbeddingGateway(
            client=client,
            fallback_dimension=settings.embedding_vector_dimension,
        ),
        document_repository=document_repo,
        chunk_repository=chunk_repo,
        vector_store=vector_store,
    )


def _build_request(settings, sources: Sequence[str]) -> IndexingRequest:
    """Construct indexing request from settings."""
    return IndexingRequest(
        sources=tuple(sources),
        chunking_settings=ChunkingSettings(
            chunk_size_tokens=settings.embedding_chunk_size_tokens,
            chunk_overlap_tokens=settings.embedding_chunk_overlap_tokens,
            min_chunk_tokens=settings.embedding_min_chunk_tokens,
        ),
        extra_tags={
            "stage": settings.embedding_stage_tag,
            "language": settings.embedding_default_language,
        },
        max_file_size_bytes=settings.embedding_max_file_size_mb * 1024 * 1024,
        batch_size=settings.embedding_batch_size,
    )


def _gather_stats(settings, mongo_client: MongoClient, redis_client: Redis, *, show_fallback: bool) -> dict[str, str]:
    """Collect index statistics from MongoDB and Redis."""
    database = mongo_client[settings.embedding_mongo_database]
    docs = database[settings.embedding_mongo_documents_collection].count_documents({})
    chunks = database[settings.embedding_mongo_chunks_collection].count_documents({})
    fallback_count = 0
    if show_fallback:
        fallback_count = database[settings.embedding_mongo_chunks_collection].count_documents(
            {"metadata.fallback": {"$exists": True}}
        )
    redis_stats = _fetch_redis_stats(redis_client, settings.embedding_redis_index_name)
    result = {"documents": docs, "chunks": chunks}
    if show_fallback:
        result["fallback_chunks"] = fallback_count
    result.update(redis_stats)
    return result


def _fetch_redis_stats(client: Redis, index_name: str) -> dict[str, str]:
    """Fetch Redis index metadata."""
    try:
        info = client.execute_command("FT.INFO", index_name)
    except ResponseError:
        return {"redis_index": "missing"}
    except Exception as error:  # noqa: BLE001
        return {"redis_error": str(error)}
    stats = {}
    for key, value in zip(info[::2], info[1::2]):
        decoded_key = key.decode() if isinstance(key, bytes) else str(key)
        decoded_value = value.decode() if isinstance(value, bytes) else value
        stats[decoded_key] = decoded_value
    return {
        "redis_index": "ready",
        "redis_docs": str(stats.get("num_docs", "0")),
    }


def _cleanup_fallback_entries(
    settings,
    mongo_client: MongoClient,
    redis_client: Redis,
    fallback_path: Path,
) -> None:
    """Remove previously stored fallback embeddings."""
    chunks_collection = mongo_client[settings.embedding_mongo_database][
        settings.embedding_mongo_chunks_collection
    ]
    fallback_chunks = list(
        chunks_collection.find(
            {"metadata.fallback": {"$exists": True}},
            {"chunk_id": 1},
        )
    )
    if fallback_chunks:
        chunk_ids = [chunk["chunk_id"] for chunk in fallback_chunks if "chunk_id" in chunk]
        if chunk_ids:
            redis_keys = [
                f"{settings.embedding_redis_key_prefix}{chunk_id}" for chunk_id in chunk_ids
            ]
            try:
                redis_client.delete(*redis_keys)
            except Exception as error:  # noqa: BLE001
                click.echo(f"warning: failed to delete Redis fallback keys ({error})")
        chunks_collection.delete_many({"metadata.fallback": {"$exists": True}})
    if fallback_path.exists():
        try:
            fallback_path.unlink()
        except OSError as error:
            click.echo(f"warning: failed to remove fallback index file ({error})")


def _fallback_index_path() -> Path:
    """Return path for local fallback index."""
    return Path("var/indices/embedding_index_v1.pkl")


def _resolve_mongo_url(url: str) -> str:
    """Normalise Mongo connection string, falling back to env credentials when needed."""
    sanitized = url.replace("\n", "").strip()
    if "@" in sanitized:
        return sanitized
    user = os.getenv("MONGO_USER") or "admin"
    password = _get_secret_value(
        env_key="MONGO_PASSWORD",
        fallback_paths=[
            Path.home() / "work/infra/secrets/mongo_password.txt",
            Path.home() / "work/infra/.env.infra",
        ],
    )
    if user and password:
        host = os.getenv("MONGO_HOST", "127.0.0.1")
        port = os.getenv("MONGO_PORT", "27017")
        database = os.getenv("MONGO_DATABASE")
        auth_source = os.getenv("MONGO_AUTHSRC", "admin")
        from urllib.parse import quote_plus

        safe_user = quote_plus(user.strip())
        safe_password = quote_plus(password.strip())
        click.echo(f"[index] Mongo credentials loaded (user={safe_user}, password_len={len(password.strip())})")
        params = {
            "authSource": auth_source,
            "authMechanism": os.getenv("MONGO_AUTH_MECHANISM", "SCRAM-SHA-256"),
        }
        query = "&".join(f"{key}={value}" for key, value in params.items())
        if database:
            return f"mongodb://{safe_user}:{safe_password}@{host}:{port}/{database}?{query}"
        return f"mongodb://{safe_user}:{safe_password}@{host}:{port}/?{query}"
    click.echo("[index] Mongo credentials missing; using default unauthenticated URL.")
    return sanitized


def _sanitize_password(password: str | None) -> str | None:
    """Strip whitespace/newlines from optional password."""
    if password:
        return password.replace("\n", "").strip()
    secret = _get_secret_value(
        env_key="REDIS_PASSWORD",
        fallback_paths=[
            Path.home() / "work/infra/secrets/redis_password.txt",
            Path.home() / "work/infra/.env.infra",
        ],
    )
    if secret:
        click.echo(f"[index] Redis password loaded (length={len(secret)})")
    else:
        click.echo("[index] Redis password not found; connecting without auth.")
    return secret or None


def _load_settings():
    """Reload settings to honour freshly exported environment variables."""
    try:
        get_settings.cache_clear()  # type: ignore[attr-defined]
    except AttributeError:
        pass
    return get_settings()


def _get_secret_value(env_key: str, fallback_paths: list[Path]) -> str:
    """Fetch secret from environment or fallback files."""
    value = os.getenv(env_key)
    if value and value.strip():
        return value.strip()
    for path in fallback_paths:
        expanded = path.expanduser()
        if not expanded.exists():
            continue
        try:
            if expanded.suffix in {".txt", ".secret", ".pwd"}:
                content = expanded.read_text(encoding="utf-8").strip()
                if content:
                    return content
            else:
                parsed = _parse_env_file(expanded, env_key)
                if parsed:
                    return parsed
        except OSError:
            continue
    return ""


def _parse_env_file(path: Path, env_key: str) -> str:
    """Parse dotenv-style file for the specified key."""
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() == env_key and value.strip():
            return value.strip()
    return ""
