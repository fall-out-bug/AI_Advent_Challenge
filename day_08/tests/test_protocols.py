"""
Tests for protocol definitions.
"""

import pytest
from typing import List, Optional, Dict, Any

from core.interfaces.protocols import (
    TokenCounterProtocol,
    CompressorProtocol,
    ModelClientProtocol,
    ReporterProtocol,
    StatisticsCalculatorProtocol,
    ExperimentRunnerProtocol,
    ConfigurationProtocol,
    LoggerProtocol,
    RetryProtocol,
    CircuitBreakerProtocol,
    CacheProtocol,
    ValidatorProtocol,
    FactoryProtocol,
    MetricsProtocol,
)
from models.data_models import TokenInfo, ModelLimits, CompressionResult, ExperimentResult


class TestProtocols:
    """Test protocol definitions."""
    
    def test_token_counter_protocol(self):
        """Test TokenCounterProtocol interface."""
        
        class MockTokenCounter:
            def count_tokens(self, text: str, model_name: str) -> TokenInfo:
                return TokenInfo(count=10, estimated_cost=0.0, model_name=model_name)
            
            def check_limit_exceeded(self, text: str, model_name: str) -> bool:
                return len(text) > 100
            
            def get_model_limits(self, model_name: str) -> ModelLimits:
                return ModelLimits(max_input_tokens=4096, max_output_tokens=1024, max_total_tokens=6000)
            
            def get_available_models(self) -> List[str]:
                return ["starcoder", "mistral"]
            
            def estimate_compression_target(self, text: str, model_name: str, safety_margin: float) -> int:
                return int(len(text) * safety_margin)
        
        counter = MockTokenCounter()
        assert isinstance(counter, TokenCounterProtocol)
        
        # Test methods
        result = counter.count_tokens("test", "starcoder")
        assert result.count == 10
        
        assert counter.check_limit_exceeded("short", "starcoder") is False
        assert counter.check_limit_exceeded("x" * 200, "starcoder") is True
        
        limits = counter.get_model_limits("starcoder")
        assert limits.max_input_tokens == 4096
        
        models = counter.get_available_models()
        assert "starcoder" in models
    
    def test_compressor_protocol(self):
        """Test CompressorProtocol interface."""
        
        class MockCompressor:
            def compress_by_truncation(self, text: str, max_tokens: int, model_name: str) -> CompressionResult:
                return CompressionResult(
                    original_text=text,
                    compressed_text=text[:max_tokens],
                    original_tokens=len(text),
                    compressed_tokens=max_tokens,
                    compression_ratio=0.5,
                    strategy_used="truncation"
                )
            
            def compress_by_keywords(self, text: str, max_tokens: int, model_name: str) -> CompressionResult:
                return CompressionResult(
                    original_text=text,
                    compressed_text="keywords",
                    original_tokens=len(text),
                    compressed_tokens=max_tokens,
                    compression_ratio=0.3,
                    strategy_used="keywords"
                )
            
            def compress_by_extractive(self, text: str, max_tokens: int, model_name: str) -> CompressionResult:
                return CompressionResult(
                    original_text=text,
                    compressed_text="extractive",
                    original_tokens=len(text),
                    compressed_tokens=max_tokens,
                    compression_ratio=0.4,
                    strategy_used="extractive"
                )
            
            def compress_by_semantic(self, text: str, max_tokens: int, model_name: str) -> CompressionResult:
                return CompressionResult(
                    original_text=text,
                    compressed_text="semantic",
                    original_tokens=len(text),
                    compressed_tokens=max_tokens,
                    compression_ratio=0.6,
                    strategy_used="semantic"
                )
            
            def compress_by_summarization(self, text: str, max_tokens: int, model_name: str) -> CompressionResult:
                return CompressionResult(
                    original_text=text,
                    compressed_text="summary",
                    original_tokens=len(text),
                    compressed_tokens=max_tokens,
                    compression_ratio=0.2,
                    strategy_used="summarization"
                )
        
        compressor = MockCompressor()
        assert isinstance(compressor, CompressorProtocol)
        
        # Test methods
        result = compressor.compress_by_truncation("test text", 5, "starcoder")
        assert result.strategy_used == "truncation"
        assert result.compression_ratio == 0.5
        
        result = compressor.compress_by_keywords("test text", 5, "starcoder")
        assert result.strategy_used == "keywords"
        assert result.compression_ratio == 0.3
    
    def test_model_client_protocol(self):
        """Test ModelClientProtocol interface."""
        
        class MockModelClient:
            async def make_request(self, model_name: str, query: str, max_tokens: int = 1000) -> Any:
                return {"response": "test response", "tokens": 10}
            
            async def health_check(self) -> bool:
                return True
            
            def get_available_models(self) -> List[str]:
                return ["starcoder", "mistral"]
        
        client = MockModelClient()
        assert isinstance(client, ModelClientProtocol)
        
        # Test methods
        models = client.get_available_models()
        assert "starcoder" in models
    
    def test_reporter_protocol(self):
        """Test ReporterProtocol interface."""
        
        class MockReporter:
            def print_summary(self, results: List[ExperimentResult]) -> None:
                pass
            
            def print_detailed_analysis(self, results: List[ExperimentResult]) -> None:
                pass
            
            def print_recommendations(self, results: List[ExperimentResult]) -> None:
                pass
            
            def generate_report(self, results: List[ExperimentResult]) -> str:
                return "test report"
        
        reporter = MockReporter()
        assert isinstance(reporter, ReporterProtocol)
        
        # Test methods
        report = reporter.generate_report([])
        assert report == "test report"
    
    def test_statistics_calculator_protocol(self):
        """Test StatisticsCalculatorProtocol interface."""
        
        class MockStatisticsCalculator:
            def calculate_average(self, values: List[float]) -> float:
                return sum(values) / len(values) if values else 0.0
            
            def calculate_median(self, values: List[float]) -> float:
                sorted_values = sorted(values)
                n = len(sorted_values)
                if n % 2 == 0:
                    return (sorted_values[n//2-1] + sorted_values[n//2]) / 2
                return sorted_values[n//2]
            
            def calculate_percentile(self, values: List[float], percentile: float) -> float:
                sorted_values = sorted(values)
                index = int(len(sorted_values) * percentile / 100)
                return sorted_values[min(index, len(sorted_values) - 1)]
            
            def calculate_compression_stats(self, results: List[CompressionResult]) -> Dict[str, float]:
                return {"avg_ratio": 0.5, "min_ratio": 0.2, "max_ratio": 0.8}
        
        calculator = MockStatisticsCalculator()
        assert isinstance(calculator, StatisticsCalculatorProtocol)
        
        # Test methods
        avg = calculator.calculate_average([1.0, 2.0, 3.0])
        assert avg == 2.0
        
        median = calculator.calculate_median([1.0, 2.0, 3.0, 4.0])
        assert median == 2.5
        
        percentile = calculator.calculate_percentile([1.0, 2.0, 3.0, 4.0, 5.0], 50.0)
        assert percentile == 3.0
        
        stats = calculator.calculate_compression_stats([])
        assert "avg_ratio" in stats
    
    def test_configuration_protocol(self):
        """Test ConfigurationProtocol interface."""
        
        class MockConfiguration:
            def get_setting(self, key: str, default: Any = None) -> Any:
                settings = {"debug": True, "timeout": 30}
                return settings.get(key, default)
            
            def get_model_limits(self, model_name: str, profile: str) -> Optional[ModelLimits]:
                return ModelLimits(max_input_tokens=4096, max_output_tokens=1024, max_total_tokens=6000)
            
            def get_available_models(self) -> List[str]:
                return ["starcoder", "mistral"]
            
            def reload(self) -> None:
                pass
        
        config = MockConfiguration()
        assert isinstance(config, ConfigurationProtocol)
        
        # Test methods
        debug = config.get_setting("debug")
        assert debug is True
        
        timeout = config.get_setting("timeout")
        assert timeout == 30
        
        limits = config.get_model_limits("starcoder", "practical")
        assert limits is not None
        assert limits.max_input_tokens == 4096
        
        models = config.get_available_models()
        assert "starcoder" in models
    
    def test_logger_protocol(self):
        """Test LoggerProtocol interface."""
        
        class MockLogger:
            def debug(self, message: str, **kwargs: Any) -> None:
                pass
            
            def info(self, message: str, **kwargs: Any) -> None:
                pass
            
            def warning(self, message: str, **kwargs: Any) -> None:
                pass
            
            def error(self, message: str, **kwargs: Any) -> None:
                pass
            
            def critical(self, message: str, **kwargs: Any) -> None:
                pass
        
        logger = MockLogger()
        assert isinstance(logger, LoggerProtocol)
        
        # Test methods
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")
        logger.critical("critical message")
    
    def test_retry_protocol(self):
        """Test RetryProtocol interface."""
        
        class MockRetry:
            async def execute_with_retry(self, func, *args, **kwargs) -> Any:
                return await func(*args, **kwargs)
            
            def should_retry(self, exception: Exception, attempt: int) -> bool:
                return attempt < 3
            
            def get_delay(self, attempt: int) -> float:
                return 1.0 * (2 ** attempt)
        
        retry = MockRetry()
        assert isinstance(retry, RetryProtocol)
        
        # Test methods
        should_retry = retry.should_retry(Exception(), 1)
        assert should_retry is True
        
        delay = retry.get_delay(2)
        assert delay == 4.0
    
    def test_circuit_breaker_protocol(self):
        """Test CircuitBreakerProtocol interface."""
        
        class MockCircuitBreaker:
            async def call(self, func, *args, **kwargs) -> Any:
                return await func(*args, **kwargs)
            
            def is_open(self) -> bool:
                return False
            
            def is_half_open(self) -> bool:
                return False
            
            def is_closed(self) -> bool:
                return True
        
        breaker = MockCircuitBreaker()
        assert isinstance(breaker, CircuitBreakerProtocol)
        
        # Test methods
        assert breaker.is_closed() is True
        assert breaker.is_open() is False
        assert breaker.is_half_open() is False
    
    def test_cache_protocol(self):
        """Test CacheProtocol interface."""
        
        class MockCache:
            def __init__(self):
                self._cache = {}
            
            def get(self, key: str) -> Optional[Any]:
                return self._cache.get(key)
            
            def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
                self._cache[key] = value
            
            def delete(self, key: str) -> None:
                self._cache.pop(key, None)
            
            def clear(self) -> None:
                self._cache.clear()
            
            def size(self) -> int:
                return len(self._cache)
        
        cache = MockCache()
        assert isinstance(cache, CacheProtocol)
        
        # Test methods
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.size() == 1
        
        cache.delete("key1")
        assert cache.get("key1") is None
        assert cache.size() == 0
        
        cache.clear()
        assert cache.size() == 0
    
    def test_validator_protocol(self):
        """Test ValidatorProtocol interface."""
        
        class MockValidator:
            def validate_text(self, text: str) -> bool:
                return len(text) > 0
            
            def validate_model_name(self, model_name: str) -> bool:
                return model_name in ["starcoder", "mistral"]
            
            def validate_token_count(self, count: int) -> bool:
                return count >= 0
            
            def validate_compression_result(self, result: CompressionResult) -> bool:
                return result.compression_ratio >= 0.0
        
        validator = MockValidator()
        assert isinstance(validator, ValidatorProtocol)
        
        # Test methods
        assert validator.validate_text("test") is True
        assert validator.validate_text("") is False
        
        assert validator.validate_model_name("starcoder") is True
        assert validator.validate_model_name("unknown") is False
        
        assert validator.validate_token_count(100) is True
        assert validator.validate_token_count(-1) is False
    
    def test_factory_protocol(self):
        """Test FactoryProtocol interface."""
        
        class MockFactory:
            def create_token_counter(self, config: Dict[str, Any]) -> TokenCounterProtocol:
                return MockTokenCounter()
            
            def create_compressor(self, config: Dict[str, Any]) -> CompressorProtocol:
                return MockCompressor()
            
            def create_model_client(self, config: Dict[str, Any]) -> ModelClientProtocol:
                return MockModelClient()
            
            def create_reporter(self, config: Dict[str, Any]) -> ReporterProtocol:
                return MockReporter()
        
        factory = MockFactory()
        assert isinstance(factory, FactoryProtocol)
        
        # Test methods
        counter = factory.create_token_counter({})
        assert isinstance(counter, TokenCounterProtocol)
        
        compressor = factory.create_compressor({})
        assert isinstance(compressor, CompressorProtocol)
    
    def test_metrics_protocol(self):
        """Test MetricsProtocol interface."""
        
        class MockMetrics:
            def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
                pass
            
            def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
                pass
            
            def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
                pass
            
            def record_timing(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None) -> None:
                pass
        
        metrics = MockMetrics()
        assert isinstance(metrics, MetricsProtocol)
        
        # Test methods
        metrics.increment_counter("requests")
        metrics.record_gauge("memory_usage", 0.5)
        metrics.record_histogram("response_time", 1.2)
        metrics.record_timing("operation", 0.5)


# Mock classes for testing
class MockTokenCounter:
    def count_tokens(self, text: str, model_name: str) -> TokenInfo:
        return TokenInfo(count=10, estimated_cost=0.0, model_name=model_name)
    
    def check_limit_exceeded(self, text: str, model_name: str) -> bool:
        return len(text) > 100
    
    def get_model_limits(self, model_name: str) -> ModelLimits:
        return ModelLimits(max_input_tokens=4096, max_output_tokens=1024, max_total_tokens=6000)
    
    def get_available_models(self) -> List[str]:
        return ["starcoder", "mistral"]
    
    def estimate_compression_target(self, text: str, model_name: str, safety_margin: float) -> int:
        return int(len(text) * safety_margin)


class MockCompressor:
    def compress_by_truncation(self, text: str, max_tokens: int, model_name: str) -> CompressionResult:
        return CompressionResult(
            original_text=text,
            compressed_text=text[:max_tokens],
            original_tokens=len(text),
            compressed_tokens=max_tokens,
            compression_ratio=0.5,
            strategy_used="truncation"
        )
    
    def compress_by_keywords(self, text: str, max_tokens: int, model_name: str) -> CompressionResult:
        return CompressionResult(
            original_text=text,
            compressed_text="keywords",
            original_tokens=len(text),
            compressed_tokens=max_tokens,
            compression_ratio=0.3,
            strategy_used="keywords"
        )
    
    def compress_by_extractive(self, text: str, max_tokens: int, model_name: str) -> CompressionResult:
        return CompressionResult(
            original_text=text,
            compressed_text="extractive",
            original_tokens=len(text),
            compressed_tokens=max_tokens,
            compression_ratio=0.4,
            strategy_used="extractive"
        )
    
    def compress_by_semantic(self, text: str, max_tokens: int, model_name: str) -> CompressionResult:
        return CompressionResult(
            original_text=text,
            compressed_text="semantic",
            original_tokens=len(text),
            compressed_tokens=max_tokens,
            compression_ratio=0.6,
            strategy_used="semantic"
        )
    
    def compress_by_summarization(self, text: str, max_tokens: int, model_name: str) -> CompressionResult:
        return CompressionResult(
            original_text=text,
            compressed_text="summary",
            original_tokens=len(text),
            compressed_tokens=max_tokens,
            compression_ratio=0.2,
            strategy_used="summarization"
        )


class MockModelClient:
    async def make_request(self, model_name: str, query: str, max_tokens: int = 1000) -> Any:
        return {"response": "test response", "tokens": 10}
    
    async def health_check(self) -> bool:
        return True
    
    def get_available_models(self) -> List[str]:
        return ["starcoder", "mistral"]


class MockReporter:
    def print_summary(self, results: List[ExperimentResult]) -> None:
        pass
    
    def print_detailed_analysis(self, results: List[ExperimentResult]) -> None:
        pass
    
    def print_recommendations(self, results: List[ExperimentResult]) -> None:
        pass
    
    def generate_report(self, results: List[ExperimentResult]) -> str:
        return "test report"
