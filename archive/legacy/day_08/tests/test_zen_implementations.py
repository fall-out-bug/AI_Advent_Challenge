"""
Tests for Zen Python implementations.

Following Zen principles:
- Explicit is better than implicit - clear test cases
- Simple is better than complex - focused test functions
- Readability counts - descriptive test names
"""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from core.experiments_zen import (
    ExperimentConfig,
    ExperimentError,
    ExperimentRunner,
    QueryGenerator,
    TokenLimitExperiments,
)
from core.ml_client_zen import (
    HybridTokenCounter,
    InvalidRequestError,
    MLServiceError,
    ServiceConfig,
    ServiceUnavailableError,
    TokenAnalysisClient,
)
from core.token_analyzer_zen import (
    MODEL_LIMITS_MAP,
    LimitProfile,
    SimpleTokenCounter,
    TokenCounter,
    TokenCounterError,
)


class TestSimpleTokenCounterZen:
    """Test SimpleTokenCounter Zen implementation."""

    @pytest.fixture
    def token_counter(self):
        return SimpleTokenCounter(LimitProfile.PRACTICAL)

    def test_count_tokens_empty_text(self, token_counter):
        """Test counting tokens in empty text."""
        result = token_counter.count_tokens("")
        assert result.count == 0
        assert result.model_name == "starcoder"

    def test_count_tokens_simple_text(self, token_counter):
        """Test counting tokens in simple text."""
        result = token_counter.count_tokens("Hello world")
        assert result.count == 2  # 2 words * 1.3 = 2 tokens
        assert result.model_name == "starcoder"

    def test_count_tokens_invalid_input(self, token_counter):
        """Test counting tokens with invalid input."""
        with pytest.raises(TokenCounterError):
            token_counter.count_tokens(123)  # Not a string

    def test_get_model_limits_starcoder(self, token_counter):
        """Test getting limits for StarCoder model."""
        limits = token_counter.get_model_limits("starcoder")
        assert limits.max_input_tokens == 4096  # Practical limit
        assert limits.max_output_tokens == 1024

    def test_get_model_limits_unknown_model(self, token_counter):
        """Test getting limits for unknown model (should default to starcoder)."""
        limits = token_counter.get_model_limits("unknown_model")
        assert limits.max_input_tokens == 4096  # Defaults to starcoder

    def test_check_limit_exceeded_within_limit(self, token_counter):
        """Test limit checking with text within limits."""
        text = "Short text"
        assert not token_counter.check_limit_exceeded(text, "starcoder")

    def test_check_limit_exceeded_over_limit(self, token_counter):
        """Test limit checking with text over limits."""
        # Create text that exceeds practical limit (4096 tokens)
        long_text = "word " * 3500  # This should be > 4096 tokens
        assert token_counter.check_limit_exceeded(long_text, "starcoder")

    def test_estimate_compression_target(self, token_counter):
        """Test compression target estimation."""
        text = "Some text"
        target = token_counter.estimate_compression_target(text, "starcoder", 0.9)
        assert target == int(4096 * 0.9)  # 3686

    def test_estimate_compression_target_invalid_margin(self, token_counter):
        """Test compression target with invalid safety margin."""
        with pytest.raises(TokenCounterError):
            token_counter.estimate_compression_target("text", "starcoder", 1.5)

    def test_set_limit_profile(self, token_counter):
        """Test changing limit profile."""
        token_counter.set_limit_profile(LimitProfile.THEORETICAL)
        limits = token_counter.get_model_limits("starcoder")
        assert limits.max_input_tokens == 16384  # Theoretical limit


class TestTokenCounterZen:
    """Test unified TokenCounter Zen implementation."""

    def test_token_counter_simple_mode(self):
        """Test TokenCounter in simple mode."""
        counter = TokenCounter(mode="simple", limit_profile=LimitProfile.PRACTICAL)
        result = counter.count_tokens("Hello world")
        assert result.count == 2
        assert counter.mode == "simple"

    def test_token_counter_accurate_mode(self):
        """Test TokenCounter in accurate mode."""
        counter = TokenCounter(mode="accurate", limit_profile=LimitProfile.PRACTICAL)
        assert counter.mode == "accurate"
        # Note: actual token counting would require ML service

    def test_token_counter_invalid_mode(self):
        """Test TokenCounter with invalid mode."""
        with pytest.raises(TokenCounterError):
            TokenCounter(mode="invalid")


class TestQueryGeneratorZen:
    """Test QueryGenerator Zen implementation."""

    def test_create_long_query(self):
        """Test creating long query."""
        query = QueryGenerator.create_long_query(multiplier=2)
        assert len(query) > len(QueryGenerator.BASE_QUERY)
        assert QueryGenerator.BASE_QUERY in query

    def test_create_long_query_invalid_multiplier(self):
        """Test creating long query with invalid multiplier."""
        with pytest.raises(ExperimentError):
            QueryGenerator.create_long_query(multiplier=0)

    def test_create_short_query(self):
        """Test creating short query."""
        query = QueryGenerator.create_short_query()
        assert isinstance(query, str)
        assert len(query) < len(QueryGenerator.BASE_QUERY)


class TestExperimentConfigZen:
    """Test ExperimentConfig Zen implementation."""

    def test_experiment_config_defaults(self):
        """Test experiment config with defaults."""
        config = ExperimentConfig(model_name="starcoder")
        assert config.model_name == "starcoder"
        assert config.max_retries == 3
        assert config.timeout_seconds == 30
        assert config.compression_strategies == ["truncation", "keywords"]

    def test_experiment_config_custom(self):
        """Test experiment config with custom values."""
        config = ExperimentConfig(
            model_name="mistral",
            max_retries=5,
            timeout_seconds=60,
            compression_strategies=["extractive", "semantic"],
        )
        assert config.model_name == "mistral"
        assert config.max_retries == 5
        assert config.timeout_seconds == 60
        assert config.compression_strategies == ["extractive", "semantic"]

    def test_experiment_config_invalid_retries(self):
        """Test experiment config with invalid retries."""
        with pytest.raises(ExperimentError):
            ExperimentConfig(model_name="starcoder", max_retries=0)

    def test_experiment_config_invalid_timeout(self):
        """Test experiment config with invalid timeout."""
        with pytest.raises(ExperimentError):
            ExperimentConfig(model_name="starcoder", timeout_seconds=0)


class TestServiceConfigZen:
    """Test ServiceConfig Zen implementation."""

    def test_service_config_defaults(self):
        """Test service config with defaults."""
        config = ServiceConfig()
        assert config.base_url == "http://localhost:8004"
        assert config.timeout_seconds == 30
        assert config.max_retries == 3
        assert config.retry_delay == 1.0

    def test_service_config_custom(self):
        """Test service config with custom values."""
        config = ServiceConfig(
            base_url="http://example.com:8080",
            timeout_seconds=60,
            max_retries=5,
            retry_delay=2.0,
        )
        assert config.base_url == "http://example.com:8080"
        assert config.timeout_seconds == 60
        assert config.max_retries == 5
        assert config.retry_delay == 2.0

    def test_service_config_invalid_timeout(self):
        """Test service config with invalid timeout."""
        with pytest.raises(MLServiceError):
            ServiceConfig(timeout_seconds=0)

    def test_service_config_invalid_retries(self):
        """Test service config with invalid retries."""
        with pytest.raises(MLServiceError):
            ServiceConfig(max_retries=-1)

    def test_service_config_invalid_delay(self):
        """Test service config with invalid delay."""
        with pytest.raises(MLServiceError):
            ServiceConfig(retry_delay=-1.0)


class TestTokenAnalysisClientZen:
    """Test TokenAnalysisClient Zen implementation."""

    @pytest.fixture
    def mock_client(self):
        """Create mock HTTP client."""
        with patch("httpx.AsyncClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            yield mock_instance

    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_client):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy", "models": ["starcoder"]}
        mock_client.request.return_value = mock_response

        client = TokenAnalysisClient()
        result = await client.health_check()

        assert result["status"] == "healthy"
        assert "starcoder" in result["models"]

    @pytest.mark.asyncio
    async def test_health_check_service_unavailable(self, mock_client):
        """Test health check when service is unavailable."""
        mock_client.request.side_effect = httpx.RequestError("Connection failed")

        client = TokenAnalysisClient()
        with pytest.raises(ServiceUnavailableError):
            await client.health_check()

    @pytest.mark.asyncio
    async def test_count_tokens_success(self, mock_client):
        """Test successful token counting."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "count": 5,
            "estimated_cost": 0.0,
            "model_name": "starcoder",
        }
        mock_client.request.return_value = mock_response

        client = TokenAnalysisClient()
        result = await client.count_tokens("Hello world", "starcoder")

        assert result.count == 5
        assert result.model_name == "starcoder"

    @pytest.mark.asyncio
    async def test_count_tokens_invalid_input(self, mock_client):
        """Test token counting with invalid input."""
        client = TokenAnalysisClient()

        with pytest.raises(InvalidRequestError):
            await client.count_tokens(123)  # Not a string

        with pytest.raises(InvalidRequestError):
            await client.count_tokens("text", 123)  # Model name not string

    @pytest.mark.asyncio
    async def test_compress_text_success(self, mock_client):
        """Test successful text compression."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "original_text": "long text",
            "compressed_text": "short text",
            "original_tokens": 100,
            "compressed_tokens": 50,
            "compression_ratio": 0.5,
            "strategy_used": "extractive",
        }
        mock_client.request.return_value = mock_response

        client = TokenAnalysisClient()
        result = await client.compress_text("long text", 50, "starcoder", "extractive")

        assert result.compression_ratio == 0.5
        assert result.strategy_used == "extractive"

    @pytest.mark.asyncio
    async def test_compress_text_invalid_strategy(self, mock_client):
        """Test text compression with invalid strategy."""
        client = TokenAnalysisClient()

        with pytest.raises(InvalidRequestError):
            await client.compress_text("text", 100, "starcoder", "invalid")

    @pytest.mark.asyncio
    async def test_compress_text_invalid_max_tokens(self, mock_client):
        """Test text compression with invalid max_tokens."""
        client = TokenAnalysisClient()

        with pytest.raises(InvalidRequestError):
            await client.compress_text("text", 0, "starcoder", "extractive")

        with pytest.raises(InvalidRequestError):
            await client.compress_text("text", -1, "starcoder", "extractive")


class TestHybridTokenCounterZen:
    """Test HybridTokenCounter Zen implementation."""

    @pytest.fixture
    def mock_ml_client(self):
        """Create mock ML client."""
        client = AsyncMock()
        client.health_check.return_value = {"status": "healthy"}
        return client

    @pytest.fixture
    def mock_fallback_counter(self):
        """Create mock fallback counter."""
        counter = Mock()
        counter.count_tokens.return_value = Mock(count=5, model_name="starcoder")
        return counter

    @pytest.mark.asyncio
    async def test_count_tokens_ml_service_available(
        self, mock_ml_client, mock_fallback_counter
    ):
        """Test token counting when ML service is available."""
        mock_ml_client.count_tokens.return_value = Mock(
            count=10, model_name="starcoder"
        )

        hybrid = HybridTokenCounter(mock_ml_client, mock_fallback_counter)
        result = await hybrid.count_tokens("Hello world")

        assert result.count == 10
        mock_ml_client.count_tokens.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_tokens_ml_service_unavailable(
        self, mock_ml_client, mock_fallback_counter
    ):
        """Test token counting when ML service is unavailable."""
        mock_ml_client.health_check.side_effect = ServiceUnavailableError(
            "Service down"
        )

        hybrid = HybridTokenCounter(mock_ml_client, mock_fallback_counter)
        result = await hybrid.count_tokens("Hello world")

        assert result.count == 5  # Fallback result
        mock_fallback_counter.count_tokens.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_tokens_no_fallback(self, mock_ml_client):
        """Test token counting when no fallback is available."""
        mock_ml_client.health_check.side_effect = ServiceUnavailableError(
            "Service down"
        )

        hybrid = HybridTokenCounter(mock_ml_client, None)

        with pytest.raises(MLServiceError):
            await hybrid.count_tokens("Hello world")
