"""
Baseline tests - фиксируют текущее поведение ПЕРЕД рефакторингом.

Эти тесты НЕ ДОЛЖНЫ меняться после рефакторинга.
Они служат для проверки что функциональность не сломалась.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from core.token_analyzer import SimpleTokenCounter, LimitProfile
from core.text_compressor import SimpleTextCompressor
from models.data_models import TokenInfo, CompressionResult


@pytest.mark.regression
class TestBaselineBehavior:
    """Tests current system behavior as baseline."""
    
    def test_token_counting_baseline(self):
        """Current token counting behavior."""
        counter = SimpleTokenCounter(limit_profile=LimitProfile.PRACTICAL)
        
        # Зафиксированные примеры с известными результатами
        assert counter.count_tokens("Hello world", "starcoder").count == 2
        assert counter.count_tokens("Привет мир", "starcoder").count == 2
        assert counter.count_tokens("", "starcoder").count == 0
        
        # Длинный текст для проверки коэффициента 1.3
        long_text = "This is a test text with multiple words to verify token counting accuracy"
        result = counter.count_tokens(long_text, "starcoder")
        assert result.count == 16  # 12 words * 1.3 = 15.6 -> 16 (actual behavior)
        
    def test_model_limits_baseline(self):
        """Current model limits configuration."""
        from tests.mocks.mock_config import MockConfiguration
        counter = SimpleTokenCounter(config=MockConfiguration(), limit_profile=LimitProfile.PRACTICAL)
        
        # StarCoder limits
        starcoder_limits = counter.get_model_limits("starcoder")
        assert starcoder_limits.max_input_tokens == 4096
        assert starcoder_limits.max_output_tokens == 1024
        assert starcoder_limits.max_total_tokens == 6000
        
        # Mistral limits
        mistral_limits = counter.get_model_limits("mistral")
        assert mistral_limits.max_input_tokens == 8192
        assert mistral_limits.max_output_tokens == 1024
        
        # TinyLlama limits
        tinyllama_limits = counter.get_model_limits("tinyllama")
        assert tinyllama_limits.max_input_tokens == 2048
        assert tinyllama_limits.max_output_tokens == 512
        
    def test_limit_exceeded_check_baseline(self):
        """Current limit exceeded checking behavior."""
        counter = SimpleTokenCounter(limit_profile=LimitProfile.PRACTICAL)
        
        # Short text should not exceed limits
        short_text = "Hello world"
        assert not counter.check_limit_exceeded(short_text, "starcoder")
        
        # Very long text should exceed limits
        very_long_text = "word " * 5000  # ~5000 words = ~6500 tokens
        assert counter.check_limit_exceeded(very_long_text, "starcoder")
        
    def test_compression_ratio_baseline(self):
        """Current compression ratios."""
        counter = SimpleTokenCounter(limit_profile=LimitProfile.PRACTICAL)
        compressor = SimpleTextCompressor(counter)
        
        # Create a long text that exceeds limits
        long_text = """
        This is a very long text that contains multiple sentences and paragraphs.
        It should be compressed to fit within the token limits.
        The compression should preserve the most important information.
        We need to test both truncation and keywords strategies.
        The text should be long enough to trigger compression.
        """ * 50  # Make it very long
        
        # Test truncation compression
        truncation_result = compressor.compress_by_truncation(long_text, 1000, "starcoder")
        assert truncation_result.compression_ratio < 1.0
        assert truncation_result.compressed_tokens <= 1000
        assert truncation_result.strategy_used == "truncation"
        
        # Test keywords compression
        keywords_result = compressor.compress_by_keywords(long_text, 1000, "starcoder")
        assert keywords_result.compression_ratio < 1.0
        assert keywords_result.compressed_tokens <= 1000
        assert keywords_result.strategy_used == "keywords"
        
        # Both strategies should compress effectively (actual behavior may vary)
        assert keywords_result.compression_ratio < 1.0
        assert truncation_result.compression_ratio < 1.0
        
    def test_compression_no_compression_needed(self):
        """Test compression when no compression is needed."""
        counter = SimpleTokenCounter(limit_profile=LimitProfile.PRACTICAL)
        compressor = SimpleTextCompressor(counter)
        
        short_text = "This is a short text that does not need compression."
        
        # Both strategies should return original text
        truncation_result = compressor.compress_by_truncation(short_text, 1000, "starcoder")
        assert truncation_result.compression_ratio == 1.0
        assert truncation_result.strategy_used == "no_compression"
        assert truncation_result.compressed_text == short_text
        
        keywords_result = compressor.compress_by_keywords(short_text, 1000, "starcoder")
        assert keywords_result.compression_ratio == 1.0
        assert keywords_result.strategy_used == "no_compression"
        assert keywords_result.compressed_text == short_text
        
    def test_available_models_baseline(self):
        """Current available models list."""
        counter = SimpleTokenCounter()
        models = counter.get_available_models()
        
        expected_models = ["starcoder", "mistral", "qwen", "tinyllama"]
        assert set(models) == set(expected_models)
        
    def test_limit_profile_switching(self):
        """Test switching between limit profiles."""
        from tests.mocks.mock_config import MockConfiguration
        
        # Theoretical profile
        theoretical_counter = SimpleTokenCounter(config=MockConfiguration(), limit_profile=LimitProfile.THEORETICAL)
        theoretical_limits = theoretical_counter.get_model_limits("starcoder")
        assert theoretical_limits.max_input_tokens == 16384
        
        # Practical profile
        practical_counter = SimpleTokenCounter(config=MockConfiguration(), limit_profile=LimitProfile.PRACTICAL)
        practical_limits = practical_counter.get_model_limits("starcoder")
        assert practical_limits.max_input_tokens == 4096
        
        # Profile switching
        theoretical_counter.set_limit_profile(LimitProfile.PRACTICAL)
        switched_limits = theoretical_counter.get_model_limits("starcoder")
        assert switched_limits.max_input_tokens == 4096
        
    def test_compression_target_estimation(self):
        """Test compression target estimation."""
        counter = SimpleTokenCounter(limit_profile=LimitProfile.PRACTICAL)
        
        # Test with different safety margins
        target_90 = counter.estimate_compression_target("test", "starcoder", 0.9)
        target_80 = counter.estimate_compression_target("test", "starcoder", 0.8)
        
        assert target_90 == 3686  # 4096 * 0.9
        assert target_80 == 3276  # 4096 * 0.8
        assert target_90 > target_80
        
    @pytest.mark.slow
    async def test_full_experiment_baseline(self):
        """Full experiment flow with known results."""
        # Mock the model client to avoid external dependencies
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.response = "This is a test response from the model."
        mock_response.response_time = 1.5
        mock_client.make_request.return_value = mock_response
        
        # Create components
        counter = SimpleTokenCounter(limit_profile=LimitProfile.PRACTICAL)
        compressor = SimpleTextCompressor(counter)
        
        # Test experiment setup
        from core.experiments import TokenLimitExperiments
        experiments = TokenLimitExperiments(mock_client, counter, compressor)
        
        # Test that we can create a long query
        long_query = experiments._create_long_query()
        assert len(long_query) > 10000  # Should be very long
        assert "трансформеров" in long_query  # Should contain Russian text
        
        # Test token counting on the long query
        token_count = counter.count_tokens(long_query, "starcoder").count
        assert token_count > 1000  # Should exceed limits
        
        # Test compression on the long query
        compression_result = compressor.compress_by_truncation(long_query, 1000, "starcoder")
        assert compression_result.compression_ratio < 1.0
        assert compression_result.compressed_tokens <= 1000
        
    def test_token_info_structure(self):
        """Test TokenInfo dataclass structure."""
        info = TokenInfo(count=100, estimated_cost=0.0, model_name="starcoder")
        
        assert info.count == 100
        assert info.estimated_cost == 0.0
        assert info.model_name == "starcoder"
        
    def test_compression_result_structure(self):
        """Test CompressionResult dataclass structure."""
        result = CompressionResult(
            original_text="original",
            compressed_text="compressed",
            original_tokens=100,
            compressed_tokens=50,
            compression_ratio=0.5,
            strategy_used="truncation"
        )
        
        assert result.original_text == "original"
        assert result.compressed_text == "compressed"
        assert result.original_tokens == 100
        assert result.compressed_tokens == 50
        assert result.compression_ratio == 0.5
        assert result.strategy_used == "truncation"


@pytest.mark.regression
class TestBaselineEdgeCases:
    """Test edge cases in current implementation."""
    
    def test_empty_and_none_inputs(self):
        """Test handling of empty and None inputs."""
        counter = SimpleTokenCounter()
        
        # Empty string
        result = counter.count_tokens("", "starcoder")
        assert result.count == 0
        
        # Whitespace only
        result = counter.count_tokens("   \n\t   ", "starcoder")
        assert result.count == 0
        
        # Single character
        result = counter.count_tokens("a", "starcoder")
        assert result.count == 1
        
    def test_unicode_and_special_characters(self):
        """Test handling of Unicode and special characters."""
        counter = SimpleTokenCounter()
        
        # Russian text
        result = counter.count_tokens("Привет мир!", "starcoder")
        assert result.count == 2
        
        # Mixed languages
        result = counter.count_tokens("Hello мир!", "starcoder")
        assert result.count == 2
        
        # Special characters
        result = counter.count_tokens("Hello, world! How are you?", "starcoder")
        assert result.count == 6
        
    def test_very_long_text(self):
        """Test handling of very long text."""
        counter = SimpleTokenCounter()
        
        # Create a very long text
        long_text = "word " * 100000  # 100k words
        
        # Should not crash
        result = counter.count_tokens(long_text, "starcoder")
        assert result.count > 100000
        
        # Should exceed limits
        assert counter.check_limit_exceeded(long_text, "starcoder")
        
    def test_compression_edge_cases(self):
        """Test compression with edge cases."""
        counter = SimpleTokenCounter()
        compressor = SimpleTextCompressor(counter)
        
        # Single sentence
        single_sentence = "This is a single sentence."
        result = compressor.compress_by_truncation(single_sentence, 10, "starcoder")
        assert result.compression_ratio <= 1.0
        
        # Text with no keywords (all short words)
        short_words = "a b c d e f g h i j k l m n o p q r s t u v w x y z"
        result = compressor.compress_by_keywords(short_words, 10, "starcoder")
        assert result.compression_ratio <= 1.0
        
        # Text with only punctuation
        punctuation = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        result = compressor.compress_by_keywords(punctuation, 10, "starcoder")
        assert result.compression_ratio <= 1.0
