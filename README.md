# AI Advent Challenge

[English](README.md) | [Русский](README.ru.md)

> Daily AI-powered projects exploring language models and multi-agent systems

## 🤖 Quick Start for AI Agents

**Repository Structure:**
- `local_models/` - Local language model infrastructure (shared module)
- `shared/` - SDK for unified model interaction (shared module)
- `day_01/` to `day_04/` - Learning projects exploring basics
- `day_05/`, `day_06/` - Production projects using SDK
- `day_07/` - Multi-Agent System for code generation and review
- Each `day_XX/` is a standalone project with its own dependencies and tests

**Key Components:**
- **Local Models**: FastAPI servers in `local_models/` (ports 8000-8002)
- **SDK**: Unified interface for model interaction in `shared/`
- **Chat Bots**: Terminal applications with AI-powered interactions
- **Advisor Mode**: Structured dialogue with model constraints
- **Unified API**: `api <provider>` command for all models
- **Multi-Agent System**: Specialized agents for code generation and review

**Quick Start for Agents:**
1. Study `local_models/README.md` - local model architecture
2. Choose project `day_XX/` by complexity
3. Run `make install && make run` in selected project

## 📁 Project Structure

```
AI_Advent_Challenge/
├── .gitignore              # Ignored files
├── config.py              # API key configuration (shared)
├── api_key.txt.example    # Template for API keys
├── Makefile              # Project setup commands
├── README.md             # This file (English)
├── README.ru.md          # Russian version
├── AGENTS.md             # AI agents documentation (English)
├── AGENTS.ru.md          # AI agents documentation (Russian)
├── AGENTS_QUICK_REFERENCE.md # Quick reference (English)
├── AGENTS_QUICK_REFERENCE.ru.md # Quick reference (Russian)
├── local_models/         # 🏠 Local language model infrastructure
│   ├── chat_api.py       # FastAPI server for local models
│   ├── docker-compose.yml # Docker Compose configuration
│   ├── Dockerfile        # Image for running models
│   ├── download_model.py # Script for pre-downloading models
│   └── README.md         # Local models documentation
├── shared/               # 🛠️ SDK for unified model interaction
│   ├── config/          # Model configuration and constants
│   ├── clients/         # Model clients
│   ├── exceptions/      # Standardized exceptions
│   ├── tests/           # SDK tests (98.59% coverage)
│   ├── pyproject.toml   # SDK dependencies
│   └── README.md        # SDK documentation
├── day_01/               # Day 1 - Terminal chat with AI
│   ├── terminal_chat.py  # Main application
│   ├── pyproject.toml    # Poetry dependencies
│   ├── .venv/           # Poetry virtual environment
│   ├── Makefile         # Development commands
│   └── README.md        # Project documentation
├── day_02/               # Day 2 - Improved chat with JSON responses
│   ├── terminal_chat_v2.py # Improved application
│   ├── pyproject.toml    # Poetry dependencies
│   ├── .venv/           # Poetry virtual environment
│   ├── Makefile         # Development commands
│   └── README.md        # Project documentation
├── day_03/               # Day 3 - Advisor mode with model constraints
│   ├── terminal_chat_v3.py # Chat with advisor mode
│   ├── advice_session.py   # Session state management
│   ├── advice_mode.py      # Advisor mode logic
│   ├── tests/             # Tests for all components
│   ├── pyproject.toml     # Poetry dependencies
│   ├── Makefile          # Development commands
│   └── README.md         # Project documentation
├── day_04/               # Day 4 - Improved advisor mode with temperature
│   ├── terminal_chat_v4.py # Chat with improved advisor mode
│   ├── advice_mode.py      # Advisor mode logic
│   ├── advice_session.py   # Session state management
│   ├── temperature_utils.py # Temperature utilities
│   ├── experiment_temperature.py # Temperature experiments
│   ├── tests/             # Tests for all components
│   ├── pyproject.toml     # Poetry dependencies
│   ├── Makefile          # Development commands
│   └── README.md         # Project documentation
├── day_05/               # Day 5 - Local models and message history
│   ├── terminal_chat_v5.py # Chat with local model support
│   ├── advice_mode_v5.py   # Advisor mode for local models
│   ├── advice_session.py   # Session state management
│   ├── temperature_utils.py # Temperature utilities
│   ├── check_models.py     # Local model availability check
│   ├── demo_*.py          # Demo scripts
│   ├── tests/             # Tests for all components
│   ├── requirements.txt   # Project dependencies
│   ├── Makefile          # Development commands
│   └── README.md         # Project documentation
├── day_06/               # Day 6 - Testing local models on logical puzzles
│   ├── src/              # Testing system source code
│   │   ├── main.py       # Main testing module
│   │   ├── model_client.py # Local model client
│   │   ├── riddles.py    # Collection of logical puzzles
│   │   ├── report_generator.py # Report generator
│   │   └── __init__.py   # Package initialization
│   ├── tests/           # Tests for all components
│   ├── pyproject.toml   # Poetry dependencies
│   ├── Makefile         # Development commands
│   └── README.md        # Project documentation
└── day_07/               # Day 7 - Multi-Agent System for Code Generation and Review
    ├── agents/          # System agents
    │   ├── api/        # FastAPI services for agents
    │   │   ├── generator_api.py # Generator agent API
    │   │   └── reviewer_api.py  # Reviewer agent API
    │   └── core/       # Agent core (generator, reviewer)
    │       ├── base_agent.py # Base agent class
    │       ├── code_generator.py # Code generator agent
    │       ├── code_reviewer.py # Code reviewer agent
    │       └── model_client_adapter.py # Model integration
    ├── communication/   # Communication layer between agents
    │   ├── agent_client.py # HTTP client with retry logic
    │   └── message_schema.py # Request/response models
    ├── prompts/        # Prompt templates for models
    │   ├── generator_prompts.py # Generation prompts
    │   └── reviewer_prompts.py  # Review prompts
    ├── tests/          # System tests
    │   ├── test_generator.py
    │   ├── test_reviewer.py
    │   └── test_orchestrator.py
    ├── examples/       # Usage examples
    ├── orchestrator.py # Workflow orchestrator
    ├── main.py         # CLI interface
    ├── demo.py         # Demo examples
    ├── Dockerfile      # Multi-stage Docker image
    ├── docker-compose*.yml # Deployment configurations
    ├── README.md       # Project documentation (EN)
    ├── README.ru.md    # Project documentation (RU)
    ├── DEVELOPER_GUIDE.md # Developer guide (EN)
    ├── DEVELOPER_GUIDE.ru.md # Developer guide (RU)
    ├── ARCHITECTURE.md # System architecture (EN)
    ├── ARCHITECTURE.ru.md # System architecture (RU)
    ├── DEPLOYMENT.md   # Deployment guide (EN)
    ├── DEPLOYMENT.ru.md # Deployment guide (RU)
    ├── TROUBLESHOOTING.md # Troubleshooting guide (EN)
    ├── TROUBLESHOOTING.ru.md # Troubleshooting guide (RU)
    ├── pyproject.toml  # Poetry dependencies
    ├── Makefile        # Development commands
    └── constants.py    # Configuration constants
└── day_08/               # Day 8 - Enhanced Token Analysis System
    ├── core/           # Core business logic
    │   ├── token_analyzer.py # Token counting strategies
    │   ├── text_compressor.py # Text compression with strategy pattern
    │   ├── ml_client.py # ML service client with retry logic
    │   ├── experiments.py # Experiment management
    │   ├── compressors/ # Compression strategy implementations
    │   ├── factories/  # Factory pattern implementations
    │   ├── builders/   # Builder pattern implementations
    │   └── validators/ # Request validation
    ├── domain/         # Domain layer (DDD)
    │   ├── entities/   # Domain entities
    │   ├── value_objects/ # Immutable value objects
    │   ├── repositories/ # Repository interfaces
    │   └── services/   # Domain services
    ├── application/    # Application layer
    │   ├── use_cases/  # Business use cases
    │   ├── services/   # Application services
    │   └── dto/        # Data transfer objects
    ├── infrastructure/ # Infrastructure layer
    │   ├── repositories/ # Repository implementations
    │   ├── external/   # External service integrations
    │   └── config/     # Configuration management
    ├── tests/          # Comprehensive test suite
    │   ├── integration/ # End-to-end tests
    │   ├── regression/ # Baseline behavior tests
    │   ├── performance/ # Performance baseline tests
    │   └── mocks/      # Test doubles
    ├── docs/           # Technical documentation
    │   ├── DEVELOPMENT_GUIDE.md # Development practices
    │   ├── DOMAIN_GUIDE.md # Domain-driven design
    │   ├── ML_ENGINEERING.md # ML framework guide
    │   └── ASYNC_TESTING_BEST_PRACTICES.md # Testing guide
    ├── examples/       # Usage examples
    ├── reports/        # Demo and analysis reports
    ├── demo_enhanced.py # Enhanced demonstration
    ├── demo.py         # Basic demonstration
    ├── README.md       # Comprehensive documentation (EN)
    ├── README.ru.md    # Executive summary (RU)
    ├── architecture.md # System architecture
    ├── api.md          # API reference
    ├── TASK.md         # Original requirements
    ├── TASK_VERIFICATION_REPORT.md # Requirements verification
    ├── PROJECT_SUMMARY.md # Project achievements
    ├── pyproject.toml  # Poetry dependencies
    ├── Makefile        # Development commands
    └── pytest.ini      # Test configuration
```

## 🚀 Quick Start

### 1. Setup API Keys

```bash
make setup  # Creates api_key.txt from template
# Add your API keys to api_key.txt:
# perplexity:your_perplexity_key
# chadgpt:your_chadgpt_key
```

### 2. Start Local Models (Optional)

```bash
# Start all local models
cd local_models
docker-compose up -d

# Check availability
curl http://localhost:8000/chat  # Qwen
curl http://localhost:8001/chat  # Mistral
curl http://localhost:8002/chat  # TinyLlama
```

### 3. Choose a Project

```bash
# Day 1 - Simple chat
cd day_01
make install
make chat

# Day 2 - Improved chat with JSON responses
cd ../day_02
make install
make chat

# Day 3 - Advisor mode with model constraints
cd ../day_03
make install
make run

# Day 4 - Improved advisor mode with temperature
cd ../day_04
make install
make run

# Day 5 - Local models and message history
cd ../day_05
make install
make run

# Day 6 - Testing local models on logical puzzles
cd ../day_06
make install
make run

# Day 7 - Multi-Agent System for Code Generation and Review
cd ../day_07

# Start StarCoder (required)
cd ../local_models
docker-compose up -d starcoder-chat

# Start agents via Docker Compose
cd ../day_07
make start-bridge  # Simple startup
# or
make start-traefik # With Traefik reverse proxy

# CLI usage
make demo          # Run demo
make run-simple    # Simple code generation

# Day 8 - Enhanced Token Analysis System
cd ../day_08

# Install dependencies
make install-dev

# Run comprehensive tests
make test

# Run demonstrations
make demo          # Basic demo
make demo-enhanced # Enhanced demo with reports
python examples/task_demonstration.py # TASK.md verification
```

## 📊 Project Comparison

| Project | Complexity | Technologies | Models | Features |
|---------|-----------|--------------|--------|----------|
| day_01 | ⭐ | Python, API | Perplexity | Simple chat |
| day_02 | ⭐⭐ | Python, JSON | Perplexity | JSON responses |
| day_03 | ⭐⭐ | Python, State | Perplexity | Advisor mode |
| day_04 | ⭐⭐⭐ | Python, Temperature | Perplexity | Temperature experiments |
| day_05 | ⭐⭐⭐ | Python, SDK, Docker | Local | SDK integration |
| day_06 | ⭐⭐⭐⭐ | Python, SDK, Testing | Local | Model testing |
| day_07 | ⭐⭐⭐⭐⭐ | FastAPI, Docker, Traefik | 4 models | Multi-Agent System |
| day_08 | ⭐⭐⭐⭐⭐ | Clean Architecture, DDD, ML Engineering | 4 models | Token Analysis & Compression |

## 📚 Project Descriptions

### Local Models - Local Language Model Infrastructure

🏠 **Shared module** for working with local language models. Provides a unified API for various models and can be used by any project in the repository.

**Technologies:**
- FastAPI (API server)
- Docker Compose (orchestration)
- HuggingFace Transformers
- NVIDIA CUDA (GPU acceleration)
- 4-bit quantization (memory efficiency)

**Supported Models:**
- **Qwen-4B** (port 8000) - Fast responses, ~8GB RAM
- **Mistral-7B** (port 8001) - High quality, ~14GB RAM  
- **TinyLlama-1.1B** (port 8002) - Compact, ~4GB RAM

**Key Features:**
- 🔄 **Unified API**: Standard OpenAI-compatible interface
- 🐳 **Docker Orchestration**: Automatic container management
- 🎯 **Auto-formatting**: Support for different prompt formats
- ⚡ **GPU Acceleration**: Automatic NVIDIA GPU usage
- 🔒 **Privacy**: Data never leaves local machine
- 💰 **Cost Savings**: No external API costs

**Quick Start:**
```bash
cd local_models
docker-compose up -d
curl http://localhost:8000/chat  # Test Qwen
```

**Integration:**
Used in `day_05/` and can be easily connected to any future projects.

### Shared SDK - Unified Model Interaction

🛠️ **Unified SDK** for working with various language models. Provides a consistent interface regardless of the model provider (Perplexity, ChatGPT, or local models).

**Key Features:**
- 🔄 **Unified Interface**: Same API for all models
- 🎯 **Provider Abstraction**: Easy switching between providers
- 📊 **Usage Statistics**: Token counting and cost tracking
- 🔧 **Configuration Management**: Centralized settings
- 🛡️ **Error Handling**: Standardized exception handling
- 📈 **Performance Monitoring**: Response time tracking

**Supported Providers:**
- **Perplexity**: High-quality responses
- **ChatGPT**: OpenAI's flagship model
- **Local Models**: Qwen, Mistral, TinyLlama

**Usage:**
```python
from shared.clients.model_client import ModelClient

client = ModelClient(provider="perplexity")
response = await client.chat("Hello, world!")
```

**Integration:**
Used in `day_05/` and `day_06/` for model interaction.

### Day 01 - Terminal Chat with AI

**Purpose**: Introduction to AI-powered terminal chat

**Features:**
- Simple terminal interface
- Real-time chat with AI
- Basic error handling
- Clean exit functionality

**Technologies:**
- Python 3.10+
- Perplexity API
- Terminal interface

**Quick Start:**
```bash
cd day_01
make install
make chat
```

### Day 02 - Improved Chat with JSON Responses

**Purpose**: Enhanced chat with structured JSON responses

**Features:**
- JSON-formatted responses
- Better error handling
- Improved user experience
- Response validation

**Technologies:**
- Python 3.10+
- Perplexity API
- JSON processing
- Pydantic validation

**Quick Start:**
```bash
cd day_02
make install
make chat
```

### Day 03 - Advisor Mode with Model Constraints

**Purpose**: Structured dialogue with AI advisor mode

**Features:**
- Advisor mode with constraints
- Session state management
- Context preservation
- Structured responses

**Technologies:**
- Python 3.10+
- Perplexity API
- State management
- Context handling

**Quick Start:**
```bash
cd day_03
make install
make run
```

### Day 04 - Improved Advisor Mode with Temperature

**Purpose**: Enhanced advisor mode with temperature control

**Features:**
- Temperature-based response variation
- Advanced advisor mode
- Experimentation tools
- Performance metrics

**Technologies:**
- Python 3.10+
- Perplexity API
- Temperature utilities
- Experimentation framework

**Quick Start:**
```bash
cd day_04
make install
make run
```

### Day 05 - Local Models and Message History

**Purpose**: Integration with local models and message history

**Features:**
- Local model support
- Message history
- Unified API
- SDK integration

**Technologies:**
- Python 3.10+
- Shared SDK
- Local models
- Docker integration

**Quick Start:**
```bash
cd day_05
make install
make run
```

### Day 06 - Testing Local Models on Logical Puzzles

**Purpose**: Comprehensive testing of local models on logical puzzles

**Features:**
- Logical puzzle testing
- Model comparison
- Report generation
- Performance analysis

**Technologies:**
- Python 3.10+
- Shared SDK
- Testing framework
- Report generation

**Quick Start:**
```bash
cd day_06
make install
make run
```

### Day 07 - Multi-Agent System for Code Generation and Review

🤖 **Professional system** for automated Python code generation and review using specialized AI agents. Supports multiple language models (StarCoder, Mistral, Qwen, TinyLlama).

#### Architecture

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

#### Technologies
- FastAPI (REST API for agents)
- Docker Compose (service orchestration)
- Traefik (reverse proxy and load balancer)
- Poetry (dependency management)
- Shared SDK (unified model interaction)
- Pydantic (data validation)
- pytest (testing)

#### Supported Models
- **StarCoder-7B** (default) - Specialized for code generation
- **Mistral-7B** - High quality, general-purpose model
- **Qwen-4B** - Fast responses, good quality
- **TinyLlama-1.1B** - Compact and fast

#### Key Components

**1. Code Generator Agent (port 9001)**
- Generates Python functions from descriptions
- Creates comprehensive tests
- Validates generated code
- Supports code refinement
- API endpoints: /generate, /refine, /validate

**2. Code Reviewer Agent (port 9002)**
- Analyzes code quality
- Checks PEP8 compliance
- Evaluates test coverage
- Calculates code complexity
- API endpoints: /review, /analyze-pep8, /calculate-complexity

**3. Orchestrator**
- Coordinates workflow between agents
- Manages task processing
- Saves results
- Collects statistics
- Handles errors with retry logic

**4. Communication Layer**
- HTTP client with retry logic
- Exponential backoff for resilience
- Pydantic models for validation
- Structured requests/responses

#### Key Features

- ✨ **Multi-Model Support**: Choice of 4 language models
- 🤖 **Specialized Agents**: Separate agents for generation and review
- 🔄 **Workflow Orchestration**: Automatic agent coordination
- 📊 **Quality Metrics**: PEP8, test coverage, complexity
- 🐳 **Docker Deployment**: Multiple deployment options
- 🔍 **Health Monitoring**: Endpoints for status checks
- 📈 **Statistics**: Detailed agent performance metrics
- 🛡️ **Error Handling**: Retry logic with exponential backoff
- 📝 **Comprehensive Docs**: 5 documents including architecture and deployment
- 🔒 **Security**: Multi-stage Docker builds, non-root users

#### Deployment Options

**Bridge Network (simple)**:
```bash
make start-bridge
```
- Generator: http://localhost:9001
- Reviewer: http://localhost:9002

**Traefik Reverse Proxy (production)**:
```bash
make start-traefik
```
- Generator: http://generator.localhost
- Reviewer: http://reviewer.localhost
- Traefik Dashboard: http://localhost:8080

#### Usage Examples

**CLI Generation**:
```bash
python main.py "Create a function to calculate fibonacci numbers"
```

**Python API**:
```python
from orchestrator import MultiAgentOrchestrator
from communication.message_schema import OrchestratorRequest

orchestrator = MultiAgentOrchestrator()

# Simple generation
request = OrchestratorRequest(
    task_description="Create a REST API endpoint",
    model_name="starcoder"
)
result = await orchestrator.process_task(request)

# Different models for generation and review
request = OrchestratorRequest(
    task_description="Create a data processing pipeline",
    model_name="starcoder",
    reviewer_model_name="mistral"
)
result = await orchestrator.process_task(request)
```

## Performance Optimization

### StarCoder2 GPTQ Optimization (Recommended for RTX 3070 Ti)

The system uses optimized StarCoder2-7B-GPTQ variant with:
- 4-bit GPTQ quantization (~6-7GB VRAM)
- FlashAttention for 2-3x faster inference
- BFloat16 precision
- Optimized generation parameters

**Expected Performance**:
- VRAM usage: 6-7GB (down from 14GB)
- Inference speed: 2-3x faster
- Quality: ~95% of full precision model

**Dependencies**:
- `auto-gptq`: GPTQ model loading
- `flash-attn`: Optimized attention mechanism
- `optimum`: Hugging Face optimizations

**Installation Notes**:
```bash
# flash-attn requires CUDA toolkit and may take 5-10 minutes to compile
pip install flash-attn --no-build-isolation
```

#### Workflow Process

1. **Task Submission**: User submits task description
2. **Code Generation**: Generator Agent creates code and tests
3. **Code Review**: Reviewer Agent analyzes quality
4. **Results Aggregation**: Orchestrator collects results
5. **Persistence**: Results saved to JSON
6. **Statistics Update**: Performance metrics updated

#### API Endpoints

**Generator Agent (9001)**:
- POST /generate - code generation
- POST /refine - code improvement
- POST /validate - code validation
- GET /health - health check
- GET /stats - performance statistics

**Reviewer Agent (9002)**:
- POST /review - full code review
- POST /analyze-pep8 - PEP8 analysis
- POST /analyze-test-coverage - coverage analysis
- POST /calculate-complexity - complexity calculation
- GET /health - health check
- GET /stats - performance statistics

#### Testing

```bash
# All tests
make test

# With coverage
make test-coverage

# Unit tests only
make test-unit

# Integration tests only
make test-integration
```

#### Documentation

The project includes a complete documentation set:

- **README.md** - Main documentation and quick start
- **DEVELOPER_GUIDE.md** - Developer guide
- **ARCHITECTURE.md** - Detailed system architecture
- **DEPLOYMENT.md** - Deployment guide
- **TROUBLESHOOTING.md** - Troubleshooting guide
- **API.md** - API endpoint documentation

#### SDK Integration

Uses `shared/` SDK for unified model interaction:
- Unified interface for all models
- Automatic configuration
- Error handling
- Retry logic

#### Performance

**Typical generation time**:
- StarCoder: 5-10 seconds
- Mistral: 6-12 seconds
- Qwen: 3-8 seconds
- TinyLlama: 2-5 seconds

**Resource requirements**:
- CPU: 4+ cores (recommended)
- RAM: 16GB+ (32GB for StarCoder)
- GPU: NVIDIA with 12GB+ VRAM (for StarCoder)
- Disk: 20GB+ (for models)

#### Scaling

Supports horizontal scaling:
```bash
docker-compose up -d --scale generator-agent=3 --scale reviewer-agent=2
```

#### Security

- Multi-stage Docker builds for minimal size
- Non-root users in containers
- Health checks for monitoring
- Resource limits for all services
- Traefik for secure routing

#### Monitoring

- Health endpoints for status checks
- Agent performance statistics
- All workflow results saved
- Comprehensive logging

#### Production Ready

- ✅ Comprehensive documentation
- ✅ Unit and integration tests
- ✅ Error handling with retries
- ✅ Health monitoring
- ✅ Docker multi-stage builds
- ✅ Resource management
- ✅ Security best practices
- ✅ Logging and metrics

#### Next Steps

1. Study documentation in `day_07/DEVELOPER_GUIDE.md`
2. Run demo to understand workflow
3. Experiment with different models
4. Integrate into your own projects
5. Extend functionality with new agents

### Day 08 - Enhanced Token Analysis System

🎯 **Production-ready system** for token analysis, compression, and ML model interaction. Features Clean Architecture with Domain-Driven Design, comprehensive testing, and ML Engineering framework.

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Day 08 Enhanced System                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Demo      │  │   Enhanced  │  │  SDK        │            │
│  │  Scripts    │  │  Features   │  │  Adapters   │            │
│  │             │  │             │  │             │            │
│  │ • Enhanced  │  │ • Model     │  │ • Generator │            │
│  │ • Model     │  │   Switching │  │ • Reviewer  │            │
│  │   Switching │  │ • Quality   │  │ • Direct    │            │
│  │ • Reports   │  │   Analysis  │  │ • REST      │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│         │                 │                 │                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Core Day 08 Components                        │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │ │
│  │  │   Token     │  │   Text      │  │   ML        │        │ │
│  │  │   Counter   │  │  Compressor │  │   Client    │        │ │
│  │  │             │  │             │  │             │        │ │
│  │  │ • Simple    │  │ • Strategy  │  │ • Retry     │        │ │
│  │  │ • Accurate  │  │ • Template  │  │ • Circuit   │        │ │
│  │  │ • Hybrid    │  │ • Factory   │  │ • Breaker   │        │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘        │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │ │
│  │  │   Model     │  │   Token     │  │ Compression │        │ │
│  │  │   Switcher  │  │   Limit    │  │ Evaluator   │        │ │
│  │  │             │  │   Tester   │  │             │        │ │
│  │  │ • SDK       │  │ • Three-   │  │ • All       │        │ │
│  │  │   Workflow  │  │   Stage    │  │   Algorithms│        │ │
│  │  │ • Quality   │  │ • Dynamic  │  │ • Quality   │        │ │
│  │  │   Analysis  │  │ • Model-   │  │ • Performance│       │ │
│  │  │             │  │   Specific │  │             │        │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘        │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

#### Technologies

- **Clean Architecture**: Domain, Application, Infrastructure, Presentation layers
- **Domain-Driven Design**: Entities, value objects, repositories, domain services
- **SOLID Principles**: Single responsibility, dependency injection, interface segregation
- **Design Patterns**: Strategy, Factory, Builder, Template Method, Circuit Breaker, Facade
- **ML Engineering**: Model evaluation, performance monitoring, experiment tracking, model registry
- **Comprehensive Testing**: 282 tests with 74% coverage, integration, regression, performance tests
- **Type Safety**: 100% type hints coverage in core modules
- **Quality Assurance**: Strict linting, pre-commit hooks, security scanning

#### Supported Models

- **StarCoder-7B** (default) - Specialized for code generation
- **Mistral-7B** - High quality, general-purpose model
- **Qwen-4B** - Fast responses, good quality
- **TinyLlama-1.1B** - Compact and fast

#### Key Components

**1. Token Analysis (`core/token_analyzer.py`)**
- Multiple counting strategies (simple estimation, ML-based, hybrid)
- Model-specific limits and validation
- Input/output token counting for requests and responses
- Support for all models with accurate token estimation

**2. Text Compression (`core/text_compressor.py`)**
- Strategy pattern with 5 compression algorithms
- Truncation, keywords, extractive, semantic, summarization
- Automatic compression on limit-exceeding queries
- Compression ratio calculation and quality analysis

**3. ML Client (`core/ml_client.py`)**
- Resilient client with retry logic and circuit breaker
- Request validation and error handling
- Performance monitoring and statistics
- Integration with SDK agents

**4. Experiments (`core/experiments.py`)**
- Builder pattern for experiment result construction
- Comprehensive experiment tracking and management
- Model comparison and analysis
- Structured logging and reporting

#### Key Features

- ✨ **Token Analysis**: Accurate token counting with multiple strategies
- 🗜️ **Text Compression**: 5 compression algorithms with quality evaluation
- 🏗️ **Clean Architecture**: Domain-driven design with SOLID principles
- 🧪 **Comprehensive Testing**: 282 tests with excellent coverage
- 📊 **ML Engineering**: Production-ready MLOps framework
- 🔄 **SDK Integration**: Unified agent system integration
- 📈 **Performance Monitoring**: Detailed metrics and analytics
- 🛡️ **Error Handling**: Robust exception management and retry logic
- 📝 **Documentation**: 12+ comprehensive guides and examples
- 🔒 **Security**: Input validation and security scanning

#### TASK.md Requirements Fulfillment

✅ **Requirement 1: Token Counting**
- Implementation: `core/token_analyzer.py`
- Features: Input/output token counting, multiple strategies, model limits
- Verification: All models tested with accurate token counts

✅ **Requirement 2: Query Comparison**
- Implementation: `core/token_limit_tester.py`
- Features: Three-stage testing (short/medium/long queries)
- Verification: Comprehensive query analysis and behavior documentation

✅ **Requirement 3: Text Compression**
- Implementation: `core/text_compressor.py` with strategy pattern
- Features: 5 compression algorithms, automatic application
- Verification: Compression applied to limit-exceeding queries

#### Performance Metrics

- **Token counting**: ~0.1ms per 1000 characters
- **Text compression**: ~5ms per 10KB text
- **ML requests**: ~200ms average response time
- **Memory usage**: ~50MB baseline
- **Test execution**: 282 tests in ~4.6 seconds
- **Code coverage**: 74% with comprehensive test suite

#### Production Ready Features

- ✅ **Robust Error Handling**: Comprehensive exception hierarchy
- ✅ **Type Safety**: 100% type hints in core modules
- ✅ **Security**: Input validation and sanitization
- ✅ **Monitoring**: Performance metrics and health checks
- ✅ **Documentation**: Complete API reference and guides
- ✅ **Testing**: Unit, integration, regression, performance tests
- ✅ **Quality**: PEP8 compliance, linting, pre-commit hooks
- ✅ **Architecture**: Clean Architecture with DDD patterns

#### Usage Examples

**Basic Token Counting:**
```python
from core.token_analyzer import SimpleTokenCounter
from tests.mocks.mock_config import MockConfiguration

config = MockConfiguration()
counter = SimpleTokenCounter(config=config)
token_info = counter.count_tokens("Hello world", "starcoder")
print(f"Tokens: {token_info.count}")
```

**Text Compression:**
```python
from core.text_compressor import SimpleTextCompressor

compressor = SimpleTextCompressor(token_counter)
result = compressor.compress_text(
    text="Very long text...",
    max_tokens=1000,
    model_name="starcoder",
    strategy="truncation"
)
print(f"Compression ratio: {result.compression_ratio}")
```

**Running Experiments:**
```python
from core.experiments import TokenLimitExperiments

experiments = TokenLimitExperiments(ml_client, token_counter, compressor)
results = await experiments.run_limit_exceeded_experiment("starcoder")
```

#### Next Steps

1. Study comprehensive documentation in `day_08/README.md`
2. Run `make demo` to see token analysis in action
3. Explore `examples/task_demonstration.py` for TASK.md verification
4. Review `docs/` directory for technical guides
5. Integrate token analysis into your own projects
6. Extend compression strategies for specific use cases

## 🛠️ Technologies and Dependencies

### Core Technologies
- **Python 3.10+**: Main programming language
- **Poetry**: Dependency management
- **Docker**: Containerization
- **Docker Compose**: Service orchestration
- **FastAPI**: Web framework for APIs
- **Pydantic**: Data validation
- **pytest**: Testing framework

### AI/ML Technologies
- **HuggingFace Transformers**: Model integration
- **NVIDIA CUDA**: GPU acceleration
- **4-bit Quantization**: Memory optimization
- **Local Models**: Qwen, Mistral, TinyLlama, StarCoder
- **Token Analysis**: Advanced token counting and compression strategies
- **ML Engineering**: Model evaluation, monitoring, experiment tracking

### Architecture & Design Technologies
- **Clean Architecture**: Domain, Application, Infrastructure layers
- **Domain-Driven Design**: Entities, value objects, repositories
- **SOLID Principles**: Design patterns and best practices
- **Design Patterns**: Strategy, Factory, Builder, Template Method, Circuit Breaker
- **Type Safety**: Comprehensive type hints and validation

### Infrastructure Technologies
- **Traefik**: Reverse proxy and load balancer
- **NVIDIA Container Toolkit**: GPU support
- **Multi-stage Docker builds**: Security and optimization

## 🤝 Contributing

We welcome contributions! Please see individual project README files for specific contribution guidelines.

### General Guidelines
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Code Standards
- Follow PEP 8 for Python code
- Use type hints
- Write comprehensive tests
- Document your changes
- Follow existing patterns

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- HuggingFace for model hosting and transformers library
- OpenAI for API inspiration
- The open-source community for tools and libraries
- Contributors and users of this project

---

**Note**: This is a learning project exploring AI and language models. Use responsibly and in accordance with applicable terms of service.