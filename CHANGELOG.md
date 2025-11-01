# Changelog

All notable changes to the AI Challenge project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

