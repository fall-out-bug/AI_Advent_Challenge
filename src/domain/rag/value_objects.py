"""RAG domain value objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class Query:
    """User query for Q&A system.

    Purpose:
        Represent a question to be answered by the RAG system.

    Attributes:
        id: Unique query identifier.
        question: Question text.
        category: Optional category tag (e.g., "Architecture", "Lectures").
        language: ISO language code (default: "ru" for Russian).
        expectation: Optional ground truth answer for evaluation.
    """

    id: str
    question: str
    category: str | None = None
    language: str = "ru"
    expectation: str | None = None

    def __post_init__(self) -> None:
        """Validate Query fields.

        Purpose:
            Ensure required fields are present and valid.

        Raises:
            ValueError: When validation fails.

        Example:
            >>> Query(id="q1", question="Что такое MapReduce?")
        """
        if not self.id or not self.id.strip():
            raise ValueError("id cannot be empty.")
        if not self.question or not self.question.strip():
            raise ValueError("question cannot be empty.")
        if not self.language or not self.language.strip():
            raise ValueError("language cannot be empty.")


@dataclass(frozen=True)
class Answer:
    """LLM-generated answer.

    Purpose:
        Encapsulate answer text with generation metadata.

    Attributes:
        text: Generated answer text.
        model: LLM model identifier used for generation.
        latency_ms: Generation latency in milliseconds.
        tokens_generated: Number of tokens in the answer.
        metadata: Optional extra metadata (e.g., finish reason, usage).
    """

    text: str
    model: str
    latency_ms: int
    tokens_generated: int
    metadata: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        """Validate Answer fields.

        Purpose:
            Ensure answer text and metadata are valid.

        Raises:
            ValueError: When validation fails.

        Example:
            >>> Answer(
            ...     text="MapReduce — это модель программирования...",
            ...     model="qwen",
            ...     latency_ms=1500,
            ...     tokens_generated=120,
            ... )
        """
        if not self.text or not self.text.strip():
            raise ValueError("text cannot be empty.")
        if not self.model or not self.model.strip():
            raise ValueError("model cannot be empty.")
        if self.latency_ms < 0:
            raise ValueError("latency_ms must be non-negative.")
        if self.tokens_generated < 0:
            raise ValueError("tokens_generated must be non-negative.")


@dataclass(frozen=True)
class RetrievedChunk:
    """Retrieved document chunk with similarity score.

    Purpose:
        Represent a chunk retrieved from the vector index.

    Attributes:
        chunk_id: Unique chunk identifier.
        document_id: Parent document identifier.
        text: Chunk text content.
        similarity_score: Similarity score (0.0-1.0, higher is better).
        source_path: Filesystem path to the source document.
        metadata: Optional chunk metadata (tags, ordinal, etc.).
    """

    chunk_id: str
    document_id: str
    text: str
    similarity_score: float
    source_path: str
    metadata: Mapping[str, str]

    def __post_init__(self) -> None:
        """Validate RetrievedChunk fields.

        Purpose:
            Ensure chunk data is complete and similarity score is valid.

        Raises:
            ValueError: When validation fails.

        Example:
            >>> RetrievedChunk(
            ...     chunk_id="chunk-1",
            ...     document_id="doc-1",
            ...     text="MapReduce — это...",
            ...     similarity_score=0.85,
            ...     source_path="/docs/architecture.md",
            ...     metadata={"ordinal": "0", "language": "ru"},
            ... )
        """
        if not self.chunk_id or not self.chunk_id.strip():
            raise ValueError("chunk_id cannot be empty.")
        if not self.document_id or not self.document_id.strip():
            raise ValueError("document_id cannot be empty.")
        if not self.text or not self.text.strip():
            raise ValueError("text cannot be empty.")
        if not self.source_path or not self.source_path.strip():
            raise ValueError("source_path cannot be empty.")
        if not 0.0 <= self.similarity_score <= 1.0:
            raise ValueError("similarity_score must be between 0.0 and 1.0.")


@dataclass(frozen=True)
class ComparisonResult:
    """Side-by-side comparison of RAG vs non-RAG answers.

    Purpose:
        Encapsulate the complete result of a RAG comparison run.

    Attributes:
        query: Original user query.
        without_rag: Answer generated without retrieval (baseline).
        with_rag: Answer generated with retrieved context.
        chunks_used: Sequence of chunks used for RAG answer.
        timestamp: ISO 8601 timestamp of comparison run.
    """

    query: Query
    without_rag: Answer
    with_rag: Answer
    chunks_used: Sequence[RetrievedChunk]
    timestamp: str

    def __post_init__(self) -> None:
        """Validate ComparisonResult fields.

        Purpose:
            Ensure all required components are present.

        Raises:
            ValueError: When validation fails.

        Example:
            >>> ComparisonResult(
            ...     query=Query(id="q1", question="Что такое MapReduce?"),
            ...     without_rag=Answer(
            ...         text="...", model="qwen", latency_ms=1000, tokens_generated=100
            ...     ),
            ...     with_rag=Answer(
            ...         text="...", model="qwen", latency_ms=1500, tokens_generated=150
            ...     ),
            ...     chunks_used=[],
            ...     timestamp="2025-11-11T12:00:00Z",
            ... )
        """
        if not isinstance(self.query, Query):
            raise ValueError("query must be a Query instance.")
        if not isinstance(self.without_rag, Answer):
            raise ValueError("without_rag must be an Answer instance.")
        if not isinstance(self.with_rag, Answer):
            raise ValueError("with_rag must be an Answer instance.")
        if not isinstance(self.chunks_used, Sequence):
            raise ValueError("chunks_used must be a Sequence.")
        if not self.timestamp or not self.timestamp.strip():
            raise ValueError("timestamp cannot be empty.")
