# AI Advent Challenge

[English](README.md) | [Русский](README.ru.md)

> Daily AI-powered projects exploring language models and multi-agent systems

## Overview

This repository contains daily challenges building AI-powered systems with language models. Each day introduces new concepts and builds upon previous challenges.

**Current Status:** ✅ Day 14 Complete - Multi-Pass Code Review & MCP Homework Review

**Project Status:**
- ✅ 14 daily challenges completed
- ✅ Clean Architecture fully implemented
- ✅ 400+ tests with 80%+ coverage
- ✅ Production-ready multi-agent system
- ✅ Comprehensive documentation for AI assistants

**Key Features:**
- ✅ 14 daily challenges from simple chat to production-ready multi-agent systems
- ✅ Clean Architecture with SOLID principles
- ✅ 400+ tests with 80%+ coverage
- ✅ Multi-model support (StarCoder, Mistral, Qwen, TinyLlama)
- ✅ MCP (Model Context Protocol) integration with HTTP server
- ✅ MCP-aware agent with automatic tool discovery and execution
- ✅ FSM-based Telegram bot with natural language task creation
- ✅ **Hybrid Intent Recognition** (Rule-based + LLM with caching)
- ✅ **HW Checker integration** (all_checks_status, queue_status, retry_check)
- ✅ **Homework Review via Telegram** (list homeworks, review by commit hash)
- ✅ Channel digests with metadata support (title, description)
- ✅ PDF digest generation with automatic post collection
- ✅ Centralized logging system with structured output
- ✅ Health monitoring and metrics dashboard
- ✅ Hotreload for development (uvicorn --reload + watchdog)
- ✅ **Multi-Pass Code Review** (3-pass architecture for homework analysis)

## Quick Start

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

For detailed setup instructions, see [DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Project Structure

```
AI_Challenge/
├── src/              # Clean Architecture Core
│   ├── domain/      # Business logic layer
│   ├── application/ # Use cases and orchestrators
│   ├── infrastructure/ # External integrations
│   └── presentation/   # API and CLI
├── tasks/           # Daily Challenges (day_01 - day_12)
├── local_models/    # Local model infrastructure
├── shared/          # Unified SDK for model interaction
├── scripts/         # Utility scripts
├── config/          # Configuration files
└── docs/            # Complete documentation
```

## Daily Challenges

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
| Day 10 | Production MCP system | MCP, Streaming, Orchestration | ✅ Complete |
| Day 11 | Butler Bot FSM | Telegram Bot, FSM, Intent Parsing | ✅ Complete |
| Day 12 | PDF Digest System | MongoDB, PDF Generation, MCP Tools | ✅ Complete |
| Day 13 | Butler Agent Refactoring | Hybrid Intent Recognition, HW Checker, Metadata | ✅ Complete |
| Day 14 | Multi-Pass Code Review | MCP Homework Review, 3-Pass Analysis | ✅ Complete |

## Core Infrastructure

### Local Models
- **Qwen-4B** (port 8000) - Fast responses, ~8GB RAM
- **Mistral-7B** (port 8001) - High quality, ~14GB RAM  
- **TinyLlama-1.1B** (port 8002) - Compact, ~4GB RAM
- **StarCoder-7B** (port 9000) - Specialized for code generation

### Shared SDK
Unified SDK for model interaction across all challenges.

```python
from shared.clients.model_client import ModelClient
client = ModelClient(provider="perplexity")
response = await client.chat("Hello, world!")
```

## Docker Compose Files

The project uses multiple docker-compose files for different scenarios:

- **`docker-compose.yml`** - Main/default services (MongoDB, basic setup)
- **`docker-compose.day11.yml`** - Butler Bot system (Telegram bot, MCP server, Mistral)
- **`docker-compose.day12.yml`** - Full system with Post Fetcher & PDF Digest (Day 12 features)
- **`docker-compose.mcp-demo.yml`** - MCP demo services for testing

**Quick Start:**
```bash
# Day 12 (current production setup)
make day-12-up

# Day 11 (Butler Bot only)
make day-11-up

# MCP Demo
make mcp-demo-start
```

## Current Features (Day 14)

**Butler Agent System:**
- **Hybrid Intent Recognition**: Two-layer architecture (rule-based + LLM fallback) with caching
- **HW Checker Integration**: Full status monitoring, queue management, and retry functionality
- **Homework Review**: List recent commits and perform code review via Telegram bot
- **Multi-Pass Code Review**: 3-pass architecture (Architecture → Component → Synthesis) for comprehensive code analysis
- **Channel Metadata**: Automatic title and description fetching from Telegram API
- **Enhanced Digests**: Adaptive summary length based on post count, time-aware prompts
- **Markdown Escaping**: Safe Telegram message formatting
- **Hotreload Development**: Fast iteration with automatic code reloading

**PDF Digest Generation System:**
- PDF digest generation via MCP tools (5 tools)
- Automatic hourly post collection via `PostFetcherWorker`
- Hybrid deduplication (message_id + content_hash)
- PDF caching with 1-hour TTL for instant delivery
- MongoDB storage with 7-day TTL for automatic cleanup

**MCP-Aware Agent:**
- Automatic tool discovery via MCPToolsRegistry (5-minute cache)
- LLM-based tool selection and execution
- Robust retry logic with exponential backoff
- Dialog history management with automatic compression
- Prometheus metrics integration

Quick start:
```bash
# Ensure MongoDB is running
docker-compose up -d mongodb

# Run post fetcher worker (hourly collection)
python src/workers/post_fetcher_worker.py

# Or run bot for PDF digest generation
make run-bot
```

**Homework Review Commands:**
- `Покажи домашки` - List recent homework commits with status
- `Сделай ревью {commit_hash}` - Download archive and perform code review
- Review results are sent as Markdown files via Telegram

**Day 14 - Multi-Pass Code Review:**
- 3-pass architecture for comprehensive code analysis
- Automatic component detection (Airflow, Spark, MLflow, Docker)
- Technology-specific deep-dive analysis
- Integration synthesis and recommendations
- Markdown report generation with haiku summaries

See [docs/day12/USER_GUIDE.md](docs/day12/USER_GUIDE.md) for user guide and [docs/day12/api.md](docs/day12/api.md) for API documentation.

## AI Assistant Support

This repository includes comprehensive documentation for AI-assisted development:

- **[AI_CONTEXT.md](AI_CONTEXT.md)** - Complete project context for AI assistants
- **[.cursorrules](.cursorrules)** - Coding standards and conventions
- **[docs/INDEX.md](docs/INDEX.md)** - Organized documentation index

These files help AI coding assistants understand the project structure, patterns, and conventions.

## Technologies

**Core**: Python 3.10+, Poetry, Docker, FastAPI, Pydantic, pytest

**AI/ML**: HuggingFace Transformers, NVIDIA CUDA, 4-bit Quantization, Local Models

**Architecture**: Clean Architecture, Domain-Driven Design, SOLID Principles

**Infrastructure**: Traefik, NVIDIA Container Toolkit, Multi-stage Docker builds

## Documentation

Main documentation:
- [DEVELOPMENT.md](docs/DEVELOPMENT.md) - Setup, deployment, and operations
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture
- [USER_GUIDE.md](docs/USER_GUIDE.md) - User guide
- [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) - Complete API reference
- [AGENT_INTEGRATION.md](docs/AGENT_INTEGRATION.md) - MCP-aware agent integration guide
- [MONITORING.md](docs/MONITORING.md) - Monitoring setup and Grafana dashboards
- [SECURITY.md](docs/SECURITY.md) - Security policies and practices

Day 12 documentation:
- [PDF Digest User Guide](docs/day12/USER_GUIDE.md)
- [PDF Digest API](docs/day12/api.md)
- [PDF Digest Architecture](docs/day12/ARCHITECTURE.md)

See [docs/INDEX.md](docs/INDEX.md) for complete documentation index.

## Monitoring

```bash
# Start monitoring stack (Prometheus + Grafana)
docker-compose -f docker-compose.day12.yml up -d prometheus grafana

# Access Grafana: http://localhost:3000 (admin/admin)
# Access Prometheus: http://localhost:9090
```

Available dashboards:
1. **App Health** - System resources, HTTP metrics, latency, availability
2. **ML Service Metrics** - LLM inference latency, token usage, model versioning
3. **Post Fetcher & PDF Metrics** - Post collection and PDF generation metrics

See [MONITORING.md](docs/MONITORING.md) for detailed setup.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

**Key Guidelines:**
- Follow PEP 8 and Zen of Python
- Functions max 15 lines where possible
- 100% type hints coverage
- 80%+ test coverage
- Document all changes

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Note**: This is a learning project exploring AI and language models. Use responsibly and in accordance with applicable terms of service.
