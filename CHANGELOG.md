# Changelog

All notable changes to the AI Challenge project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Refactored `summary_worker.py` (700 lines → 258 lines) into modular structure:
  - Extracted `formatters.py` for message formatting (format_summary, format_single_digest, clean_markdown)
  - Extracted `message_sender.py` for message sending with retry logic and error handling
  - Extracted `data_fetchers.py` for data fetching (get_summary_text, get_digest_texts)
  - Improved code readability and maintainability following Clean Architecture principles
- Updated tests to use new modular structure

### Fixed
- Implemented TODO in `client.py`: added tool call parsing in interactive mode (supports JSON and key=value formats)

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

