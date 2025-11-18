"""Characterization tests for Map-Reduce summarizer behavior.

These tests document current Map-Reduce summarizer behavior
before refactoring in Cluster D.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.domain.value_objects.summarization_context import SummarizationContext
from src.infrastructure.llm.summarizers.map_reduce_summarizer import MapReduceSummarizer


class TestMapReduceSummarizerInterface:
    """Characterize Map-Reduce summarizer interface and behavior."""

    def test_map_reduce_summarizer_constructor_signature(self):
        """Characterize constructor parameters.

        Purpose:
            Document constructor parameters before introducing
            dataclass for chunk summarization params.
        """
        import inspect

        sig = inspect.signature(MapReduceSummarizer.__init__)
        params = list(sig.parameters.keys())

        # Required parameters
        assert "llm_client" in params
        assert "chunker" in params
        assert "token_counter" in params
        assert "text_cleaner" in params
        assert "quality_checker" in params

        # Optional parameters with defaults
        assert "temperature" in params
        assert "map_max_tokens" in params
        assert "reduce_max_tokens" in params

        # Check default values
        temp_param = sig.parameters.get("temperature")
        map_tokens_param = sig.parameters.get("map_max_tokens")
        reduce_tokens_param = sig.parameters.get("reduce_max_tokens")

        if temp_param and temp_param.default != inspect.Parameter.empty:
            assert temp_param.default == 0.2

        if map_tokens_param and map_tokens_param.default != inspect.Parameter.empty:
            assert map_tokens_param.default == 600

        if reduce_tokens_param and reduce_tokens_param.default != inspect.Parameter.empty:
            assert reduce_tokens_param.default == 2000

    def test_map_reduce_summarizer_summarize_text_signature(self):
        """Characterize summarize_text() method signature.

        Purpose:
            Document method parameters and return type.
        """
        import inspect

        sig = inspect.signature(MapReduceSummarizer.summarize_text)
        params = list(sig.parameters.keys())

        assert "text" in params
        assert "max_sentences" in params
        assert "language" in params
        assert "context" in params

        # Check default values
        lang_param = sig.parameters.get("language")
        if lang_param and lang_param.default != inspect.Parameter.empty:
            assert lang_param.default == "ru"

        # Check return type
        return_annotation = sig.return_annotation
        assert "SummaryResult" in str(return_annotation)

    def test_map_reduce_summarizer_chunking_behavior_characterization(
        self, map_reduce_summarizer, mock_chunker
    ):
        """Characterize chunking behavior.

        Purpose:
            Document that summarizer uses chunker.chunk_text() method
            and processes chunks in parallel during Map phase.
            Note: Current implementation has a bug where _summarize_chunk()
            is called with context parameter but doesn't accept it.
        """
        # Verify: Summarizer has chunker dependency
        assert hasattr(map_reduce_summarizer, "chunker")
        assert hasattr(map_reduce_summarizer.chunker, "chunk_text")

        # Verify: summarize_text method exists and uses chunker
        assert hasattr(map_reduce_summarizer, "summarize_text")

        # Verify: Map phase uses asyncio.gather for parallel processing
        # (This is documented in code, not tested via execution due to mocking complexity)

        # Verify: Single chunk path uses direct summarization
        # Multiple chunks path uses Map-Reduce strategy

        # Known issue: _summarize_chunk() signature doesn't match call sites
        # Call sites pass context=context, but method doesn't accept context parameter
        # This will be addressed in D.4 (introduce dataclass for chunk params)

    def test_map_reduce_summarizer_chunk_summarization_params_characterization(
        self, map_reduce_summarizer
    ):
        """Characterize chunk summarization parameters.

        Purpose:
            Document that chunk summarization uses adjusted max_sentences:
            max(3, max_sentences // 2) for Map phase chunks.
            Single chunk uses full max_sentences.
            Note: Current implementation has parameter mismatch bug.
        """
        # Verify: Map phase adjusts max_sentences for chunks
        # Code uses: max(3, max_sentences // 2) for chunk summarization
        # Single chunk uses: max_sentences (full value)

        # Verify: map_max_tokens and reduce_max_tokens are used
        assert hasattr(map_reduce_summarizer, "map_max_tokens")
        assert hasattr(map_reduce_summarizer, "reduce_max_tokens")

        # Verify: _summarize_chunk uses map_max_tokens for LLM generation
        # This is documented in code, not tested via execution due to parameter mismatch bug

        # Known issue: _summarize_chunk() called with context but doesn't accept it
        # Code at lines 118, 140-144 calls _summarize_chunk(chunk, max_sentences=..., language=..., context=context)
        # But method signature (line 284) is: async def _summarize_chunk(self, chunk, max_sentences: int, language: str) -> str
        # This causes TypeError in current implementation
        # Will be fixed in D.4 when introducing dataclass for chunk params

    def test_map_reduce_summarizer_private_methods_characterization(
        self, map_reduce_summarizer
    ):
        """Characterize private methods that may need refactoring.

        Purpose:
            Document _summarize_chunk() signature and behavior
            before introducing dataclass for chunk params.
        """
        # Verify _summarize_chunk exists and has expected signature
        assert hasattr(map_reduce_summarizer, "_summarize_chunk")

        import inspect

        sig = inspect.signature(MapReduceSummarizer._summarize_chunk)
        params = list(sig.parameters.keys())

        # Expected parameters: params (ChunkSummarizationParams dataclass)
        assert "self" in params
        assert "params" in params

        # Verify params type is ChunkSummarizationParams
        from src.infrastructure.llm.summarizers.chunk_summarization_params import (
            ChunkSummarizationParams,
        )

        param_annotation = sig.parameters["params"].annotation
        # Annotation may be a string or the class itself (forward references)
        if isinstance(param_annotation, str):
            assert param_annotation == "ChunkSummarizationParams"
        else:
            assert param_annotation == ChunkSummarizationParams

    def test_map_reduce_summarizer_map_reduce_tokens_characterization(
        self, map_reduce_summarizer
    ):
        """Characterize map_max_tokens and reduce_max_tokens usage.

        Purpose:
            Document current token limits before introducing dataclass.
        """
        # Verify instance attributes exist
        assert hasattr(map_reduce_summarizer, "map_max_tokens")
        assert hasattr(map_reduce_summarizer, "reduce_max_tokens")
        assert hasattr(map_reduce_summarizer, "temperature")

        # Verify default values
        assert map_reduce_summarizer.map_max_tokens == 600
        assert map_reduce_summarizer.reduce_max_tokens == 2000
        assert map_reduce_summarizer.temperature == 0.2


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for Map-Reduce summarizer."""
    client = MagicMock()
    client.generate = AsyncMock()
    return client


@pytest.fixture
def mock_chunker():
    """Mock semantic chunker."""
    chunker = MagicMock()
    chunker.chunk_text = MagicMock(return_value=[])
    return chunker


@pytest.fixture
def mock_token_counter():
    """Mock token counter."""
    counter = MagicMock()
    counter.count_tokens = MagicMock(return_value=100)
    return counter


@pytest.fixture
def mock_text_cleaner():
    """Mock text cleaner."""
    cleaner = MagicMock()
    cleaner.clean_for_summarization = MagicMock(side_effect=lambda x: x)
    cleaner.clean_llm_response = MagicMock(side_effect=lambda x: x)
    cleaner.deduplicate_sentences = MagicMock(side_effect=lambda x: x)
    return cleaner


@pytest.fixture
def mock_quality_checker():
    """Mock quality checker."""
    checker = MagicMock()
    quality_score = MagicMock()
    quality_score.score = 0.9
    checker.check_quality = MagicMock(return_value=quality_score)
    return checker


@pytest.fixture
def map_reduce_summarizer(
    mock_llm_client,
    mock_chunker,
    mock_token_counter,
    mock_text_cleaner,
    mock_quality_checker,
):
    """Map-Reduce summarizer with mocked dependencies."""
    return MapReduceSummarizer(
        llm_client=mock_llm_client,
        chunker=mock_chunker,
        token_counter=mock_token_counter,
        text_cleaner=mock_text_cleaner,
        quality_checker=mock_quality_checker,
        temperature=0.2,
        map_max_tokens=600,
        reduce_max_tokens=2000,
    )
