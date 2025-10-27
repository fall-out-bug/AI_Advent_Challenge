# Demo Scripts Guide

This guide covers the various demo scripts available in the `examples/demos/` directory, showcasing different aspects of the StarCoder Multi-Agent System.

## Available Demos

### 1. Basic Demo (`demo.py`)
**Core functionality demonstration**

```bash
python examples/demos/demo.py
```

**What it shows:**
- Basic code generation workflow
- Simple task processing
- Result display

### 2. Quick Demo (`quick_demo.py`)
**Fast demonstration of main features**

```bash
python examples/demos/quick_demo.py
```

**What it shows:**
- Smart model recommendations for different tasks
- Task complexity analysis
- Automatic optimal model selection
- Demo with real API (if key available)

### 3. Interactive Demo (`interactive_demo.py`)
**Interactive demo with user input**

```bash
python examples/demos/interactive_demo.py
```

**Features:**
- User-defined task input
- Preference selection (speed/quality)
- Live code generation
- Task analysis
- Result saving

### 4. Smart Selection Demo (`demo_smart_selection.py`)
**Intelligent model selection system**

```bash
python examples/demos/demo_smart_selection.py
```

**What it demonstrates:**
- Task type analysis
- Model recommendation engine
- Performance comparison
- Optimal provider selection

### 5. External API Demo (`demo_external_api.py`)
**External API integration**

```bash
python examples/demos/demo_external_api.py
```

**Features:**
- ChatGPT integration
- Claude integration
- Provider switching
- External vs local model comparison

### 6. Comparison Demo (`comparison_demo.py`)
**Model comparison and benchmarking**

```bash
python examples/demos/comparison_demo.py
```

**What it shows:**
- Side-by-side model comparison
- Performance metrics
- Quality assessment
- Speed vs accuracy trade-offs

### 7. Smart ChadGPT Demo (`smart_chadgpt_demo.py`)
**Full-featured ChadGPT integration**

```bash
python examples/demos/smart_chadgpt_demo.py
```

**Includes:**
- Smart model selection
- Code generation with optimal models
- Code analysis with best models
- Multi-agent orchestration
- Performance comparison

### 8. Quick ChadGPT Demo (`quick_chadgpt_demo.py`)
**Quick ChadGPT functionality**

```bash
python examples/demos/quick_chadgpt_demo.py
```

**Features:**
- Fast ChadGPT integration
- Basic task processing
- Simple result display

### 9. Quick Model Test (`quick_model_test.py`)
**Model testing utility**

```bash
python examples/demos/quick_model_test.py
```

**Purpose:**
- Test model availability
- Quick functionality verification
- Basic connectivity check

## Running Demos

### Prerequisites

1. **Install dependencies:**
   ```bash
   poetry install
   ```

2. **Set up API keys (for external demos):**
   ```bash
   export OPENAI_API_KEY="your-key"
   export ANTHROPIC_API_KEY="your-key"
   ```

3. **Start local models (for local demos):**
   ```bash
   cd ../local_models
   docker-compose up -d
   ```

### Running Specific Demos

**Basic functionality:**
```bash
python examples/demos/demo.py
python examples/demos/quick_demo.py
```

**Interactive demos:**
```bash
python examples/demos/interactive_demo.py
python examples/demos/demo_smart_selection.py
```

**External API demos:**
```bash
python examples/demos/demo_external_api.py
python examples/demos/smart_chadgpt_demo.py
```

**Comparison and testing:**
```bash
python examples/demos/comparison_demo.py
python examples/demos/quick_model_test.py
```

## Demo Categories

### Core Functionality
- `demo.py` - Basic workflow
- `quick_demo.py` - Fast overview

### Interactive Features
- `interactive_demo.py` - User interaction
- `demo_smart_selection.py` - Smart selection

### External Integration
- `demo_external_api.py` - External APIs
- `smart_chadgpt_demo.py` - ChadGPT integration
- `quick_chadgpt_demo.py` - Quick ChadGPT

### Analysis and Testing
- `comparison_demo.py` - Model comparison
- `quick_model_test.py` - Model testing

## Customization

### Modifying Demo Tasks

Most demos allow you to customize the task:

```python
# In interactive_demo.py
task = input("Enter your task: ")

# In other demos, modify the task_description
request = CodeGenerationRequest(
    task_description="Your custom task here",
    language="python"
)
```

### Adding New Demos

1. Create new file in `examples/demos/`
2. Follow the pattern of existing demos
3. Add proper error handling
4. Update this documentation

### Demo Configuration

Some demos support configuration:

```python
# Model selection
model_name = "starcoder"  # or "mistral", "qwen", "tinyllama"

# Provider selection
external_provider = "chatgpt"  # or "claude"

# Task requirements
requirements = ["Use async/await", "Add type hints"]
```

## Troubleshooting

### Common Issues

1. **Import errors:**
   - Ensure you're running from the project root
   - Check that all dependencies are installed

2. **API key errors:**
   - Verify environment variables are set
   - Check API key validity

3. **Model connection errors:**
   - Ensure local models are running
   - Check network connectivity for external APIs

4. **Path errors:**
   - Run demos from the project root directory
   - Use absolute paths if needed

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Best Practices

1. **Start with basic demos** (`demo.py`, `quick_demo.py`)
2. **Use interactive demos** for experimentation
3. **Run comparison demos** to understand model differences
4. **Test external APIs** before production use
5. **Check model availability** before running demos

## Contributing

When adding new demos:

1. Follow existing naming conventions
2. Add proper error handling
3. Include usage examples
4. Update this documentation
5. Test with different models/providers
