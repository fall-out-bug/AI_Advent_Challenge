# User Guide

## Table of Contents

- [Introduction](#introduction)
- [Quick Start](#quick-start)
- [Using the CLI](#using-the-cli)
- [Using the API](#using-the-api)
- [Models](#models)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Introduction

The AI Challenge project is a Clean Architecture system for AI-powered code generation and review. It provides both a command-line interface (CLI) and a REST API for interacting with AI agents.

### Key Features

- **Multi-Agent Orchestration**: Coordinate code generation and review workflows
- **Multiple Models**: Support for StarCoder, Mistral, Qwen, and TinyLlama
- **Token Management**: Automatic token counting and compression
- **Health Monitoring**: Built-in health checks and metrics
- **Experiment Tracking**: Track and manage experiments

## Quick Start

### Installation

```bash
# Install dependencies
make install

# Or with Poetry
poetry install
```

### Start the API

```bash
# Start API server
make run-api

# Or with Poetry
poetry run uvicorn src.presentation.api.__main__:create_app --reload
```

The API will be available at `http://localhost:8000`

### Start the CLI

```bash
# Run CLI
make run-cli

# Or directly
poetry run python -m src.presentation.cli.main_cli
```

## Using the CLI

### Available Commands

#### Generate Code

Generate Python code from a description:

```bash
python -m src.presentation.cli.main_cli generate "Create a fibonacci function"
```

**Options:**
- `--agent-name NAME`: Specify agent name
- `--model MODEL`: Specify model to use

**Example:**
```bash
python -m src.presentation.cli.main_cli generate "Create a REST API for task management" --model starcoder
```

#### Review Code

Review existing code for quality:

```bash
python -m src.presentation.cli.main_cli review "<code_file.py>"
```

#### Status Check

Check system status:

```bash
python -m src.presentation.cli.main_cli status
```

**Output includes:**
- API health status
- Model availability
- Storage status
- Configuration info

#### Health Check

Detailed health information:

```bash
python -m src.presentation.cli.main_cli health
```

**Components checked:**
- Storage health
- Model endpoints
- Configuration validity

#### Metrics

View and export metrics:

```bash
# View metrics
python -m src.presentation.cli.main_cli metrics

# Export to JSON
python -m src.presentation.cli.main_cli metrics export json metrics.json

# Export to CSV
python -m src.presentation.cli.main_cli metrics export csv metrics.csv
```

#### Configuration

View and manage configuration:

```bash
# View current configuration
python -m src.presentation.cli.main_cli config

# Validate configuration
python -m src.presentation.cli.main_cli config validate

# List available experiments
python -m src.presentation.cli.main_cli config experiments
```

## Using the API

### Base URL

```
http://localhost:8000
```

### Generate Code Endpoint

**POST** `/api/agents/generate`

Generate code from a description.

**Request Body:**
```json
{
  "prompt": "Create a fibonacci function",
  "agent_name": "generator",
  "model_name": "starcoder"
}
```

**Response:**
```json
{
  "task_id": "uuid",
  "status": "completed",
  "code": "def fibonacci(n): ...",
  "metrics": {
    "complexity": "low",
    "lines_of_code": 15
  }
}
```

**Example with curl:**
```bash
curl -X POST http://localhost:8000/api/agents/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a function to calculate factorial",
    "model_name": "starcoder"
  }'
```

### Review Code Endpoint

**POST** `/api/agents/review`

Review code for quality.

**Request Body:**
```json
{
  "code": "def fibonacci(n): ...",
  "agent_name": "reviewer",
  "model_name": "mistral"
}
```

**Response:**
```json
{
  "task_id": "uuid",
  "status": "completed",
  "review": "Overall quality assessment...",
  "quality_metrics": {
    "pep8_score": 9.5,
    "complexity": "low",
    "test_coverage": "high"
  }
}
```

**Example with curl:**
```bash
curl -X POST http://localhost:8000/api/agents/review \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def fibonacci(n): return n if n < 2 else fibonacci(n-1) + fibonacci(n-2)",
    "model_name": "mistral"
  }'
```

### Health Endpoints

#### Simple Health Check

**GET** `/health/`

Returns basic health status.

```bash
curl http://localhost:8000/health/
```

**Response:**
```json
{
  "status": "ok"
}
```

#### Detailed Readiness Check

**GET** `/health/ready`

Returns detailed health status for all components.

```bash
curl http://localhost:8000/health/ready
```

**Response:**
```json
{
  "overall": "ready",
  "checks": {
    "storage": {
      "status": "healthy",
      "message": "Storage is accessible",
      "response_time_ms": 2.5
    },
    "models": {
      "status": "healthy",
      "message": "All models are available",
      "response_time_ms": 45.2
    }
  }
}
```

#### Model Health Check

**GET** `/health/models`

Check individual model availability.

```bash
curl http://localhost:8000/health/models
```

#### Storage Health Check

**GET** `/health/storage`

Check storage accessibility.

```bash
curl http://localhost:8000/health/storage
```

### Dashboard

**GET** `/dashboard/`

Access the metrics dashboard.

```bash
# Open in browser
open http://localhost:8000/dashboard/

# Or with curl
curl http://localhost:8000/dashboard/data
```

### API Documentation

Interactive API documentation is available at:

```
http://localhost:8000/docs
```

## Models

### Available Models

#### StarCoder (Recommended for Code Generation)

- **Port**: 9000
- **Specialty**: Code generation
- **VRAM**: ~14GB (full precision) / ~7GB (GPTQ)
- **Best for**: Python, JavaScript, TypeScript

```bash
# Use StarCoder
python -m src.presentation.cli.main_cli generate "Create a REST API" --model starcoder
```

#### Mistral

- **Port**: 9001
- **Specialty**: General purpose, high quality
- **VRAM**: ~14GB
- **Best for**: Code review, documentation

```bash
# Use Mistral
python -m src.presentation.cli.main_cli review "<code>" --model mistral
```

#### Qwen

- **Port**: 9002
- **Specialty**: Fast responses
- **VRAM**: ~8GB
- **Best for**: Quick prototypes, simple tasks

```bash
# Use Qwen
python -m src.presentation.cli.main_cli generate "Simple function" --model qwen
```

#### TinyLlama

- **Port**: 9003
- **Specialty**: Compact and fast
- **VRAM**: ~4GB
- **Best for**: Lightweight tasks, testing

```bash
# Use TinyLlama
python -m src.presentation.cli.main_cli generate "Hello world function" --model tinyllama
```

### Model Selection

Models can be specified via:

**CLI:**
```bash
--model <model_name>
```

**API:**
```json
{
  "model_name": "starcoder"
}
```

**Environment Variable:**
```bash
export MODEL_NAME=starcoder
```

## Examples

### Example 1: Generate and Review Code

```bash
# Generate code
python -m src.presentation.cli.main_cli generate "Create a binary search function" > result.txt

# Review the generated code
cat result.txt | python -m src.presentation.cli.main_cli review
```

### Example 2: Batch Generation

```python
#!/usr/bin/env python3
from src.application.use_cases.generate_code import GenerateCodeUseCase

# Create use case instance
use_case = GenerateCodeUseCase(...)

# Generate multiple functions
prompts = [
    "Create a fibonacci function",
    "Create a factorial function",
    "Create a bubble sort function"
]

for prompt in prompts:
    task = await use_case.execute(prompt, "generator")
    print(f"Generated: {task.task_id}")
    print(f"Code: {task.result}")
```

### Example 3: Custom Workflow

```python
#!/usr/bin/env python3
from src.application.orchestrators.multi_agent_orchestrator import MultiAgentOrchestrator
from src.domain.messaging.message_schema import OrchestratorRequest

# Create orchestrator
orchestrator = MultiAgentOrchestrator()

# Create request
request = OrchestratorRequest(
    task_description="Create a REST API for task management",
    model_name="starcoder",
    reviewer_model_name="mistral"
)

# Process task
response = await orchestrator.process_task(request)

# Print results
print(f"Code:\n{response.generated_code}")
print(f"Review:\n{response.review}")
print(f"Quality Score: {response.quality_metrics.overall_score}")
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Problem**: `Address already in use`

**Solution**:
```bash
# Change port
export PORT=8001
poetry run uvicorn src.presentation.api.__main__:create_app --port 8001
```

#### 2. Models Not Available

**Problem**: Health checks report model failures

**Solution**:
```bash
# Check model endpoints
curl http://localhost:9000/health  # StarCoder
curl http://localhost:9001/health  # Mistral

# Restart Docker containers
cd local_models
docker-compose restart
```

#### 3. Import Errors

**Problem**: `ModuleNotFoundError`

**Solution**:
```bash
# Reinstall dependencies
poetry install

# Check Python path
poetry run python -c "import src"
```

#### 4. Slow Performance

**Problem**: Slow responses

**Solution**:
- Check GPU availability
- Use TinyLlama for testing
- Monitor system resources

```bash
# Check system resources
docker stats

# Use faster model
export MODEL_NAME=tinyllama
```

### Getting Help

1. Check logs:
```bash
# Docker logs
docker-compose logs api

# Application logs
tail -f logs/app.log
```

2. Health check:
```bash
python -m src.presentation.cli.main_cli health
```

3. View documentation:
```bash
# API docs
open http://localhost:8000/docs

# Project docs
cat docs/OPERATIONS.md
```

## Best Practices

1. **Start Simple**: Begin with TinyLlama for testing
2. **Monitor Resources**: Check GPU/RAM usage before heavy workloads
3. **Health Checks**: Run health checks regularly
4. **Backup Data**: Backup important results
5. **Use Appropriate Models**: Use StarCoder for code, Mistral for review

## Additional Resources

- [Architecture Documentation](ARCHITECTURE.md)
- [Testing Guide](TESTING.md)
- [Operations Guide](OPERATIONS.md)
- [Local Deployment](LOCAL_DEPLOYMENT.md)
- [API Reference](http://localhost:8000/docs)

