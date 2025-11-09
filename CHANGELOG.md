# Changelog

All notable changes to the AI Challenge project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Day 19] - 2025-11-08

### Added
- Tenacity-backed retry policy for all modular reviewer LLM calls (shared package + bridge service)
- Partial-failure handling in `MultiPassReport` with status/error metadata and trace-aware logging
- Negative test suites for modular reviewer integration (`tests/unit/application/services/test_modular_review_service.py`)
- Latency benchmarking helper for Qwen (`/v1/chat/completions`) and documentation updates (`docs/USER_GUIDE.md`, `docs/PERFORMANCE_BENCHMARKS.md`)

### Changed
- `ModularReviewService` wires Prometheus checker/pass metrics and trace-aware logging end-to-end
- UnifiedModelClient alias handling tightened; OpenAI-compatible endpoint recommended for shared `llm-api`
- Documentation refreshed to cover new environment variables (`LLM_URL`, `LLM_MODEL=qwen`) and failover guidance

### Fixed
- Reviewer integration now skips checker metrics when a pass fails and surfaces package errors in legacy reports
- Health script instructions clarified for authenticated Mongo URLs pointing at shared infra

### Performance
- Dummy LLM review averages 0.00068s; Qwen via `/v1/chat/completions` averages 4.08s across 5 runs (see docs/PERFORMANCE_BENCHMARKS.md)

## [Day 18] - 2025-11-07

### Added
- **Shared Infra Cutover**: Application connects to `infra_shared`/`infra_infra_db-network`
  services (MongoDB, Prometheus, Grafana, Mistral) with integration and e2e tests.
- **Reusable Multipass Reviewer Package**: `packages/multipass-reviewer` published with
  Clean Architecture layout, prompt embedding, configurable passes, Spark/Airflow and
  MLOps/Data checkers, plus metrics wiring.
- **Bridge Service**: `ModularReviewService` adapts the new package to existing
  repositories, adds checker-level Prometheus counters and structured logging.
- **Documentation Refresh**: Updated user guide, development guide, API docs, and new
  troubleshooting matrix for shared infra scenarios.

### Changed
- **ReviewSubmissionUseCase**: Optional dependencies default to production-grade log
  parser/normalizer/analyzer, uses feature flag to switch to modular reviewer, and reuses
  shared logger.
- **LLM Client Integration**: Added alias adapter translating package model names to shared
  infrastructure identifiers (normalises `mistral-7b-instruct-v0.2` → `mistral`).
- **E2E Pipeline**: Runs inside a dual-network container, exercising shared services,
  modular reviewer flag, and haiku generation.
- **Compose & Env**: Docker stack and `.env` defaults updated to drop local Mongo/LLM and
  rely on shared services.

### Fixed
- Prevented `Unknown model: summary` and Pydantic validation errors by normalising model
  aliases before delegating to `UnifiedModelClient`.
- Eliminated flaky e2e skips by ensuring tests attach to shared networks and supplying
  authenticated Mongo URLs.

---

## [Day 17] - 2025-11-07

### Added
- **Pass 4 Log Analysis**: End-to-end pipeline (parsers, normalizer, `LLMLogAnalyzer`) with severity thresholds and grouped RCA output.
- **Static Analysis Bundle**: Flake8, Pylint, MyPy, Black, isort executed during reviews and embedded into `MultiPassReport`.
- **MCP-first Publishing Flow**: LLM-triggered tool call (`submit_review_result`) via `MCPHTTPClient` plus resilient fallback to `ExternalAPIClient`.
- **Review Haiku Enhancements**: Unified haiku generation across passes with default fallback text.
- **Integration Contracts**: OpenAPI spec, JSON schema, cURL/Python examples, and contract tests reflecting mandatory `new_commit` field.
- **Documentation**: Updated README (EN/RU), new Day 17 architecture notes, expanded review system docs.
- **Tests**: Unit coverage for MCP publishing helpers (`test_review_submission_llm_mcp.py`) and log-analysis execution (`test_review_submission_pass4.py`).

### Changed
- **ReviewSubmissionUseCase**: Stores unified client, orchestrates static analysis + Pass 4 logs, enriches publish payloads, and routes MCP publishing with fallback.
- **SummaryWorker**: Wires `MCPHTTPClient`, fallback publisher, and new log-analysis dependencies.
- **Settings**: Added `hw_checker_mcp_url` and `hw_checker_mcp_enabled` flags for configuration.
- **Docker Compose Layout**: Archived legacy manifests to `archive/docker-compose/`; active stacks consolidated in `docker-compose.butler.yml` / `.butler.dev.yml`.
- **Makefile**: Legacy Day 11 targets continue to function via archived compose files (no runtime regressions).
- **Contracts & Guides**: `review_api_v1.yaml`, `hw_check_payload_schema.json`, `INTEGRATION_GUIDE.md` updated with mandatory `new_commit`, Pass 4 content, and haiku fields.

### Fixed
- Ensured `_extract_overall_score` handles mocked reports during tests.
- Improved resiliency around MCP tool discovery and JSON parsing of LLM responses.

### Removed
- Top-level docker compose variants (`docker-compose.yml`, `day11`, `day12`, `full`, `mcp`, `mcp-demo`) moved to archive for historical reference.

### Performance
- Reduced duplicate MCP client instantiation; reuse within `ReviewSubmissionUseCase`.
- Log analysis capped by configurable group count for predictable LLM usage.

See `docs/day17/` (architecture & integration) for deep dives and migration notes.

## [Day 15] - 2025-11-05

### Added
- **LLM-as-Judge Quality Assessment**: Automatic evaluation of summarization quality using Mistral LLM
  - Metrics: Coverage, Accuracy, Coherence, Informativeness (0.0-1.0 scale)
  - Fire-and-forget pattern: Asynchronous evaluation that doesn't block main flow
  - Implementation: `src/infrastructure/llm/evaluation/summarization_evaluator.py`
- **Automatic Fine-tuning System**: Self-improving system that fine-tunes models on high-quality samples
  - Trigger: 100+ high-quality samples (>0.8 average score)
  - Docker-based fine-tuning with Hugging Face Transformers
  - JSONL dataset export for training data
  - Implementation: `src/infrastructure/finetuning/finetuning_service.py`, `src/workers/finetuning_worker.py`
- **Advanced Summarization Strategies**:
  - **Map-Reduce Summarizer**: For texts >4000 tokens, uses hierarchical summarization
  - **Adaptive Summarizer**: For medium texts (1000-4000 tokens), single-pass with optimized prompts
  - **Semantic Chunking**: Smart text splitting that preserves semantic boundaries
- **Async Long Summarization**: Queue-based processing for large digests with 600s timeout
- **New Modules**:
  - `src/infrastructure/llm/evaluation/` - Quality assessment infrastructure
  - `src/infrastructure/llm/chunking/` - Text chunking strategies
  - `src/infrastructure/llm/summarizers/` - Multiple summarization implementations
  - `src/infrastructure/finetuning/` - Fine-tuning service
  - `src/domain/services/summary_quality_checker.py` - Quality validation
  - `src/domain/services/text_cleaner.py` - Text cleaning utilities
- **Testing Coverage**: 24 new test files (E2E, integration, unit tests)
- **Documentation**:
  - `docs/day15/README.md` - Day 15 overview and guide
  - `docs/day15/api.md` - API documentation for evaluation and fine-tuning
  - `docs/day15/MIGRATION_FROM_DAY12.md` - Migration guide
  - `docs/architecture/SUMMARIZATION_CURRENT_STATE.md` - Comprehensive architecture (1,623 lines)
  - Module-level READMEs for llm, finetuning, and mcp tools channels
- **Infrastructure**:
  - Enhanced `docker-compose.butler.yml` with fine-tuning support
  - Grafana dashboard for quality metrics
  - Stress test results documented
- **Configuration Files**:
  - `.editorconfig` - Editor configuration
  - `.gitattributes` - Git attributes for line endings
  - `.importlinter` - Import linting for Clean Architecture
  - Enhanced `.pre-commit-config.yaml` with docstring coverage, spell checking, markdown link checking

### Changed
- Updated `AI_CONTEXT.md` to Day 15 status with new modules and features
- Updated `README.md` and `README.ru.md` with Day 15 completion status
- Enhanced tag extraction in channel digests (hashtag extraction implemented)
- Added language toggle headers to bilingual documentation
- Improved Makefile with new automation targets (`make check-all`, `make security`, etc.)

### Fixed
- Resolved TODO comments in `generate_channel_digest_by_name.py` (tag extraction)
- Fixed import organization and code quality standards

### Performance
- Async processing for long summarization tasks
- Queue-based processing prevents blocking
- Stress test results documented

See [docs/release_notes/day_15.md](docs/release_notes/day_15.md) for complete release notes.

## [Day 14] - 2025-11-04

### Added
- Multi-Pass Code Review system with 3-pass architecture:
  - **Pass 1: Architecture Overview** - Detects project structure and components
  - **Pass 2: Component Deep-Dive** - Per-component technology-specific analysis
  - **Pass 3: Synthesis** - Integration analysis and recommendations
- Automatic component detection (Airflow, Spark, MLflow, Docker, generic)
- Technology-specific review passes with specialized prompts
- Comprehensive markdown report generation with haiku summaries
- Homework review integration via Telegram bot (`homework_review_tool`)
- Session-based state management for multi-pass reviews
- Review logger for detailed review process tracking
- Code quality checker integration (flake8, pylint, mypy, black, isort)
- Test fixture optimization (reduced from 100 to 15 files for large_project)
- AI assistant documentation:
  - `AI_CONTEXT.md` - Comprehensive project context for AI assistants
  - `.cursorrules` - Coding standards and conventions
- Docker compose file cleanup (removed outdated files)

### Changed
- Updated README.md with Day 14 completion status and docker-compose clarifications
- Enhanced homework review workflow with multi-pass analysis
- Improved report generation with structured findings and metadata

### Fixed
- Session file restoration from TELEGRAM_SESSION_STRING environment variable
- Test fixture reduction to optimize repository size

## [Unreleased]

### Added
- MCP-aware agent (`MCPAwareAgent`) with automatic tool discovery and execution
- MCP Tools Registry (`MCPToolsRegistry`) with 5-minute caching for tool metadata
- Robust MCP Client (`RobustMCPClient`) with exponential backoff retry logic
- Dialog Manager (`DialogManager`) for MongoDB-based conversation history
- History Compressor (`HistoryCompressor`) for LLM-based dialog compression
- Graceful shutdown manager (`GracefulShutdown`) for clean service termination
- Prometheus metrics integration for agent operations
- Path utilities (`path_utils.py`) for centralized shared package imports
- Agent integration documentation (`docs/AGENT_INTEGRATION.md` and `.ru.md`)
- Comprehensive test suite for agent components (26+ tests)

### Changed
- Refactored `summary_worker.py` (700 lines → 258 lines) into modular structure:
  - Extracted `formatters.py` for message formatting (format_summary, format_single_digest, clean_markdown)
  - Extracted `message_sender.py` for message sending with retry logic and error handling
  - Extracted `data_fetchers.py` for data fetching (get_summary_text, get_digest_texts)
  - Improved code readability and maintainability following Clean Architecture principles
- Replaced `sys.path.insert` anti-pattern with centralized `ensure_shared_in_path()` utility
- Extracted magic numbers into class constants (DEFAULT_MODEL_NAME, MAX_RETRIES, COMPRESSION_THRESHOLD, etc.)
- Enhanced docstrings with usage examples following Google Style Guide
- Updated Dockerfile.bot: unified Python version to 3.10, improved healthcheck, added ENTRYPOINT
- Updated README.md and README.ru.md with MCP-aware agent documentation

### Fixed
- Completed unfinished tests: `test_process_request_tool_selection` and `test_process_request_invalid_tool`
- Removed unused imports (`Type` from `mcp_client_robust.py`)
- Fixed Dockerfile.bot healthcheck to verify actual bot module import
- Improved error handling in agent with more specific exceptions

## [Day 12] - 2025-01-XX

### Added
- PDF digest generation via MCP tools (`get_posts_from_db`, `summarize_posts`, `format_digest_markdown`, `combine_markdown_sections`, `convert_markdown_to_pdf`)
- Post collection worker (`PostFetcherWorker`) with hourly schedule for automatic post collection from subscribed Telegram channels
- Hybrid deduplication system (message_id + content_hash) to prevent duplicate posts
- PDF caching mechanism with 1-hour TTL for improved performance
- Post repository (`PostRepository`) with MongoDB integration and TTL support (7 days)
- PDF digest bot handler with automatic fallback to text digest on errors
- Comprehensive test suite: 63 tests (40 unit, 6 integration, 5 E2E, 12 contract tests)
- PDF digest API documentation (`docs/day12/api.md`)
- PDF digest user guide (`docs/day12/USER_GUIDE.md`)
- PDF digest architecture documentation with Mermaid diagrams (`docs/day12/ARCHITECTURE.md`)

### Changed
- Digest generation now reads from MongoDB instead of Telegram API (faster, more reliable)
- `get_channel_digest` updated to use database queries instead of direct API calls
- `fetch_channel_posts` now supports automatic saving to database via repository
- Settings extended with PDF-related configuration (`pdf_cache_ttl_hours`, `pdf_summary_sentences`, `pdf_summary_max_chars`, `pdf_max_posts_per_channel`)

### Fixed
- Post deduplication prevents duplicate entries in database
- Error handling improved with graceful fallback mechanisms
- Empty digest handling with informative user messages

### Performance
- PDF caching reduces regeneration time (instant delivery on cache hit)
- MongoDB indexes optimize post queries
- Limits prevent token overflow (max 100 posts per channel, max 10 channels)

## [Day 11] - 2025-01-XX

### Added
- FSM-based conversation flow for multi-turn task creation
- Clarifying questions for ambiguous task inputs
- Enhanced intent orchestrator with context-aware parsing (Russian/English)
- Domain value objects for task summary and digest formatting (`TaskSummary`, `DigestMessage`)
- Comprehensive test suite: unit, integration, E2E, and contract tests
- MCP tools API documentation with examples (`docs/API_MCP_TOOLS.md`)
- Architecture diagrams for FSM flow (`docs/ARCHITECTURE_FSM.md`)
- Quick start guide for Day 11 features (`docs/QUICK_START_DAY11.md`)
- Telegram bot menu integration with summary and digest callbacks
- State persistence middleware for FSM conversations
- Natural language task creation with intent parsing

### Changed
- Refactored `reminder_tools.py`: extracted query builder and stats calculator into helpers
- All functions now ≤15 lines (extracted from large functions)
- Improved Russian language support in intent parsing
- Menu summary/digest handlers now fully functional via MCP tools
- Enhanced error handling with user-friendly messages

### Fixed
- Missing `asyncio` import in `summarizer.py` (line 246)
- Debug print statements replaced with structured logging
- Timezone handling in `get_summary` simplified
- Overdue task calculation (excludes completed tasks)

### Performance
- Token cost reduced through helper extraction
- Test coverage maintained at 76%+ (target: 80%+)

## [Day 10] - 2024-12-25

### Added
- MCP (Model Context Protocol) integration with 10 tools
- Mistral orchestrator with intent parsing and workflow planning
- Result caching with TTL support (ResultCache service)
- Error recovery with exponential backoff
- Plan optimization service (ExecutionOptimizer)
- Context window management with automatic summarization
- Dynamic prompts and static resources (7 resources, 2 prompts)
- Streaming chat interface for better UX
- Docker optimization with multi-stage builds
- Comprehensive test suite (unit, integration, e2e)
- Security hardening (non-root user, minimal image)
- Health check endpoint for Docker containers
- Production readiness validation scripts
- Quality check automation scripts

### Changed
- Optimized Docker image size (<2GB)
- Improved error handling in MCP tools
- Enhanced logging with structured output
- Simplified Makefile by removing duplicate commands
- Consolidated example files

### Fixed
- Memory leaks in long-running conversations
- Race conditions in concurrent tool execution
- Context window token limit errors

## [Unreleased - Previous]

### Added
- Clean Architecture implementation with Domain-Driven Design
- Multi-agent orchestrator for code generation and review workflows
- Comprehensive test suite with 311 tests and 76.10% coverage
- MCP (Model Context Protocol) integration for AI assistants
- Health check system with model and storage monitoring
- CLI interface with status, health, metrics, and config commands
- Dashboard for real-time metrics visualization
- Support for multiple language models (StarCoder, Mistral, Qwen, TinyLlama)
- Token analysis and compression features
- Experiment tracking and management

### Changed
- Refactored from monolithic architecture to Clean Architecture
- Reorganized codebase following SOLID principles
- Improved error handling and logging

### Fixed
- Memory leaks in agent workflows
- Race conditions in parallel orchestrator
- Token counting accuracy issues

## [1.0.0] - 2024-01-01

### Added
- Initial Clean Architecture implementation
- Basic multi-agent orchestration
- Core domain entities and services
- Infrastructure layer with repository patterns
- Presentation layer with FastAPI and CLI

### Changed
- Restructured from legacy day-based structure to Clean Architecture

## [0.9.0] - 2023-12-25

### Added
- Day 08: Enhanced Token Analysis System
- Day 07: Multi-Agent System for Code Generation and Review
- Day 06: Testing local models on logical puzzles
- Day 05: Local models and message history
- Day 04: Improved advisor mode with temperature
- Day 03: Advisor mode with model constraints
- Day 02: Improved chat with JSON responses
- Day 01: Terminal chat with AI

---

## Types of Changes

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** in case of vulnerabilities

