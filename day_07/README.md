# Multi-Model Multi-Agent System

[English](README.md) | [Русский](README.ru.md)

A sophisticated multi-agent system with support for multiple language models (StarCoder, Mistral, Qwen, TinyLlama) for automated Python code generation and review. The system consists of two specialized AI agents that work together to generate high-quality Python code and provide comprehensive code reviews.

## 🌟 Features

- **Multi-Model Support**: Choose from StarCoder, Mistral, Qwen, or TinyLlama
- **Code Generation Agent**: Generates Python functions with comprehensive tests
- **Code Review Agent**: Analyzes code quality, PEP8 compliance, and provides recommendations
- **REST API Communication**: Agents communicate via HTTP APIs for scalability
- **Docker Orchestration**: Easy deployment with Docker Compose
- **Comprehensive Testing**: Unit and integration tests included
- **Results Persistence**: All workflow results saved for analysis
- **Real-time Monitoring**: Health checks and statistics endpoints
- **Shared SDK Integration**: Unified interface for all language models

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Orchestrator  │    │  Code Generator │    │  Code Reviewer  │
│                 │    │     Agent       │    │     Agent       │
│  - Coordinates  │◄──►│  - Generates    │◄──►│  - Reviews      │
│  - Manages      │    │  - Creates      │    │  - Analyzes     │
│  - Saves        │    │  - Validates    │    │  - Scores       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Shared SDK     │
                    │  - StarCoder    │
                    │  - Mistral      │
                    │  - Qwen         │
                    │  - TinyLlama    │
                    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- NVIDIA GPU (for StarCoder)
- Python 3.10+ (for local development)
- Poetry (for dependency management)
- Hugging Face token (for downloading StarCoder model)

### Environment Variables

Before starting the services, you need to configure environment variables:

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` file and set your Hugging Face token and model preferences:
   ```
   HF_TOKEN=your_actual_huggingface_token_here
   MODEL_NAME=starcoder
   STARCODER_URL=http://localhost:8003/chat
   MISTRAL_URL=http://localhost:8001
   QWEN_URL=http://localhost:8000
   TINYLLAMA_URL=http://localhost:8002
   ```

3. Also configure the local_models directory:
   ```bash
   cd ../local_models
   cp .env.example .env
   ```
   
   Edit the local_models `.env` file:
   ```
   HF_TOKEN=your_actual_huggingface_token_here
   ```

### 1. Start StarCoder Service

First, start the StarCoder model service:

```bash
cd ../local_models
docker-compose up -d starcoder-chat
```

Wait for the model to load (this may take several minutes on first run).

### 2. Start Agent Services

```bash
cd day_07
docker-compose up -d
```

This will start:
- Code Generator Agent on port 9001
- Code Reviewer Agent on port 9002
- StarCoder service on port 8003

### 3. Run Demo

```bash
python demo.py
```

## 🤖 Multi-Model Support

The system now supports multiple language models:

- **StarCoder-7B** (default): Specialized for code generation
- **Mistral-7B**: High-quality general-purpose model
- **Qwen-4B**: Fast responses, good quality
- **TinyLlama-1.1B**: Compact and fast

### Using Different Models

```python
# Use Mistral for generation
request = OrchestratorRequest(
    task_description="Create a REST API",
    model_name="mistral"
)

# Use different models for generation and review
request = OrchestratorRequest(
    task_description="Create a REST API",
    model_name="starcoder",
    reviewer_model_name="mistral"
)
```

### Model Configuration

Each model has optimized settings:

```python
MODEL_SPECIFIC_SETTINGS = {
    "starcoder": {
        "generator_temperature": 0.3,
        "reviewer_temperature": 0.2,
        "generator_max_tokens": 1500,
        "reviewer_max_tokens": 1200
    },
    "mistral": {
        "generator_temperature": 0.4,
        "reviewer_temperature": 0.3,
        "generator_max_tokens": 1500,
        "reviewer_max_tokens": 1200
    }
    # ... other models
}
```

## 🛠️ Development Setup

### Using Poetry (Recommended)

This project uses Poetry for dependency management. Poetry provides better dependency resolution, virtual environment management, and reproducible builds.

#### Install Poetry

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"
```

#### Setup Development Environment

```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run isort .

# Run linting
poetry run flake8 .
```

#### Poetry Commands

```bash
# Add new dependency
poetry add package-name

# Add development dependency
poetry add --group dev package-name

# Update dependencies
poetry update

# Export requirements.txt (for Docker)
poetry export -f requirements.txt --output requirements.txt --without-hashes

# Show dependency tree
poetry show --tree
```

### Using pip (Alternative)

If you prefer using pip directly:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 📖 Usage

### Simple Task Processing

```python
from orchestrator import process_simple_task

# Process a simple task
result = await process_simple_task(
    task_description="Create a function to calculate fibonacci numbers",
    language="python",
    requirements=["Include type hints", "Handle edge cases"]
)

if result.success:
    print(f"Code quality: {result.review_result.code_quality_score}/10")
    print(f"Generated code: {result.generation_result.generated_code}")
    print(f"Tests: {result.generation_result.tests}")
```

### Advanced Orchestration

```python
from orchestrator import MultiAgentOrchestrator
from communication.message_schema import OrchestratorRequest

# Create orchestrator
orchestrator = MultiAgentOrchestrator(
    generator_url="http://localhost:9001",
    reviewer_url="http://localhost:9002"
)

# Process complex task
request = OrchestratorRequest(
    task_description="Create a REST API client with retry logic",
    language="python",
    requirements=["Use httpx", "Implement exponential backoff", "Add logging"]
)

result = await orchestrator.process_task(request)
```

### Direct Agent Communication

```python
from communication.agent_client import AgentClient
from communication.message_schema import CodeGenerationRequest

async with AgentClient() as client:
    # Generate code
    request = CodeGenerationRequest(
        task_description="Create a data validation function",
        requirements=["Use Pydantic", "Handle nested objects"]
    )
    
    response = await client.generate_code(
        "http://localhost:9001",
        request
    )
    
    print(f"Generated: {response.generated_code}")
```

## 🔧 API Reference

### Code Generator Agent (Port 9001)

#### `POST /generate`
Generate Python code and tests.

**Request:**
```json
{
    "task_description": "Create a function to sort a list",
    "language": "python",
    "requirements": ["Use quicksort", "Include type hints"],
    "max_tokens": 1000
}
```

**Response:**
```json
{
    "task_description": "Create a function to sort a list",
    "generated_code": "def quicksort(arr: List[int]) -> List[int]: ...",
    "tests": "def test_quicksort(): ...",
    "metadata": {
        "complexity": "medium",
        "lines_of_code": 25,
        "dependencies": ["typing"]
    },
    "generation_time": "2024-01-15T10:30:00",
    "tokens_used": 450
}
```

#### `GET /health`
Check agent health status.

#### `GET /stats`
Get agent performance statistics.

### Code Reviewer Agent (Port 9002)

#### `POST /review`
Review generated code for quality and best practices.

**Request:**
```json
{
    "task_description": "Create a function to sort a list",
    "generated_code": "def quicksort(arr: List[int]) -> List[int]: ...",
    "tests": "def test_quicksort(): ...",
    "metadata": {
        "complexity": "medium",
        "lines_of_code": 25
    }
}
```

**Response:**
```json
{
    "code_quality_score": 8.5,
    "metrics": {
        "pep8_compliance": true,
        "pep8_score": 9.0,
        "has_docstrings": true,
        "has_type_hints": true,
        "test_coverage": "good",
        "complexity_score": 7.0
    },
    "issues": ["Consider adding error handling for empty lists"],
    "recommendations": ["Add input validation", "Consider edge cases"],
    "review_time": "2024-01-15T10:30:05",
    "tokens_used": 320
}
```

## 🧪 Testing

### Using Makefile (Recommended)

```bash
# Run all tests
make test

# Run linting
make lint

# Format code
make format

# Quick test
make quick-test
```

### Using Poetry

```bash
# Run unit tests
poetry run pytest tests/ -v

# Run integration tests
poetry run pytest tests/test_integration.py -v

# Test coverage
poetry run pytest --cov=. --cov-report=html
```

### Using pip

```bash
# Run unit tests
pytest tests/ -v

# Run integration tests
pytest tests/test_integration.py -v

# Test coverage
pytest --cov=. --cov-report=html
```

## 📊 Monitoring

### Health Checks

```bash
# Check generator agent
curl http://localhost:9001/health

# Check reviewer agent
curl http://localhost:9002/health
```

### Statistics

```bash
# Get generator stats
curl http://localhost:9001/stats

# Get reviewer stats
curl http://localhost:9002/stats
```

### Results Analysis

```python
from orchestrator import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator()
summary = orchestrator.get_results_summary()

print(f"Success rate: {summary['success_rate']:.1%}")
print(f"Average quality: {summary['average_quality_score']:.1f}/10")
```

## 🔧 Configuration

### Environment Variables

- `STARCODER_URL`: URL of StarCoder service (default: `http://localhost:8003/chat`)
- `PORT`: Agent service port (default: 9001/9002)
- `HF_TOKEN`: HuggingFace token for model access

### Docker Configuration

The system provides two Docker deployment options:

#### Option 1: Host Network (Recommended for Development)
```bash
# Uses host network for easy access to local models
docker-compose up -d
```

**Features:**
- Direct access to local models (StarCoder, Mistral, etc.)
- Ports 9001 (generator) and 9002 (reviewer) automatically available
- Simple networking configuration
- Best for development and testing

#### Option 2: Bridge Network (Production)
```bash
# Uses bridge network with explicit port mapping
docker-compose -f docker-compose.bridge.yml up -d
```

**Features:**
- Isolated network environment
- Explicit port mapping: 9001:9001 and 9002:9002
- Uses `host.docker.internal` for model access
- Better for production deployments

**Configuration includes:**
- Resource limits (CPU: 2 cores, Memory: 4GB)
- Environment variables for model selection
- Volume mounts for results persistence
- Health checks and restart policies

#### Option 3: Traefik Reverse Proxy (Recommended for Production)

```bash
# All-in-one solution with Traefik
make start-traefik
```

**Features:**
- Single entry point through Traefik reverse proxy
- Automatic service discovery
- Domain-based routing (generator.localhost, reviewer.localhost)
- Integrated Dashboard at http://localhost:8080
- All models and agents in isolated network
- No port conflicts

**Access:**
- Generator API: http://generator.localhost
- Reviewer API: http://reviewer.localhost
- Traefik Dashboard: http://localhost:8080

**Note:** Add to /etc/hosts if needed:
```
127.0.0.1 generator.localhost reviewer.localhost
```

## 🏗️ Development

### Project Structure

```
day_07/
├── agents/
│   ├── api/                 # FastAPI services
│   │   ├── generator_api.py
│   │   └── reviewer_api.py
│   └── core/                # Agent implementations
│       ├── base_agent.py
│       ├── code_generator.py
│       └── code_reviewer.py
├── communication/           # Inter-agent communication
│   ├── agent_client.py
│   └── message_schema.py
├── prompts/                 # Prompt templates
│   ├── generator_prompts.py
│   └── reviewer_prompts.py
├── tests/                   # Test suite
├── results/                 # Workflow results
├── orchestrator.py          # Main orchestrator
├── demo.py                  # Demo script
├── main.py                  # CLI entry point
├── pyproject.toml          # Poetry configuration
├── poetry.lock             # Poetry lock file
├── requirements.txt       # Pip requirements (exported from Poetry)
├── docker-compose.yml      # Docker orchestration
├── Dockerfile             # Container definition
└── Makefile               # Development commands
```

### Adding New Agents

1. Create new agent class inheriting from `BaseAgent`
2. Implement the `process()` method
3. Create FastAPI service
4. Add to docker-compose.yml
5. Update orchestrator if needed

### Custom Prompts

Modify prompt templates in `prompts/` directory to customize agent behavior.

## 🚨 Troubleshooting

### Common Issues

**Docker image pull errors:**
```bash
# Error: pull access denied for local_models_chat_api
# Solution: Build the StarCoder image first
cd ../local_models
docker-compose build starcoder-chat
```

**HF_TOKEN not set warnings:**
```bash
# Solution: Configure environment variables
cp .env.example .env
# Edit .env file with your actual HF_TOKEN
```

**StarCoder not responding:**
```bash
# Check if StarCoder is running
curl http://localhost:8003/health

# Check logs
cd ../local_models
docker-compose logs starcoder-chat

# Check if port 8003 is available
netstat -tulpn | grep :8003
```

**Agent services not starting:**
```bash
# Check agent logs
docker-compose logs generator-agent
docker-compose logs reviewer-agent

# Verify ports are available
netstat -tulpn | grep :9001
netstat -tulpn | grep :9002

# Check if StarCoder is accessible from agents
curl http://localhost:8003/health
```

**Out of memory errors:**
- Reduce `max_tokens` in requests
- Use smaller StarCoder model
- Increase Docker memory limits in docker-compose.yml
- Monitor with `nvidia-smi` for GPU memory usage

**Services can't communicate:**
- Ensure StarCoder is running on port 8003
- Check firewall settings
- Verify docker network configuration
- Use `make health` to check all service statuses

### Performance Optimization

- Use SSD storage for model cache
- Allocate sufficient RAM (16GB+ recommended)
- Monitor GPU utilization with `nvidia-smi`
- Adjust batch sizes and timeouts

## 📈 Performance Metrics

Typical performance on a modern GPU:
- Code generation: 2-5 seconds
- Code review: 1-3 seconds
- Full workflow: 3-8 seconds
- Memory usage: ~8-12GB for StarCoder-7B

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is part of the AI Challenge study series.

## 🙏 Acknowledgments

- BigCode team for StarCoder model
- FastAPI for excellent web framework
- HuggingFace for model hosting
