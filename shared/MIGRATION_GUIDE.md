# Migration Guide: From Day 07/Day 08 to SDK Agents

## Overview

This guide helps you migrate from the day-specific agent implementations (day_07/day_08) to the new unified SDK agentic architecture. The migration maintains full backward compatibility while providing enhanced functionality and better maintainability.

## Migration Benefits

- **Unified Interface**: Single SDK for all agent operations
- **Enhanced Orchestration**: Advanced workflow patterns and coordination
- **Better Error Handling**: Comprehensive exception hierarchy
- **Type Safety**: Full Pydantic schema validation
- **Extensibility**: Easy to add new agents and patterns
- **Testing**: Comprehensive test coverage and mocking support

## Quick Migration Checklist

- [ ] Update imports to use `shared_package.agents`
- [ ] Replace direct API calls with `AgentRequest`/`AgentResponse` schemas
- [ ] Use `DirectAdapter` for local operations
- [ ] Update error handling to use SDK exceptions
- [ ] Leverage orchestration patterns for complex workflows
- [ ] Update tests to use SDK mocking

## Detailed Migration Steps

### 1. Import Changes

#### Before (Day 07/Day 08)
```python
# Day 07 approach
from day_07.agents.code_generator import CodeGeneratorAgent
from day_07.agents.code_reviewer import CodeReviewerAgent

# Day 08 approach
from day_08.agents.code_generator_adapter import CodeGeneratorAdapter
from day_08.agents.code_reviewer_adapter import CodeReviewerAdapter
```

#### After (SDK Agents)
```python
# New SDK approach
from shared_package.agents import (
    CodeGeneratorAgent,
    CodeReviewerAgent,
    AgentRequest,
    AgentResponse
)
from shared_package.orchestration.adapters import DirectAdapter
from shared_package.clients.unified_client import UnifiedModelClient
```

### 2. Agent Initialization

#### Before (Day 07)
```python
# Direct agent creation
generator = CodeGeneratorAgent()
reviewer = CodeReviewerAgent()

# Direct API calls
result = await generator.generate_code(prompt)
```

#### Before (Day 08)
```python
# Adapter pattern
generator_adapter = CodeGeneratorAdapter()
reviewer_adapter = CodeReviewerAdapter()

# Adapter calls
result = await generator_adapter.generate_code(prompt)
```

#### After (SDK Agents)
```python
# SDK agent initialization
async with UnifiedModelClient() as client:
    generator = CodeGeneratorAgent(client, adapter=DirectAdapter())
    reviewer = CodeReviewerAgent(client, adapter=DirectAdapter())
    
    # Structured request/response
    request = AgentRequest(
        task_id="gen_001",
        task_type="code_generation",
        task=prompt,
        context={"language": "python"}
    )
    
    result = await generator.process(request)
```

### 3. Request/Response Handling

#### Before (Day 07/Day 08)
```python
# Simple string-based requests
prompt = "Generate a Python function"
result = await agent.generate_code(prompt)

# Direct string responses
if result:
    print(f"Generated: {result}")
else:
    print("Generation failed")
```

#### After (SDK Agents)
```python
# Structured requests with metadata
request = AgentRequest(
    task_id="gen_001",
    task_type="code_generation",
    task="Generate a Python function",
    context={
        "language": "python",
        "style": "clean",
        "include_docstring": True
    },
    timestamp=datetime.now()
)

# Structured responses with metadata
response = await agent.process(request)

if response.success:
    print(f"Generated: {response.result}")
    print(f"Quality: {response.metadata.quality_metrics.score}")
    print(f"Model: {response.metadata.model_name}")
else:
    print(f"Error: {response.error}")
```

### 4. Error Handling

#### Before (Day 07/Day 08)
```python
# Basic error handling
try:
    result = await agent.generate_code(prompt)
    if not result:
        print("Generation failed")
except Exception as e:
    print(f"Error: {e}")
```

#### After (SDK Agents)
```python
# Comprehensive error handling
from shared_package.exceptions.model_errors import (
    ModelConnectionError,
    ModelRequestError,
    ModelTimeoutError
)

try:
    response = await agent.process(request)
    if not response.success:
        print(f"Agent error: {response.error}")
except ModelConnectionError as e:
    print(f"Connection error: {e}")
except ModelRequestError as e:
    print(f"Request error: {e}")
except ModelTimeoutError as e:
    print(f"Timeout error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### 5. Workflow Orchestration

#### Before (Day 07/Day 08)
```python
# Manual workflow coordination
generator = CodeGeneratorAgent()
reviewer = CodeReviewerAgent()

# Generate code
code = await generator.generate_code(prompt)
if code:
    # Review code
    review = await reviewer.review_code(code)
    if review:
        print(f"Code: {code}")
        print(f"Review: {review}")
```

#### After (SDK Agents)
```python
# Orchestrated workflow
from shared_package.orchestration import SequentialOrchestrator

async with UnifiedModelClient() as client:
    generator = CodeGeneratorAgent(client, adapter=DirectAdapter())
    reviewer = CodeReviewerAgent(client, adapter=DirectAdapter())
    
    orchestrator = SequentialOrchestrator(DirectAdapter())
    
    request = AgentRequest(
        task_id="workflow_001",
        task_type="code_generation",
        task=prompt,
        context={"language": "python"}
    )
    
    # Execute workflow
    results = await orchestrator.execute(request, [generator, reviewer])
    
    for i, result in enumerate(results):
        if result.success:
            print(f"Step {i+1}: {result.result[:100]}...")
        else:
            print(f"Step {i+1} failed: {result.error}")
```

### 6. Configuration Management

#### Before (Day 07/Day 08)
```python
# Hardcoded configurations
MODEL_URLS = {
    "qwen": "http://localhost:8000",
    "mistral": "http://localhost:8001"
}

# Manual configuration
generator = CodeGeneratorAgent(model_url=MODEL_URLS["qwen"])
```

#### After (SDK Agents)
```python
# Centralized configuration
from shared_package.config.models import MODEL_CONFIGS
from shared_package.config.agents import AgentConfig

# Use centralized config
async with UnifiedModelClient() as client:
    config = AgentConfig(
        max_tokens=5000,
        temperature=0.3,
        timeout=60.0
    )
    
    generator = CodeGeneratorAgent(
        client, 
        config=config,
        adapter=DirectAdapter()
    )
```

### 7. Testing Updates

#### Before (Day 07/Day 08)
```python
# Basic mocking
from unittest.mock import patch, AsyncMock

@patch('day_07.agents.code_generator.requests.post')
async def test_generator(mock_post):
    mock_post.return_value.json.return_value = {
        "response": "Generated code"
    }
    
    generator = CodeGeneratorAgent()
    result = await generator.generate_code("test")
    
    assert result == "Generated code"
```

#### After (SDK Agents)
```python
# Comprehensive SDK testing
import pytest
from unittest.mock import AsyncMock, MagicMock
from shared_package.agents import CodeGeneratorAgent, AgentRequest
from shared_package.clients.unified_client import UnifiedModelClient

@pytest.mark.asyncio
async def test_generator():
    # Mock client
    mock_client = MagicMock(spec=UnifiedModelClient)
    mock_client.make_request = AsyncMock(return_value=ModelResponse(
        response="Generated code",
        response_tokens=10,
        input_tokens=5,
        total_tokens=15,
        model_name="qwen",
        response_time=1.0
    ))
    
    # Test agent
    agent = CodeGeneratorAgent(mock_client)
    request = AgentRequest(
        task_id="test_001",
        task_type="code_generation",
        task="test prompt"
    )
    
    response = await agent.process(request)
    
    assert response.success is True
    assert response.result == "Generated code"
    assert response.metadata.model_name == "qwen"
```

## Advanced Migration Patterns

### 1. Custom Agent Implementation

#### Before (Day 07/Day 08)
```python
# Custom agent extending base classes
class CustomAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_type = "custom"
    
    async def process(self, input_data):
        # Custom processing logic
        return processed_result
```

#### After (SDK Agents)
```python
# Custom agent extending SDK BaseAgent
from shared_package.agents import BaseAgent, AgentRequest, AgentResponse

class CustomAgent(BaseAgent):
    def __init__(self, client, config=None):
        super().__init__(client, config)
        self.agent_name = "custom_agent"
    
    async def process(self, request: AgentRequest) -> AgentResponse:
        # Custom processing logic using SDK client
        response = await self.client.make_request(
            "qwen", 
            request.task,
            max_tokens=self.config.max_tokens
        )
        
        return AgentResponse(
            task_id=request.task_id,
            result=response.response,
            success=True,
            metadata=self._create_metadata(
                request.task_type,
                "qwen",
                request.task_id
            )
        )
```

### 2. Parallel Processing

#### Before (Day 07/Day 08)
```python
# Manual parallel processing
import asyncio

async def parallel_generation():
    tasks = []
    for model in ["qwen", "mistral", "tinyllama"]:
        agent = CodeGeneratorAgent(model=model)
        task = agent.generate_code(prompt)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results
```

#### After (SDK Agents)
```python
# Orchestrated parallel processing
from shared_package.orchestration import ParallelOrchestrator

async def parallel_generation():
    async with UnifiedModelClient() as client:
        agents = [
            CodeGeneratorAgent(client, model_name="qwen"),
            CodeGeneratorAgent(client, model_name="mistral"),
            CodeGeneratorAgent(client, model_name="tinyllama")
        ]
        
        orchestrator = ParallelOrchestrator(DirectAdapter())
        
        request = AgentRequest(
            task_id="parallel_001",
            task_type="code_generation",
            task=prompt,
            context={"language": "python"}
        )
        
        results = await orchestrator.execute(request, agents)
        return results
```

### 3. Distributed Processing

#### Before (Day 07/Day 08)
```python
# Manual HTTP calls for distributed processing
import aiohttp

async def distributed_generation():
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://remote-agent:8000/generate",
            json={"prompt": prompt}
        ) as response:
            result = await response.json()
            return result["generated_code"]
```

#### After (SDK Agents)
```python
# Adapter-based distributed processing
from shared_package.orchestration.adapters import RestAdapter

async def distributed_generation():
    async with UnifiedModelClient() as client:
        adapter = RestAdapter(base_url="http://remote-agent:8000")
        agent = CodeGeneratorAgent(client, adapter=adapter)
        
        request = AgentRequest(
            task_id="distributed_001",
            task_type="code_generation",
            task=prompt,
            context={"language": "python"}
        )
        
        response = await agent.process(request)
        return response.result
```

## Common Migration Issues and Solutions

### Issue 1: Import Errors
**Problem**: `ModuleNotFoundError` when importing SDK modules
**Solution**: Ensure `shared` directory is in Python path
```python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))
```

### Issue 2: Schema Validation Errors
**Problem**: `ValidationError` when creating requests
**Solution**: Use proper schema fields
```python
# Correct
request = AgentRequest(
    task_id="gen_001",  # Required
    task_type="code_generation",  # Required
    task="Generate code",  # Required
    context={"language": "python"}  # Optional
)

# Incorrect
request = AgentRequest(task="Generate code")  # Missing required fields
```

### Issue 3: Adapter Configuration
**Problem**: Agents not working with adapters
**Solution**: Always specify adapter parameter
```python
# Correct
agent = CodeGeneratorAgent(client, adapter=DirectAdapter())

# Incorrect
agent = CodeGeneratorAgent(client)  # Missing adapter
```

### Issue 4: Async Context Management
**Problem**: Client not properly closed
**Solution**: Use async context manager
```python
# Correct
async with UnifiedModelClient() as client:
    agent = CodeGeneratorAgent(client)
    response = await agent.process(request)

# Incorrect
client = UnifiedModelClient()
agent = CodeGeneratorAgent(client)
response = await agent.process(request)
# Forgot to close client
```

## Performance Considerations

### 1. Connection Pooling
The SDK automatically manages connection pooling for better performance:
```python
# SDK handles connection pooling internally
async with UnifiedModelClient() as client:
    # Multiple agents can share the same client
    generator = CodeGeneratorAgent(client)
    reviewer = CodeReviewerAgent(client)
```

### 2. Caching
Implement response caching for repeated requests:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_generation(prompt_hash):
    # Cache based on prompt hash
    pass
```

### 3. Batch Processing
Use orchestration for efficient batch processing:
```python
# Process multiple requests efficiently
orchestrator = ParallelOrchestrator(DirectAdapter())
results = await orchestrator.execute(request, agents)
```

## Migration Timeline

### Phase 1: Basic Migration (Week 1)
- [ ] Update imports and basic agent initialization
- [ ] Convert simple string-based requests to `AgentRequest`
- [ ] Update error handling to use SDK exceptions
- [ ] Run basic functionality tests

### Phase 2: Advanced Features (Week 2)
- [ ] Implement orchestration patterns
- [ ] Add adapter switching capabilities
- [ ] Update tests to use SDK mocking
- [ ] Performance optimization

### Phase 3: Production Deployment (Week 3)
- [ ] Full integration testing
- [ ] Performance benchmarking
- [ ] Documentation updates
- [ ] Team training

## Support and Resources

### Documentation
- [SDK README](README.md) - Complete SDK documentation
- [API Reference](docs/api_reference.md) - Detailed API documentation
- [Examples](examples/) - Code examples and patterns

### Testing
- [Test Suite](tests/) - Comprehensive test coverage
- [Test Utilities](tests/utils/) - Testing helpers and fixtures

### Community
- [Issues](https://github.com/your-repo/issues) - Bug reports and feature requests
- [Discussions](https://github.com/your-repo/discussions) - Community discussions

## Conclusion

The migration to SDK agents provides significant benefits in terms of maintainability, extensibility, and functionality. While the initial migration requires some effort, the long-term benefits make it worthwhile.

Key advantages:
- **Unified Architecture**: Single source of truth for agent logic
- **Enhanced Testing**: Comprehensive test coverage and mocking
- **Better Error Handling**: Structured exception hierarchy
- **Advanced Orchestration**: Sophisticated workflow patterns
- **Type Safety**: Full Pydantic schema validation
- **Extensibility**: Easy to add new agents and patterns

Follow this guide step by step, and you'll have a robust, maintainable agentic architecture that scales with your needs.
