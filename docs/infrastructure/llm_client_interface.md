# LLM Client Interface Specification

## Overview

The `LLMClient` Protocol defines the canonical interface for all LLM (Large Language Model) client implementations in the system. This Protocol serves as the adapter interface that enables dependency injection and testability.

## Location

- **Protocol Definition**: `src/infrastructure/llm/clients/llm_client.py`
- **Export**: `src/infrastructure/llm/clients/__init__.py`

## Interface Definition

```python
@runtime_checkable
class LLMClient(Protocol):
    """Protocol for LLM client implementations."""
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 256,
        stop_sequences: list[str] | None = None,
    ) -> str:
        """Generate a text completion for a prompt.
        
        Args:
            prompt: Input prompt text.
            temperature: Sampling temperature (0.0-2.0). Higher = more creative.
            max_tokens: Maximum tokens to generate.
            stop_sequences: Optional list of stop sequences to end generation.
            
        Returns:
            Generated text completion.
            
        Raises:
            Exception: On generation errors (implementation-specific).
        """
        ...
    
    async def batch_generate(
        self,
        prompts: list[str],
        temperature: float = 0.2,
        max_tokens: int = 256,
        stop_sequences: list[str] | None = None,
    ) -> list[str]:
        """Generate completions for multiple prompts in parallel.
        
        Args:
            prompts: List of input prompts.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens per completion.
            stop_sequences: Optional stop sequences.
            
        Returns:
            List of generated texts (one per prompt).
            
        Raises:
            Exception: On batch generation errors.
        """
        ...
```

## Implementations

### ResilientLLMClient

**Location**: `src/infrastructure/llm/clients/resilient_client.py`

**Features**:
- Wraps primary LLM client with automatic fallback to `FallbackLLMClient` on errors
- Implements exponential backoff retry logic
- Records Prometheus metrics for request duration, success/failure counts, and fallback usage
- Handles connection errors, timeouts, rate limits, and server errors

**Configuration**:
- `url`: Optional LLM service URL (defaults to `Settings.llm_url`)
- `max_retries`: Maximum retry attempts (default: 3)
- `initial_backoff`: Initial backoff delay in seconds (default: 1.0)
- `max_backoff`: Maximum backoff delay in seconds (default: 60.0)
- `backoff_factor`: Multiplier for exponential backoff (default: 2.0)
- `timeout`: Request timeout in seconds (default: 120.0)

**Usage**:
```python
from src.infrastructure.llm.clients import ResilientLLMClient
from src.infrastructure.config.settings import get_settings

settings = get_settings()
client = ResilientLLMClient(url=settings.llm_url, timeout=settings.summarizer_timeout_seconds_long)
result = await client.generate(prompt="Summarize this text", temperature=0.2, max_tokens=500)
```

### HTTPLLMClient

**Location**: `src/infrastructure/clients/llm_client.py`

**Features**:
- Direct HTTP client for Mistral/OpenAI-compatible chat APIs
- Automatically detects Docker vs host access and adjusts URL accordingly
- Supports both `/chat` and `/v1/chat/completions` endpoints

**Configuration**:
- `url`: Base URL of the LLM service (defaults to `Settings.llm_url` or `http://localhost:8001`)
- `timeout`: Request timeout in seconds (default: 30.0)
- `model`: Model name (defaults to `Settings.llm_model` or `mistralai/Mistral-7B-Instruct-v0.2`)

### FallbackLLMClient

**Location**: `src/infrastructure/clients/llm_client.py`

**Features**:
- Trivial fallback implementation that returns context-aware responses
- Analyzes the prompt to determine if it's for summarization or intent parsing
- Returns appropriate fallback format without making actual LLM calls
- Used as fallback when primary client fails

## Parameter Defaults

The Protocol defines standard default values for all methods:

- `temperature`: `0.2` (deterministic output)
- `max_tokens`: `256` (conservative token limit)
- `stop_sequences`: `None` (no stop sequences)

Implementations may override these defaults, but should respect them when not specified.

## Runtime Checking

The Protocol is marked with `@runtime_checkable`, allowing `isinstance()` checks:

```python
from src.infrastructure.llm.clients import LLMClient

if isinstance(client, LLMClient):
    # client implements the LLMClient Protocol
    result = await client.generate(prompt="Test")
```

## Factory Usage

The recommended way to create LLM clients is through factory functions in `src/infrastructure/di/factories.py`:

```python
from src.infrastructure.di.factories import create_adaptive_summarizer

# Factory creates ResilientLLMClient with appropriate configuration
summarizer = create_adaptive_summarizer()
```

## Settings Integration

LLM clients should use `Settings` for configuration:

- `llm_url`: Base URL for LLM service
- `llm_model`: Model name
- `summarizer_timeout_seconds_long`: Timeout for long-running summarization tasks

## Testing

When testing code that depends on `LLMClient`, use a mock implementation:

```python
from unittest.mock import AsyncMock, MagicMock

mock_client = MagicMock(spec=LLMClient)
mock_client.generate = AsyncMock(return_value="Mocked response")
mock_client.batch_generate = AsyncMock(return_value=["Response 1", "Response 2"])
```

## Migration Notes

**Legacy Protocol**: `src/infrastructure/clients/llm_client.py` also defines an `LLMClient` Protocol, but it's missing `batch_generate()` and `stop_sequences` parameters. New code should use the Protocol from `src/infrastructure/llm/clients/llm_client.py`.

**Compatibility**: The legacy Protocol is still used in some places, but implementations like `ResilientLLMClient` support both interfaces for backward compatibility.

## See Also

- `src/infrastructure/llm/summarizers/`: Summarizers that use `LLMClient`
- `src/infrastructure/di/factories.py`: Factory functions for creating LLM clients
- `src/infrastructure/config/settings.py`: Configuration settings for LLM clients

