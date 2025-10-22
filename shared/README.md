# AI Challenge SDK Documentation

## Overview

The AI Challenge SDK (`shared/`) provides a unified interface for interacting with both local and external language models. It eliminates code duplication across projects and provides a consistent API for model operations.

## Features

- **Unified Model Interface**: Single client for all model types (local and external)
- **Centralized Configuration**: All model configurations in one place
- **Standardized Exceptions**: Consistent error handling across projects
- **Type Safety**: Full type hints and validation
- **Async Support**: Built-in async/await support
- **Extensible**: Easy to add new models and features

## Quick Start

### Basic Usage

```python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from shared.clients.unified_client import UnifiedModelClient
from shared.config.models import MODEL_CONFIGS

async def main():
    # Initialize client
    client = UnifiedModelClient()
    
    # Make a request to a local model
    response = await client.make_request("qwen", "Hello, how are you?")
    print(f"Response: {response.response}")
    print(f"Tokens: {response.total_tokens}")
    
    # Check model availability
    is_available = await client.check_availability("mistral")
    print(f"Mistral available: {is_available}")
    
    # Close client
    await client.close()

# Run the example
import asyncio
asyncio.run(main())
```

### Using with Context Manager

```python
async def main():
    async with UnifiedModelClient() as client:
        response = await client.make_request("tinyllama", "What is Python?")
        print(response.response)
```

## Configuration

### Model Configuration

All model configurations are centralized in `shared/config/models.py`:

```python
MODEL_CONFIGS = {
    "qwen": {
        "type": "local",
        "port": 8000,
        "url": "http://localhost:8000",
        "display_name": "Qwen-4B",
        "description": "Быстрые ответы, хорошее качество"
    },
    "mistral": {
        "type": "local", 
        "port": 8001,
        "url": "http://localhost:8001",
        "display_name": "Mistral-7B",
        "description": "Высокое качество, рекомендована"
    },
    "tinyllama": {
        "type": "local",
        "port": 8002, 
        "url": "http://localhost:8002",
        "display_name": "TinyLlama-1.1B",
        "description": "Компактная, быстрая"
    },
    "perplexity": {
        "type": "external",
        "url": "https://api.perplexity.ai/chat/completions",
        "display_name": "Perplexity Sonar",
        "description": "Внешний API"
    },
    "chadgpt": {
        "type": "external",
        "url": "https://ask.chadgpt.ru/api/public/gpt-5-mini",
        "display_name": "ChadGPT", 
        "description": "Внешний API"
    }
}
```

### Constants

Common constants are available in `shared/config/constants.py`:

```python
DEFAULT_TIMEOUT = 120.0
DEFAULT_MAX_TOKENS = 10000
DEFAULT_TEMPERATURE = 0.7
QUICK_TIMEOUT = 5.0
TEST_TIMEOUT = 30.0
```

## API Reference

### UnifiedModelClient

The main client class for interacting with models.

#### Constructor

```python
UnifiedModelClient(timeout: float = DEFAULT_TIMEOUT)
```

#### Methods

##### `make_request(model_name: str, prompt: str, max_tokens: int = DEFAULT_MAX_TOKENS, temperature: float = DEFAULT_TEMPERATURE) -> ModelResponse`

Make a request to a specific model.

**Parameters:**
- `model_name`: Name of the model (e.g., "qwen", "mistral", "perplexity")
- `prompt`: The input prompt
- `max_tokens`: Maximum tokens to generate (default: 10000)
- `temperature`: Sampling temperature (default: 0.7)

**Returns:** `ModelResponse` object with response data

**Raises:**
- `ModelConfigurationError`: If model is not configured
- `ModelConnectionError`: If connection fails
- `ModelTimeoutError`: If request times out
- `ModelRequestError`: If request fails

##### `check_availability(model_name: str) -> bool`

Check if a model is available.

**Parameters:**
- `model_name`: Name of the model to check

**Returns:** `True` if model is available, `False` otherwise

##### `check_all_availability() -> Dict[str, bool]`

Check availability of all configured models.

**Returns:** Dictionary mapping model names to availability status

##### `close() -> None`

Close the client and cleanup resources.

### ModelResponse

Response object containing model output and metadata.

```python
@dataclass
class ModelResponse:
    response: str              # The generated text
    input_tokens: int          # Number of input tokens
    response_tokens: int       # Number of generated tokens
    total_tokens: int          # Total tokens used
    model_name: str            # Name of the model used
    response_time: float       # Response time in seconds
```

## Error Handling

The SDK provides standardized exceptions for consistent error handling:

### Exception Hierarchy

```python
ModelClientError (Exception)
├── ModelConnectionError      # Connection issues
├── ModelRequestError         # Request failures
├── ModelTimeoutError         # Timeout errors
└── ModelConfigurationError   # Configuration issues
```

### Example Error Handling

```python
from shared.exceptions.model_errors import (
    ModelConnectionError, 
    ModelRequestError,
    ModelConfigurationError
)

async def safe_request(client, model_name, prompt):
    try:
        response = await client.make_request(model_name, prompt)
        return response
    except ModelConfigurationError as e:
        print(f"Configuration error: {e}")
    except ModelConnectionError as e:
        print(f"Connection error: {e}")
    except ModelRequestError as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
```

## Advanced Usage

### Extending the Client

You can extend `UnifiedModelClient` to add custom functionality:

```python
class CustomModelClient(UnifiedModelClient):
    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        super().__init__(timeout)
        self.conversation_history = []
    
    async def chat_with_history(self, model_name: str, prompt: str):
        # Add to history
        self.conversation_history.append({"role": "user", "content": prompt})
        
        # Make request
        response = await self.make_request(model_name, prompt)
        
        # Add response to history
        self.conversation_history.append({"role": "assistant", "content": response.response})
        
        return response
    
    def clear_history(self):
        self.conversation_history = []
```

### Batch Processing

```python
async def test_all_models():
    """Test all available models with the same prompt."""
    async with UnifiedModelClient() as client:
        prompt = "What is artificial intelligence?"
        
        # Check availability first
        availability = await client.check_all_availability()
        
        for model_name, is_available in availability.items():
            if is_available:
                try:
                    response = await client.make_request(model_name, prompt)
                    print(f"{model_name}: {response.response[:100]}...")
                except Exception as e:
                    print(f"{model_name}: Error - {e}")
            else:
                print(f"{model_name}: Not available")
```

## Integration Examples

### Day 05 Integration

```python
# In terminal_chat_v5.py
class LocalModelClient(UnifiedModelClient):
    def __init__(self, model_name: str):
        super().__init__(timeout=None)
        self.model_name = model_name
        self.conversation_history = []
    
    async def chat(self, messages: list, max_tokens: int = DEFAULT_MAX_TOKENS, 
                   temperature: float = DEFAULT_TEMPERATURE, use_history: bool = False) -> dict:
        # Convert messages to prompt
        user_content = "\n".join([msg["content"] for msg in messages if msg["role"] == "user"])
        
        # Make request using SDK
        response = await self.make_request(self.model_name, user_content, max_tokens, temperature)
        
        # Handle history if needed
        if use_history:
            self.conversation_history.extend(messages)
            self.conversation_history.append({
                "role": "assistant", 
                "content": response.response
            })
        
        return {
            "response": response.response,
            "input_tokens": response.input_tokens,
            "response_tokens": response.response_tokens,
            "total_tokens": response.total_tokens
        }
```

### Day 06 Integration

```python
# In model_client.py
class LocalModelClient(UnifiedModelClient):
    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        super().__init__(timeout)
    
    async def _make_request(self, model_name: str, prompt: str) -> ModelResponse:
        """Backward compatibility method."""
        return await self.make_request(model_name, prompt)
    
    async def test_all_models(self, riddles: List[Dict]) -> Dict[str, List[Dict]]:
        """Test all local models with riddles."""
        results = {}
        
        for model_name in MODEL_CONFIGS.keys():
            if MODEL_CONFIGS[model_name]["type"] == "local":
                results[model_name] = []
                
                for riddle in riddles:
                    try:
                        response = await self.make_request(model_name, riddle["text"])
                        results[model_name].append({
                            "riddle": riddle,
                            "response": response.response,
                            "tokens": response.total_tokens,
                            "time": response.response_time
                        })
                    except Exception as e:
                        results[model_name].append({
                            "riddle": riddle,
                            "error": str(e)
                        })
        
        return results
```

## Testing

The SDK includes comprehensive tests with 98.59% coverage:

```bash
# Run SDK tests
cd shared
python -m pytest tests/ -v --cov=shared --cov-report=html

# Run integration tests
cd ../day_05
python -m pytest tests/ -v

cd ../day_06  
python -m pytest tests/ -v
```

## Migration Guide

### From Day 05

1. **Replace LocalModelClient**: Inherit from `UnifiedModelClient` instead of implementing your own
2. **Update Imports**: Import from `shared` modules
3. **Use Centralized Config**: Replace hardcoded URLs with `MODEL_CONFIGS`
4. **Update Tests**: Mock `make_request` instead of HTTP calls

### From Day 06

1. **Remove Base Classes**: Use `UnifiedModelClient` instead of custom base classes
2. **Update Constants**: Import from `shared.config.constants`
3. **Simplify Error Handling**: Use standardized exceptions
4. **Update Tests**: Adjust for new API

## Best Practices

1. **Always Use Context Managers**: Ensure proper cleanup
2. **Handle Exceptions**: Use specific exception types
3. **Check Availability**: Verify model availability before making requests
4. **Use Type Hints**: Leverage full type safety
5. **Test Thoroughly**: Write tests for all custom extensions

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `shared` directory is in Python path
2. **Model Not Found**: Check `MODEL_CONFIGS` for correct model names
3. **Connection Errors**: Verify local models are running
4. **Timeout Issues**: Adjust timeout values for slow models

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# SDK will show detailed request/response information
```

## Contributing

When adding new models or features:

1. Update `MODEL_CONFIGS` in `shared/config/models.py`
2. Add tests in `shared/tests/`
3. Update documentation
4. Ensure backward compatibility
5. Run full test suite

## License

This SDK is part of the AI Challenge project and follows the same license terms.
