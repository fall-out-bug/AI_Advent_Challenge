<!-- 50dd257e-6b11-4ab6-9e80-c03a68efc014 9d53a6a6-9aca-4f4d-a479-b5e634403123 -->
# Phase 4: Complete MCP System with Advanced Features

## Overview

Complete Phase 2 implementation and add advanced orchestrator features to create a production-ready MCP development assistant system.

## Part 1: Complete Phase 2 (MCP Resources & Tests)

### 1.1 MCP Resources Implementation

**Create**: `src/presentation/mcp/resources/prompts.py`

- `get_python_developer_prompt()` - Python developer system prompt
- `get_architect_prompt()` - Software architect system prompt
- `get_technical_writer_prompt()` - Technical writing prompt
- `get_coding_standards()` - JSON config for coding standards

**Create**: `src/presentation/mcp/resources/templates.py`

- `get_project_structure_template()` - Standard Python project structure
- `get_pytest_template()` - Pytest test template
- `get_class_template()` - Python class template

**Wire in**: `src/presentation/mcp/server.py`

- Add `@mcp.resource()` decorators for all resources
- Use format: `@mcp.resource("prompts://python-developer")`

### 1.2 Dynamic Prompts

**Create**: `src/presentation/mcp/prompts/code_review.py`

- `code_review_prompt(code, language, style)` - Generate review prompt dynamically
- Use variables from plan spec lines 318-336

**Create**: `src/presentation/mcp/prompts/test_generation.py`

- `test_generation_prompt(code, framework)` - Generate test prompt dynamically
- Use variables from plan spec lines 337-352

**Wire in**: `src/presentation/mcp/server.py`

- Add `@mcp.prompt()` decorators for dynamic prompts
- Format: `@mcp.prompt("code-review")`

### 1.3 Comprehensive Testing

**Create**: `tests/unit/presentation/mcp/test_format_adapter.py`

- Test format_code with valid Python code
- Test formatter validation (black, autopep8)
- Test error handling for invalid code

**Create**: `tests/unit/presentation/mcp/test_complexity_adapter.py`

- Test analyze_complexity metrics extraction
- Test radon integration
- Test detailed vs simple mode

**Create**: `tests/unit/presentation/mcp/test_test_generation_adapter.py`

- Test test generation with mock models
- Test framework selection (pytest, unittest)
- Test coverage calculation

**Create**: `tests/integration/test_mcp_resources.py`

- Test resource discovery and retrieval
- Test prompt templates generation
- Test dynamic prompt variable substitution

### 1.4 Docker Optimization

**Update**: `Dockerfile.mcp`

- Add multi-stage build to reduce image size
- Optimize layer caching for dependencies
- Add .dockerignore file

**Update**: `docker-compose.mcp.yml`

- Add healthcheck dependencies
- Optimize resource limits
- Add network isolation

## Part 2: Advanced Orchestrator Features

### 2.1 Result Caching

**Create**: `src/application/services/result_cache.py`

- `ResultCache` class with TTL support
- Cache tool results keyed by tool_name + hashed args
- Thread-safe with lock mechanism
- Optional cache warming from conversation history

**Integrate**: `src/presentation/mcp/orchestrators/mcp_mistral_wrapper.py`

- Check cache before tool execution
- Store successful results in cache
- Bypass cache for specific tools (e.g., formalize_task)

**Config**: `config/mistral_orchestrator.yml`

- Add `cache_enabled: true`, `cache_ttl: 3600`

### 2.2 Error Recovery & Retries

**Update**: `src/presentation/mcp/orchestrators/mcp_mistral_wrapper.py`

- Add `async _execute_tool_with_retry()` method
- Exponential backoff retry logic
- Retry on timeout and network errors
- Configurable max retries (default: 3)

**Update**: `src/application/orchestrators/mistral_orchestrator.py`

- Add fallback responses for model failures
- Graceful degradation when tools unavailable
- Continue workflow on non-critical failures

### 2.3 Plan Optimization

**Update**: `src/application/orchestrators/mistral_orchestrator.py`

- Add `_optimize_plan()` method
- Remove redundant tool calls
- Reorder tools for parallel execution where possible
- Detect circular dependencies

**Add**: `ExecutionOptimizer` class in `src/application/services/plan_optimizer.py`

- Analyze tool dependencies
- Suggest parallel execution groups
- Estimate execution time

### 2.4 Context Window Management

**Create**: `src/application/services/context_manager.py`

- `ContextManager` class managing conversation context
- Automatic summarization when approaching token limits
- Sliding window for message history
- Priority-based message retention

**Integrate**: `src/application/orchestrators/mistral_orchestrator.py`

- Check context size before each model call
- Summarize old messages when needed
- Preserve recent messages and tool results

### 2.5 Streaming Support

**Create**: `src/presentation/mcp/cli/streaming_chat.py`

- Streaming version of interactive chat
- Display partial responses as they arrive
- Better UX for long-running operations

**Update**: `UnifiedModelClient` wrapper (if needed)

- Support streaming flag in requests
- Yield chunks as they arrive
- Handle partial responses gracefully

## Part 3: Documentation & Examples

### 3.1 Update Documentation

**Create**: `tasks/day_10/README.phase4.md`

- Document new features (caching, retries, optimization)
- Usage examples for resources and prompts
- Configuration reference

**Update**: `README.md`

- Add Phase 4 section
- Update architecture diagram
- Add quick start for complete system

### 3.2 Enhanced Examples

**Create**: `examples/day10_advanced_demo.py`

- Demonstrate caching behavior
- Show error recovery in action
- Test plan optimization
- Context management examples

## Success Criteria

- [ ] All Phase 2 resources and prompts implemented and wired
- [ ] Unit tests with 80%+ coverage for new adapters
- [ ] Docker image optimized to <2GB
- [ ] Result caching reduces duplicate tool calls by 50%+
- [ ] Error recovery handles failures gracefully with retries
- [ ] Plan optimization reduces execution time by 20%+
- [ ] Context management prevents token limit errors
- [ ] All features documented with examples
- [ ] Clean Architecture maintained throughout
- [ ] Functions ≤15 lines per requirement

### To-dos

- [ ] Create MCP resources (prompts.py, templates.py) with @mcp.resource decorators in server.py
- [ ] Create dynamic prompts (code_review.py, test_generation.py) with @mcp.prompt decorators
- [ ] Write unit tests for format_adapter, complexity_adapter, test_generation_adapter
- [ ] Optimize Dockerfile.mcp with multi-stage build and improve docker-compose.mcp.yml
- [ ] Implement ResultCache service and integrate caching in MCP wrapper
- [ ] Add error recovery and retry logic with exponential backoff to MCP wrapper
- [ ] Implement plan optimization to reduce redundant calls and enable parallel execution
- [ ] Add context window management with automatic summarization for long conversations
- [ ] Update documentation with Phase 4 features and enhanced examples
- [ ] Create integration tests for complete workflows including caching and error recovery
