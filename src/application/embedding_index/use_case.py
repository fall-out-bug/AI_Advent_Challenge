"""Use case for building the document embedding index."""

from __future__ import annotations

from collections import deque
from dataclasses import replace
from typing import Deque, List, Mapping, MutableMapping, Sequence

from src.application.embedding_index.dtos import IndexingRequest, IndexingResult
from src.domain.embedding_index import (
    Chunker,
    ChunkingSettings,
    ChunkRepository,
    DocumentChunk,
    DocumentCollector,
    DocumentPayload,
    DocumentRecord,
    DocumentRepository,
    EmbeddingGateway,
    EmbeddingVector,
    VectorStore,
)


class BuildEmbeddingIndexUseCase:
    """Coordinate the ingestion → embedding → persistence flow.

    Purpose:
        Orchestrate document collection, chunking, embedding generation, and
        persistence while staying within Clean Architecture boundaries.
    """

    def __init__(
        self,
        collector: DocumentCollector,
        chunker: Chunker,
        embedding_gateway: EmbeddingGateway,
        document_repository: DocumentRepository,
        chunk_repository: ChunkRepository,
        vector_store: VectorStore,
    ) -> None:
        """Initialise the use case with required dependencies.

        Purpose:
            Capture injected collaborators for later execution.

        Args:
            collector: Adapter responsible for discovering documents.
            chunker: Service that splits documents into chunks.
            embedding_gateway: Embedding API adapter.
            document_repository: Persistence adapter for documents.
            chunk_repository: Persistence adapter for chunks.
            vector_store: Persistence adapter for embeddings.

        Example:
            >>> BuildEmbeddingIndexUseCase(
            ...     collector=object(),  # doctest: +SKIP
            ...     chunker=object(),
            ...     embedding_gateway=object(),
            ...     document_repository=object(),
            ...     chunk_repository=object(),
            ...     vector_store=object(),
            ... )
        """
        self._collector = collector
        self._chunker = chunker
        self._embedding_gateway = embedding_gateway
        self._document_repository = document_repository
        self._chunk_repository = chunk_repository
        self._vector_store = vector_store

    def execute(self, request: IndexingRequest) -> IndexingResult:
        """Run the indexing pipeline using the provided request.

        Purpose:
            Perform document ingestion, chunking, embedding generation, and
            persistence, returning execution metrics.

        Args:
            request: Indexing configuration supplied by the caller.

        Returns:
            IndexingResult: Counts summarising indexing activity.

        Raises:
            RuntimeError: If mismatched embedding/chunk counts are returned by
                the embedding gateway.

        Example:
            >>> # See tests for end-to-end execution example.  # doctest: +SKIP
        """
        documents_indexed = 0
        chunks_indexed = 0
        embeddings_indexed = 0
        pending_chunks: Deque[DocumentChunk] = deque()

        for payload in self._collector.collect(
            sources=request.sources,
            max_file_size_bytes=request.max_file_size_bytes,
            extra_tags=request.extra_tags,
        ):
            documents_indexed += 1
            record = self._prepare_record(payload.record, request.extra_tags)
            self._document_repository.upsert_document(record)

            prepared_chunks = self._prepare_chunks(
                payload=payload,
                chunking_settings=request.chunking_settings,
                request_tags=request.extra_tags,
                record_tags=dict(record.tags or {}),
            )
            if not prepared_chunks:
                continue

            self._chunk_repository.upsert_chunks(prepared_chunks)
            chunks_indexed += len(prepared_chunks)
            pending_chunks.extend(prepared_chunks)

            embeddings_indexed += self._flush_batches(
                pending_chunks=pending_chunks,
                batch_size=request.batch_size,
            )

        embeddings_indexed += self._finalise_batches(pending_chunks)

        return IndexingResult(
            documents_indexed=documents_indexed,
            chunks_indexed=chunks_indexed,
            embeddings_indexed=embeddings_indexed,
        )

    def _prepare_record(
        self,
        record: DocumentRecord,
        extra_tags: Mapping[str, str],
    ) -> DocumentRecord:
        """Merge document tags with request-provided tags."""
        tags: MutableMapping[str, str] = dict(record.tags or {})
        tags.setdefault("source", record.source)
        tags.setdefault("language", record.language)
        for key, value in extra_tags.items():
            tags[key] = value
        return replace(record, tags=dict(tags))

    def _prepare_chunks(
        self,
        payload: DocumentPayload,
        request_tags: Mapping[str, str],
        record_tags: Mapping[str, str],
        chunking_settings: ChunkingSettings,
    ) -> List[DocumentChunk]:
        """Chunk a document payload and enrich metadata."""
        chunks = self._chunker.build_chunks(
            payload=payload,
            settings=chunking_settings,
        )
        # Fallback: direct use of request settings when chunker ignores metadata
        if not chunks:
            return []

        enriched: List[DocumentChunk] = []
        for chunk in chunks:
            metadata: MutableMapping[str, str] = dict(chunk.metadata or {})
            for key, value in record_tags.items():
                metadata[key] = value
            for key, value in request_tags.items():
                metadata[key] = value
            metadata["document_id"] = chunk.document_id
            enriched.append(replace(chunk, metadata=dict(metadata)))
        return enriched

    def _flush_batches(
        self,
        pending_chunks: Deque,
        batch_size: int,
    ) -> int:
        """Flush ready batches and persist embeddings."""
        embeddings_written = 0
        while len(pending_chunks) >= batch_size:
            batch = [pending_chunks.popleft() for _ in range(batch_size)]
            vectors = self._embedding_gateway.embed(batch)
            self._validate_embedding_batch(batch, vectors)
            annotated_chunks = self._annotate_chunks_with_vectors(batch, vectors)
            self._chunk_repository.upsert_chunks(annotated_chunks)
            self._vector_store.upsert(annotated_chunks, vectors)
            embeddings_written += len(vectors)
        return embeddings_written

    def _finalise_batches(self, pending_chunks: Deque) -> int:
        """Flush remaining chunks smaller than a batch."""
        if not pending_chunks:
            return 0
        batch = list(pending_chunks)
        pending_chunks.clear()
        vectors = self._embedding_gateway.embed(batch)
        self._validate_embedding_batch(batch, vectors)
        annotated_chunks = self._annotate_chunks_with_vectors(batch, vectors)
        self._chunk_repository.upsert_chunks(annotated_chunks)
        self._vector_store.upsert(annotated_chunks, vectors)
        return len(vectors)

    def _validate_embedding_batch(
        self,
        chunks: Sequence[DocumentChunk],
        vectors: Sequence[EmbeddingVector],
    ) -> None:
        """Ensure embedding batch length matches chunk count."""
        if len(chunks) != len(vectors):
            raise RuntimeError(
                "Embedding gateway returned mismatched vector count: "
                f"{len(vectors)} for {len(chunks)} chunks.",
            )

    def _annotate_chunks_with_vectors(
        self,
        chunks: Sequence[DocumentChunk],
        vectors: Sequence[EmbeddingVector],
    ) -> List[DocumentChunk]:
        """Merge embedding metadata into chunk metadata."""
        annotated: List[DocumentChunk] = []
        for chunk, vector in zip(chunks, vectors):
            metadata: MutableMapping[str, str] = dict(chunk.metadata or {})
            metadata["embedding_model"] = vector.model
            for key, value in (vector.metadata or {}).items():
                metadata[key] = str(value)
            annotated.append(replace(chunk, metadata=dict(metadata)))
        return annotated
