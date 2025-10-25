# Architecture Documentation

## System Overview

The Enhanced Token Analysis System is a modular, extensible platform for token counting, text compression, and AI model experimentation. Built with modern software engineering principles, it provides a robust foundation for AI-powered text processing.

## Core Principles

### 1. SOLID Principles

- **Single Responsibility Principle (SRP)**: Each class has one reason to change
- **Open/Closed Principle (OCP)**: Open for extension, closed for modification
- **Liskov Substitution Principle (LSP)**: Derived classes are substitutable for base classes
- **Interface Segregation Principle (ISP)**: Clients depend only on interfaces they use
- **Dependency Inversion Principle (DIP)**: Depend on abstractions, not concretions

### 2. Design Patterns

- **Strategy Pattern**: Compression strategies
- **Factory Pattern**: Object creation
- **Builder Pattern**: Complex object construction
- **Template Method**: Common algorithm structure
- **Circuit Breaker**: Fault tolerance
- **Facade Pattern**: Simplified interfaces

### 3. Quality Attributes

- **Maintainability**: Clean code, comprehensive tests
- **Extensibility**: Plugin architecture, strategy pattern
- **Reliability**: Error handling, circuit breaker
- **Performance**: Efficient algorithms, caching
- **Testability**: Dependency injection, mocking

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  Experiments  │  Console Reporter  │  Model Comparison  │ Demo │
├─────────────────────────────────────────────────────────────────┤
│                           Core Layer                            │
├─────────────────────────────────────────────────────────────────┤
│ Token Analyzer │ Text Compressor │ ML Client │ Validators │ ... │
├─────────────────────────────────────────────────────────────────┤
│                        Infrastructure Layer                     │
├─────────────────────────────────────────────────────────────────┤
│   Config      │   Logging    │   Retry     │   Statistics   │   │
├─────────────────────────────────────────────────────────────────┤
│                        Data Layer                               │
├─────────────────────────────────────────────────────────────────┤
│  Data Models  │  Protocols   │  Interfaces │  Enums        │   │
└─────────────────────────────────────────────────────────────────┘
```

### Component Dependencies

```
┌─────────────────┐
│   Experiments   │
└─────────┬───────┘
          │
    ┌─────┴─────┐
    │           │
┌───▼───┐   ┌───▼───┐   ┌─────────┐
│ Token │   │ Text  │   │   ML    │
│Counter│   │Compres│   │ Client  │
└───┬───┘   └───┬───┘   └─────────┘
    │           │
    └───────────┼───────────┐
                │           │
        ┌───────▼───┐   ┌───▼───┐
        │   Config  │   │ Utils │
        └───────────┘   └───────┘
```

## Core Components

### 1. Token Analyzer (`core/token_analyzer.py`)

**Purpose**: Accurate token counting for various AI models

**Key Classes**:
- `SimpleTokenCounter`: Heuristic-based token counting
- `AccurateTokenCounter`: ML-based token counting
- `HybridTokenCounter`: Combines multiple strategies

**Architecture**:
```python
class SimpleTokenCounter:
    def __init__(self, config: ConfigurationProtocol):
        self.config = config
        self.limit_profile = LimitProfile.PRACTICAL
    
    def count_tokens(self, text: str, model_name: str) -> TokenInfo:
        # Template method pattern
        self._validate_input(text, model_name)
        tokens = self._estimate_tokens(text, model_name)
        return self._build_token_info(tokens, model_name)
```

**Design Patterns**:
- **Template Method**: Common counting algorithm
- **Strategy**: Different estimation strategies
- **Dependency Injection**: Configuration injection

### 2. Text Compressor (`core/text_compressor.py`)

**Purpose**: Intelligent text compression using multiple strategies

**Key Classes**:
- `SimpleTextCompressor`: Facade for compression
- `BaseCompressor`: Abstract base class
- `TruncationCompressor`: Truncation strategy
- `KeywordsCompressor`: Keywords extraction

**Architecture**:
```python
class BaseCompressor(ABC):
    def compress(self, text: str, max_tokens: int, model_name: str) -> CompressionResult:
        # Template method
        if not self._should_compress(text, max_tokens, model_name):
            return self._no_compression_result(text, model_name)
        
        compressed = self._apply_compression_strategy(text, max_tokens, model_name)
        return self._build_compression_result(text, compressed, model_name)
    
    @abstractmethod
    def _apply_compression_strategy(self, text: str, max_tokens: int, model_name: str) -> str:
        pass
```

**Design Patterns**:
- **Strategy Pattern**: Different compression algorithms
- **Template Method**: Common compression workflow
- **Factory Pattern**: Compressor creation
- **Facade Pattern**: Simplified interface

### 3. ML Client (`core/ml_client.py`)

**Purpose**: Resilient communication with ML services

**Key Classes**:
- `TokenAnalysisClient`: Main ML client
- `HybridTokenCounter`: Combines local and ML counting
- `RequestValidator`: Input validation

**Architecture**:
```python
class TokenAnalysisClient:
    def __init__(self, base_url: str = "http://localhost:8004"):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.resilient_client = ResilientClient(retry_config, cb_config)
    
    async def count_tokens(self, text: str, model_name: str) -> TokenInfo:
        self._validate_count_tokens_input(text, model_name)
        response_data = await self._execute_count_request(text, model_name)
        return self._parse_token_info(response_data)
```

**Design Patterns**:
- **Circuit Breaker**: Fault tolerance
- **Retry Pattern**: Resilience
- **Validation Pattern**: Input sanitization

### 4. Experiments (`core/experiments.py`)

**Purpose**: Comprehensive experiment management and analysis

**Key Classes**:
- `TokenLimitExperiments`: Main experiment orchestrator
- `ExperimentResultBuilder`: Builder for results
- `QueryInfo`, `ResponseInfo`: Data transfer objects

**Architecture**:
```python
class TokenLimitExperiments:
    async def run_limit_exceeded_experiment(self, model_name: str) -> List[ExperimentResult]:
        context = self._prepare_experiment_context(model_name)
        
        no_comp_result = await self._run_no_compression_test(context)
        trunc_result = await self._run_truncation_test(context)
        keywords_result = await self._run_keywords_test(context)
        
        return self._collect_results([no_comp_result, trunc_result, keywords_result])
```

**Design Patterns**:
- **Builder Pattern**: Complex result construction
- **Data Transfer Object**: Structured data passing
- **Template Method**: Experiment workflow

## Data Flow

### 1. Token Counting Flow

```
Text Input → Validation → Token Estimation → Model Limits Check → TokenInfo
     │              │              │                │
     ▼              ▼              ▼                ▼
  Empty?        Length OK?      Strategy         Within Limits?
     │              │              │                │
     ▼              ▼              ▼                ▼
  Error         Continue        Count Tokens    Return Result
```

### 2. Compression Flow

```
Long Text → Token Count → Limit Check → Strategy Selection → Compression → Result
     │           │            │              │                │
     ▼           ▼            ▼              ▼                ▼
  Validate   Count Tokens   Exceeds?      Choose Method    Apply Algorithm
     │           │            │              │                │
     ▼           ▼            ▼              ▼                ▼
  Valid?     How Many?     Yes/No         Truncation/      Compressed Text
     │           │            │           Keywords/        + Metadata
     ▼           ▼            ▼           Advanced
  Continue   Continue     Compress?      Strategy
```

### 3. Experiment Flow

```
Experiment Request → Context Preparation → Query Processing → Model Execution → Result Building
         │                    │                    │                │                │
         ▼                    ▼                    ▼                ▼                ▼
    Parameters          ExperimentContext      QueryInfo        ResponseInfo    ExperimentResult
         │                    │                    │                │                │
         ▼                    ▼                    ▼                ▼                ▼
    Model Name          Long Query            Compression?      ML Request      Builder Pattern
    Strategy            Setup                 Applied           Execution       Data Assembly
```

## Configuration Architecture

### Configuration Hierarchy

```
Environment Variables (Highest Priority)
         │
         ▼
    .env File
         │
         ▼
    model_limits.yaml
         │
         ▼
    Default Values (Lowest Priority)
```

### Configuration Classes

```python
@dataclass
class AppConfig:
    ml_service_url: str = "http://localhost:8004"
    ml_service_timeout: float = 30.0
    retry_max_attempts: int = 3
    retry_base_delay: float = 1.0
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: float = 60.0
    log_level: str = "INFO"
    log_format: str = "json"
```

## Error Handling Strategy

### Error Hierarchy

```
Exception
├── TokenAnalysisError
│   ├── TokenCountError
│   ├── ModelLimitError
│   └── CompressionError
├── MLClientError
│   ├── NetworkError
│   ├── TimeoutError
│   └── ServiceUnavailableError
└── ValidationError
    ├── TextValidationError
    ├── ModelValidationError
    └── StrategyValidationError
```

### Error Handling Patterns

1. **Fail Fast**: Validate inputs early
2. **Graceful Degradation**: Fallback strategies
3. **Circuit Breaker**: Prevent cascade failures
4. **Retry Logic**: Transient error recovery
5. **Structured Logging**: Error tracking and debugging

## Testing Architecture

### Test Pyramid

```
                    ┌─────────────────┐
                    │   E2E Tests     │  ← Few, High Value
                    │   (Integration) │
                    └─────────────────┘
                 ┌───────────────────────┐
                 │    Integration        │  ← Some, Medium Value
                 │       Tests           │
                 └───────────────────────┘
            ┌─────────────────────────────────┐
            │         Unit Tests              │  ← Many, Fast
            │      (Core Functionality)       │
            └─────────────────────────────────┘
```

### Test Categories

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Component interaction testing
3. **Regression Tests**: Behavior preservation testing
4. **Performance Tests**: Baseline metric testing
5. **Property-Based Tests**: Edge case discovery

## Performance Considerations

### Optimization Strategies

1. **Caching**: Token count results
2. **Lazy Loading**: Configuration and dependencies
3. **Connection Pooling**: HTTP client reuse
4. **Batch Processing**: Multiple operations together
5. **Async Operations**: Non-blocking I/O

### Performance Metrics

- **Token Counting**: ~0.1ms per 1000 characters
- **Text Compression**: ~5ms per 10KB text
- **ML Requests**: ~200ms average response time
- **Memory Usage**: ~50MB baseline

## Security Considerations

### Security Measures

1. **Input Validation**: Sanitize all inputs
2. **Rate Limiting**: Prevent abuse
3. **Authentication**: Secure ML service access
4. **Data Privacy**: No sensitive data logging
5. **Dependency Scanning**: Regular security audits

### Security Tools

- **Bandit**: Static security analysis
- **Safety**: Dependency vulnerability scanning
- **Pre-commit hooks**: Automated security checks

## Deployment Architecture

### Container Strategy

```
┌─────────────────────────────────────────────────────────┐
│                    Host Machine                         │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │   ML Service    │  │  Main App       │              │
│  │   Container     │  │  Container      │              │
│  │                 │  │                 │              │
│  │ • FastAPI       │  │ • Python App   │              │
│  │ • Model Server  │  │ • Token Counter │              │
│  │ • Port 8004     │  │ • Experiments  │              │
│  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────┘
```

### Environment Configuration

- **Development**: Local Docker containers
- **Testing**: Isolated test environment
- **Production**: Orchestrated containers with monitoring

## Monitoring and Observability

### Logging Strategy

```python
# Structured logging with context
logger.info(
    "token_count_completed",
    text_length=len(text),
    model_name=model_name,
    token_count=result.count,
    processing_time=duration
)
```

### Metrics Collection

- **Performance Metrics**: Response times, throughput
- **Error Metrics**: Error rates, failure patterns
- **Business Metrics**: Token counts, compression ratios
- **System Metrics**: Memory usage, CPU utilization

## Future Extensibility

### Extension Points

1. **New Compression Strategies**: Implement `BaseCompressor`
2. **New Token Counters**: Implement `TokenCounterProtocol`
3. **New ML Models**: Extend `TokenAnalysisClient`
4. **New Experiment Types**: Extend `TokenLimitExperiments`

### Plugin Architecture

```python
# Example: Adding new compression strategy
class SemanticCompressor(BaseCompressor):
    def _apply_compression_strategy(self, text: str, max_tokens: int, model_name: str) -> str:
        # Implement semantic compression
        pass

# Register with factory
CompressionStrategyFactory.register(CompressionStrategy.SEMANTIC, SemanticCompressor)
```

## Conclusion

The Enhanced Token Analysis System demonstrates modern software architecture principles with clean separation of concerns, comprehensive testing, and robust error handling. The modular design allows for easy extension and maintenance while providing excellent performance and reliability.

The system successfully balances complexity with usability, providing both simple interfaces for common use cases and advanced features for sophisticated requirements. The comprehensive test suite and quality assurance measures ensure reliability and maintainability.
