# External API Integration Guide

This guide explains how to integrate and use external AI API providers (like ChatGPT, Claude) with the multi-agent system.

## Overview

The external API integration system allows you to:
- Use external AI services (ChatGPT, Claude) alongside local models
- Switch between providers dynamically at runtime
- Configure multiple providers with different settings
- Maintain the same interface for all providers

## Quick Start

### 1. Set up API Keys

Set your API keys as environment variables:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### 2. Create Agents with External Providers

```python
from agents.core.code_generator import CodeGeneratorAgent

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

### 3. Use Agents Normally

```python
from communication.message_schema import CodeGenerationRequest

request = CodeGenerationRequest(
    task_description="Create a fibonacci function",
    language="python"
)

result = await generator.process(request)
print(result.generated_code)
```

## Configuration

### Environment Variables

The system automatically loads configuration from environment variables:

```bash
# ChadGPT Configuration (Primary)
export CHADGPT_API_KEY="your-key"
export CHADGPT_MODEL="gpt-5-mini"
export CHADGPT_TIMEOUT="60.0"
export CHADGPT_MAX_TOKENS="4000"
export CHADGPT_TEMPERATURE="0.7"

# OpenAI Configuration
export OPENAI_API_KEY="your-key"
export OPENAI_MODEL="gpt-3.5-turbo"
export OPENAI_TIMEOUT="60.0"
export OPENAI_MAX_TOKENS="4000"
export OPENAI_TEMPERATURE="0.7"

# Anthropic Configuration
export ANTHROPIC_API_KEY="your-key"
export ANTHROPIC_MODEL="claude-3-sonnet-20240229"
export ANTHROPIC_TIMEOUT="60.0"
export ANTHROPIC_MAX_TOKENS="4000"
export ANTHROPIC_TEMPERATURE="0.7"

# Default Provider
export DEFAULT_EXTERNAL_PROVIDER="chadgpt"
```

### Configuration File

Create `external_api_config.json`:

```json
{
  "providers": {
    "chatgpt": {
      "provider_type": "chatgpt",
      "api_key": "your-openai-api-key",
      "model": "gpt-3.5-turbo",
      "timeout": 60.0,
      "enabled": true,
      "max_tokens": 4000,
      "temperature": 0.7
    },
    "claude": {
      "provider_type": "claude",
      "api_key": "your-anthropic-api-key",
      "model": "claude-3-sonnet-20240229",
      "timeout": 60.0,
      "enabled": true,
      "max_tokens": 4000,
      "temperature": 0.7
    }
  },
  "default_provider": "chatgpt"
}
```

## Provider Management CLI

Use the CLI tool to manage providers:

```bash
# Show status
python manage_providers.py status

# Add a provider
python manage_providers.py add chatgpt-4 chatgpt your-api-key --model gpt-4

# Test providers
python manage_providers.py test

# Validate configuration
python manage_providers.py validate
```

## Dynamic Provider Switching

Switch between providers at runtime:

```python
# Start with local model
generator = CodeGeneratorAgent(model_name="starcoder")

# Switch to ChatGPT
success = await generator.switch_to_external_provider("chatgpt")
if success:
    print("Switched to ChatGPT")

# Switch to Claude
success = await generator.switch_to_external_provider("claude")
if success:
    print("Switched to Claude")

# Switch back to local
success = await generator.switch_to_local_model("mistral")
if success:
    print("Switched to local Mistral")
```

## Error Handling

The system provides comprehensive error handling:

```python
try:
    generator = CodeGeneratorAgent(external_provider="chatgpt")
    
    # Check availability
    if await generator.check_provider_availability():
        result = await generator.process(request)
    else:
        print("Provider not available")
        
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"API error: {e}")
```

## Performance Monitoring

Monitor provider performance:

```python
# Get provider information
info = generator.get_provider_info()
print(f"Using: {info['type']} - {info.get('provider', info['model'])}")

# Get statistics
stats = generator.model_adapter.get_stats()
print(f"Success rate: {stats['stats'].get('success_rate', 0):.1f}%")
print(f"Average response time: {stats['stats'].get('average_response_time', 0):.2f}s")
```

## Supported Providers

### ChadGPT (Primary)
- **Models**: gpt-5-mini
- **API**: ChadGPT API (https://ask.chadgpt.ru/api/public/gpt-5-mini)
- **Features**: Fast responses, good code generation, Russian-friendly
- **Priority**: This is the primary external API provider

### ChatGPT (OpenAI)
- **Models**: gpt-3.5-turbo, gpt-4, gpt-4-turbo
- **API**: OpenAI Chat Completions API
- **Features**: Fast responses, good code generation

### Claude (Anthropic)
- **Models**: claude-3-sonnet-20240229, claude-3-opus-20240229
- **API**: Anthropic Messages API
- **Features**: High-quality responses, good reasoning

## Best Practices

### 1. Provider Selection
- Use **ChadGPT** for primary external API (fast, reliable, Russian-friendly)
- Use **ChatGPT** for fast, cost-effective code generation
- Use **Claude** for complex reasoning and high-quality code review
- Use **local models** for privacy-sensitive tasks

### 2. Error Handling
- Always check provider availability before use
- Implement fallback strategies
- Monitor API rate limits and costs

### 3. Configuration Management
- Use environment variables for API keys
- Keep configuration files in version control (without keys)
- Validate configuration before deployment

### 4. Performance Optimization
- Set appropriate timeouts
- Use appropriate temperature settings
- Monitor token usage and costs

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   ```
   Error: Provider 'chatgpt' not found
   ```
   **Solution**: Set `OPENAI_API_KEY` environment variable

2. **Provider Not Available**
   ```
   Error: External provider 'chatgpt' is not available
   ```
   **Solution**: Check API key validity and network connectivity

3. **Rate Limit Exceeded**
   ```
   Error: HTTP error 429: Rate limit exceeded
   ```
   **Solution**: Implement retry logic or use different provider

4. **Configuration Validation Failed**
   ```
   Error: Configuration has errors
   ```
   **Solution**: Run `python manage_providers.py validate` to check configuration

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Examples

See `examples/external_api_example.py` for comprehensive usage examples including:
- Basic usage with different providers
- Dynamic provider switching
- Configuration management
- Error handling
- Performance comparison

## API Reference

### Core Classes

- `ExternalAPIProvider`: Base class for external API providers
- `ChatGPTProvider`: OpenAI ChatGPT API provider
- `ClaudeProvider`: Anthropic Claude API provider
- `UnifiedModelAdapter`: Unified interface for all providers
- `ExternalAPIConfig`: Configuration management

### Key Methods

- `make_request()`: Make API request
- `check_availability()`: Check provider availability
- `switch_to_external_provider()`: Switch to external provider
- `switch_to_local_model()`: Switch to local model
- `get_provider_info()`: Get current provider information

## Contributing

To add a new external API provider:

1. Create a new provider class inheriting from `ExternalAPIProvider`
2. Implement `make_request()` and `check_availability()` methods
3. Add provider type to `ProviderType` enum
4. Update configuration system
5. Add tests and documentation

## License

This external API integration system is part of the AI Challenge project and follows the same license terms.
