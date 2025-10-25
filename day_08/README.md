# Day 8: Enhanced Token Analysis System

A comprehensive token analysis and compression system for AI models, featuring accurate token counting, advanced compression strategies, and robust experiment management.

## 🚀 Features

- **Accurate Token Counting**: Multiple strategies (simple estimation, ML-based, hybrid)
- **Advanced Compression**: Strategy pattern with truncation, keywords, extractive, semantic, and summarization
- **Robust ML Integration**: Retry logic, circuit breaker, and request validation
- **Comprehensive Experiments**: Builder pattern for experiment results with structured logging
- **Modern Architecture**: SOLID principles, design patterns, dependency injection
- **High Test Coverage**: 74% coverage with 282 passing tests
- **Quality Assurance**: Strict linting, pre-commit hooks, security scanning

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Examples](#examples)
- [Testing](#testing)
- [Development](#development)
- [Migration Guide](#migration-guide)

## 🏃 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd day_08

# Install dependencies
make install-dev

# Run tests
make test

# Run experiments
make run
```

### Basic Usage

```python
from core.token_analyzer import SimpleTokenCounter
from core.text_compressor import SimpleTextCompressor
from core.experiments import TokenLimitExperiments
from tests.mocks.mock_config import MockConfiguration

# Initialize components
config = MockConfiguration()
token_counter = SimpleTokenCounter(config=config)
text_compressor = SimpleTextCompressor(token_counter)

# Count tokens
text = "This is a test text for token analysis"
token_info = token_counter.count_tokens(text, "starcoder")
print(f"Tokens: {token_info.count}")

# Compress text
compression_result = text_compressor.compress_text(
    text="Very long text that exceeds model limits...",
    max_tokens=1000,
    model_name="starcoder",
    strategy="truncation"
)
print(f"Compression ratio: {compression_result.compression_ratio}")
```

## 🏗️ Architecture

### System Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Token Counter │    │ Text Compressor │    │   ML Client     │
│                 │    │                 │    │                 │
│ • Simple        │    │ • Strategy      │    │ • Retry Logic   │
│ • Accurate      │    │ • Template      │    │ • Circuit       │
│ • Hybrid        │    │ • Factory       │    │   Breaker       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Experiments   │
                    │                 │
                    │ • Builder       │
                    │ • Dataclasses   │
                    │ • Logging       │
                    └─────────────────┘
```

### Design Patterns

- **Strategy Pattern**: Compression strategies (truncation, keywords, etc.)
- **Factory Pattern**: Token counter and compressor creation
- **Builder Pattern**: Experiment result construction
- **Template Method**: Base compressor with common logic
- **Circuit Breaker**: ML client resilience
- **Facade Pattern**: Simple interfaces for complex subsystems

### Core Components

#### 1. Token Analysis (`core/token_analyzer.py`)

```python
class SimpleTokenCounter:
    """Simple token counter with configurable limits."""
    
    def count_tokens(self, text: str, model_name: str) -> TokenInfo:
        """Count tokens using heuristic estimation."""
        
    def check_limit_exceeded(self, text: str, model_name: str) -> bool:
        """Check if text exceeds model limits."""
        
    def estimate_compression_target(self, text: str, model_name: str) -> int:
        """Estimate target tokens for compression."""
```

#### 2. Text Compression (`core/text_compressor.py`)

```python
class SimpleTextCompressor:
    """Facade for text compression with strategy pattern."""
    
    def compress_text(
        self, 
        text: str, 
        max_tokens: int, 
        model_name: str = "starcoder",
        strategy: str = "truncation"
    ) -> CompressionResult:
        """Compress text using specified strategy."""
```

#### 3. ML Client (`core/ml_client.py`)

```python
class TokenAnalysisClient:
    """Resilient ML client with retry and circuit breaker."""
    
    async def count_tokens(self, text: str, model_name: str) -> TokenInfo:
        """Count tokens using ML service."""
        
    async def make_request(
        self, 
        model_name: str, 
        prompt: str, 
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> ModelResponse:
        """Make request to ML model."""
```

#### 4. Experiments (`core/experiments.py`)

```python
class TokenLimitExperiments:
    """Experiment management with builder pattern."""
    
    async def run_limit_exceeded_experiment(
        self, 
        model_name: str = "starcoder"
    ) -> List[ExperimentResult]:
        """Run experiments with limit-exceeding queries."""
        
    async def run_model_comparison_experiment(
        self, 
        models: List[str], 
        query: str, 
        auto_swap: bool = True
    ) -> List[ExperimentResult]:
        """Compare multiple models."""
```

## 📚 API Reference

### Data Models

#### TokenInfo
```python
@dataclass
class TokenInfo:
    count: int
    model_name: str
    method: str = "simple"
    confidence: float = 1.0
```

#### CompressionResult
```python
@dataclass
class CompressionResult:
    original_text: str
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    strategy_used: str
```

#### ExperimentResult
```python
@dataclass
class ExperimentResult:
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

### Compression Strategies

#### Available Strategies
- `truncation`: Keep first and last sentences with middle portion
- `keywords`: Extract keywords longer than 4 characters
- `extractive`: Advanced extraction (requires ML service)
- `semantic`: Semantic compression (requires ML service)
- `summarization`: AI-powered summarization (requires ML service)

#### Strategy Usage
```python
from core.compressors import CompressionStrategy, CompressionStrategyFactory

# Create compressor
compressor = CompressionStrategyFactory.create(
    CompressionStrategy.TRUNCATION,
    token_counter
)

# Compress text
result = compressor.compress(text, max_tokens=1000, model_name="starcoder")
```

### Builder Pattern

#### ExperimentResultBuilder
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

## ⚙️ Configuration

### Model Limits

Configure model limits in `config/model_limits.yaml`:

```yaml
models:
  starcoder:
    theoretical:
      max_input_tokens: 16384
      max_output_tokens: 2048
      max_total_tokens: 16384
    practical:
      max_input_tokens: 4096
      max_output_tokens: 1024
      max_total_tokens: 6000
```

### Environment Variables

Create `.env` file:

```bash
# ML Service Configuration
ML_SERVICE_URL=http://localhost:8004
ML_SERVICE_TIMEOUT=30.0

# Retry Configuration
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_DELAY=1.0

# Circuit Breaker Configuration
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60.0

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## 💡 Examples

### Basic Token Counting

```python
from core.token_analyzer import SimpleTokenCounter
from tests.mocks.mock_config import MockConfiguration

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

# Compress long text
long_text = "This is a very long text. " * 1000
result = compressor.compress_text(
    text=long_text,
    max_tokens=1000,
    model_name="starcoder",
    strategy="truncation"
)

print(f"Original tokens: {result.original_tokens}")
print(f"Compressed tokens: {result.compressed_tokens}")
print(f"Compression ratio: {result.compression_ratio:.2f}")
```

### Running Experiments

```python
from core.experiments import TokenLimitExperiments
from core.ml_client import TokenAnalysisClient

# Initialize components
ml_client = TokenAnalysisClient()
experiments = TokenLimitExperiments(ml_client, token_counter, compressor)

# Run limit exceeded experiment
results = await experiments.run_limit_exceeded_experiment("starcoder")

for result in results:
    print(f"Experiment: {result.experiment_name}")
    print(f"Response time: {result.response_time:.2f}s")
    print(f"Total tokens: {result.total_tokens}")
```

### Model Comparison

```python
# Compare multiple models
models = ["starcoder", "mistral", "qwen"]
query = "Explain machine learning in simple terms."

results = await experiments.run_model_comparison_experiment(
    models=models,
    query=query,
    auto_swap=True
)

# Analyze results
for result in results:
    print(f"Model: {result.model_name}")
    print(f"Response: {result.response[:100]}...")
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test categories
make test-integration
make test-zen

# Run linting
make lint

# Run security checks
make security
```

### Test Structure

```
tests/
├── integration/          # End-to-end tests
├── regression/           # Baseline behavior tests
├── performance/          # Performance baseline tests
├── mocks/               # Mock configurations
└── test_*.py            # Unit tests
```

### Test Coverage

Current coverage: **74%** with **282 passing tests**

- Unit tests: Core functionality
- Integration tests: Component interaction
- Regression tests: Behavior preservation
- Performance tests: Baseline metrics

## 🛠️ Development

### Code Quality

```bash
# Format code
make format

# Run all quality checks
make quality-check

# Install pre-commit hooks
make pre-commit
```

### Linting Tools

- **mypy**: Static type checking (strict mode)
- **pylint**: Code quality analysis
- **ruff**: Fast Python linter
- **bandit**: Security vulnerability scanner
- **black**: Code formatting
- **isort**: Import sorting

### Development Workflow

1. **Create feature branch**
2. **Write tests first** (TDD)
3. **Implement feature**
4. **Run quality checks**: `make quality-check`
5. **Run tests**: `make test`
6. **Create pull request**

### Architecture Guidelines

- **Functions ≤15 lines** (where possible)
- **SOLID principles** applied
- **Design patterns** for common problems
- **Dependency injection** for testability
- **Structured logging** instead of print statements
- **Type hints** for all public APIs

## 📖 Migration Guide

### From Legacy Code

If migrating from older versions:

1. **Update imports**:
   ```python
   # Old
   from core.token_analyzer import SimpleTokenCounter
   
   # New
   from core.token_analyzer import SimpleTokenCounter
   from tests.mocks.mock_config import MockConfiguration
   ```

2. **Update initialization**:
   ```python
   # Old
   counter = SimpleTokenCounter()
   
   # New
   config = MockConfiguration()
   counter = SimpleTokenCounter(config=config)
   ```

3. **Update compression usage**:
   ```python
   # Old
   result = compressor.compress_by_truncation(text, max_tokens)
   
   # New
   result = compressor.compress_text(text, max_tokens, strategy="truncation")
   ```

### Breaking Changes

- **Configuration injection**: All components now require configuration
- **Method signatures**: Some methods have additional parameters
- **Return types**: Enhanced data models with more fields
- **Error handling**: Structured exceptions instead of generic errors

### Compatibility

- **Python 3.10+** required
- **Backward compatibility** maintained for public APIs
- **Deprecated methods** marked with warnings

## 📊 Performance

### Benchmarks

- **Token counting**: ~0.1ms per 1000 characters
- **Text compression**: ~5ms per 10KB text
- **ML requests**: ~200ms average response time
- **Memory usage**: ~50MB baseline

### Optimization Tips

1. **Use appropriate token counter**:
   - Simple: Fast, good for most cases
   - Accurate: Slower, more precise
   - Hybrid: Best of both worlds

2. **Choose compression strategy**:
   - Truncation: Fastest, good for structured text
   - Keywords: Good for keyword-rich content
   - Advanced: Slower but better quality

3. **Batch operations**: Process multiple texts together
4. **Cache results**: Reuse token counts for repeated texts

## 🤝 Contributing

### Getting Started

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes following the architecture guidelines
4. Add tests for new functionality
5. Run quality checks: `make quality-check`
6. Commit changes: `git commit -m 'Add amazing feature'`
7. Push to branch: `git push origin feature/amazing-feature`
8. Open Pull Request

### Code Standards

- Follow PEP 8 style guide
- Use type hints for all functions
- Write comprehensive docstrings
- Maintain test coverage above 70%
- Use meaningful variable names
- Keep functions under 15 lines when possible

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **AI Challenge** for the project framework
- **Python community** for excellent libraries
- **Contributors** who helped improve the system

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Documentation**: [Wiki](https://github.com/your-repo/wiki)

---

**Made with ❤️ for the AI Challenge**