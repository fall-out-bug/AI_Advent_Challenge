# Migration Guide

## Overview

This guide helps you migrate from previous versions of the Token Analysis System to the enhanced version with modern architecture, design patterns, and improved APIs.

## Migration Checklist

- [ ] Update imports and dependencies
- [ ] Update initialization patterns
- [ ] Update method calls and parameters
- [ ] Update error handling
- [ ] Update configuration
- [ ] Test migration with existing code
- [ ] Update documentation and examples

## Breaking Changes

### 1. Configuration Injection

**Before (v0.x)**:
```python
from core.token_analyzer import SimpleTokenCounter

# Direct initialization
counter = SimpleTokenCounter()
```

**After (v1.x)**:
```python
from core.token_analyzer import SimpleTokenCounter
from tests.mocks.mock_config import MockConfiguration

# Configuration injection required
config = MockConfiguration()
counter = SimpleTokenCounter(config=config)
```

**Migration Steps**:
1. Import configuration class
2. Create configuration instance
3. Pass configuration to constructor

### 2. Compression Method Changes

**Before (v0.x)**:
```python
from core.text_compressor import SimpleTextCompressor

compressor = SimpleTextCompressor(token_counter)

# Separate methods for each strategy
result = compressor.compress_by_truncation(text, max_tokens)
result = compressor.compress_by_keywords(text, max_tokens)
```

**After (v1.x)**:
```python
from core.text_compressor import SimpleTextCompressor

compressor = SimpleTextCompressor(token_counter)

# Unified method with strategy parameter
result = compressor.compress_text(text, max_tokens, strategy="truncation")
result = compressor.compress_text(text, max_tokens, strategy="keywords")
```

**Migration Steps**:
1. Replace `compress_by_truncation()` with `compress_text(strategy="truncation")`
2. Replace `compress_by_keywords()` with `compress_text(strategy="keywords")`
3. Add `model_name` parameter if needed

### 3. Experiment API Changes

**Before (v0.x)**:
```python
from core.experiments import TokenLimitExperiments

experiments = TokenLimitExperiments(model_client, token_counter, text_compressor)

# Direct method calls
results = await experiments.run_limit_exceeded_experiment("starcoder")
```

**After (v1.x)**:
```python
from core.experiments import TokenLimitExperiments

experiments = TokenLimitExperiments(model_client, token_counter, text_compressor)

# Same API, but enhanced with structured logging
results = await experiments.run_limit_exceeded_experiment("starcoder")
```

**Migration Steps**:
1. No changes needed for basic usage
2. Update logging configuration if using custom logging
3. Take advantage of new builder pattern for custom experiments

### 4. Error Handling Changes

**Before (v0.x)**:
```python
try:
    result = counter.count_tokens(text, model_name)
except Exception as e:
    print(f"Error: {e}")
```

**After (v1.x)**:
```python
from core.exceptions import TokenAnalysisError, ValidationError

try:
    result = counter.count_tokens(text, model_name)
except ValidationError as e:
    logger.error("validation_failed", error=str(e))
except TokenAnalysisError as e:
    logger.error("token_analysis_failed", error=str(e))
```

**Migration Steps**:
1. Import specific exception types
2. Handle exceptions by type
3. Use structured logging instead of print statements

## Non-Breaking Changes

### 1. Enhanced Data Models

**Before (v0.x)**:
```python
# Basic TokenInfo
token_info = counter.count_tokens(text, model_name)
print(f"Tokens: {token_info.count}")
```

**After (v1.x)**:
```python
# Enhanced TokenInfo with more fields
token_info = counter.count_tokens(text, model_name)
print(f"Tokens: {token_info.count}")
print(f"Method: {token_info.method}")
print(f"Confidence: {token_info.confidence}")
```

**Migration Steps**:
1. Existing code continues to work
2. Optionally use new fields for enhanced functionality

### 2. New Factory Methods

**Before (v0.x)**:
```python
# Direct instantiation
counter = SimpleTokenCounter()
compressor = SimpleTextCompressor(counter)
```

**After (v1.x)**:
```python
# Factory methods (optional)
from core.factories import TokenCounterFactory

counter = TokenCounterFactory.create_simple(config=config)
compressor = CompressionStrategyFactory.create(CompressionStrategy.TRUNCATION, counter)
```

**Migration Steps**:
1. Existing code continues to work
2. Optionally use factory methods for better organization

### 3. Enhanced Logging

**Before (v0.x)**:
```python
# Print statements
print(f"Processing text: {text}")
print(f"Tokens: {tokens}")
```

**After (v1.x)**:
```python
# Structured logging
from utils.logging import LoggerFactory

logger = LoggerFactory.create_logger(__name__)
logger.info("text_processing", text_length=len(text), tokens=tokens)
```

**Migration Steps**:
1. Replace print statements with structured logging
2. Use appropriate log levels (info, warning, error)
3. Include relevant context in log messages

## Step-by-Step Migration

### Step 1: Update Dependencies

```bash
# Update to new version
pip install -U token-analysis-system

# Or if using poetry
poetry update
```

### Step 2: Update Imports

**Before**:
```python
from core.token_analyzer import SimpleTokenCounter
from core.text_compressor import SimpleTextCompressor
```

**After**:
```python
from core.token_analyzer import SimpleTokenCounter
from core.text_compressor import SimpleTextCompressor
from tests.mocks.mock_config import MockConfiguration
from core.factories import TokenCounterFactory
```

### Step 3: Update Initialization

**Before**:
```python
# Old initialization
counter = SimpleTokenCounter()
compressor = SimpleTextCompressor(counter)
```

**After**:
```python
# New initialization with configuration
config = MockConfiguration()
counter = SimpleTokenCounter(config=config)
compressor = SimpleTextCompressor(counter)
```

### Step 4: Update Method Calls

**Before**:
```python
# Old compression methods
result = compressor.compress_by_truncation(text, max_tokens)
result = compressor.compress_by_keywords(text, max_tokens)
```

**After**:
```python
# New unified method
result = compressor.compress_text(text, max_tokens, strategy="truncation")
result = compressor.compress_text(text, max_tokens, strategy="keywords")
```

### Step 5: Update Error Handling

**Before**:
```python
try:
    result = counter.count_tokens(text, model_name)
except Exception as e:
    print(f"Error: {e}")
```

**After**:
```python
from core.exceptions import ValidationError, TokenAnalysisError

try:
    result = counter.count_tokens(text, model_name)
except ValidationError as e:
    logger.error("validation_failed", error=str(e))
except TokenAnalysisError as e:
    logger.error("token_analysis_failed", error=str(e))
```

### Step 6: Update Configuration

**Before**:
```python
# Hardcoded configuration
counter = SimpleTokenCounter()
```

**After**:
```python
# Configuration-based
config = MockConfiguration()
counter = SimpleTokenCounter(config=config)
```

## Migration Examples

### Example 1: Basic Token Counting

**Before**:
```python
from core.token_analyzer import SimpleTokenCounter

counter = SimpleTokenCounter()
text = "Hello, world!"
token_info = counter.count_tokens(text, "starcoder")
print(f"Tokens: {token_info.count}")
```

**After**:
```python
from core.token_analyzer import SimpleTokenCounter
from tests.mocks.mock_config import MockConfiguration

config = MockConfiguration()
counter = SimpleTokenCounter(config=config)
text = "Hello, world!"
token_info = counter.count_tokens(text, "starcoder")
print(f"Tokens: {token_info.count}")
```

### Example 2: Text Compression

**Before**:
```python
from core.text_compressor import SimpleTextCompressor

compressor = SimpleTextCompressor(counter)
long_text = "This is a very long text..."
result = compressor.compress_by_truncation(long_text, 1000)
print(f"Compression ratio: {result.compression_ratio}")
```

**After**:
```python
from core.text_compressor import SimpleTextCompressor

compressor = SimpleTextCompressor(counter)
long_text = "This is a very long text..."
result = compressor.compress_text(long_text, 1000, strategy="truncation")
print(f"Compression ratio: {result.compression_ratio}")
```

### Example 3: Experiments

**Before**:
```python
from core.experiments import TokenLimitExperiments

experiments = TokenLimitExperiments(model_client, counter, compressor)
results = await experiments.run_limit_exceeded_experiment("starcoder")

for result in results:
    print(f"Experiment: {result.experiment_name}")
    print(f"Tokens: {result.total_tokens}")
```

**After**:
```python
from core.experiments import TokenLimitExperiments

experiments = TokenLimitExperiments(model_client, counter, compressor)
results = await experiments.run_limit_exceeded_experiment("starcoder")

for result in results:
    print(f"Experiment: {result.experiment_name}")
    print(f"Tokens: {result.total_tokens}")
    print(f"Response time: {result.response_time:.2f}s")
```

## Testing Migration

### 1. Run Existing Tests

```bash
# Run your existing test suite
python -m pytest tests/

# Check for any failures
```

### 2. Update Test Code

**Before**:
```python
def test_token_counting():
    counter = SimpleTokenCounter()
    result = counter.count_tokens("test", "starcoder")
    assert result.count > 0
```

**After**:
```python
def test_token_counting():
    config = MockConfiguration()
    counter = SimpleTokenCounter(config=config)
    result = counter.count_tokens("test", "starcoder")
    assert result.count > 0
```

### 3. Add New Tests

```python
def test_compression_strategies():
    config = MockConfiguration()
    counter = SimpleTokenCounter(config=config)
    compressor = SimpleTextCompressor(counter)
    
    text = "This is a test text for compression"
    result = compressor.compress_text(text, 10, strategy="truncation")
    
    assert result.compression_ratio < 1.0
    assert result.strategy_used == "truncation"
```

## Performance Considerations

### 1. Configuration Caching

**Before**:
```python
# Creating new instances frequently
for text in texts:
    counter = SimpleTokenCounter()
    result = counter.count_tokens(text, "starcoder")
```

**After**:
```python
# Reuse instances
config = MockConfiguration()
counter = SimpleTokenCounter(config=config)

for text in texts:
    result = counter.count_tokens(text, "starcoder")
```

### 2. Async Operations

**Before**:
```python
# Synchronous operations
results = []
for text in texts:
    result = counter.count_tokens(text, "starcoder")
    results.append(result)
```

**After**:
```python
# Async operations for better performance
async def process_texts(texts):
    tasks = [counter.count_tokens(text, "starcoder") for text in texts]
    results = await asyncio.gather(*tasks)
    return results
```

## Troubleshooting

### Common Issues

#### 1. Configuration Not Found

**Error**: `TypeError: __init__() missing 1 required positional argument: 'config'`

**Solution**:
```python
# Add configuration
config = MockConfiguration()
counter = SimpleTokenCounter(config=config)
```

#### 2. Method Not Found

**Error**: `AttributeError: 'SimpleTextCompressor' object has no attribute 'compress_by_truncation'`

**Solution**:
```python
# Use new method signature
result = compressor.compress_text(text, max_tokens, strategy="truncation")
```

#### 3. Import Errors

**Error**: `ImportError: cannot import name 'MockConfiguration'`

**Solution**:
```python
# Ensure you're importing from the correct location
from tests.mocks.mock_config import MockConfiguration
```

### Getting Help

1. **Check the API documentation**: [api.md](api.md)
2. **Review the architecture**: [architecture.md](architecture.md)
3. **Run the test suite**: `make test`
4. **Check the examples**: [README.md](README.md)

## Rollback Plan

If you need to rollback to the previous version:

1. **Revert code changes**:
   ```bash
   git revert <commit-hash>
   ```

2. **Downgrade dependencies**:
   ```bash
   pip install token-analysis-system==0.x.x
   ```

3. **Restore configuration**:
   ```bash
   cp config/backup.yaml config/model_limits.yaml
   ```

## Conclusion

The migration to the enhanced Token Analysis System provides:

- **Better Architecture**: SOLID principles and design patterns
- **Improved Reliability**: Error handling and resilience features
- **Enhanced Performance**: Optimized algorithms and async support
- **Better Maintainability**: Clean code and comprehensive tests
- **Future-Proof Design**: Extensible and configurable architecture

While there are some breaking changes, the migration process is straightforward and the benefits significantly outweigh the effort required.

For additional support during migration, please refer to the documentation or create an issue in the project repository.
