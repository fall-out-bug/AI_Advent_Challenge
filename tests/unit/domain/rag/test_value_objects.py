"""Unit tests for RAG domain value objects."""

import pytest

from src.domain.rag import Answer, ComparisonResult, Query, RetrievedChunk


class TestQuery:
    """Test suite for Query value object."""

    def test_valid_query_creation(self) -> None:
        """Test creating a valid Query."""
        query = Query(
            id="q1",
            question="Что такое MapReduce?",
            category="Lectures",
            language="ru",
        )

        assert query.id == "q1"
        assert query.question == "Что такое MapReduce?"
        assert query.category == "Lectures"
        assert query.language == "ru"
        assert query.expectation is None

    def test_query_with_expectation(self) -> None:
        """Test Query with ground truth expectation."""
        query = Query(
            id="q2",
            question="Что такое CAP-теорема?",
            expectation="Consistency, Availability, Partition tolerance",
        )

        assert query.expectation == "Consistency, Availability, Partition tolerance"

    def test_query_default_language(self) -> None:
        """Test Query uses Russian as default language."""
        query = Query(id="q3", question="Test?")
        assert query.language == "ru"

    def test_query_empty_id_raises(self) -> None:
        """Test Query validation fails on empty ID."""
        with pytest.raises(ValueError, match="id cannot be empty"):
            Query(id="", question="Test?")

    def test_query_whitespace_id_raises(self) -> None:
        """Test Query validation fails on whitespace-only ID."""
        with pytest.raises(ValueError, match="id cannot be empty"):
            Query(id="   ", question="Test?")

    def test_query_empty_question_raises(self) -> None:
        """Test Query validation fails on empty question."""
        with pytest.raises(ValueError, match="question cannot be empty"):
            Query(id="q1", question="")

    def test_query_empty_language_raises(self) -> None:
        """Test Query validation fails on empty language."""
        with pytest.raises(ValueError, match="language cannot be empty"):
            Query(id="q1", question="Test?", language="")

    def test_query_immutability(self) -> None:
        """Test Query is immutable (frozen dataclass)."""
        query = Query(id="q1", question="Test?")
        with pytest.raises(AttributeError):
            query.question = "Modified?"  # type: ignore


class TestAnswer:
    """Test suite for Answer value object."""

    def test_valid_answer_creation(self) -> None:
        """Test creating a valid Answer."""
        answer = Answer(
            text="MapReduce — это модель программирования...",
            model="qwen",
            latency_ms=1500,
            tokens_generated=120,
        )

        assert answer.text.startswith("MapReduce")
        assert answer.model == "qwen"
        assert answer.latency_ms == 1500
        assert answer.tokens_generated == 120
        assert answer.metadata is None

    def test_answer_with_metadata(self) -> None:
        """Test Answer with optional metadata."""
        answer = Answer(
            text="Test answer",
            model="gpt-4",
            latency_ms=2000,
            tokens_generated=150,
            metadata={"finish_reason": "stop", "temperature": "0.7"},
        )

        assert answer.metadata == {"finish_reason": "stop", "temperature": "0.7"}

    def test_answer_empty_text_raises(self) -> None:
        """Test Answer validation fails on empty text."""
        with pytest.raises(ValueError, match="text cannot be empty"):
            Answer(text="", model="qwen", latency_ms=1000, tokens_generated=50)

    def test_answer_empty_model_raises(self) -> None:
        """Test Answer validation fails on empty model."""
        with pytest.raises(ValueError, match="model cannot be empty"):
            Answer(text="Test", model="", latency_ms=1000, tokens_generated=50)

    def test_answer_negative_latency_raises(self) -> None:
        """Test Answer validation fails on negative latency."""
        with pytest.raises(ValueError, match="latency_ms must be non-negative"):
            Answer(text="Test", model="qwen", latency_ms=-100, tokens_generated=50)

    def test_answer_negative_tokens_raises(self) -> None:
        """Test Answer validation fails on negative tokens."""
        with pytest.raises(ValueError, match="tokens_generated must be non-negative"):
            Answer(text="Test", model="qwen", latency_ms=1000, tokens_generated=-50)

    def test_answer_zero_latency_allowed(self) -> None:
        """Test Answer allows zero latency (edge case)."""
        answer = Answer(text="Test", model="qwen", latency_ms=0, tokens_generated=10)
        assert answer.latency_ms == 0

    def test_answer_immutability(self) -> None:
        """Test Answer is immutable."""
        answer = Answer(text="Test", model="qwen", latency_ms=1000, tokens_generated=50)
        with pytest.raises(AttributeError):
            answer.text = "Modified"  # type: ignore


class TestRetrievedChunk:
    """Test suite for RetrievedChunk value object."""

    def test_valid_chunk_creation(self) -> None:
        """Test creating a valid RetrievedChunk."""
        chunk = RetrievedChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            text="MapReduce — это модель...",
            similarity_score=0.85,
            source_path="/docs/lectures/mapreduce.md",
            metadata={"ordinal": "0", "language": "ru"},
        )

        assert chunk.chunk_id == "chunk-1"
        assert chunk.document_id == "doc-1"
        assert chunk.text.startswith("MapReduce")
        assert chunk.similarity_score == 0.85
        assert chunk.source_path == "/docs/lectures/mapreduce.md"
        assert chunk.metadata["ordinal"] == "0"

    def test_chunk_empty_chunk_id_raises(self) -> None:
        """Test RetrievedChunk validation fails on empty chunk_id."""
        with pytest.raises(ValueError, match="chunk_id cannot be empty"):
            RetrievedChunk(
                chunk_id="",
                document_id="doc-1",
                text="Test",
                similarity_score=0.5,
                source_path="/path",
                metadata={},
            )

    def test_chunk_empty_document_id_raises(self) -> None:
        """Test RetrievedChunk validation fails on empty document_id."""
        with pytest.raises(ValueError, match="document_id cannot be empty"):
            RetrievedChunk(
                chunk_id="chunk-1",
                document_id="",
                text="Test",
                similarity_score=0.5,
                source_path="/path",
                metadata={},
            )

    def test_chunk_empty_text_raises(self) -> None:
        """Test RetrievedChunk validation fails on empty text."""
        with pytest.raises(ValueError, match="text cannot be empty"):
            RetrievedChunk(
                chunk_id="chunk-1",
                document_id="doc-1",
                text="",
                similarity_score=0.5,
                source_path="/path",
                metadata={},
            )

    def test_chunk_empty_source_path_raises(self) -> None:
        """Test RetrievedChunk validation fails on empty source_path."""
        with pytest.raises(ValueError, match="source_path cannot be empty"):
            RetrievedChunk(
                chunk_id="chunk-1",
                document_id="doc-1",
                text="Test",
                similarity_score=0.5,
                source_path="",
                metadata={},
            )

    def test_chunk_score_below_zero_raises(self) -> None:
        """Test RetrievedChunk validation fails on negative score."""
        with pytest.raises(ValueError, match="similarity_score must be between 0.0"):
            RetrievedChunk(
                chunk_id="chunk-1",
                document_id="doc-1",
                text="Test",
                similarity_score=-0.1,
                source_path="/path",
                metadata={},
            )

    def test_chunk_score_above_one_raises(self) -> None:
        """Test RetrievedChunk validation fails on score > 1.0."""
        with pytest.raises(ValueError, match="similarity_score must be between 0.0"):
            RetrievedChunk(
                chunk_id="chunk-1",
                document_id="doc-1",
                text="Test",
                similarity_score=1.5,
                source_path="/path",
                metadata={},
            )

    def test_chunk_score_boundaries(self) -> None:
        """Test RetrievedChunk allows 0.0 and 1.0 scores."""
        chunk_zero = RetrievedChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            text="Test",
            similarity_score=0.0,
            source_path="/path",
            metadata={},
        )
        assert chunk_zero.similarity_score == 0.0

        chunk_one = RetrievedChunk(
            chunk_id="chunk-2",
            document_id="doc-2",
            text="Test",
            similarity_score=1.0,
            source_path="/path",
            metadata={},
        )
        assert chunk_one.similarity_score == 1.0

    def test_chunk_immutability(self) -> None:
        """Test RetrievedChunk is immutable."""
        chunk = RetrievedChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            text="Test",
            similarity_score=0.5,
            source_path="/path",
            metadata={},
        )
        with pytest.raises(AttributeError):
            chunk.text = "Modified"  # type: ignore


class TestComparisonResult:
    """Test suite for ComparisonResult value object."""

    def test_valid_comparison_result_creation(self) -> None:
        """Test creating a valid ComparisonResult."""
        query = Query(id="q1", question="Test?")
        without_rag = Answer(
            text="Answer 1", model="qwen", latency_ms=1000, tokens_generated=100
        )
        with_rag = Answer(
            text="Answer 2", model="qwen", latency_ms=1500, tokens_generated=150
        )
        chunks = [
            RetrievedChunk(
                chunk_id="c1",
                document_id="d1",
                text="Chunk 1",
                similarity_score=0.9,
                source_path="/path",
                metadata={},
            )
        ]

        result = ComparisonResult(
            query=query,
            without_rag=without_rag,
            with_rag=with_rag,
            chunks_used=chunks,
            timestamp="2025-11-11T12:00:00Z",
        )

        assert result.query == query
        assert result.without_rag == without_rag
        assert result.with_rag == with_rag
        assert len(result.chunks_used) == 1
        assert result.timestamp == "2025-11-11T12:00:00Z"

    def test_comparison_result_empty_chunks_allowed(self) -> None:
        """Test ComparisonResult allows empty chunks list."""
        query = Query(id="q1", question="Test?")
        without_rag = Answer(
            text="Answer 1", model="qwen", latency_ms=1000, tokens_generated=100
        )
        with_rag = Answer(
            text="Answer 2", model="qwen", latency_ms=1500, tokens_generated=150
        )

        result = ComparisonResult(
            query=query,
            without_rag=without_rag,
            with_rag=with_rag,
            chunks_used=[],
            timestamp="2025-11-11T12:00:00Z",
        )

        assert len(result.chunks_used) == 0

    def test_comparison_result_invalid_query_raises(self) -> None:
        """Test ComparisonResult validation fails on invalid query."""
        with pytest.raises(ValueError, match="query must be a Query instance"):
            ComparisonResult(
                query="not a query",  # type: ignore
                without_rag=Answer(
                    text="A", model="q", latency_ms=1, tokens_generated=1
                ),
                with_rag=Answer(text="B", model="q", latency_ms=1, tokens_generated=1),
                chunks_used=[],
                timestamp="2025-11-11T12:00:00Z",
            )

    def test_comparison_result_invalid_without_rag_raises(self) -> None:
        """Test ComparisonResult validation fails on invalid without_rag."""
        query = Query(id="q1", question="Test?")
        with pytest.raises(ValueError, match="without_rag must be an Answer instance"):
            ComparisonResult(
                query=query,
                without_rag="not an answer",  # type: ignore
                with_rag=Answer(text="B", model="q", latency_ms=1, tokens_generated=1),
                chunks_used=[],
                timestamp="2025-11-11T12:00:00Z",
            )

    def test_comparison_result_invalid_with_rag_raises(self) -> None:
        """Test ComparisonResult validation fails on invalid with_rag."""
        query = Query(id="q1", question="Test?")
        with pytest.raises(ValueError, match="with_rag must be an Answer instance"):
            ComparisonResult(
                query=query,
                without_rag=Answer(
                    text="A", model="q", latency_ms=1, tokens_generated=1
                ),
                with_rag="not an answer",  # type: ignore
                chunks_used=[],
                timestamp="2025-11-11T12:00:00Z",
            )

    def test_comparison_result_empty_timestamp_raises(self) -> None:
        """Test ComparisonResult validation fails on empty timestamp."""
        query = Query(id="q1", question="Test?")
        without_rag = Answer(text="A", model="q", latency_ms=1, tokens_generated=1)
        with_rag = Answer(text="B", model="q", latency_ms=1, tokens_generated=1)

        with pytest.raises(ValueError, match="timestamp cannot be empty"):
            ComparisonResult(
                query=query,
                without_rag=without_rag,
                with_rag=with_rag,
                chunks_used=[],
                timestamp="",
            )

    def test_comparison_result_immutability(self) -> None:
        """Test ComparisonResult is immutable."""
        query = Query(id="q1", question="Test?")
        without_rag = Answer(text="A", model="q", latency_ms=1, tokens_generated=1)
        with_rag = Answer(text="B", model="q", latency_ms=1, tokens_generated=1)
        result = ComparisonResult(
            query=query,
            without_rag=without_rag,
            with_rag=with_rag,
            chunks_used=[],
            timestamp="2025-11-11T12:00:00Z",
        )

        with pytest.raises(AttributeError):
            result.timestamp = "2025-11-12T00:00:00Z"  # type: ignore
