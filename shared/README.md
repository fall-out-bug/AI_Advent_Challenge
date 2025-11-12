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

## Agentic Architecture

The SDK now includes a comprehensive agentic architecture that supports both direct Python async calls and REST API patterns via adapter interfaces. This enables sophisticated agent coordination patterns and workflow orchestration.

### Core Agent Components

#### BaseAgent

The foundation of all agents, providing a unified async interface:

```python
from shared_package.agents import BaseAgent, AgentRequest, AgentResponse

class CustomAgent(BaseAgent):
    def __init__(self, client):
        super().__init__(client)
        self.agent_name = "custom_agent"

    async def process(self, request: AgentRequest) -> AgentResponse:
        # Implement your agent logic here
        response = await self.client.make_request("qwen", request.task)
        return AgentResponse(
            task_id=request.task_id,
            result=response.response,
            metadata=TaskMetadata(
                agent_name=self.agent_name,
                model_used="qwen",
                processing_time=response.response_time
            )
        )
```

#### Code Generation Agent

Specialized agent for generating code with intelligent prompt engineering:

```python
from shared_package.agents import CodeGeneratorAgent, AgentRequest

async def generate_code():
    async with UnifiedModelClient() as client:
        agent = CodeGeneratorAgent(client)

        request = AgentRequest(
            task_id="gen_001",
            task_type="code_generation",
            task="Create a Python function to calculate fibonacci numbers",
            context={
                "language": "python",
                "style": "recursive",
                "include_docstring": True
            }
        )

        response = await agent.process(request)
        print(f"Generated code: {response.result}")
        print(f"Quality score: {response.metadata.quality_metrics.score}")
```

#### Code Review Agent

Intelligent code review agent with quality analysis and scoring:

```python
from shared_package.agents import CodeReviewerAgent, AgentRequest

async def review_code():
    async with UnifiedModelClient() as client:
        agent = CodeReviewerAgent(client)

        code_to_review = """
        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
        """

        request = AgentRequest(
            task_id="review_001",
            task_type="code_review",
            task=code_to_review,
            context={
                "language": "python",
                "focus_areas": ["performance", "readability", "best_practices"]
            }
        )

        response = await agent.process(request)
        print(f"Review result: {response.result}")
        print(f"Quality metrics: {response.metadata.quality_metrics}")
```

### Orchestration Patterns

#### Sequential Orchestration

Execute agents in sequence for complex workflows:

```python
from shared_package.orchestration import SequentialOrchestrator
from shared_package.orchestration.adapters import DirectAdapter

async def sequential_workflow():
    async with UnifiedModelClient() as client:
        # Create agents
        generator = CodeGeneratorAgent(client)
        reviewer = CodeReviewerAgent(client)

        # Create orchestrator
        orchestrator = SequentialOrchestrator(
            agents=[generator, reviewer],
            adapter=DirectAdapter()
        )

        # Execute workflow
        request = AgentRequest(
            task_id="workflow_001",
            task_type="code_generation",
            task="Create a REST API endpoint for user authentication",
            context={"framework": "fastapi", "include_tests": True}
        )

        results = await orchestrator.execute(request)

        print("Generation result:", results[0].result)
        print("Review result:", results[1].result)
```

#### Parallel Orchestration

Execute multiple agents concurrently for comparison:

```python
from shared_package.orchestration import ParallelOrchestrator

async def parallel_comparison():
    async with UnifiedModelClient() as client:
        # Create multiple generators for different models
        agents = [
            CodeGeneratorAgent(client, model_preference="qwen"),
            CodeGeneratorAgent(client, model_preference="mistral"),
            CodeGeneratorAgent(client, model_preference="tinyllama")
        ]

        orchestrator = ParallelOrchestrator(
            agents=agents,
            adapter=DirectAdapter()
        )

        request = AgentRequest(
            task_id="compare_001",
            task_type="code_generation",
            task="Implement a binary search algorithm",
            context={"language": "python", "include_comments": True}
        )

        results = await orchestrator.execute(request)

        for i, result in enumerate(results):
            print(f"Model {i+1}: {result.result[:100]}...")
```

### Communication Adapters

The SDK supports flexible communication patterns through adapters:

#### Direct Adapter (Default)

```python
from shared_package.orchestration.adapters import DirectAdapter

# Direct async calls within the same process
adapter = DirectAdapter()
agent = CodeGeneratorAgent(client, adapter=adapter)
result = await agent.process(request)
```

#### REST Adapter

```python
from shared_package.orchestration.adapters import RestAdapter

# HTTP API calls for distributed agents
adapter = RestAdapter(base_url="http://localhost:8000")
agent = CodeGeneratorAgent(client, adapter=adapter)
result = await agent.process(request)
```

### Agent Configuration

Configure agents with specific parameters:

```python
from shared_package.config.agents import AgentConfig

# Custom agent configuration
config = AgentConfig(
    max_tokens=5000,
    temperature=0.3,
    timeout=60.0,
    retry_attempts=3
)

agent = CodeGeneratorAgent(client, config=config)
```

### Advanced Usage Examples

#### Custom Agent Implementation

```python
from shared_package.agents import BaseAgent, AgentRequest, AgentResponse
from shared_package.orchestration.adapters import DirectAdapter

class DocumentationAgent(BaseAgent):
    """Agent specialized in generating technical documentation."""

    def __init__(self, client, config=None):
        super().__init__(client, config)
        self.agent_name = "documentation_agent"
        self.adapter = DirectAdapter()

    async def process(self, request: AgentRequest) -> AgentResponse:
        """Generate documentation for the given code."""
        prompt = f"""
        Generate comprehensive documentation for the following code:

        {request.task}

        Include:
        - Function/class descriptions
        - Parameter documentation
        - Return value documentation
        - Usage examples
        - Error handling notes
        """

        response = await self.client.make_request(
            "mistral",
            prompt,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature
        )

        return AgentResponse(
            task_id=request.task_id,
            result=response.response,
            metadata=TaskMetadata(
                agent_name=self.agent_name,
                model_used="mistral",
                processing_time=response.response_time,
                quality_metrics=QualityMetrics(
                    score=0.95,  # High quality for documentation
                    readability=0.9,
                    completeness=0.95
                )
            )
        )
```

#### Workflow with Error Handling

```python
async def robust_workflow():
    """Example of workflow with comprehensive error handling."""
    async with UnifiedModelClient() as client:
        try:
            # Create agents
            generator = CodeGeneratorAgent(client)
            reviewer = CodeReviewerAgent(client)

            # Create orchestrator
            orchestrator = SequentialOrchestrator(
                agents=[generator, reviewer],
                adapter=DirectAdapter()
            )

            # Execute with error handling
            request = AgentRequest(
                task_id="robust_001",
                task_type="code_generation",
                task="Create a data validation function",
                context={"language": "python", "include_tests": True}
            )

            results = await orchestrator.execute(request)

            # Process results
            for i, result in enumerate(results):
                if result.success:
                    print(f"Step {i+1} completed successfully")
                    print(f"Result: {result.result[:200]}...")
                else:
                    print(f"Step {i+1} failed: {result.error}")

        except Exception as e:
            print(f"Workflow failed: {e}")
```

### Migration Guide

#### From Day 07/Day 08 to SDK Agents

**Before (Day 07/Day 08):**
```python
# Old approach with direct API calls
from day_07.agents.code_generator import CodeGeneratorAgent
from day_08.agents.code_generator_adapter import CodeGeneratorAdapter

adapter = CodeGeneratorAdapter()
result = await adapter.generate_code(prompt)
```

**After (SDK Agents):**
```python
# New approach with SDK agents
from shared_package.agents import CodeGeneratorAgent, AgentRequest
from shared_package.orchestration.adapters import DirectAdapter

async with UnifiedModelClient() as client:
    agent = CodeGeneratorAgent(client, adapter=DirectAdapter())

    request = AgentRequest(
        task_id="migration_001",
        task_type="code_generation",
        task=prompt,
        context={"language": "python"}
    )

    result = await agent.process(request)
```

#### Key Migration Steps

1. **Replace Direct Imports**: Use `shared_package.agents` instead of day-specific imports
2. **Update Request Format**: Use `AgentRequest` with proper schema
3. **Use Adapters**: Specify communication adapter (DirectAdapter for local, RestAdapter for distributed)
4. **Update Error Handling**: Use SDK exception hierarchy
5. **Leverage Orchestration**: Use orchestrators for complex workflows

#### Backward Compatibility

The SDK maintains full backward compatibility:
- Existing `UnifiedModelClient` API unchanged
- All model configurations preserved
- Exception hierarchy maintained
- No breaking changes to existing code

### Testing Agentic Architecture

```python
# Test individual agents
import pytest
from shared_package.agents import CodeGeneratorAgent, AgentRequest

@pytest.mark.asyncio
async def test_code_generator():
    async with UnifiedModelClient() as client:
        agent = CodeGeneratorAgent(client)

        request = AgentRequest(
            task_id="test_001",
            task_type="code_generation",
            task="Create a simple hello world function",
            context={"language": "python"}
        )

        response = await agent.process(request)

        assert response.success
        assert "def hello" in response.result
        assert response.metadata.agent_name == "code_generator"

# Test orchestration
@pytest.mark.asyncio
async def test_sequential_orchestration():
    async with UnifiedModelClient() as client:
        generator = CodeGeneratorAgent(client)
        reviewer = CodeReviewerAgent(client)

        orchestrator = SequentialOrchestrator(
            agents=[generator, reviewer],
            adapter=DirectAdapter()
        )

        request = AgentRequest(
            task_id="orchestration_test",
            task_type="code_generation",
            task="Create a sorting algorithm",
            context={"language": "python"}
        )

        results = await orchestrator.execute(request)

        assert len(results) == 2
        assert results[0].success  # Generation successful
        assert results[1].success  # Review successful
```

## License

This SDK is part of the AI Challenge project and follows the same license terms.
