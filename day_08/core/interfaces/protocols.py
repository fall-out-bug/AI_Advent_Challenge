"""
Protocol definitions for Token Analysis System.

This module defines interfaces for all major components
to enable dependency injection and SOLID principles.
"""

from typing import Protocol, List, Optional, Dict, Any, runtime_checkable
from abc import abstractmethod

from models.data_models import TokenInfo, ModelLimits, CompressionResult, ExperimentResult


@runtime_checkable
class TokenCounterProtocol(Protocol):
    """Protocol for token counting functionality."""
    
    def count_tokens(self, text: str, model_name: str) -> TokenInfo:
        """Count tokens in text for specified model."""
        ...
    
    def check_limit_exceeded(self, text: str, model_name: str) -> bool:
        """Check if text exceeds model limits."""
        ...
    
    def get_model_limits(self, model_name: str) -> ModelLimits:
        """Get limits for specified model."""
        ...
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names."""
        ...
    
    def estimate_compression_target(self, text: str, model_name: str, safety_margin: float) -> int:
        """Estimate target token count for compression."""
        ...


@runtime_checkable
class CompressorProtocol(Protocol):
    """Protocol for text compression functionality."""
    
    def compress_by_truncation(self, text: str, max_tokens: int, model_name: str) -> CompressionResult:
        """Compress text by truncation strategy."""
        ...
    
    def compress_by_keywords(self, text: str, max_tokens: int, model_name: str) -> CompressionResult:
        """Compress text by keywords strategy."""
        ...
    
    def compress_by_extractive(self, text: str, max_tokens: int, model_name: str) -> CompressionResult:
        """Compress text by extractive summarization."""
        ...
    
    def compress_by_semantic(self, text: str, max_tokens: int, model_name: str) -> CompressionResult:
        """Compress text by semantic chunking."""
        ...
    
    def compress_by_summarization(self, text: str, max_tokens: int, model_name: str) -> CompressionResult:
        """Compress text by LLM summarization."""
        ...


@runtime_checkable
class ModelClientProtocol(Protocol):
    """Protocol for model client functionality."""
    
    async def make_request(self, model_name: str, query: str, max_tokens: int = 1000) -> Any:
        """Make request to model."""
        ...
    
    async def health_check(self) -> bool:
        """Check if model service is healthy."""
        ...
    
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        ...


@runtime_checkable
class ReporterProtocol(Protocol):
    """Protocol for reporting functionality."""
    
    def print_summary(self, results: List[ExperimentResult]) -> None:
        """Print experiment summary."""
        ...
    
    def print_detailed_analysis(self, results: List[ExperimentResult]) -> None:
        """Print detailed analysis."""
        ...
    
    def print_recommendations(self, results: List[ExperimentResult]) -> None:
        """Print recommendations."""
        ...
    
    def generate_report(self, results: List[ExperimentResult]) -> str:
        """Generate text report."""
        ...


@runtime_checkable
class StatisticsCalculatorProtocol(Protocol):
    """Protocol for statistics calculation."""
    
    def calculate_average(self, values: List[float]) -> float:
        """Calculate average value."""
        ...
    
    def calculate_median(self, values: List[float]) -> float:
        """Calculate median value."""
        ...
    
    def calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        ...
    
    def calculate_compression_stats(self, results: List[CompressionResult]) -> Dict[str, float]:
        """Calculate compression statistics."""
        ...


@runtime_checkable
class ExperimentRunnerProtocol(Protocol):
    """Protocol for experiment execution."""
    
    async def run_limit_exceeded_experiment(self, model_name: str, query: str) -> List[ExperimentResult]:
        """Run limit exceeded experiment."""
        ...
    
    async def run_model_comparison_experiment(self, query: str, models: List[str]) -> List[ExperimentResult]:
        """Run model comparison experiment."""
        ...
    
    async def run_compression_experiment(self, model_name: str, query: str, strategies: List[str]) -> List[ExperimentResult]:
        """Run compression experiment."""
        ...
    
    async def run_single_experiment(self, model_name: str, query: str, experiment_name: str, 
                                 compress: bool = False, compression_strategy: str = "truncation") -> ExperimentResult:
        """Run single experiment."""
        ...


@runtime_checkable
class ConfigurationProtocol(Protocol):
    """Protocol for configuration management."""
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get configuration setting."""
        ...
    
    def get_model_limits(self, model_name: str, profile: str) -> Optional[ModelLimits]:
        """Get model limits."""
        ...
    
    def get_available_models(self) -> List[str]:
        """Get available models."""
        ...
    
    def reload(self) -> None:
        """Reload configuration."""
        ...


@runtime_checkable
class LoggerProtocol(Protocol):
    """Protocol for logging functionality."""
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        ...
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        ...
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        ...
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        ...
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        ...


@runtime_checkable
class RetryProtocol(Protocol):
    """Protocol for retry functionality."""
    
    async def execute_with_retry(self, func, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        ...
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Check if should retry on exception."""
        ...
    
    def get_delay(self, attempt: int) -> float:
        """Get delay for retry attempt."""
        ...


@runtime_checkable
class CircuitBreakerProtocol(Protocol):
    """Protocol for circuit breaker functionality."""
    
    async def call(self, func, *args, **kwargs) -> Any:
        """Call function through circuit breaker."""
        ...
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        ...
    
    def is_half_open(self) -> bool:
        """Check if circuit breaker is half-open."""
        ...
    
    def is_closed(self) -> bool:
        """Check if circuit breaker is closed."""
        ...


@runtime_checkable
class CacheProtocol(Protocol):
    """Protocol for caching functionality."""
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        ...
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        ...
    
    def delete(self, key: str) -> None:
        """Delete value from cache."""
        ...
    
    def clear(self) -> None:
        """Clear all cache."""
        ...
    
    def size(self) -> int:
        """Get cache size."""
        ...


@runtime_checkable
class ValidatorProtocol(Protocol):
    """Protocol for validation functionality."""
    
    def validate_text(self, text: str) -> bool:
        """Validate text input."""
        ...
    
    def validate_model_name(self, model_name: str) -> bool:
        """Validate model name."""
        ...
    
    def validate_token_count(self, count: int) -> bool:
        """Validate token count."""
        ...
    
    def validate_compression_result(self, result: CompressionResult) -> bool:
        """Validate compression result."""
        ...


@runtime_checkable
class FactoryProtocol(Protocol):
    """Protocol for factory functionality."""
    
    def create_token_counter(self, config: Dict[str, Any]) -> TokenCounterProtocol:
        """Create token counter instance."""
        ...
    
    def create_compressor(self, config: Dict[str, Any]) -> CompressorProtocol:
        """Create compressor instance."""
        ...
    
    def create_model_client(self, config: Dict[str, Any]) -> ModelClientProtocol:
        """Create model client instance."""
        ...
    
    def create_reporter(self, config: Dict[str, Any]) -> ReporterProtocol:
        """Create reporter instance."""
        ...


@runtime_checkable
class MetricsProtocol(Protocol):
    """Protocol for metrics collection."""
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment counter metric."""
        ...
    
    def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record gauge metric."""
        ...
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record histogram metric."""
        ...
    
    def record_timing(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record timing metric."""
        ...
