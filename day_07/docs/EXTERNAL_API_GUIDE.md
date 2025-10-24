# External API Integration Guide

This guide explains how to integrate and use external AI API providers (like ChatGPT, Claude) with the StarCoder Multi-Agent System.

## Overview

The external API integration system allows you to:
- Use external AI services (ChatGPT, Claude) alongside local models
- Switch between providers dynamically at runtime
- Configure multiple providers with different settings
- Maintain the same interface for all providers

## Features

- **Multiple Provider Support**: ChatGPT (OpenAI), Claude (Anthropic)
- **Dynamic Switching**: Switch between providers at runtime
- **Unified Interface**: Same API for all providers (local and external)
- **Configuration Management**: Environment variables and JSON config files
- **Error Handling**: Comprehensive error handling and fallback strategies
- **Performance Monitoring**: Statistics and availability checking
- **CLI Management**: Command-line tool for provider management

## Quick Start

### 1. Set up API Keys

Set your API keys as environment variables:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### 2. Install Dependencies

```bash
pip install httpx click
```

### 3. Create Agents with External Providers

```python
from agents.core.code_generator import CodeGeneratorAgent
from agents.core.code_reviewer import CodeReviewerAgent

# Use ChatGPT
generator = CodeGeneratorAgent(
    model_name="gpt-3.5-turbo",
    external_provider="chatgpt"
)

# Use Claude
reviewer = CodeReviewerAgent(
    model_name="claude-3-sonnet-20240229",
    external_provider="claude"
)
```

### 4. Use Agents Normally

```python
from communication.message_schema import CodeGenerationRequest

request = CodeGenerationRequest(
    task_description="Create a fibonacci function",
    language="python"
)

result = await generator.generate_code(request)
```

## Configuration

### Environment Variables

```bash
# OpenAI
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # Optional

# Anthropic
export ANTHROPIC_API_KEY="your-key"
export ANTHROPIC_BASE_URL="https://api.anthropic.com"  # Optional
```

### JSON Configuration

Create `external_api_config.json`:

```json
{
  "providers": {
    "chatgpt": {
      "api_key": "your-openai-key",
      "base_url": "https://api.openai.com/v1",
      "models": ["gpt-3.5-turbo", "gpt-4"]
    },
    "claude": {
      "api_key": "your-anthropic-key",
      "base_url": "https://api.anthropic.com",
      "models": ["claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
    }
  },
  "default_provider": "chatgpt",
  "timeout": 30,
  "max_retries": 3
}
```

## Usage Examples

### Basic Usage

```python
from agents.core.code_generator import CodeGeneratorAgent

# Create agent with external provider
agent = CodeGeneratorAgent(
    model_name="gpt-3.5-turbo",
    external_provider="chatgpt"
)

# Generate code
request = CodeGenerationRequest(
    task_description="Create a REST API endpoint",
    language="python"
)

result = await agent.generate_code(request)
print(result.generated_code)
```

### Switching Providers

```python
# Start with ChatGPT
generator = CodeGeneratorAgent(
    model_name="gpt-3.5-turbo",
    external_provider="chatgpt"
)

# Switch to Claude
generator.set_provider("claude", "claude-3-sonnet-20240229")
```

### Error Handling

```python
try:
    result = await agent.generate_code(request)
except ModelConnectionError as e:
    print(f"Connection failed: {e}")
    # Fallback to local model
    agent.set_provider("local", "starcoder")
    result = await agent.generate_code(request)
```

## CLI Management

Use the `manage_providers.py` script for provider management:

```bash
# List available providers
python manage_providers.py list

# Test provider connection
python manage_providers.py test chatgpt

# Show provider statistics
python manage_providers.py stats

# Run demo
python manage_providers.py demo
```

## File Structure

### Core Implementation
- `agents/core/external_api_provider.py` - Base classes and provider implementations
- `agents/core/external_api_config.py` - Configuration management system
- `agents/core/unified_model_adapter.py` - Unified interface for all providers

### Updated Files
- `agents/core/base_agent.py` - Updated to support external providers
- `agents/core/code_generator.py` - Updated constructor for external providers

### Tools and Examples
- `manage_providers.py` - CLI tool for provider management
- `examples/demos/demo_external_api.py` - Demo script showing functionality
- `examples/external_api_example.py` - Comprehensive usage examples
- `external_api_config.example.json` - Example configuration file
- `tests/test_external_api.py` - Comprehensive test suite

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Ensure environment variables are set correctly
   - Check JSON configuration file format

2. **Connection Timeout**
   - Increase timeout in configuration
   - Check network connectivity

3. **Rate Limiting**
   - Implement exponential backoff
   - Use multiple API keys for rotation

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Considerations

- External APIs have network latency
- Implement caching for repeated requests
- Use connection pooling for high-volume usage
- Monitor API usage and costs

## Security Best Practices

- Store API keys in environment variables, not in code
- Use least-privilege API keys
- Implement request/response logging for audit
- Rotate API keys regularly
