# External API Integration for Multi-Agent System

This implementation adds support for external AI API providers (ChatGPT, Claude) to the multi-agent system, allowing seamless switching between local models and external services.

## 🚀 Features

- **Multiple Provider Support**: ChatGPT (OpenAI), Claude (Anthropic)
- **Dynamic Switching**: Switch between providers at runtime
- **Unified Interface**: Same API for all providers (local and external)
- **Configuration Management**: Environment variables and JSON config files
- **Error Handling**: Comprehensive error handling and fallback strategies
- **Performance Monitoring**: Statistics and availability checking
- **CLI Management**: Command-line tool for provider management

## 📁 New Files

### Core Implementation
- `agents/core/external_api_provider.py` - Base classes and provider implementations
- `agents/core/external_api_config.py` - Configuration management system
- `agents/core/unified_model_adapter.py` - Unified interface for all providers

### Updated Files
- `agents/core/base_agent.py` - Updated to support external providers
- `agents/core/code_generator.py` - Updated constructor for external providers

### Tools and Examples
- `manage_providers.py` - CLI tool for provider management
- `demo_external_api.py` - Demo script showing functionality
- `examples/external_api_example.py` - Comprehensive usage examples
- `external_api_config.example.json` - Example configuration file
- `tests/test_external_api.py` - Comprehensive test suite

### Documentation
- `EXTERNAL_API_GUIDE.md` - Complete usage guide

## 🛠️ Quick Setup

### 1. Install Dependencies

```bash
pip install httpx click
```

### 2. Set API Keys

```bash
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### 3. Run Demo

```bash
python demo_external_api.py
```

## 💡 Usage Examples

### Basic Usage

```python
from agents.core.code_generator import CodeGeneratorAgent
from communication.message_schema import CodeGenerationRequest

# Use ChatGPT
generator = CodeGeneratorAgent(
    model_name="gpt-3.5-turbo",
    external_provider="chatgpt"
)

# Generate code
request = CodeGenerationRequest(
    task_description="Create a fibonacci function",
    language="python"
)

result = await generator.process(request)
print(result.generated_code)
```

### Dynamic Provider Switching

```python
# Start with local model
generator = CodeGeneratorAgent(model_name="starcoder")

# Switch to ChatGPT
await generator.switch_to_external_provider("chatgpt")

# Switch to Claude
await generator.switch_to_external_provider("claude")

# Switch back to local
await generator.switch_to_local_model("mistral")
```

### Configuration Management

```python
from agents.core.external_api_config import get_config

config = get_config()

# Add provider
config.add_provider("chatgpt-4", ProviderConfig(
    provider_type=ProviderType.CHATGPT,
    api_key="your-key",
    model="gpt-4"
))

# Validate configuration
results = config.validate_config()
```

## 🎯 CLI Management

```bash
# Show status
python manage_providers.py status

# Add provider
python manage_providers.py add chatgpt-4 chatgpt your-api-key --model gpt-4

# Test providers
python manage_providers.py test

# Validate configuration
python manage_providers.py validate
```

## 🧪 Testing

Run the test suite:

```bash
python -m pytest tests/test_external_api.py -v
```

## 📊 Architecture

The implementation follows several design patterns:

- **Strategy Pattern**: Different providers implement the same interface
- **Adapter Pattern**: UnifiedModelAdapter provides consistent interface
- **Factory Pattern**: ModelProviderFactory creates appropriate adapters
- **Configuration Pattern**: Centralized configuration management

## 🔧 Configuration Options

### Environment Variables

```bash
# OpenAI
OPENAI_API_KEY="your-key"
OPENAI_MODEL="gpt-3.5-turbo"
OPENAI_TIMEOUT="60.0"
OPENAI_MAX_TOKENS="4000"
OPENAI_TEMPERATURE="0.7"

# Anthropic
ANTHROPIC_API_KEY="your-key"
ANTHROPIC_MODEL="claude-3-sonnet-20240229"
ANTHROPIC_TIMEOUT="60.0"
ANTHROPIC_MAX_TOKENS="4000"
ANTHROPIC_TEMPERATURE="0.7"

# Default Provider
DEFAULT_EXTERNAL_PROVIDER="chatgpt"
```

### JSON Configuration

```json
{
  "providers": {
    "chatgpt": {
      "provider_type": "chatgpt",
      "api_key": "your-key",
      "model": "gpt-3.5-turbo",
      "timeout": 60.0,
      "enabled": true,
      "max_tokens": 4000,
      "temperature": 0.7
    }
  },
  "default_provider": "chatgpt"
}
```

## 🚨 Error Handling

The system provides comprehensive error handling:

- **Configuration Errors**: Invalid API keys, missing providers
- **Network Errors**: Connection timeouts, rate limits
- **API Errors**: Invalid requests, authentication failures
- **Fallback Strategies**: Automatic fallback to local models

## 📈 Performance Monitoring

Monitor provider performance:

```python
# Get provider info
info = generator.get_provider_info()

# Get statistics
stats = generator.model_adapter.get_stats()
print(f"Success rate: {stats['stats'].get('success_rate', 0):.1f}%")
```

## 🔒 Security Considerations

- API keys are loaded from environment variables
- Configuration files should not contain sensitive data
- Use appropriate timeouts to prevent hanging requests
- Monitor API usage to avoid unexpected costs

## 🤝 Contributing

To add a new external API provider:

1. Create provider class inheriting from `ExternalAPIProvider`
2. Implement `make_request()` and `check_availability()` methods
3. Add provider type to `ProviderType` enum
4. Update configuration system
5. Add tests and documentation

## 📚 Documentation

- `EXTERNAL_API_GUIDE.md` - Complete usage guide
- `examples/external_api_example.py` - Comprehensive examples
- `tests/test_external_api.py` - Test cases and usage patterns

## 🎉 Benefits

- **Flexibility**: Use the best model for each task
- **Reliability**: Fallback to local models when external APIs fail
- **Cost Optimization**: Choose providers based on cost and performance
- **Scalability**: Easy to add new providers
- **Maintainability**: Clean separation of concerns

This implementation seamlessly integrates external AI services into the existing multi-agent system while maintaining backward compatibility and providing a smooth developer experience.
