# API Reference

## Overview

This document provides comprehensive API reference for the Enhanced Token Analysis System. All APIs are designed with type safety, clear error handling, and comprehensive documentation.

## Core APIs

### Token Analysis API

#### SimpleTokenCounter

```python
class SimpleTokenCounter:
    """Simple token counter with configurable limits."""
    
    def __init__(self, config: Optional[ConfigurationProtocol] = None, limit_profile: LimitProfile = LimitProfile.PRACTICAL):
        """
        Initialize token counter.
        
        Args:
            config: Configuration protocol implementation
            limit_profile: Limit profile (THEORETICAL or PRACTICAL)
        """
    
    def count_tokens(self, text: str, model_name: str) -> TokenInfo:
        """
        Count tokens in text using heuristic estimation.
        
        Args:
            text: Text to analyze
            model_name: Name of the model (e.g., "starcoder", "mistral")
            
        Returns:
            TokenInfo: Token count and metadata
            
        Raises:
            ValueError: If text is empty or model_name is invalid
        """
    
    def check_limit_exceeded(self, text: str, model_name: str) -> bool:
        """
        Check if text exceeds model token limits.
        
        Args:
            text: Text to check
            model_name: Name of the model
            
        Returns:
            bool: True if limits exceeded, False otherwise
        """
    
    def estimate_compression_target(self, text: str, model_name: str) -> int:
        """
        Estimate target token count for compression.
        
        Args:
            text: Text to compress
            model_name: Name of the model
            
        Returns:
            int: Estimated target token count
        """
    
    def get_model_limits(self, model_name: str) -> ModelLimits:
        """
        Get token limits for specified model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            ModelLimits: Model token limits
        """
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available models.
        
        Returns:
            List[str]: Available model names
        """
```

#### AccurateTokenCounter

```python
class AccurateTokenCounter:
    """ML-based token counter for accurate counting."""
    
    def __init__(self, config: Optional[ConfigurationProtocol] = None):
        """
        Initialize accurate token counter.
        
        Args:
            config: Configuration protocol implementation
        """
    
    def count_tokens(self, text: str, model_name: str) -> TokenInfo:
        """
        Count tokens using ML-based estimation.
        
        Args:
            text: Text to analyze
            model_name: Name of the model
            
        Returns:
            TokenInfo: Accurate token count and metadata
        """
```

#### HybridTokenCounter

```python
class HybridTokenCounter:
    """Hybrid token counter combining multiple strategies."""
    
    def __init__(self, ml_client: TokenAnalysisClient, fallback_counter: TokenCounterProtocol):
        """
        Initialize hybrid token counter.
        
        Args:
            ml_client: ML service client
            fallback_counter: Fallback token counter
        """
    
    async def count_tokens(self, text: str, model_name: str) -> TokenInfo:
        """
        Count tokens using hybrid approach.
        
        Args:
            text: Text to analyze
            model_name: Name of the model
            
        Returns:
            TokenInfo: Token count using best available method
        """
```

### Text Compression API

#### SimpleTextCompressor

```python
class SimpleTextCompressor:
    """Facade for text compression with strategy pattern."""
    
    def __init__(self, token_counter: TokenCounterProtocol):
        """
        Initialize text compressor.
        
        Args:
            token_counter: Token counter instance
        """
    
    def compress_text(
        self, 
        text: str, 
        max_tokens: int, 
        model_name: str = "starcoder",
        strategy: str = "truncation"
    ) -> CompressionResult:
        """
        Compress text using specified strategy.
        
        Args:
            text: Text to compress
            max_tokens: Maximum allowed tokens
            model_name: Name of the model
            strategy: Compression strategy ("truncation", "keywords", etc.)
            
        Returns:
            CompressionResult: Compression result with metadata
            
        Raises:
            ValueError: If strategy is not supported
        """
    
    def compress_by_truncation(
        self, 
        text: str, 
        max_tokens: int, 
        model_name: str = "starcoder"
    ) -> CompressionResult:
        """
        Compress text using truncation strategy.
        
        Args:
            text: Text to compress
            max_tokens: Maximum allowed tokens
            model_name: Name of the model
            
        Returns:
            CompressionResult: Truncation compression result
        """
    
    def compress_by_keywords(
        self, 
        text: str, 
        max_tokens: int, 
        model_name: str = "starcoder"
    ) -> CompressionResult:
        """
        Compress text using keywords extraction.
        
        Args:
            text: Text to compress
            max_tokens: Maximum allowed tokens
            model_name: Name of the model
            
        Returns:
            CompressionResult: Keywords compression result
        """
    
    def get_compression_preview(
        self, 
        text: str, 
        max_tokens: int, 
        model_name: str = "starcoder"
    ) -> Dict[str, CompressionResult]:
        """
        Get compression preview for all strategies.
        
        Args:
            text: Text to compress
            max_tokens: Maximum allowed tokens
            model_name: Name of the model
            
        Returns:
            Dict[str, CompressionResult]: Results for each strategy
        """
```

#### Compression Strategies

```python
class CompressionStrategy(Enum):
    """Available compression strategies."""
    TRUNCATION = "truncation"
    KEYWORDS = "keywords"
    EXTRACTIVE = "extractive"
    SEMANTIC = "semantic"
    SUMMARIZATION = "summarization"

class CompressionStrategyFactory:
    """Factory for creating compression strategies."""
    
    @classmethod
    def create(
        cls,
        strategy: CompressionStrategy,
        token_counter: TokenCounterProtocol
    ) -> CompressorProtocol:
        """
        Create compressor instance for specified strategy.
        
        Args:
            strategy: Compression strategy to use
            token_counter: Token counter instance
            
        Returns:
            CompressorProtocol: Configured compressor instance
            
        Raises:
            ValueError: If strategy is not supported
        """
```

### ML Client API

#### TokenAnalysisClient

```python
class TokenAnalysisClient:
    """Resilient ML client with retry and circuit breaker."""
    
    def __init__(self, base_url: str = "http://localhost:8004"):
        """
        Initialize ML client.
        
        Args:
            base_url: Base URL of the ML service
        """
    
    async def count_tokens(self, text: str, model_name: str) -> TokenInfo:
        """
        Count tokens using ML service.
        
        Args:
            text: Text to analyze
            model_name: Name of the model
            
        Returns:
            TokenInfo: Token count from ML service
            
        Raises:
            MLClientError: If service is unavailable
            ValidationError: If input is invalid
        """
    
    async def make_request(
        self, 
        model_name: str, 
        prompt: str, 
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> ModelResponse:
        """
        Make request to ML model.
        
        Args:
            model_name: Name of the model
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            ModelResponse: Model response with metadata
            
        Raises:
            MLClientError: If request fails
        """
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check ML service health.
        
        Returns:
            Dict[str, Any]: Health status information
        """
    
    async def check_availability(self, model_name: str) -> bool:
        """
        Check if model is available.
        
        Args:
            model_name: Name of the model
            
        Returns:
            bool: True if model is available
        """
```

### Experiment API

#### TokenLimitExperiments

```python
class TokenLimitExperiments:
    """Experiment management with builder pattern."""
    
    def __init__(self, model_client: TokenAnalysisClient, token_counter: TokenCounterProtocol, text_compressor: SimpleTextCompressor):
        """
        Initialize experiments.
        
        Args:
            model_client: ML client instance
            token_counter: Token counter instance
            text_compressor: Text compressor instance
        """
    
    async def run_limit_exceeded_experiment(
        self, 
        model_name: str = "starcoder"
    ) -> List[ExperimentResult]:
        """
        Run experiments with limit-exceeding queries.
        
        Args:
            model_name: Name of the model to test
            
        Returns:
            List[ExperimentResult]: Results of all experiments
        """
    
    async def run_model_comparison_experiment(
        self, 
        models: List[str], 
        query: str, 
        auto_swap: bool = True
    ) -> List[ExperimentResult]:
        """
        Compare multiple models.
        
        Args:
            models: List of model names to compare
            query: Query to test with all models
            auto_swap: Whether to automatically manage containers
            
        Returns:
            List[ExperimentResult]: Results from all models
        """
    
    async def run_advanced_compression_experiment(
        self, 
        model_name: str = "starcoder", 
        strategies: Optional[List[str]] = None
    ) -> List[ExperimentResult]:
        """
        Run experiments with advanced compression strategies.
        
        Args:
            model_name: Model to test with
            strategies: List of compression strategies to test
            
        Returns:
            List[ExperimentResult]: Results from all strategies
        """
    
    async def run_short_query_experiment(
        self, 
        model_name: str = "starcoder"
    ) -> List[ExperimentResult]:
        """
        Run experiments with short queries for comparison.
        
        Args:
            model_name: Name of the model to test
            
        Returns:
            List[ExperimentResult]: Results of short query experiments
        """
    
    def get_experiment_summary(self, results: List[ExperimentResult]) -> Dict[str, Any]:
        """
        Get summary statistics for experiment results.
        
        Args:
            results: List of experiment results
            
        Returns:
            Dict[str, Any]: Summary statistics
        """
```

#### ExperimentResultBuilder

```python
class ExperimentResultBuilder:
    """Builder pattern for ExperimentResult construction."""
    
    def __init__(self):
        """Initialize builder with empty result."""
    
    def with_experiment_name(self, name: str) -> 'ExperimentResultBuilder':
        """
        Set experiment name.
        
        Args:
            name: Name of the experiment
            
        Returns:
            Self for method chaining
        """
    
    def with_model(self, model_name: str) -> 'ExperimentResultBuilder':
        """
        Set model name.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Self for method chaining
        """
    
    def with_query(self, original: str, processed: str) -> 'ExperimentResultBuilder':
        """
        Set query information.
        
        Args:
            original: Original query text
            processed: Processed query text
            
        Returns:
            Self for method chaining
        """
    
    def with_response(self, response: str) -> 'ExperimentResultBuilder':
        """
        Set response text.
        
        Args:
            response: Response text from model
            
        Returns:
            Self for method chaining
        """
    
    def with_tokens(self, input_t: int, output_t: int, total: int) -> 'ExperimentResultBuilder':
        """
        Set token counts.
        
        Args:
            input_t: Input token count
            output_t: Output token count
            total: Total token count
            
        Returns:
            Self for method chaining
        """
    
    def with_timing(self, duration: float) -> 'ExperimentResultBuilder':
        """
        Set response timing.
        
        Args:
            duration: Response duration in seconds
            
        Returns:
            Self for method chaining
        """
    
    def with_compression(
        self, 
        applied: bool, 
        result: Optional[CompressionResult] = None
    ) -> 'ExperimentResultBuilder':
        """
        Set compression information.
        
        Args:
            applied: Whether compression was applied
            result: Compression result if applied
            
        Returns:
            Self for method chaining
        """
    
    def with_timestamp(self, timestamp: Optional[datetime] = None) -> 'ExperimentResultBuilder':
        """
        Set experiment timestamp.
        
        Args:
            timestamp: Timestamp (defaults to now)
            
        Returns:
            Self for method chaining
        """
    
    def build(self) -> ExperimentResult:
        """
        Build ExperimentResult from collected data.
        
        Returns:
            ExperimentResult: Constructed experiment result
            
        Raises:
            ValueError: If required fields are missing
        """
```

### Factory APIs

#### TokenCounterFactory

```python
class TokenCounterFactory:
    """Factory for creating token counter instances."""
    
    @staticmethod
    def create_simple(
        limit_profile: LimitProfile = LimitProfile.PRACTICAL,
        config: Optional[ConfigurationProtocol] = None
    ) -> SimpleTokenCounter:
        """
        Create simple token counter.
        
        Args:
            limit_profile: Limit profile to use
            config: Configuration protocol implementation
            
        Returns:
            SimpleTokenCounter: Configured simple token counter
        """
    
    @staticmethod
    def create_accurate(config: Optional[ConfigurationProtocol] = None) -> AccurateTokenCounter:
        """
        Create accurate token counter.
        
        Args:
            config: Configuration protocol implementation
            
        Returns:
            AccurateTokenCounter: Configured accurate token counter
        """
    
    @staticmethod
    def create_hybrid(
        ml_client: TokenAnalysisClient,
        fallback_counter: Optional[TokenCounterProtocol] = None,
        config: Optional[ConfigurationProtocol] = None
    ) -> HybridTokenCounter:
        """
        Create hybrid token counter.
        
        Args:
            ml_client: ML client instance
            fallback_counter: Fallback token counter
            config: Configuration protocol implementation
            
        Returns:
            HybridTokenCounter: Configured hybrid token counter
        """
    
    @staticmethod
    def create_from_config(config: ConfigurationProtocol) -> TokenCounterProtocol:
        """
        Create token counter from configuration.
        
        Args:
            config: Configuration protocol implementation
            
        Returns:
            TokenCounterProtocol: Configured token counter
        """
```

### Validation APIs

#### RequestValidator

```python
class RequestValidator:
    """Request validation utilities."""
    
    @staticmethod
    def validate_text(text: str, max_length: int = 1000000) -> None:
        """
        Validate text input.
        
        Args:
            text: Text to validate
            max_length: Maximum allowed length
            
        Raises:
            ValueError: If text is invalid
        """
    
    @staticmethod
    def validate_model_name(model_name: str, allowed: Optional[List[str]] = None) -> None:
        """
        Validate model name.
        
        Args:
            model_name: Model name to validate
            allowed: List of allowed model names
            
        Raises:
            ValueError: If model name is invalid
        """
    
    @staticmethod
    def validate_strategy(strategy: str) -> CompressionStrategy:
        """
        Validate compression strategy.
        
        Args:
            strategy: Strategy string to validate
            
        Returns:
            CompressionStrategy: Validated strategy enum
            
        Raises:
            ValueError: If strategy is invalid
        """
    
    @staticmethod
    def validate_max_tokens(max_tokens: int, min_tokens: int = 1) -> None:
        """
        Validate max tokens parameter.
        
        Args:
            max_tokens: Max tokens to validate
            min_tokens: Minimum allowed tokens
            
        Raises:
            ValueError: If max_tokens is invalid
        """
    
    @staticmethod
    def validate_texts_list(texts: List[str], max_length: int = 1000000) -> None:
        """
        Validate list of texts.
        
        Args:
            texts: List of texts to validate
            max_length: Maximum allowed length per text
            
        Raises:
            ValueError: If any text is invalid
        """
```

## Data Models

### TokenInfo

```python
@dataclass
class TokenInfo:
    """Token count information."""
    count: int
    model_name: str
    method: str = "simple"
    confidence: float = 1.0
```

### CompressionResult

```python
@dataclass
class CompressionResult:
    """Text compression result."""
    original_text: str
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    strategy_used: str
```

### ExperimentResult

```python
@dataclass
class ExperimentResult:
    """Experiment execution result."""
    experiment_name: str
    model_name: str
    original_query: str
    processed_query: str
    response: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    response_time: float
    compression_applied: bool
    compression_result: Optional[CompressionResult]
    timestamp: datetime
```

### ModelLimits

```python
@dataclass
class ModelLimits:
    """Model token limits."""
    max_input_tokens: int
    max_output_tokens: int
    max_total_tokens: int
    sliding_window: Optional[int] = None
    recommended_input: Optional[int] = None
```

### ModelResponse

```python
@dataclass
class ModelResponse:
    """ML model response."""
    response: str
    model_name: str
    tokens_used: int
    response_time: float
    metadata: Optional[Dict[str, Any]] = None
```

## Error Handling

### Exception Hierarchy

```python
class TokenAnalysisError(Exception):
    """Base exception for token analysis errors."""
    pass

class TokenCountError(TokenAnalysisError):
    """Token counting related errors."""
    pass

class ModelLimitError(TokenAnalysisError):
    """Model limit related errors."""
    pass

class CompressionError(TokenAnalysisError):
    """Text compression related errors."""
    pass

class MLClientError(Exception):
    """ML client related errors."""
    pass

class NetworkError(MLClientError):
    """Network related errors."""
    pass

class TimeoutError(MLClientError):
    """Timeout related errors."""
    pass

class ServiceUnavailableError(MLClientError):
    """Service unavailable errors."""
    pass

class ValidationError(Exception):
    """Input validation errors."""
    pass

class TextValidationError(ValidationError):
    """Text validation errors."""
    pass

class ModelValidationError(ValidationError):
    """Model validation errors."""
    pass

class StrategyValidationError(ValidationError):
    """Strategy validation errors."""
    pass
```

## Usage Examples

### Basic Token Counting

```python
from core.token_analyzer import SimpleTokenCounter
from tests.mocks.mock_config import MockConfiguration

# Initialize
config = MockConfiguration()
counter = SimpleTokenCounter(config=config)

# Count tokens
text = "Hello, world! This is a test."
token_info = counter.count_tokens(text, "starcoder")
print(f"Tokens: {token_info.count}")

# Check limits
exceeds = counter.check_limit_exceeded(text, "starcoder")
print(f"Exceeds limits: {exceeds}")
```

### Text Compression

```python
from core.text_compressor import SimpleTextCompressor

compressor = SimpleTextCompressor(token_counter)

# Compress text
long_text = "This is a very long text. " * 1000
result = compressor.compress_text(
    text=long_text,
    max_tokens=1000,
    model_name="starcoder",
    strategy="truncation"
)

print(f"Compression ratio: {result.compression_ratio:.2f}")
print(f"Compressed text: {result.compressed_text[:100]}...")
```

### Running Experiments

```python
from core.experiments import TokenLimitExperiments

experiments = TokenLimitExperiments(ml_client, token_counter, compressor)

# Run experiments
results = await experiments.run_limit_exceeded_experiment("starcoder")

for result in results:
    print(f"Experiment: {result.experiment_name}")
    print(f"Response time: {result.response_time:.2f}s")
    print(f"Total tokens: {result.total_tokens}")
```

### Using Builder Pattern

```python
from core.builders import ExperimentResultBuilder

builder = ExperimentResultBuilder()
result = (builder
         .with_experiment_name("test_experiment")
         .with_model("starcoder")
         .with_query("original query", "processed query")
         .with_response("model response")
         .with_tokens(100, 50, 150)
         .with_timing(2.0)
         .with_compression(True, compression_result)
         .with_timestamp()
         .build())
```

## Performance Considerations

### Best Practices

1. **Reuse instances**: Create token counters and compressors once
2. **Batch operations**: Process multiple texts together when possible
3. **Choose appropriate strategies**: Use simple strategies for basic needs
4. **Cache results**: Store token counts for repeated texts
5. **Async operations**: Use async methods for I/O operations

### Performance Tips

- Use `SimpleTokenCounter` for most use cases
- Use `HybridTokenCounter` for accuracy-critical applications
- Choose compression strategies based on text type
- Implement connection pooling for ML clients
- Use structured logging for performance monitoring

## Version Compatibility

### API Versioning

- **v1.0**: Initial release with core functionality
- **v1.1**: Added builder pattern and advanced compression
- **v1.2**: Added ML client with resilience features

### Backward Compatibility

- All public APIs maintain backward compatibility
- Deprecated methods are marked with warnings
- Breaking changes are documented in migration guides
- Configuration changes are handled gracefully

This API reference provides comprehensive documentation for all public interfaces. For implementation details and internal APIs, refer to the source code documentation.
