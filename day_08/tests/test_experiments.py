"""
Tests for experiments module with refactored structure.

Tests TokenLimitExperiments, dataclasses, and ExperimentResultBuilder
with structured logging and broken-down methods.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from core.builders import ExperimentResultBuilder
from models.data_models import (
    CompressionResult,
    ExperimentResult,
    ModelLimits,
    TokenInfo,
)
from models.experiment_models import (
    ExperimentContext,
    ExperimentMetrics,
    QueryInfo,
    ResponseInfo,
)


class TestExperimentModels:
    """Test experiment data models."""

    def test_query_info_creation(self):
        """Test QueryInfo dataclass creation."""
        compression_result = CompressionResult(
            original_text="original",
            compressed_text="compressed",
            original_tokens=100,
            compressed_tokens=50,
            compression_ratio=0.5,
            strategy_used="truncation",
        )

        query_info = QueryInfo(
            original_text="original text",
            processed_text="processed text",
            original_tokens=100,
            processed_tokens=50,
            compression_applied=True,
            compression_result=compression_result,
        )

        assert query_info.original_text == "original text"
        assert query_info.processed_text == "processed text"
        assert query_info.original_tokens == 100
        assert query_info.processed_tokens == 50
        assert query_info.compression_applied is True
        assert query_info.compression_result == compression_result

    def test_response_info_creation(self):
        """Test ResponseInfo dataclass creation."""
        response_info = ResponseInfo(
            text="response text", tokens=25, duration=1.5, success=True, error=None
        )

        assert response_info.text == "response text"
        assert response_info.tokens == 25
        assert response_info.duration == 1.5
        assert response_info.success is True
        assert response_info.error is None

    def test_experiment_context_creation(self):
        """Test ExperimentContext dataclass creation."""
        context = ExperimentContext(
            model_name="starcoder",
            query="test query",
            experiment_name="test_experiment",
            compress=True,
            compression_strategy="truncation",
        )

        assert context.model_name == "starcoder"
        assert context.query == "test query"
        assert context.experiment_name == "test_experiment"
        assert context.compress is True
        assert context.compression_strategy == "truncation"

    def test_experiment_metrics_creation(self):
        """Test ExperimentMetrics dataclass creation."""
        metrics = ExperimentMetrics(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            response_time=2.0,
            compression_ratio=0.5,
        )

        assert metrics.input_tokens == 100
        assert metrics.output_tokens == 50
        assert metrics.total_tokens == 150
        assert metrics.response_time == 2.0
        assert metrics.compression_ratio == 0.5


class TestExperimentResultBuilder:
    """Test ExperimentResultBuilder with Builder pattern."""

    def test_builder_fluent_interface(self):
        """Test fluent interface of builder."""
        builder = ExperimentResultBuilder()

        result = (
            builder.with_experiment_name("test")
            .with_model("starcoder")
            .with_query("original", "processed")
            .with_response("response")
            .with_tokens(100, 50, 150)
            .with_timing(2.0)
            .with_compression(True, None)
            .with_timestamp()
            .build()
        )

        assert isinstance(result, ExperimentResult)
        assert result.experiment_name == "test"
        assert result.model_name == "starcoder"
        assert result.original_query == "original"
        assert result.processed_query == "processed"
        assert result.response == "response"
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert result.total_tokens == 150
        assert result.response_time == 2.0
        assert result.compression_applied is True

    def test_builder_missing_required_fields(self):
        """Test builder with missing required fields."""
        builder = ExperimentResultBuilder()

        with pytest.raises(ValueError, match="Missing required fields"):
            builder.build()

    def test_builder_with_compression_result(self):
        """Test builder with compression result."""
        compression_result = CompressionResult(
            original_text="original",
            compressed_text="compressed",
            original_tokens=100,
            compressed_tokens=50,
            compression_ratio=0.5,
            strategy_used="truncation",
        )

        builder = ExperimentResultBuilder()

        result = (
            builder.with_experiment_name("test")
            .with_model("starcoder")
            .with_query("original", "processed")
            .with_response("response")
            .with_tokens(100, 50, 150)
            .with_timing(2.0)
            .with_compression(True, compression_result)
            .with_timestamp()
            .build()
        )

        assert result.compression_result == compression_result

    def test_builder_default_values(self):
        """Test builder default values."""
        builder = ExperimentResultBuilder()

        result = (
            builder.with_experiment_name("test")
            .with_model("starcoder")
            .with_query("original", "processed")
            .with_response("response")
            .with_tokens(100, 50, 150)
            .with_timing(2.0)
            .build()
        )

        assert result.compression_applied is False
        assert result.compression_result is None
        assert isinstance(result.timestamp, datetime)


class TestTokenLimitExperiments:
    """Test TokenLimitExperiments with refactored methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_model_client = Mock()
        self.mock_token_counter = Mock()
        self.mock_text_compressor = Mock()

        # Mock token counter responses
        self.mock_token_counter.count_tokens.return_value = TokenInfo(count=100)
        self.mock_token_counter.get_model_limits.return_value = ModelLimits(
            max_input_tokens=1000, max_output_tokens=500, max_total_tokens=1500
        )

        # Mock text compressor response
        self.mock_text_compressor.compress_text.return_value = CompressionResult(
            original_text="original",
            compressed_text="compressed",
            original_tokens=100,
            compressed_tokens=50,
            compression_ratio=0.5,
            strategy_used="truncation",
        )

        # Mock model client response
        mock_response = Mock()
        mock_response.response = "Model response"
        self.mock_model_client.make_request = AsyncMock(return_value=mock_response)

        from core.experiments import TokenLimitExperiments

        self.experiments = TokenLimitExperiments(
            self.mock_model_client, self.mock_token_counter, self.mock_text_compressor
        )

    def test_init_with_logging(self):
        """Test initialization with logging."""
        assert self.experiments.logger is not None
        assert self.experiments.model_client == self.mock_model_client
        assert self.experiments.token_counter == self.mock_token_counter
        assert self.experiments.text_compressor == self.mock_text_compressor

    def test_prepare_experiment_context(self):
        """Test experiment context preparation."""
        context = self.experiments._prepare_experiment_context("starcoder")

        assert isinstance(context, ExperimentContext)
        assert context.model_name == "starcoder"
        assert context.experiment_name == "limit_exceeded"
        assert context.compress is False
        assert len(context.query) > 0  # Should have long query

    def test_count_query_tokens(self):
        """Test query token counting."""
        tokens = self.experiments._count_query_tokens("test query", "starcoder")

        assert tokens == 100
        self.mock_token_counter.count_tokens.assert_called_once_with(
            "test query", "starcoder"
        )

    def test_should_compress_true(self):
        """Test compression decision when should compress."""
        should_compress = self.experiments._should_compress(True, 1500, "starcoder")

        assert should_compress is True

    def test_should_compress_false(self):
        """Test compression decision when should not compress."""
        should_compress = self.experiments._should_compress(False, 1500, "starcoder")

        assert should_compress is False

        should_compress = self.experiments._should_compress(True, 500, "starcoder")

        assert should_compress is False

    def test_compress_query(self):
        """Test query compression."""
        query_info = self.experiments._compress_query(
            "original query", "starcoder", "truncation", 100
        )

        assert isinstance(query_info, QueryInfo)
        assert query_info.original_text == "original query"
        assert query_info.processed_text == "compressed"
        assert query_info.original_tokens == 100
        assert query_info.processed_tokens == 100  # Mock returns 100
        assert query_info.compression_applied is True
        assert query_info.compression_result is not None

    def test_no_compression_query_info(self):
        """Test query info without compression."""
        query_info = self.experiments._no_compression_query_info("test query", 100)

        assert isinstance(query_info, QueryInfo)
        assert query_info.original_text == "test query"
        assert query_info.processed_text == "test query"
        assert query_info.original_tokens == 100
        assert query_info.processed_tokens == 100
        assert query_info.compression_applied is False
        assert query_info.compression_result is None

    @pytest.mark.asyncio
    async def test_execute_model_request_success(self):
        """Test successful model request execution."""
        query_info = QueryInfo(
            original_text="original",
            processed_text="processed",
            original_tokens=100,
            processed_tokens=50,
            compression_applied=True,
            compression_result=None,
        )

        response_info = await self.experiments._execute_model_request(
            "starcoder", query_info
        )

        assert isinstance(response_info, ResponseInfo)
        assert response_info.text == "Model response"
        assert response_info.tokens == 100  # Mock returns 100
        assert response_info.success is True
        assert response_info.error is None

    @pytest.mark.asyncio
    async def test_execute_model_request_failure(self):
        """Test failed model request execution."""
        self.mock_model_client.make_request.side_effect = Exception("Model error")

        query_info = QueryInfo(
            original_text="original",
            processed_text="processed",
            original_tokens=100,
            processed_tokens=50,
            compression_applied=True,
            compression_result=None,
        )

        response_info = await self.experiments._execute_model_request(
            "starcoder", query_info
        )

        assert isinstance(response_info, ResponseInfo)
        assert response_info.text == ""
        assert response_info.tokens == 0
        assert response_info.success is False
        assert response_info.error == "Model error"

    def test_build_experiment_result(self):
        """Test experiment result building."""
        query_info = QueryInfo(
            original_text="original",
            processed_text="processed",
            original_tokens=100,
            processed_tokens=50,
            compression_applied=True,
            compression_result=None,
        )

        response_info = ResponseInfo(
            text="response", tokens=25, duration=0.0, success=True, error=None
        )

        result = self.experiments._build_experiment_result(
            "test_experiment", "starcoder", query_info, response_info, 0.0
        )

        assert isinstance(result, ExperimentResult)
        assert result.experiment_name == "test_experiment"
        assert result.model_name == "starcoder"
        assert result.original_query == "original"
        assert result.processed_query == "processed"
        assert result.response == "response"
        assert result.input_tokens == 50
        assert result.output_tokens == 25
        assert result.total_tokens == 75
        assert result.compression_applied is True

    def test_collect_results(self):
        """Test result collection."""
        result1 = Mock(spec=ExperimentResult)
        result2 = Mock(spec=ExperimentResult)
        result3 = None

        results = self.experiments._collect_results([result1, result2, result3])

        assert len(results) == 2
        assert result1 in results
        assert result2 in results
        assert result3 not in results


class TestExperimentsIntegration:
    """Integration tests for experiments."""

    def setup_method(self):
        """Set up integration test fixtures."""
        self.mock_model_client = Mock()
        self.mock_token_counter = Mock()
        self.mock_text_compressor = Mock()

        # Mock responses
        self.mock_token_counter.count_tokens.return_value = TokenInfo(count=100)
        self.mock_token_counter.get_model_limits.return_value = ModelLimits(
            max_input_tokens=1000, max_output_tokens=500, max_total_tokens=1500
        )

        mock_response = Mock()
        mock_response.response = "Model response"
        self.mock_model_client.make_request = AsyncMock(return_value=mock_response)

        from core.experiments import TokenLimitExperiments

        self.experiments = TokenLimitExperiments(
            self.mock_model_client, self.mock_token_counter, self.mock_text_compressor
        )

    @pytest.mark.asyncio
    async def test_prepare_query_with_compression(self):
        """Test query preparation with compression."""
        # Mock compression needed
        self.mock_token_counter.count_tokens.return_value = TokenInfo(count=1500)

        query_info = self.experiments._prepare_query(
            "starcoder", "test query", True, "truncation"
        )

        assert query_info.compression_applied is True
        assert query_info.processed_text != query_info.original_text

    @pytest.mark.asyncio
    async def test_prepare_query_without_compression(self):
        """Test query preparation without compression."""
        # Mock no compression needed
        self.mock_token_counter.count_tokens.return_value = TokenInfo(count=500)

        query_info = self.experiments._prepare_query(
            "starcoder", "test query", True, "truncation"
        )

        assert query_info.compression_applied is False
        assert query_info.processed_text == query_info.original_text

    @pytest.mark.asyncio
    async def test_run_single_experiment_flow(self):
        """Test complete single experiment flow."""
        # Mock no compression needed
        self.mock_token_counter.count_tokens.return_value = TokenInfo(count=500)

        result = await self.experiments._run_single_experiment(
            model_name="starcoder",
            query="test query",
            experiment_name="test_experiment",
            compress=False,
        )

        assert isinstance(result, ExperimentResult)
        assert result.experiment_name == "test_experiment"
        assert result.model_name == "starcoder"
        assert result.response == "Model response"
        assert result.compression_applied is False
