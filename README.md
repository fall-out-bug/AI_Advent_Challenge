# AI Advent Challenge

[English](README.md) | [Русский](README.ru.md)

> Daily AI-powered projects exploring language models and multi-agent systems

## Overview

This repository contains daily challenges building AI-powered systems with language models. Each day introduces new concepts and builds upon previous challenges.

**Updates:** Project news and daily recaps are published in the Telegram channel [Высоконагруженный кабанчик](https://t.me/data_intensive_boar).

**Current Status:** 🏆 Day 25 COMPLETED & DEPLOYED — Personalised Butler with Alfred-style дворецкий persona, user profiles, and memory management (Epic 25). Voice commands integrated (Epic 24), observability & benchmarks delivered (Epic 23).

### Day 21 (Completed)
- Summary: `docs/specs/epic_21/epic_21.md`
- Archive Index: `docs/specs/epic_21/ARCHIVE_INDEX.md`
- Demo quick start:
  - `make day_21_demo` — interactive console demo
  - `make day_21_batch` — batch run on 10 questions
  - `make day_21_metrics` — print key rag_* metrics

**Project Status:**
- ✅ 25 daily challenges completed
- ✅ Clean Architecture fully implemented (Day 21)
- ✅ Security hardening deployed (path traversal protection, input validation)
- ✅ Quality automation established (pre-commit hooks, automated linting)
- ✅ Production-ready multi-agent system with self-improvement
- ✅ Automatic quality evaluation and fine-tuning
- ✅ Comprehensive documentation for AI assistants
- ✅ **Personalised Butler** (Day 25) with user profiles, memory, and interest extraction

**Key Features:**
- ✅ 25 daily challenges from simple chat to observability, benchmarks, voice commands, and personalization
- ✅ Clean Architecture with SOLID principles
- ✅ 420+ tests with 80%+ coverage
- ✅ Multi-model support (StarCoder, Mistral, Qwen, TinyLlama)
- ✅ MCP (Model Context Protocol) integration with HTTP server
- ✅ MCP-aware agent with automatic tool discovery and execution
- ✅ FSM-based Telegram bot for channel management and digest delivery
- ✅ **Hybrid Intent Recognition** (Rule-based + LLM with caching)
- ✅ **HW Checker integration** (all_checks_status, queue_status, retry_check)
- ✅ **Homework Review via Telegram** (list homeworks, review by commit hash)
- ✅ Channel digests with metadata support (title, description)
- ✅ PDF digest generation with automatic post collection
- ✅ Centralized logging system with structured output
- ✅ Health monitoring and metrics dashboard
- ✅ Hotreload for development (uvicorn --reload + watchdog)
- ✅ **Multi-Pass Code Review** (3-pass architecture for homework analysis)
- ✅ **LLM-as-Judge Quality Assessment** (automatic evaluation of summaries)
- ✅ **Self-Improving System** (automatic fine-tuning on high-quality data)
- ✅ **Stage 05 RU Benchmarks** (release-cadence quality scoreboard for channel digests & reviewer summaries)
- ✅ **Async Long Summarization** (queue-based processing with 600s timeout)
- ✅ **Code Review Queue System** (Day 17 - async review pipeline with diff analysis)
- ✅ **Pass 4 Log Analysis** (LLM-powered grouping, classification, and RCA for runtime logs)
- ✅ **Static Analysis Integration** (Flake8, Pylint, MyPy, Black, isort in the review loop)
- ✅ **MCP-first Publishing** (LLM calls external HW Checker MCP tool with automatic HTTP fallback)
- ✅ **Haiku Generation** (poetic postscript highlighting review sentiment)
- ✅ **Integration Contracts** (OpenAPI spec, JSON schema, cURL/Python examples for partners)
- ✅ **Personalised Butler** (Day 25 - user profiles, memory management, "Alfred-style дворецкий" persona, automatic interest extraction)

## Quick Start

```bash
# Install dependencies
make install

# Start shared infrastructure (MongoDB, Prometheus, reviewer API)
./scripts/infra/start_shared_infra.sh

# Load shared infra credentials for Mongo/Prometheus
set -a
source ~/work/infra/.env.infra
set +a
export MONGODB_URL="mongodb://admin:${MONGO_PASSWORD}@127.0.0.1:27017/butler_test?authSource=admin"

# Run tests (local baseline 429 pass / 2 xfail due to latency thresholds)
poetry run pytest -q

# Run the API
make run-api

# Backoffice CLI
poetry run python -m src.presentation.cli.backoffice.main --help
```

### Document Embedding Index

```bash
# Load credentials (example)
export MONGO_USER=admin
export MONGO_PASSWORD=$(cat ~/work/infra/secrets/mongo_password.txt)
export MONGODB_URL="mongodb://${MONGO_USER}:${MONGO_PASSWORD}@127.0.0.1:27017/butler?authSource=admin"
export TEST_MONGODB_URL="$MONGODB_URL"
export REDIS_HOST=127.0.0.1
export REDIS_PORT=6379
export REDIS_PASSWORD=$(cat ~/work/infra/secrets/redis_password.txt)

# Build index across docs + lecture corpora
poetry run python -m src.presentation.cli.backoffice.main index run

# Inspect summary counts
poetry run python -m src.presentation.cli.backoffice.main index inspect
```

See `docs/specs/epic_19/stage_19_04_runbook.md` for detailed instructions,
troubleshooting, and maintenance guidance.

### Large Data Files

Some large JSONL files (>500KB) are stored in compressed format (.gz) to reduce repository size:
- `results_stage20.jsonl.gz` (compressed from 555KB to ~148KB, 26.5% of original)
- `results_with_labels.jsonl.gz` (compressed from 555KB to ~148KB, 26.5% of original)

To decompress:
```bash
gunzip results_stage20.jsonl.gz
gunzip results_with_labels.jsonl.gz
```

To compress new JSONL files:
```bash
python scripts/tools/compress_jsonl.py <file.jsonl>
```

For detailed setup instructions, see [DEVELOPMENT.md](docs/guides/en/DEVELOPMENT.md) and the [Maintainer Playbook](docs/MAINTAINERS_GUIDE.md).

## Project Structure

```
AI_Challenge/
├── src/              # Clean Architecture Core
│   ├── domain/      # Business logic layer
│   ├── application/ # Use cases and orchestrators
│   ├── infrastructure/ # External integrations
│   └── presentation/   # API and CLI
├── tasks/           # Daily Challenges (historical archive)
├── archive/legacy/local_models/    # Archived local model infrastructure (deprecated)
├── shared/          # Unified SDK for model interaction
├── scripts/         # Utility scripts (infra, maintenance, quality)
├── config/          # Configuration files
└── docs/            # Specifications, guides, references, archives
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
| Day 15 | Quality Assessment & Fine-tuning | LLM-as-Judge, Self-Improving System, Hugging Face | ✅ Complete |
| Day 17 | Code Review Platform & MCP Publishing | Async queue, static analysis, log diagnostics, MCP tool calls | ✅ Complete |
| Day 18 | Performance Benchmarks | Prometheus, Benchmarking | ✅ Complete |
| Day 19 | Document Embedding Index | Redis/FAISS, Mongo, LLM API | ✅ Complete |
| Day 20 | RAG vs Non‑RAG Answering Agent | Retrieval, LLM-as-Judge | ✅ Complete |
| Day 21 | Repository Refactor & RAG++ | Clean Architecture, Reranking, Observability | ✅ Complete |
| Day 22 | RAG Citations & Source Attribution | RAG, MongoDB, Vector Search | ✅ Complete |
| Day 23 | Observability & Benchmark Enablement | Prometheus, Grafana, Loki, Benchmarks | ✅ Complete |
| Day 24 | Voice Commands Integration | Telegram Bot, Whisper STT, Butler Orchestrator | ✅ Complete |
| Day 25 | Personalised Butler | User Profiles, Memory Management, Interest Extraction, Alfred-style дворецкий | ✅ Complete |

## Core Infrastructure

### Local Models (archived)
- Local model containers are deprecated in favor of shared infrastructure.
- Legacy manifests are preserved under `archive/legacy/local_models/`.

### Shared SDK
Unified SDK for model interaction across all challenges.

```python
from shared.clients.model_client import ModelClient
client = ModelClient(provider="perplexity")
response = await client.chat("Hello, world!")
```

### Stage 05 Benchmark Smoke (Dry Run)

```bash
poetry run python scripts/quality/benchmark/run_benchmark.py \
  --scenario channel_digest_ru \
  --dataset data/benchmarks/benchmark_digest_ru_v1/2025-11-09_samples.jsonl \
  --dry-run --fail-on-warn
```

The `--dry-run` flag reuses stored judge scores, enabling CI smoke checks without
incurring LLM costs. Omit it to execute live evaluations (requires shared infra
credentials).

## Code Review System

- **Five-pass insight pipeline**: Architecture overview → Component deep dives → Synthesis → Static analysis (Flake8, Pylint, MyPy, Black, isort) → Pass 4 log analysis with LLM-generated classification, root-cause, and remediation tips.
- **Archive-aware diffing**: ZIP ingestion, semantic diff analysis, and repository persistence via `ReviewSubmissionUseCase`.
- **Runtime diagnostics**: `LogParserImpl` + `LogNormalizer` feed curated groups into `LLMLogAnalyzer` with severity thresholds and configurable timeouts.
- **Creative postscript**: Automatic haiku summarises review tone and highlights key risks.
- **Publishing workflow**: LLM invokes the external HW Checker MCP tool (`submit_review_result`) through `MCPHTTPClient`; resilient fallback reuses `ExternalAPIClient` when needed.
- **Integration assets**: Contracts live in `contracts/` (OpenAPI spec, JSON schema, examples) with deep-dive docs under `docs/day17/` and `docs/reference/en/review_system_architecture.md`.
- **Observability-first**: Structured review logs, Prometheus metrics, and MongoDB audit trail for every session.

## Docker Compose Files

Primary entry points:

- **`docker-compose.butler.yml`** – production stack (MongoDB, MCP server, workers, bot, Prometheus, Grafana).
- **`docker-compose.butler.dev.yml`** – development variant with hot reload and lightweight defaults.

Legacy configurations (Day 11/12 demos, full GPU stacks, experimental layouts) now live under `archive/docker-compose/`. Existing `make` targets keep working and reference the archived manifests.

**Quick Start:**
```bash
# Run the full Butler/Day 17 stack
make butler-up

# Tear down when finished
make butler-down

# Explore the legacy Day 11 demo (still available via archive files)
make day-11-up
```

## Current Features

**Self-Improving LLM System:**
- **LLM-as-Judge**: Automatic quality assessment using Mistral (coverage, accuracy, coherence, informativeness)
- **Automatic Fine-tuning**: Self-improvement by training on high-quality samples (100+ samples trigger)
- **Asynchronous Evaluation**: Fire-and-forget pattern, no blocking of main flow
- **Extensible Architecture**: Support for multiple fine-tuning tasks (summarization, classification, Q&A)
- **Docker-based ML**: Full Hugging Face Transformers integration in containers
- **Dataset Management**: Automatic JSONL export for fine-tuning datasets

**Butler Agent System:**
- **Hybrid Intent Recognition**: Two-layer architecture (rule-based + LLM fallback) with caching
- **HW Checker Integration**: Full status monitoring, queue management, and retry functionality
- **Homework Review**: List recent commits and perform code review via Telegram bot
- **Multi-Pass Code Review Platform**: Architecture → Components → Synthesis → Static Analysis → Pass 4 Log Insights + Haiku
- **LLM-driven MCP Publishing**: Tool calling against external HW Checker MCP with resilient HTTP fallback
- **Static Analysis Bundle**: Flake8, Pylint, MyPy, Black, isort results embedded into review reports
- **Runtime Log Triage**: Grouping, classification, and remediation tips generated by the LLM
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

**Personalised Butler (Day 25):**
- **User Profiles**: Auto-created profiles with "Alfred-style дворецкий" persona
- **Memory Management**: Remembers last 50 messages per user with automatic compression
- **Interest Extraction**: Automatically extracts user interests from conversations (Task 16)
- **Alfred Persona**: Witty, caring, respectful responses (English humour, Russian language)
- **Voice Integration**: Works with voice messages via Whisper STT
- **Privacy**: All data stored locally in MongoDB (no external SaaS)
- See [Personalized Butler User Guide](docs/guides/personalized_butler_user_guide.md) for details

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

**Day 17 - Code Review Platform Enhancements:**
- Static analysis (Flake8, Pylint, MyPy, Black, isort) bundled into every report
- Pass 4 log analysis with severity filtering, grouping, and LLM-derived root causes
- External MCP publishing invoked directly by the reviewer LLM (with HTTP fallback)
- Integration contracts (OpenAPI, JSON schema, cURL/Python) for external consumers
- Markdown report enriched with consolidated findings, log diagnostics, and haiku postscript

See [docs/day12/USER_GUIDE.md](docs/day12/USER_GUIDE.md) for user guide and [docs/day12/api.md](docs/day12/api.md) for API documentation.

## AI Assistant Support

This repository includes comprehensive documentation for AI-assisted development:

- **[AI_CONTEXT.md](AI_CONTEXT.md)** - Complete project context for AI assistants
- **[.cursorrules](.cursorrules)** - Coding standards and conventions
- **[docs/INDEX.md](docs/INDEX.md)** - Organized documentation index

These files help AI coding assistants understand the project structure, patterns, and conventions.

## Technologies

**Core**: Python 3.10+, Poetry, Docker, FastAPI, Pydantic, pytest

**AI/ML**: HuggingFace Transformers, PyTorch, NVIDIA CUDA, 4-bit Quantization, Local Models, Fine-tuning

**Architecture**: Clean Architecture, Domain-Driven Design, SOLID Principles, LLM-as-Judge Pattern

**Infrastructure**: Traefik, NVIDIA Container Toolkit, Multi-stage Docker builds, MongoDB, Prometheus

## Documentation

Main documentation:
- [DEVELOPMENT.md](docs/guides/en/DEVELOPMENT.md) - Setup, deployment, and operations
- [ARCHITECTURE.md](docs/reference/en/ARCHITECTURE.md) - System architecture
- [USER_GUIDE.md](docs/guides/en/USER_GUIDE.md) - User guide
- [API_DOCUMENTATION.md](docs/reference/en/API_DOCUMENTATION.md) - Complete API reference
- [AGENT_INTEGRATION.md](docs/guides/en/AGENT_INTEGRATION.md) - MCP-aware agent integration guide
- [MONITORING.md](docs/reference/en/MONITORING.md) - Monitoring setup and Grafana dashboards
- [SECURITY.md](docs/reference/en/SECURITY.md) - Security policies and practices

Day 15 documentation (current):
- [Quality Assessment & Fine-tuning Guide](docs/day15/README.md)
- [API Documentation](docs/day15/api.md)
- [Migration from Day 12](docs/day15/MIGRATION_FROM_DAY12.md)

Day 12 documentation:
- [PDF Digest User Guide](docs/day12/USER_GUIDE.md)
- [PDF Digest API](docs/day12/api.md)
- [PDF Digest Architecture](docs/day12/ARCHITECTURE.md)

See [docs/INDEX.md](docs/INDEX.md) for complete documentation index.

## Monitoring

```bash
# Start monitoring stack (Prometheus + Grafana)
docker-compose -f docker-compose.butler.yml up -d prometheus grafana

# Access Grafana: http://localhost:3000 (admin/admin)
# Access Prometheus: http://localhost:9090
```

Available dashboards:
1. **App Health** - System resources, HTTP metrics, latency, availability
2. **ML Service Metrics** - LLM inference latency, token usage, model versioning
3. **Post Fetcher & PDF Metrics** - Post collection and PDF generation metrics
4. **Quality Assessment Metrics** - Evaluation scores, fine-tuning runs, dataset growth

See [MONITORING.md](docs/reference/en/MONITORING.md) for detailed setup.

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
