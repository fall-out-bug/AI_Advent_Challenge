# AI Advent Challenge

[English](README.md) | [Русский](README.ru.md)

> Daily AI-powered projects exploring language models and multi-agent systems

## Overview

This repository contains **daily challenges** building AI-powered systems with language models. Each day introduces new concepts and builds upon previous challenges.

**Current Status:** ✅ Day 12 - PDF Digest Generation System

**Key Features:**
- ✅ 12 daily challenges from simple chat to production-ready PDF digest system
- ✅ Clean Architecture with SOLID principles
- ✅ 382+ tests with 76%+ coverage
- ✅ Multi-model support (StarCoder, Mistral, Qwen, TinyLlama)
- ✅ MCP (Model Context Protocol) integration
- ✅ FSM-based Telegram bot with natural language task creation
- ✅ PDF digest generation with automatic post collection
- ✅ Hybrid deduplication (message_id + content_hash)
- ✅ PDF caching for improved performance
- ✅ Health monitoring and metrics dashboard
- ✅ Comprehensive CLI and REST API
- ✅ Local model infrastructure with Docker
- ✅ Production-ready code quality
- ✅ Token-optimized for AI development

**Challenge Progression:**
1. **Day 1-2**: Basic terminal chat with AI
2. **Day 3-4**: Advisor mode with temperature control
3. **Day 5-6**: Local models and testing framework
4. **Day 7-8**: Multi-agent systems and token analysis
5. **Day 9**: MCP (Model Context Protocol) integration
6. **Day 10**: Production-ready MCP system with orchestration and streaming
7. **Day 11**: Butler Bot with FSM conversation flow and natural language task creation
8. **Day 12**: PDF Digest generation with automatic post collection and hybrid deduplication

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
├── tasks/           # Daily Challenges (day_01 - day_10)
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

## Technologies

**Core**: Python 3.10+, Poetry, Docker, FastAPI, Pydantic, pytest

**AI/ML**: HuggingFace Transformers, NVIDIA CUDA, 4-bit Quantization, Local Models

**Architecture**: Clean Architecture, Domain-Driven Design, SOLID Principles, Design Patterns

**Infrastructure**: Traefik, NVIDIA Container Toolkit, Multi-stage Docker builds

## Day 12 — PDF Digest Generation System

PDF digest generation system with automatic post collection from Telegram channels. Generates PDF documents containing AI-summarized channel posts with caching and error handling.

Key features:
- PDF digest generation via MCP tools (5 tools)
- Automatic hourly post collection via `PostFetcherWorker`
- Hybrid deduplication (message_id + content_hash) prevents duplicates
- PDF caching with 1-hour TTL for instant delivery
- MongoDB storage with 7-day TTL for automatic cleanup
- Graceful error handling with fallback to text digest
- Comprehensive test suite (63 tests: unit, integration, E2E, contract)

Key modules:
- `src/presentation/mcp/tools/pdf_digest_tools.py` — 5 MCP tools for PDF generation
- `src/infrastructure/repositories/post_repository.py` — Post storage with deduplication
- `src/workers/post_fetcher_worker.py` — Hourly post collection worker
- `src/infrastructure/cache/pdf_cache.py` — PDF caching mechanism
- `src/presentation/bot/handlers/menu.py` — Bot handler with PDF generation

Quick start:

```bash
# Ensure MongoDB is running
docker-compose up -d mongodb

# Run post fetcher worker (hourly collection)
python src/workers/post_fetcher_worker.py

# Or run bot for PDF digest generation
make run-bot
```

See [docs/day12/USER_GUIDE.md](docs/day12/USER_GUIDE.md) for user guide and [docs/day12/api.md](docs/day12/api.md) for API documentation.

## Day 11 — Butler Bot with FSM Conversation Flow

Telegram bot with finite state machine (FSM) for natural language task creation. Supports Russian and English, intent parsing, and clarification questions.

Key features:
- FSM-based conversation flow for multi-turn task creation
- Intent parsing with clarification questions (Russian/English)
- MCP tools integration for task management
- Scheduled notifications (morning summaries, evening digests)
- Modular worker architecture (700→258 lines)

See [QUICK_START_DAY11.md](docs/QUICK_START_DAY11.md) for detailed guide.

## Documentation

- [DEVELOPMENT.md](docs/DEVELOPMENT.md) - Setup, deployment, and operations
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture
- [TESTING.md](docs/TESTING.md) - Testing strategy and guidelines
- [MCP_GUIDE.md](docs/MCP_GUIDE.md) - MCP integration guide
- [USER_GUIDE.md](docs/USER_GUIDE.md) - User guide
- [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) - Complete API reference
- [Day 12 PDF Digest](docs/day12/) - PDF digest documentation
  - [API Documentation](docs/day12/api.md) - MCP tools API reference
  - [User Guide](docs/day12/USER_GUIDE.md) - PDF digest usage guide
  - [Architecture](docs/day12/ARCHITECTURE.md) - System architecture with diagrams
- [INDEX.md](docs/INDEX.md) - Documentation index

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Key Guidelines
- Follow PEP 8 and Zen of Python
- Functions max 15 lines where possible
- 100% type hints coverage
- 80%+ test coverage
- Document all changes

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- HuggingFace for model hosting and transformers library
- OpenAI for API inspiration
- The open-source community for tools and libraries
- Contributors and users of this project

---

**Note**: This is a learning project exploring AI and language models. Use responsibly and in accordance with applicable terms of service.
