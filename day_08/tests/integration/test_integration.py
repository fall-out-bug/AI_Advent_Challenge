"""
Integration tests for complete scenarios.

Tests end-to-end workflows combining multiple components
to ensure they work together correctly.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from core.token_analyzer import SimpleTokenCounter, LimitProfile
from core.text_compressor import SimpleTextCompressor
from core.compressors import CompressionStrategy, CompressionStrategyFactory
from core.builders import ExperimentResultBuilder
from core.experiments import TokenLimitExperiments
from core.ml_client import TokenAnalysisClient, HybridTokenCounter
from core.validators import RequestValidator
from models.data_models import TokenInfo, CompressionResult, ExperimentResult
from tests.mocks.mock_config import MockConfiguration


class TestTokenAnalysisIntegration:
    """Integration tests for token analysis workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = MockConfiguration()
        self.token_counter = SimpleTokenCounter(config=self.mock_config)
        self.text_compressor = SimpleTextCompressor(self.token_counter)
    
    def test_complete_token_analysis_workflow(self):
        """Test complete token analysis workflow."""
        # Step 1: Count tokens
        text = "This is a test text for token analysis"
        token_info = self.token_counter.count_tokens(text, "starcoder")
        
        assert isinstance(token_info, TokenInfo)
        assert token_info.count > 0
        assert token_info.model_name == "starcoder"
        
        # Step 2: Check limits
        model_limits = self.token_counter.get_model_limits("starcoder")
        limit_exceeded = self.token_counter.check_limit_exceeded(text, "starcoder")
        
        assert isinstance(model_limits.max_input_tokens, int)
        assert isinstance(limit_exceeded, bool)
        
        # Step 3: Estimate compression target if needed
        if limit_exceeded:
            target = self.token_counter.estimate_compression_target(text, "starcoder")
            assert isinstance(target, int)
            assert target < token_info.count
    
    def test_compression_workflow_integration(self):
        """Test compression workflow integration."""
        # Create long text that exceeds limits
        long_text = "This is a very long text. " * 1000
        
        # Count tokens
        token_info = self.token_counter.count_tokens(long_text, "starcoder")
        
        # Check if compression is needed
        limit_exceeded = self.token_counter.check_limit_exceeded(long_text, "starcoder")
        
        if limit_exceeded:
            # Apply compression
            compression_result = self.text_compressor.compress_text(
                text=long_text,
                max_tokens=1000,
                model_name="starcoder",
                strategy="truncation"
            )
            
            assert isinstance(compression_result, CompressionResult)
            assert compression_result.compressed_tokens < compression_result.original_tokens
            assert compression_result.compression_ratio < 1.0
            assert compression_result.strategy_used == "truncation"
    
    def test_strategy_pattern_integration(self):
        """Test Strategy pattern integration."""
        # Test different compression strategies
        text = "This is a test text for strategy pattern testing"
        
        strategies = [CompressionStrategy.TRUNCATION, CompressionStrategy.KEYWORDS]
        
        for strategy in strategies:
            compressor = CompressionStrategyFactory.create(strategy, self.token_counter)
            result = compressor.compress(text, max_tokens=10, model_name="starcoder")
            
            assert isinstance(result, CompressionResult)
            assert result.strategy_used == strategy.value
            assert result.compressed_tokens <= 10


class TestMLClientIntegration:
    """Integration tests for ML client workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = MockConfiguration()
        self.token_counter = SimpleTokenCounter(config=self.mock_config)
        
        # Mock ML client
        self.mock_ml_client = Mock()
        self.mock_ml_client.make_request = AsyncMock()
        self.mock_ml_client.health_check = AsyncMock()
        
        self.hybrid_counter = HybridTokenCounter(
            ml_client=self.mock_ml_client,
            fallback_counter=self.token_counter
        )
    
    def test_request_validation_integration(self):
        """Test request validation integration."""
        # Valid requests
        RequestValidator.validate_text("Valid text")
        RequestValidator.validate_model_name("starcoder")
        RequestValidator.validate_strategy("truncation")
        RequestValidator.validate_max_tokens(100)
        
        # Invalid requests should raise exceptions
        with pytest.raises(ValueError):
            RequestValidator.validate_text("")
        
        with pytest.raises(ValueError):
            RequestValidator.validate_strategy("invalid")
    
    @pytest.mark.asyncio
    async def test_hybrid_token_counter_integration(self):
        """Test hybrid token counter integration."""
        # Test with ML client available
        self.mock_ml_client.health_check.return_value = {"status": "healthy"}
        self.mock_ml_client.count_tokens = AsyncMock(return_value=TokenInfo(count=50))
        
        result = await self.hybrid_counter.count_tokens("test text", "starcoder")
        
        assert isinstance(result, TokenInfo)
        assert result.count == 50
    
    @pytest.mark.asyncio
    async def test_hybrid_fallback_integration(self):
        """Test hybrid counter fallback integration."""
        # Test with ML client unavailable
        self.mock_ml_client.health_check.side_effect = Exception("Service down")
        
        result = await self.hybrid_counter.count_tokens("test text", "starcoder")
        
        assert isinstance(result, TokenInfo)
        assert result.count > 0  # Should use fallback counter


class TestExperimentIntegration:
    """Integration tests for experiment workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = MockConfiguration()
        self.token_counter = SimpleTokenCounter(config=self.mock_config)
        self.text_compressor = SimpleTextCompressor(self.token_counter)
        
        # Mock model client
        self.mock_model_client = Mock()
        mock_response = Mock()
        mock_response.response = "Model response"
        self.mock_model_client.make_request = AsyncMock(return_value=mock_response)
        
        self.experiments = TokenLimitExperiments(
            self.mock_model_client,
            self.token_counter,
            self.text_compressor
        )
    
    def test_experiment_result_builder_integration(self):
        """Test experiment result builder integration."""
        builder = ExperimentResultBuilder()
        
        result = (builder
                 .with_experiment_name("integration_test")
                 .with_model("starcoder")
                 .with_query("original query", "processed query")
                 .with_response("model response")
                 .with_tokens(100, 50, 150)
                 .with_timing(2.0)
                 .with_compression(True, None)
                 .with_timestamp()
                 .build())
        
        assert isinstance(result, ExperimentResult)
        assert result.experiment_name == "integration_test"
        assert result.model_name == "starcoder"
        assert result.response == "model response"
    
    @pytest.mark.asyncio
    async def test_single_experiment_integration(self):
        """Test single experiment integration."""
        result = await self.experiments._run_single_experiment(
            model_name="starcoder",
            query="Test query for integration",
            experiment_name="integration_test",
            compress=False
        )
        
        assert isinstance(result, ExperimentResult)
        assert result.experiment_name == "integration_test"
        assert result.model_name == "starcoder"
        assert result.response == "Model response"
        assert result.compression_applied is False
    
    @pytest.mark.asyncio
    async def test_compression_experiment_integration(self):
        """Test compression experiment integration."""
        # Create long text that needs compression
        long_text = "This is a very long text. " * 1000
        
        result = await self.experiments._run_single_experiment(
            model_name="starcoder",
            query=long_text,
            experiment_name="compression_test",
            compress=True,
            compression_strategy="truncation"
        )
        
        assert isinstance(result, ExperimentResult)
        assert result.compression_applied is True
        assert result.compression_result is not None
        assert result.compression_result.strategy_used == "truncation"


class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = MockConfiguration()
        self.token_counter = SimpleTokenCounter(config=self.mock_config)
        self.text_compressor = SimpleTextCompressor(self.token_counter)
        
        # Mock model client
        self.mock_model_client = Mock()
        mock_response = Mock()
        mock_response.response = "Complete end-to-end response"
        self.mock_model_client.make_request = AsyncMock(return_value=mock_response)
        
        self.experiments = TokenLimitExperiments(
            self.mock_model_client,
            self.token_counter,
            self.text_compressor
        )
    
    @pytest.mark.asyncio
    async def test_complete_workflow_with_compression(self):
        """Test complete workflow with compression."""
        # Step 1: Create long text
        long_text = "This is a comprehensive test text. " * 500
        
        # Step 2: Analyze tokens
        token_info = self.token_counter.count_tokens(long_text, "starcoder")
        assert token_info.count > 0
        
        # Step 3: Check if compression needed
        limit_exceeded = self.token_counter.check_limit_exceeded(long_text, "starcoder")
        
        if limit_exceeded:
            # Step 4: Apply compression
            compression_result = self.text_compressor.compress_text(
                text=long_text,
                max_tokens=1000,
                model_name="starcoder",
                strategy="truncation"
            )
            
            assert compression_result.compressed_tokens < compression_result.original_tokens
            
            # Step 5: Run experiment with compressed text
            experiment_result = await self.experiments._run_single_experiment(
                model_name="starcoder",
                query=compression_result.compressed_text,
                experiment_name="end_to_end_test",
                compress=False
            )
            
            assert isinstance(experiment_result, ExperimentResult)
            assert experiment_result.response == "Complete end-to-end response"
    
    def test_factory_pattern_integration(self):
        """Test factory pattern integration."""
        # Test token counter factory
        from core.factories import TokenCounterFactory
        
        simple_counter = TokenCounterFactory.create_simple(
            limit_profile=LimitProfile.PRACTICAL,
            config=self.mock_config
        )
        
        assert isinstance(simple_counter, SimpleTokenCounter)
        
        # Test compression strategy factory
        compressor = CompressionStrategyFactory.create(
            CompressionStrategy.TRUNCATION,
            self.token_counter
        )
        
        result = compressor.compress("test text", max_tokens=10, model_name="starcoder")
        assert isinstance(result, CompressionResult)
    
    def test_error_handling_integration(self):
        """Test error handling integration."""
        # Test invalid input handling
        with pytest.raises(ValueError):
            RequestValidator.validate_text("")
        
        with pytest.raises(ValueError):
            RequestValidator.validate_max_tokens(0)
        
        # Test factory error handling - need to pass invalid enum value
        from core.compressors import CompressionStrategy
        with pytest.raises(ValueError):
            # Create invalid strategy enum value
            invalid_strategy = CompressionStrategy("invalid_strategy")
            CompressionStrategyFactory.create(invalid_strategy, self.token_counter)
        
        # Test builder error handling
        builder = ExperimentResultBuilder()
        with pytest.raises(ValueError, match="Missing required fields"):
            builder.build()


class TestPerformanceIntegration:
    """Performance integration tests."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = MockConfiguration()
        self.token_counter = SimpleTokenCounter(config=self.mock_config)
        self.text_compressor = SimpleTextCompressor(self.token_counter)
    
    def test_large_text_processing_performance(self):
        """Test performance with large text."""
        import time
        
        # Create very large text
        large_text = "Performance test text. " * 10000
        
        start_time = time.time()
        
        # Token counting
        token_info = self.token_counter.count_tokens(large_text, "starcoder")
        
        # Compression
        compression_result = self.text_compressor.compress_text(
            text=large_text,
            max_tokens=1000,
            model_name="starcoder",
            strategy="truncation"
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert processing_time < 5.0  # 5 seconds max
        assert token_info.count > 0
        assert compression_result.compressed_tokens < compression_result.original_tokens
    
    def test_multiple_strategies_performance(self):
        """Test performance with multiple compression strategies."""
        text = "Performance test for multiple strategies. " * 1000
        
        strategies = [CompressionStrategy.TRUNCATION, CompressionStrategy.KEYWORDS]
        
        for strategy in strategies:
            compressor = CompressionStrategyFactory.create(strategy, self.token_counter)
            result = compressor.compress(text, max_tokens=100, model_name="starcoder")
            
            assert isinstance(result, CompressionResult)
            assert result.strategy_used == strategy.value
