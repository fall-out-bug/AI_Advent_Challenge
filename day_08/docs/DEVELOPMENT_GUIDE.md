# Development Guide

## Overview

This guide consolidates development practices, coding standards, and best practices for the Enhanced Token Analysis System. It covers SOLID principles, Zen of Python adherence, testing strategies, and contribution workflows.

## Table of Contents

- [SOLID Principles](#solid-principles)
- [Zen of Python](#zen-of-python)
- [Code Quality Standards](#code-quality-standards)
- [Testing Strategies](#testing-strategies)
- [Development Workflow](#development-workflow)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Documentation Standards](#documentation-standards)
- [Performance Guidelines](#performance-guidelines)

## SOLID Principles

### Single Responsibility Principle (SRP)

Each class should have only one reason to change.

#### ✅ Good Example

```python
class TokenCalculator:
    """Single responsibility: Calculate token counts."""
    
    def calculate_tokens(self, text: str) -> int:
        """Calculate token count for text."""
        return len(text.split())

class LimitChecker:
    """Single responsibility: Check model limits."""
    
    def check_limit_exceeded(self, text: str, model_name: str) -> bool:
        """Check if text exceeds model limits."""
        token_count = self.token_calculator.calculate_tokens(text)
        limits = self.get_model_limits(model_name)
        return token_count > limits.max_input_tokens
```

#### ❌ Bad Example

```python
class TokenAnalyzer:
    """Multiple responsibilities: calculation, validation, reporting."""
    
    def calculate_tokens(self, text: str) -> int:
        """Calculate tokens."""
        pass
    
    def validate_text(self, text: str) -> bool:
        """Validate text."""
        pass
    
    def generate_report(self, results: Dict) -> str:
        """Generate report."""
        pass
```

### Open/Closed Principle (OCP)

Classes should be open for extension but closed for modification.

#### ✅ Good Example

```python
class BaseCompressor(ABC):
    """Open for extension, closed for modification."""
    
    def compress(self, text: str, max_tokens: int) -> CompressionResult:
        """Template method - cannot be modified."""
        if not self._should_compress(text, max_tokens):
            return self._no_compression_result(text)
        
        compressed = self._apply_compression_strategy(text, max_tokens)
        return self._build_compression_result(text, compressed)
    
    @abstractmethod
    def _apply_compression_strategy(self, text: str, max_tokens: int) -> str:
        """Extension point - can be overridden."""
        pass

class TruncationCompressor(BaseCompressor):
    """Extension without modification."""
    
    def _apply_compression_strategy(self, text: str, max_tokens: int) -> str:
        """Implement truncation strategy."""
        return self._truncate_text(text, max_tokens)
```

### Liskov Substitution Principle (LSP)

Derived classes should be substitutable for their base classes.

#### ✅ Good Example

```python
class TokenCounterProtocol(ABC):
    """Base protocol for token counters."""
    
    @abstractmethod
    def count_tokens(self, text: str, model_name: str) -> TokenInfo:
        """Count tokens in text."""
        pass

class SimpleTokenCounter(TokenCounterProtocol):
    """Substitutable implementation."""
    
    def count_tokens(self, text: str, model_name: str) -> TokenInfo:
        """Count tokens using simple estimation."""
        return TokenInfo(count=len(text.split()), model_name=model_name)

class AccurateTokenCounter(TokenCounterProtocol):
    """Substitutable implementation."""
    
    def count_tokens(self, text: str, model_name: str) -> TokenInfo:
        """Count tokens using ML-based estimation."""
        return TokenInfo(count=self._ml_count(text), model_name=model_name)

# Both implementations can be used interchangeably
def process_text(counter: TokenCounterProtocol, text: str) -> TokenInfo:
    """Function works with any TokenCounterProtocol implementation."""
    return counter.count_tokens(text, "starcoder")
```

### Interface Segregation Principle (ISP)

Clients should not depend on interfaces they don't use.

#### ✅ Good Example

```python
class TokenCounterProtocol(ABC):
    """Focused interface for token counting."""
    
    @abstractmethod
    def count_tokens(self, text: str, model_name: str) -> TokenInfo:
        """Count tokens in text."""
        pass

class CompressionProtocol(ABC):
    """Focused interface for compression."""
    
    @abstractmethod
    def compress(self, text: str, max_tokens: int) -> CompressionResult:
        """Compress text."""
        pass

class TokenAnalysisService:
    """Uses only the interfaces it needs."""
    
    def __init__(
        self,
        token_counter: TokenCounterProtocol,  # Only needs counting
        compressor: CompressionProtocol       # Only needs compression
    ):
        self.token_counter = token_counter
        self.compressor = compressor
```

#### ❌ Bad Example

```python
class AnalysisProtocol(ABC):
    """Fat interface with multiple responsibilities."""
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens."""
        pass
    
    @abstractmethod
    def compress_text(self, text: str) -> str:
        """Compress text."""
        pass
    
    @abstractmethod
    def generate_report(self, data: Dict) -> str:
        """Generate report."""
        pass
    
    @abstractmethod
    def send_notification(self, message: str) -> None:
        """Send notification."""
        pass
```

### Dependency Inversion Principle (DIP)

Depend on abstractions, not concretions.

#### ✅ Good Example

```python
class TokenAnalysisService:
    """Depends on abstractions."""
    
    def __init__(
        self,
        token_counter: TokenCounterProtocol,  # Abstraction
        repository: TokenAnalysisRepository,  # Abstraction
        logger: LoggerProtocol               # Abstraction
    ):
        self.token_counter = token_counter
        self.repository = repository
        self.logger = logger
    
    async def analyze_text(self, text: str) -> TokenAnalysisDomain:
        """Analyze text using injected dependencies."""
        self.logger.info("Starting analysis")
        
        token_info = self.token_counter.count_tokens(text, "starcoder")
        analysis = TokenAnalysisDomain(
            analysis_id=str(uuid.uuid4()),
            input_text=text,
            model_name="starcoder"
        )
        
        await self.repository.save(analysis)
        return analysis
```

#### ❌ Bad Example

```python
class TokenAnalysisService:
    """Depends on concrete implementations."""
    
    def __init__(self):
        self.token_counter = SimpleTokenCounter()  # Concrete
        self.repository = DatabaseRepository()    # Concrete
        self.logger = FileLogger()                 # Concrete
```

## Zen of Python

### Beautiful is Better Than Ugly

#### ✅ Beautiful Code

```python
def calculate_compression_ratio(original: int, compressed: int) -> float:
    """Calculate compression ratio with clear intent."""
    if original == 0:
        return 0.0
    
    return compressed / original

def is_effective_compression(ratio: float, threshold: float = 0.5) -> bool:
    """Check if compression meets effectiveness threshold."""
    return ratio <= threshold
```

#### ❌ Ugly Code

```python
def calc_comp_ratio(o, c):
    """Calculate compression ratio."""
    if o == 0:
        return 0.0
    return c / o

def is_eff_comp(r, t=0.5):
    """Check compression effectiveness."""
    return r <= t
```

### Explicit is Better Than Implicit

#### ✅ Explicit Code

```python
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

class CompressionStrategy(Enum):
    """Explicit compression strategy options."""
    TRUNCATION = "truncation"
    KEYWORDS = "keywords"
    SEMANTIC = "semantic"

@dataclass
class CompressionResult:
    """Explicit data structure."""
    original_text: str
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    strategy_used: CompressionStrategy

def compress_text(
    text: str,
    max_tokens: int,
    strategy: CompressionStrategy = CompressionStrategy.TRUNCATION
) -> CompressionResult:
    """Explicit function signature with clear types."""
    pass
```

#### ❌ Implicit Code

```python
def compress(text, max_tokens, strategy="truncation"):
    """Implicit types and unclear parameters."""
    pass
```

### Simple is Better Than Complex

#### ✅ Simple Code

```python
def count_tokens_simple(text: str) -> int:
    """Simple token counting using word splitting."""
    return len(text.split())

def is_text_too_long(text: str, max_tokens: int) -> bool:
    """Simple length check."""
    return count_tokens_simple(text) > max_tokens
```

#### ❌ Complex Code

```python
def count_tokens_complex(text: str) -> int:
    """Overly complex token counting."""
    import re
    import unicodedata
    
    # Normalize text
    normalized = unicodedata.normalize('NFKD', text)
    
    # Remove special characters
    cleaned = re.sub(r'[^\w\s]', '', normalized)
    
    # Split by multiple delimiters
    tokens = re.split(r'[\s\n\t\r]+', cleaned)
    
    # Filter empty tokens
    non_empty_tokens = [t for t in tokens if t.strip()]
    
    # Apply additional filtering
    filtered_tokens = [t for t in non_empty_tokens if len(t) > 0]
    
    return len(filtered_tokens)
```

### Flat is Better Than Nested

#### ✅ Flat Code

```python
def process_text(text: str) -> ProcessingResult:
    """Flat structure with early returns."""
    if not text:
        return ProcessingResult.error("Empty text")
    
    if len(text) > MAX_TEXT_LENGTH:
        return ProcessingResult.error("Text too long")
    
    if not is_valid_text(text):
        return ProcessingResult.error("Invalid text")
    
    # Main processing logic
    tokens = count_tokens(text)
    compressed = compress_text(text, MAX_TOKENS)
    
    return ProcessingResult.success(tokens, compressed)
```

#### ❌ Nested Code

```python
def process_text(text: str) -> ProcessingResult:
    """Nested structure that's hard to follow."""
    if text:
        if len(text) <= MAX_TEXT_LENGTH:
            if is_valid_text(text):
                tokens = count_tokens(text)
                compressed = compress_text(text, MAX_TOKENS)
                return ProcessingResult.success(tokens, compressed)
            else:
                return ProcessingResult.error("Invalid text")
        else:
            return ProcessingResult.error("Text too long")
    else:
        return ProcessingResult.error("Empty text")
```

### Readability Counts

#### ✅ Readable Code

```python
class TokenAnalysisService:
    """Service for analyzing text tokens with compression support."""
    
    def __init__(
        self,
        token_counter: TokenCounterProtocol,
        compressor: CompressionProtocol,
        repository: TokenAnalysisRepository
    ):
        """Initialize service with required dependencies."""
        self.token_counter = token_counter
        self.compressor = compressor
        self.repository = repository
    
    async def analyze_with_compression(
        self,
        text: str,
        model_spec: ModelSpecification,
        max_tokens: int
    ) -> TokenAnalysisDomain:
        """
        Analyze text and compress if necessary.
        
        This method performs complete token analysis including compression
        if the text exceeds the specified token limit.
        
        Args:
            text: Text to analyze
            model_spec: Model specification for analysis
            max_tokens: Maximum allowed tokens
            
        Returns:
            TokenAnalysisDomain: Complete analysis result
            
        Raises:
            ValidationError: If input parameters are invalid
            AnalysisError: If analysis fails
        """
        # Validate input parameters
        self._validate_analysis_input(text, model_spec, max_tokens)
        
        # Create analysis entity
        analysis = self._create_analysis_entity(text, model_spec)
        
        # Perform token counting
        token_info = await self._count_tokens(text, model_spec)
        
        # Apply compression if necessary
        if token_info.count > max_tokens:
            analysis = await self._apply_compression(analysis, max_tokens)
        
        # Save and return results
        await self.repository.save(analysis)
        return analysis
```

## Code Quality Standards

### Function Length

Functions should be no longer than 15 lines where possible.

#### ✅ Good Function Length

```python
def calculate_token_count(text: str) -> int:
    """Calculate token count using word splitting."""
    if not text:
        return 0
    
    words = text.split()
    return len(words)

def validate_model_name(model_name: str) -> bool:
    """Validate model name format."""
    if not model_name:
        return False
    
    return model_name.isalnum() and len(model_name) <= 50
```

#### ❌ Long Function

```python
def process_complex_analysis(text: str, model_name: str, options: Dict) -> Dict:
    """This function is too long and does too many things."""
    # Validation logic
    if not text:
        raise ValueError("Text cannot be empty")
    
    if not model_name:
        raise ValueError("Model name cannot be empty")
    
    if len(text) > 1000000:
        raise ValueError("Text too long")
    
    # Token counting logic
    words = text.split()
    token_count = len(words)
    
    # Model limit checking
    if model_name == "starcoder":
        max_tokens = 16384
    elif model_name == "mistral":
        max_tokens = 8192
    else:
        max_tokens = 4096
    
    # Compression logic
    if token_count > max_tokens:
        # Truncation logic
        if options.get("strategy") == "truncation":
            # Complex truncation logic here...
            pass
        # Keywords logic
        elif options.get("strategy") == "keywords":
            # Complex keywords logic here...
            pass
    
    # Result formatting
    result = {
        "token_count": token_count,
        "compressed": token_count > max_tokens,
        "strategy": options.get("strategy", "none")
    }
    
    return result
```

### Variable Naming

Use meaningful, descriptive variable names.

#### ✅ Good Naming

```python
def analyze_text_performance(text: str, model_name: str) -> PerformanceMetrics:
    """Analyze text processing performance."""
    start_time = time.time()
    
    token_count = count_tokens(text)
    processing_time = time.time() - start_time
    
    compression_ratio = calculate_compression_ratio(len(text), token_count)
    
    return PerformanceMetrics(
        token_count=token_count,
        processing_time=processing_time,
        compression_ratio=compression_ratio
    )
```

#### ❌ Poor Naming

```python
def analyze_text_performance(text: str, model_name: str) -> PerformanceMetrics:
    """Analyze text processing performance."""
    t1 = time.time()
    
    tc = len(text.split())
    pt = time.time() - t1
    
    cr = tc / len(text)
    
    return PerformanceMetrics(tc, pt, cr)
```

### Type Hints

Use type hints for all public functions and methods.

#### ✅ Good Type Hints

```python
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass

@dataclass
class TokenInfo:
    """Token count information."""
    count: int
    model_name: str
    method: str = "simple"
    confidence: float = 1.0

def count_tokens(
    text: str,
    model_name: str,
    method: str = "simple"
) -> TokenInfo:
    """Count tokens in text."""
    pass

def batch_analyze(
    texts: List[str],
    model_name: str,
    max_tokens: Optional[int] = None
) -> List[TokenInfo]:
    """Analyze multiple texts."""
    pass

def get_model_limits(model_name: str) -> Dict[str, int]:
    """Get model token limits."""
    pass
```

### Error Handling

Use specific exception types and provide meaningful error messages.

#### ✅ Good Error Handling

```python
class TokenAnalysisError(Exception):
    """Base exception for token analysis errors."""
    pass

class ValidationError(TokenAnalysisError):
    """Input validation error."""
    pass

class ModelLimitError(TokenAnalysisError):
    """Model limit exceeded error."""
    pass

def validate_text_input(text: str) -> None:
    """Validate text input."""
    if not text:
        raise ValidationError("Text cannot be empty")
    
    if len(text) > MAX_TEXT_LENGTH:
        raise ValidationError(f"Text too long: {len(text)} > {MAX_TEXT_LENGTH}")
    
    if not isinstance(text, str):
        raise ValidationError(f"Expected string, got {type(text)}")

def check_model_limits(text: str, model_name: str) -> None:
    """Check if text exceeds model limits."""
    token_count = count_tokens(text)
    limits = get_model_limits(model_name)
    
    if token_count > limits.max_input_tokens:
        raise ModelLimitError(
            f"Text exceeds {model_name} limit: {token_count} > {limits.max_input_tokens}"
        )
```

## Testing Strategies

### Test Structure

Organize tests by functionality and use descriptive names.

```python
# tests/test_token_analyzer.py
import pytest
from core.token_analyzer import SimpleTokenCounter
from tests.mocks.mock_config import MockConfiguration

class TestSimpleTokenCounter:
    """Test cases for SimpleTokenCounter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = MockConfiguration()
        self.counter = SimpleTokenCounter(config=self.config)
    
    def test_count_tokens_with_valid_text(self):
        """Test token counting with valid text."""
        text = "Hello world"
        result = self.counter.count_tokens(text, "starcoder")
        
        assert result.count == 2
        assert result.model_name == "starcoder"
        assert result.method == "simple"
    
    def test_count_tokens_with_empty_text(self):
        """Test token counting with empty text."""
        with pytest.raises(ValidationError):
            self.counter.count_tokens("", "starcoder")
    
    def test_count_tokens_with_none_text(self):
        """Test token counting with None text."""
        with pytest.raises(ValidationError):
            self.counter.count_tokens(None, "starcoder")
    
    def test_check_limit_exceeded_within_limits(self):
        """Test limit check when within limits."""
        text = "Short text"
        result = self.counter.check_limit_exceeded(text, "starcoder")
        
        assert result is False
    
    def test_check_limit_exceeded_over_limits(self):
        """Test limit check when over limits."""
        long_text = "word " * 10000  # Very long text
        result = self.counter.check_limit_exceeded(long_text, "starcoder")
        
        assert result is True
```

### Property-Based Testing

Use Hypothesis for property-based testing.

```python
# tests/property/test_token_analyzer_properties.py
from hypothesis import given, strategies as st
from core.token_analyzer import SimpleTokenCounter
from tests.mocks.mock_config import MockConfiguration

class TestTokenAnalyzerProperties:
    """Property-based tests for token analyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = MockConfiguration()
        self.counter = SimpleTokenCounter(config=self.config)
    
    @given(st.text(min_size=1, max_size=1000))
    def test_token_count_is_non_negative(self, text: str):
        """Token count should always be non-negative."""
        result = self.counter.count_tokens(text, "starcoder")
        assert result.count >= 0
    
    @given(st.text(min_size=1, max_size=1000))
    def test_token_count_increases_with_text_length(self, text: str):
        """Token count should generally increase with text length."""
        result = self.counter.count_tokens(text, "starcoder")
        
        # Simple heuristic: more characters should generally mean more tokens
        if len(text) > 100:
            assert result.count > 0
    
    @given(st.text(min_size=1, max_size=100))
    def test_same_text_gives_same_result(self, text: str):
        """Same text should give same token count."""
        result1 = self.counter.count_tokens(text, "starcoder")
        result2 = self.counter.count_tokens(text, "starcoder")
        
        assert result1.count == result2.count
        assert result1.model_name == result2.model_name
```

### Integration Testing

Test component interactions.

```python
# tests/integration/test_token_analysis_integration.py
import pytest
from core.token_analyzer import SimpleTokenCounter
from core.text_compressor import SimpleTextCompressor
from core.experiments import TokenLimitExperiments
from tests.mocks.mock_config import MockConfiguration

class TestTokenAnalysisIntegration:
    """Integration tests for token analysis system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = MockConfiguration()
        self.token_counter = SimpleTokenCounter(config=self.config)
        self.compressor = SimpleTextCompressor(self.token_counter)
    
    def test_token_counting_and_compression_workflow(self):
        """Test complete token counting and compression workflow."""
        text = "This is a test text for token analysis and compression"
        
        # Count tokens
        token_info = self.token_counter.count_tokens(text, "starcoder")
        assert token_info.count > 0
        
        # Compress if needed
        if token_info.count > 5:
            result = self.compressor.compress_text(
                text=text,
                max_tokens=5,
                model_name="starcoder",
                strategy="truncation"
            )
            
            assert result.compressed_tokens <= 5
            assert result.compression_ratio <= 1.0
    
    @pytest.mark.asyncio
    async def test_experiment_workflow(self):
        """Test complete experiment workflow."""
        # This would require actual ML client setup
        # For now, we'll test the structure
        pass
```

## Development Workflow

### Git Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/token-analysis-improvements
   ```

2. **Make Changes**
   - Write tests first (TDD)
   - Implement feature
   - Update documentation

3. **Run Quality Checks**
   ```bash
   make quality-check
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: improve token analysis accuracy

   - Add ML-based token counting
   - Implement hybrid approach
   - Add comprehensive tests
   - Update documentation"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/token-analysis-improvements
   ```

### Commit Message Format

Use conventional commit format:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

#### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build/tooling changes

#### Examples

```bash
feat(token-analyzer): add ML-based token counting
fix(compressor): handle edge case in truncation
docs(api): update token counting examples
refactor(domain): extract value objects
test(analyzer): add property-based tests
```

## Pre-commit Hooks

### Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/pycqa/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-r, ., -f, json]
```

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

## Documentation Standards

### Docstring Format

Use Google-style docstrings:

```python
def count_tokens(
    text: str,
    model_name: str,
    method: str = "simple"
) -> TokenInfo:
    """
    Count tokens in text using specified method.
    
    This function analyzes the input text and returns token count information
    using the specified counting method and model.
    
    Args:
        text: Text to analyze for token counting
        model_name: Name of the model to use for counting
        method: Counting method to use ("simple", "accurate", "hybrid")
        
    Returns:
        TokenInfo: Token count information with metadata
        
    Raises:
        ValidationError: If text is empty or model_name is invalid
        TokenAnalysisError: If token counting fails
        
    Example:
        >>> counter = SimpleTokenCounter()
        >>> result = counter.count_tokens("Hello world", "starcoder")
        >>> print(result.count)
        2
    """
    pass
```

### README Standards

Include these sections in README files:

1. **Project Description**: Clear, concise description
2. **Features**: Key capabilities and benefits
3. **Installation**: Step-by-step installation
4. **Quick Start**: Basic usage examples
5. **API Reference**: Link to detailed API docs
6. **Contributing**: How to contribute
7. **License**: License information

### Code Comments

Use comments sparingly and focus on "why" not "what":

```python
def calculate_compression_ratio(original: int, compressed: int) -> float:
    """Calculate compression ratio."""
    # Avoid division by zero
    if original == 0:
        return 0.0
    
    return compressed / original

def optimize_for_production(text: str) -> str:
    """Optimize text for production use."""
    # Use aggressive compression for production to reduce costs
    # This trades some quality for significant token reduction
    return compress_text(text, target_ratio=0.3, strategy="aggressive")
```

## Performance Guidelines

### Optimization Principles

1. **Measure First**: Profile before optimizing
2. **Optimize Hot Paths**: Focus on frequently used code
3. **Cache Results**: Cache expensive computations
4. **Use Appropriate Data Structures**: Choose efficient data structures
5. **Avoid Premature Optimization**: Don't optimize until you have data

### Performance Monitoring

```python
import time
from functools import wraps
from typing import Callable, Any

def measure_performance(func: Callable) -> Callable:
    """Decorator to measure function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger.info(
            "performance_measurement",
            function=func.__name__,
            duration=end_time - start_time,
            args_count=len(args),
            kwargs_count=len(kwargs)
        )
        
        return result
    return wrapper

@measure_performance
def count_tokens(text: str) -> int:
    """Count tokens with performance monitoring."""
    return len(text.split())
```

### Memory Management

```python
import gc
from typing import List, Generator

def process_large_dataset(texts: List[str]) -> Generator[TokenInfo, None, None]:
    """Process large dataset with memory management."""
    for i, text in enumerate(texts):
        # Process text
        result = count_tokens(text)
        yield result
        
        # Clean up memory every 1000 items
        if i % 1000 == 0:
            gc.collect()

def batch_process_texts(texts: List[str], batch_size: int = 100) -> List[TokenInfo]:
    """Process texts in batches to manage memory."""
    results = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_results = [count_tokens(text) for text in batch]
        results.extend(batch_results)
        
        # Clean up after each batch
        gc.collect()
    
    return results
```

## Conclusion

Following these development practices ensures:

- **Code Quality**: Clean, maintainable, and readable code
- **Reliability**: Comprehensive testing and error handling
- **Performance**: Optimized and monitored code
- **Collaboration**: Clear standards for team development
- **Documentation**: Well-documented and understandable code

For additional examples and best practices, refer to the project's source code and test files.
