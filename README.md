# AI Advent Challenge

[English](README.md) | [Русский](README.ru.md)

> Daily AI-powered projects exploring language models and multi-agent systems

## 🎯 Overview

This repository contains **daily challenges** building AI-powered systems with language models. Each day introduces new concepts and builds upon previous challenges.

**Current Status:** ✅ Day 09 - MCP Integration Complete

**Repository Structure:**
- `tasks/day_XX/` - Daily challenge implementations (Day 1-9)
- `src/` - Core Clean Architecture implementation
  - `domain/` - Business entities, services, and value objects
  - `application/` - Use cases and orchestrators
  - `infrastructure/` - Clients, repositories, monitoring, health
  - `presentation/` - API and CLI interfaces
- `local_models/` - Local language model infrastructure
- `shared/` - Unified SDK for model interaction
- `scripts/` - Maintenance and quality scripts
- `config/` - YAML configuration files
- `docs/` - Complete documentation

**Key Features:**
- ✅ 9 daily challenges from simple chat to multi-agent systems
- ✅ Clean Architecture with SOLID principles
- ✅ 311 tests with 76.10% coverage
- ✅ Multi-model support (StarCoder, Mistral, Qwen, TinyLlama)
- ✅ MCP (Model Context Protocol) integration
- ✅ Health monitoring and metrics dashboard
- ✅ Comprehensive CLI and REST API
- ✅ Local model infrastructure with Docker
- ✅ Production-ready code quality

**Challenge Progression:**
1. **Day 1-2**: Basic terminal chat with AI
2. **Day 3-4**: Advisor mode with temperature control
3. **Day 5-6**: Local models and testing framework
4. **Day 7-8**: Multi-agent systems and token analysis
5. **Day 9**: MCP (Model Context Protocol) integration

**Quick Start:**
1. Choose a challenge from `tasks/day_XX/`
2. Follow the challenge's README for setup
3. Run the challenge to explore AI capabilities

## 🚀 Quick Start

```bash
# Install dependencies
make install

# Run tests
make test

# Run the API
make run-api

# Run the CLI
make run-cli
```

## 📁 Project Structure

```
AI_Challenge/
├── src/                   # 🏗️ Clean Architecture Core
│   ├── domain/           # Business logic layer
│   ├── application/      # Use cases and orchestrators
│   ├── infrastructure/   # External integrations
│   ├── presentation/     # API and CLI
│   └── tests/           # Test suite (311 tests, 76.10% coverage)
├── tasks/                # 📚 Daily Challenges
│   ├── day_01/          # Day 1 - Terminal chat with AI
│   ├── day_02/          # Day 2 - Improved chat with JSON
│   ├── day_03/          # Day 3 - Advisor mode
│   ├── day_04/          # Day 4 - Temperature control
│   ├── day_05/          # Day 5 - Local models
│   ├── day_06/          # Day 6 - Testing framework
│   ├── day_07/          # Day 7 - Multi-agent system
│   ├── day_08/          # Day 8 - Token analysis
│   └── day_09/          # Day 9 - MCP integration
├── local_models/         # 🏠 Local model infrastructure
│   ├── chat_api.py      # FastAPI server
│   ├── docker-compose.yml
│   └── README.md
├── shared/               # 🛠️ SDK for model interaction
│   ├── config/          # Model configuration
│   ├── clients/         # Model clients
│   ├── exceptions/      # Error handling
│   └── README.md
├── scripts/              # 🔧 Utility scripts
├── config/               # ⚙️ Configuration files
│   ├── models.yml
│   └── experiment_templates/
├── docs/                 # 📖 Documentation
│   ├── USER_GUIDE.md
│   ├── API_DOCUMENTATION.md
│   ├── ARCHITECTURE.md
│   └── INDEX.md
├── archive/legacy/      # 📦 Archived legacy implementations
├── CHANGELOG.md          # 📜 Version history
└── CONTRIBUTING.md       # 🤝 Contribution guidelines
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

## 📊 Daily Challenges Overview

| Day | Focus Area | Key Technologies | Status |
|-----|------------|------------------|--------|
| Day 1 | Basic chat interface | Python, API | ✅ Complete |
| Day 2 | JSON structured responses | Python, JSON parsing | ✅ Complete |
| Day 3 | Advisor mode | Python, Session management | ✅ Complete |
| Day 4 | Temperature control | Python, Experimentation | ✅ Complete |
| Day 5 | Local models | SDK, Docker, FastAPI | ✅ Complete |
| Day 6 | Testing framework | Testing, Report generation | ✅ Complete |
| Day 7 | Multi-agent systems | FastAPI, Docker, Orchestration | ✅ Complete |
| Day 8 | Token analysis | Clean Architecture, ML Engineering | ✅ Complete |
| Day 9 | MCP integration | MCP Protocol, Context management | ✅ Complete |

## 📚 Daily Challenges

### Core Infrastructure

#### Local Models (`local_models/`)
Local language model infrastructure with FastAPI servers supporting multiple models.

**Models:**
- **Qwen-4B** (port 8000) - Fast responses, ~8GB RAM
- **Mistral-7B** (port 8001) - High quality, ~14GB RAM  
- **TinyLlama-1.1B** (port 8002) - Compact, ~4GB RAM
- **StarCoder-7B** (port 9000) - Specialized for code generation

#### Shared SDK (`shared/`)
Unified SDK for model interaction across all challenges.

**Usage:**
```python
from shared.clients.model_client import ModelClient
client = ModelClient(provider="perplexity")
response = await client.chat("Hello, world!")
```

### Daily Challenges

Each challenge builds upon previous concepts:

**Day 1-2** (`tasks/day_01`, `tasks/day_02`)  
Basic terminal chat with AI, JSON responses

**Day 3-4** (`tasks/day_03`, `tasks/day_04`)  
Advisor mode with temperature control and session management

**Day 5-6** (`tasks/day_05`, `tasks/day_06`)  
Local models integration, testing framework with logical puzzles

**Day 7-8** (`tasks/day_07`, `tasks/day_08`)  
Multi-agent systems for code generation and review, token analysis

**Day 9** (`tasks/day_09`)  
MCP (Model Context Protocol) integration

To explore a challenge:
```bash
cd tasks/day_XX  # Choose day 1-9
cat *_simple.md  # Read challenge description
# Follow instructions in challenge files
```


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

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Quick Start
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `make test`
5. Submit a pull request

### Key Guidelines
- Follow PEP 8 and Zen of Python
- Functions max 15 lines where possible
- 100% type hints coverage
- 80%+ test coverage
- Document all changes

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- HuggingFace for model hosting and transformers library
- OpenAI for API inspiration
- The open-source community for tools and libraries
- Contributors and users of this project

---

**Note**: This is a learning project exploring AI and language models. Use responsibly and in accordance with applicable terms of service.