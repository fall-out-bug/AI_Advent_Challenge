"""
Tests for ML client with retry logic and circuit breaker.

Tests TokenAnalysisClient, HybridTokenCounter, and RequestValidator
with resilience features.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx
from core.ml_client import TokenAnalysisClient, HybridTokenCounter
from core.validators import RequestValidator
from models.data_models import TokenInfo, CompressionResult
from utils.retry import ResilientClient, RetryConfig, CircuitBreakerConfig


class TestRequestValidator:
    """Test RequestValidator class."""
    
    def test_validate_text_valid(self):
        """Test valid text validation."""
        RequestValidator.validate_text("This is valid text")
        RequestValidator.validate_text("Short")
    
    def test_validate_text_invalid(self):
        """Test invalid text validation."""
        with pytest.raises(ValueError, match="Text must be a string"):
            RequestValidator.validate_text(123)
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            RequestValidator.validate_text("")
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            RequestValidator.validate_text("   ")
        
        with pytest.raises(ValueError, match="Text too long"):
            RequestValidator.validate_text("x" * 1000001)
    
    def test_validate_model_name_valid(self):
        """Test valid model name validation."""
        RequestValidator.validate_model_name("starcoder")
        RequestValidator.validate_model_name("mistral")
        RequestValidator.validate_model_name("starcoder", ["starcoder", "mistral"])
    
    def test_validate_model_name_invalid(self):
        """Test invalid model name validation."""
        with pytest.raises(ValueError, match="Model name must be a string"):
            RequestValidator.validate_model_name(123)
        
        with pytest.raises(ValueError, match="Model name cannot be empty"):
            RequestValidator.validate_model_name("")
        
        with pytest.raises(ValueError, match="not in allowed list"):
            RequestValidator.validate_model_name("invalid", ["starcoder"])
    
    def test_validate_strategy_valid(self):
        """Test valid strategy validation."""
        strategy = RequestValidator.validate_strategy("truncation")
        assert strategy.value == "truncation"
        
        strategy = RequestValidator.validate_strategy("keywords")
        assert strategy.value == "keywords"
    
    def test_validate_strategy_invalid(self):
        """Test invalid strategy validation."""
        with pytest.raises(ValueError, match="Invalid strategy"):
            RequestValidator.validate_strategy("invalid")
    
    def test_validate_max_tokens_valid(self):
        """Test valid max tokens validation."""
        RequestValidator.validate_max_tokens(100)
        RequestValidator.validate_max_tokens(1)
        RequestValidator.validate_max_tokens(1000, min_tokens=500)
    
    def test_validate_max_tokens_invalid(self):
        """Test invalid max tokens validation."""
        with pytest.raises(ValueError, match="Max tokens must be an integer"):
            RequestValidator.validate_max_tokens("100")
        
        with pytest.raises(ValueError, match="Max tokens must be >= 1"):
            RequestValidator.validate_max_tokens(0)
    
    def test_validate_texts_list_valid(self):
        """Test valid texts list validation."""
        texts = ["text1", "text2", "text3"]
        RequestValidator.validate_texts_list(texts)
    
    def test_validate_texts_list_invalid(self):
        """Test invalid texts list validation."""
        with pytest.raises(ValueError, match="Texts must be a list"):
            RequestValidator.validate_texts_list("not a list")
        
        with pytest.raises(ValueError, match="Texts list cannot be empty"):
            RequestValidator.validate_texts_list([])
        
        with pytest.raises(ValueError, match="Too many texts"):
            RequestValidator.validate_texts_list(["text"] * 101)
        
        with pytest.raises(ValueError, match="Invalid text at index 1"):
            RequestValidator.validate_texts_list(["valid", ""])


class TestTokenAnalysisClient:
    """Test TokenAnalysisClient with resilience."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TokenAnalysisClient("http://localhost:8004")
        self.mock_response_data = {
            "count": 10,
            "estimated_cost": 0.001,
            "model_name": "starcoder"
        }
    
    def test_init_with_resilience(self):
        """Test client initialization with resilience components."""
        assert isinstance(self.client.resilient_client, ResilientClient)
        assert self.client.logger is not None
        assert self.client.base_url == "http://localhost:8004"
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""
        with patch.object(self.client, '_execute_with_resilience') as mock_execute:
            mock_execute.return_value = {"status": "healthy", "models": ["starcoder"]}
            
            result = await self.client.health_check()
            
            assert result == {"status": "healthy", "models": ["starcoder"]}
            mock_execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check failure."""
        with patch.object(self.client, '_execute_with_resilience') as mock_execute:
            mock_execute.side_effect = Exception("Connection failed")
            
            with pytest.raises(ConnectionError, match="Cannot connect to ML service"):
                await self.client.health_check()
    
    @pytest.mark.asyncio
    async def test_count_tokens_success(self):
        """Test successful token counting."""
        with patch.object(self.client, '_execute_count_request') as mock_execute:
            mock_execute.return_value = self.mock_response_data
            
            result = await self.client.count_tokens("test text", "starcoder")
            
            assert isinstance(result, TokenInfo)
            assert result.count == 10
            assert result.estimated_cost == 0.001
            assert result.model_name == "starcoder"
    
    @pytest.mark.asyncio
    async def test_count_tokens_validation_error(self):
        """Test token counting with validation error."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await self.client.count_tokens("", "starcoder")
    
    @pytest.mark.asyncio
    async def test_count_tokens_batch_success(self):
        """Test successful batch token counting."""
        batch_data = {
            "results": [
                {"count": 5, "estimated_cost": 0.0005, "model_name": "starcoder"},
                {"count": 8, "estimated_cost": 0.0008, "model_name": "starcoder"}
            ]
        }
        
        with patch.object(self.client, '_execute_batch_request') as mock_execute:
            mock_execute.return_value = batch_data
            
            result = await self.client.count_tokens_batch(["text1", "text2"], "starcoder")
            
            assert len(result) == 2
            assert result[0].count == 5
            assert result[1].count == 8
    
    @pytest.mark.asyncio
    async def test_compress_text_success(self):
        """Test successful text compression."""
        compression_data = {
            "original_text": "long text",
            "compressed_text": "short text",
            "original_tokens": 100,
            "compressed_tokens": 50,
            "compression_ratio": 0.5,
            "strategy_used": "truncation"
        }
        
        with patch.object(self.client, '_execute_compression_request') as mock_execute:
            mock_execute.return_value = compression_data
            
            result = await self.client.compress_text("long text", 100, "starcoder", "truncation")
            
            assert isinstance(result, CompressionResult)
            assert result.original_text == "long text"
            assert result.compressed_text == "short text"
            assert result.compression_ratio == 0.5
    
    @pytest.mark.asyncio
    async def test_compress_text_validation_error(self):
        """Test compression with validation error."""
        with pytest.raises(ValueError, match="Max tokens must be >= 1"):
            await self.client.compress_text("text", 0, "starcoder", "extractive")
    
    @pytest.mark.asyncio
    async def test_preview_compression_success(self):
        """Test successful compression preview."""
        preview_data = {
            "truncation": {"ratio": 0.6, "tokens": 60},
            "keywords": {"ratio": 0.4, "tokens": 40}
        }
        
        with patch.object(self.client, '_execute_with_resilience') as mock_execute:
            mock_execute.return_value = preview_data
            
            result = await self.client.preview_compression("text", 100, "starcoder")
            
            assert result == preview_data
    
    @pytest.mark.asyncio
    async def test_get_available_models_success(self):
        """Test successful model list retrieval."""
        models_data = {"models": ["starcoder", "mistral", "qwen"]}
        
        with patch.object(self.client, '_execute_with_resilience') as mock_execute:
            mock_execute.return_value = models_data
            
            result = await self.client.get_available_models()
            
            assert result == ["starcoder", "mistral", "qwen"]
    
    @pytest.mark.asyncio
    async def test_get_available_strategies_success(self):
        """Test successful strategies list retrieval."""
        strategies_data = {
            "descriptions": {
                "extractive": "Extractive summarization",
                "semantic": "Semantic compression"
            }
        }
        
        with patch.object(self.client, '_execute_with_resilience') as mock_execute:
            mock_execute.return_value = strategies_data
            
            result = await self.client.get_available_strategies()
            
            assert result == strategies_data["descriptions"]


class TestHybridTokenCounter:
    """Test HybridTokenCounter with fallback logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_ml_client = Mock()
        self.mock_fallback_counter = Mock()
        self.hybrid_counter = HybridTokenCounter(
            ml_client=self.mock_ml_client,
            fallback_counter=self.mock_fallback_counter
        )
    
    @pytest.mark.asyncio
    async def test_service_available_uses_ml_client(self):
        """Test that ML client is used when service is available."""
        self.mock_ml_client.health_check = AsyncMock()
        self.mock_ml_client.count_tokens = AsyncMock(return_value=TokenInfo(count=10))
        
        result = await self.hybrid_counter.count_tokens("test text")
        
        assert result.count == 10
        self.mock_ml_client.count_tokens.assert_called_once_with("test text", "starcoder")
    
    @pytest.mark.asyncio
    async def test_service_unavailable_uses_fallback(self):
        """Test that fallback is used when service is unavailable."""
        self.mock_ml_client.health_check = AsyncMock(side_effect=Exception("Service down"))
        self.mock_fallback_counter.count_tokens.return_value = TokenInfo(count=8)
        
        result = await self.hybrid_counter.count_tokens("test text")
        
        assert result.count == 8
        self.mock_fallback_counter.count_tokens.assert_called_once_with("test text", "starcoder")
    
    @pytest.mark.asyncio
    async def test_ml_client_error_falls_back(self):
        """Test fallback when ML client raises error."""
        self.mock_ml_client.health_check = AsyncMock()
        self.mock_ml_client.count_tokens = AsyncMock(side_effect=Exception("ML error"))
        self.mock_fallback_counter.count_tokens.return_value = TokenInfo(count=8)
        
        result = await self.hybrid_counter.count_tokens("test text")
        
        assert result.count == 8
        self.mock_fallback_counter.count_tokens.assert_called_once_with("test text", "starcoder")
    
    @pytest.mark.asyncio
    async def test_no_fallback_counter_raises_error(self):
        """Test error when no fallback counter is available."""
        hybrid_counter = HybridTokenCounter(ml_client=None, fallback_counter=None)
        
        with pytest.raises(RuntimeError, match="No fallback counter available"):
            await hybrid_counter.count_tokens("test text")
    
    @pytest.mark.asyncio
    async def test_compress_text_extractive_fallback(self):
        """Test compression with extractive strategy fallback."""
        self.mock_ml_client.health_check = AsyncMock(side_effect=Exception("Service down"))
        
        # Mock the SimpleTextCompressor
        with patch('core.text_compressor.SimpleTextCompressor') as mock_compressor_class:
            mock_compressor = Mock()
            mock_compressor.compress_by_keywords.return_value = CompressionResult(
                original_text="text", compressed_text="compressed", 
                original_tokens=10, compressed_tokens=5, compression_ratio=0.5, strategy_used="keywords"
            )
            mock_compressor_class.return_value = mock_compressor
            
            result = await self.hybrid_counter.compress_text("text", 10, "starcoder", "extractive")
            
            assert result.strategy_used == "keywords"
            mock_compressor.compress_by_keywords.assert_called_once_with("text", 10, "starcoder")
    
    @pytest.mark.asyncio
    async def test_compress_text_default_fallback(self):
        """Test compression with default strategy fallback."""
        self.mock_ml_client.health_check = AsyncMock(side_effect=Exception("Service down"))
        
        # Mock the SimpleTextCompressor
        with patch('core.text_compressor.SimpleTextCompressor') as mock_compressor_class:
            mock_compressor = Mock()
            mock_compressor.compress_by_truncation.return_value = CompressionResult(
                original_text="text", compressed_text="compressed", 
                original_tokens=10, compressed_tokens=5, compression_ratio=0.5, strategy_used="truncation"
            )
            mock_compressor_class.return_value = mock_compressor
            
            result = await self.hybrid_counter.compress_text("text", 10, "starcoder", "semantic")
            
            assert result.strategy_used == "truncation"
            mock_compressor.compress_by_truncation.assert_called_once_with("text", 10, "starcoder")


class TestMLClientIntegration:
    """Integration tests for ML client components."""
    
    def test_request_validator_integration(self):
        """Test RequestValidator integration with ML client."""
        # Test that validation works with real client
        client = TokenAnalysisClient()
        
        # These should not raise exceptions
        RequestValidator.validate_text("Valid text")
        RequestValidator.validate_model_name("starcoder")
        RequestValidator.validate_strategy("truncation")
        RequestValidator.validate_max_tokens(100)
    
    def test_resilient_client_integration(self):
        """Test ResilientClient integration."""
        retry_config = RetryConfig(max_attempts=3, base_delay=1.0)
        cb_config = CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60.0)
        resilient_client = ResilientClient(retry_config, cb_config)
        
        assert resilient_client is not None
        assert resilient_client.retry_handler is not None
        assert resilient_client.circuit_breaker is not None
