<!-- 6cf1b895-cf7e-43fc-86ec-f8c6c6a9e7b2 c91dda0f-231b-429d-884c-1665a6aa156b -->
# Phase 2 Plan — Complete MCP Server Tools & Resources

## Scope

Building on Phase 1's foundation:

- Add 3 remaining MCP tools: `generate_tests`, `format_code`, `analyze_complexity`
- Add MCP resources (prompts, config templates)
- Add dynamic MCP prompts
- Comprehensive error handling and validation
- Docker optimization and multi-stage builds
- Integration tests

## What We Have (Phase 1)

✅ MCP server running with FastMCP

✅ Tools: `formalize_task`, `generate_code`, `review_code`, `list_models`, `check_model`, `count_tokens`, `generate_and_review`

✅ Adapters wired through `MCPApplicationAdapter`

✅ Shared SDK (`UnifiedModelClient`) integration with local_models

✅ Docker containerization (basic)

✅ Healthcheck script

## Deliverables

1. **Three New MCP Tools**

   - `generate_tests(code, test_framework, coverage_target)` - Generate comprehensive tests
   - `format_code(code, formatter, line_length)` - Format code using black/autopep8
   - `analyze_complexity(code, detailed)` - Cyclomatic/cognitive complexity analysis

2. **MCP Resources** (static context)

   - `prompts://python-developer` - Python-specific development guidelines
   - `prompts://architect` - Architecture and design patterns
   - `prompts://technical-writer` - Documentation standards
   - `config://coding-standards` - PEP8, line length, type hints
   - `templates://project-structure` - Standard project layouts

3. **Dynamic MCP Prompts**

   - `code-review` - Context-aware review prompt builder
   - `test-generation` - Framework-specific test generation prompt

4. **Enhanced Error Handling**

   - Structured exception hierarchy
   - Retry logic with exponential backoff
   - Timeout handling
   - Graceful degradation

5. **Docker Optimization**

   - Multi-stage build
   - Layer caching
   - Smaller final image (~500MB vs 2GB+)
   - Health checks for MCP + local_models connectivity

## Files to Create/Update

### New Adapters

- `src/presentation/mcp/adapters/test_generation_adapter.py` - Test generation logic
- `src/presentation/mcp/adapters/format_adapter.py` - Code formatting using black
- `src/presentation/mcp/adapters/complexity_adapter.py` - radon/complexity metrics

### MCP Resources

- `src/presentation/mcp/resources/prompts.py` - Static prompt resources
- `src/presentation/mcp/resources/templates.py` - Project structure templates
- `src/presentation/mcp/resources/config.py` - Coding standards config

### Dynamic Prompts

- `src/presentation/mcp/prompts/code_review.py` - Dynamic review prompts
- `src/presentation/mcp/prompts/test_generation.py` - Dynamic test prompts

### Server Updates

- `src/presentation/mcp/server.py` - Add 3 new tools + register resources/prompts
- `src/presentation/mcp/adapters.py` - Wire new adapters

### Docker

- `Dockerfile.mcp` - Multi-stage build, optimized layers
- `docker-compose.mcp.yml` - Enhanced healthchecks, restart policies
- `.dockerignore` - Exclude unnecessary files

### Tests

- `tests/unit/presentation/mcp/test_test_generation_adapter.py`
- `tests/unit/presentation/mcp/test_format_adapter.py`
- `tests/unit/presentation/mcp/test_complexity_adapter.py`
- `tests/integration/mcp/test_mcp_tools_e2e.py` - End-to-end MCP tool tests

### Docs

- `tasks/day_10/README.phase2.md` - Phase 2 usage guide
- Update `tasks/day_10/README.phase1.md` - Link to Phase 2

## Implementation Strategy

### 1. Test Generation Adapter (2-3 hours)

Reuse existing test generation logic from `CodeGeneratorAgent`:

```python
class TestGenerationAdapter:
    """Adapter for generating tests using shared SDK."""

    async def generate_tests(
        self,
        code: str,
        test_framework: str = "pytest",
        coverage_target: int = 80
    ) -> dict:
        # Build prompt for test generation
        # Call UnifiedModelClient via ModelClientAdapter
        # Parse test code from response
        # Estimate coverage
        return {
            "success": True,
            "test_code": "...",
            "test_count": 5,
            "coverage_estimate": 85,
            "test_cases": ["test_basic", "test_edge_case", ...]
        }
```

### 2. Format Adapter (1-2 hours)

Use `black` programmatically (no model calls):

```python
import black

class FormatAdapter:
    """Adapter for code formatting using black."""

    def format_code(
        self,
        code: str,
        formatter: str = "black",
        line_length: int = 100
    ) -> dict:
        if formatter == "black":
            mode = black.Mode(line_length=line_length)
            formatted = black.format_str(code, mode=mode)
            changes = len(code) != len(formatted)
            return {
                "formatted_code": formatted,
                "changes_made": int(changes),
                "formatter_used": "black"
            }
```

### 3. Complexity Adapter (1-2 hours)

Use `radon` for static analysis:

```python
from radon.complexity import cc_visit
from radon.metrics import mi_visit

class ComplexityAdapter:
    """Adapter for code complexity analysis."""

    def analyze_complexity(
        self,
        code: str,
        detailed: bool = True
    ) -> dict:
        # Cyclomatic complexity via radon
        cc_results = cc_visit(code)
        # Maintainability index
        mi_score = mi_visit(code, multi=True)

        return {
            "cyclomatic_complexity": max(r.complexity for r in cc_results),
            "cognitive_complexity": ...,  # Custom metric
            "lines_of_code": len(code.splitlines()),
            "maintainability_index": mi_score,
            "recommendations": [...]
        }
```

### 4. MCP Resources (2 hours)

Add static resources using FastMCP `@mcp.resource()` decorator:

```python
@mcp.resource("prompts://python-developer")
def get_python_dev_prompt() -> str:
    return """Expert Python developer guidelines:
 - PEP 8 compliant
 - Type hints required
 - Google-style docstrings
 - Error handling with specific exceptions
    ..."""

@mcp.resource("config://coding-standards")
def get_coding_standards() -> str:
    return json.dumps({
        "python": {
            "style": "pep8",
            "line_length": 100,
            "type_hints": "required"
        }
    })
```

### 5. Dynamic Prompts (1-2 hours)

Context-aware prompts using `@mcp.prompt()`:

```python
@mcp.prompt("code-review")
def code_review_prompt(code: str, language: str, focus: list) -> str:
    return f"""Review this {language} code:

    {code}

    Focus areas: {', '.join(focus)}

    Provide:
 - Quality score (0-100)
 - Issues by severity
 - Recommendations"""
```

### 6. Docker Optimization (2 hours)

Multi-stage build:

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY src/ /app/src/
COPY shared/ /app/shared/
ENV PATH=/root/.local/bin:$PATH
WORKDIR /app
ENTRYPOINT ["python", "src/presentation/mcp/server.py"]
```

## Validation Criteria

- [ ] All 3 new tools callable via MCP client
- [ ] `generate_tests` produces valid pytest code
- [ ] `format_code` uses black correctly
- [ ] `analyze_complexity` returns radon metrics
- [ ] Resources discoverable via `mcp.list_resources()`
- [ ] Dynamic prompts work with parameters
- [ ] Docker image < 1GB
- [ ] Healthcheck passes for server + local_models
- [ ] 80%+ test coverage on new adapters
- [ ] No breaking changes to Phase 1 tools

## Testing Strategy

1. **Unit Tests** - Mock UnifiedModelClient, test adapter logic
2. **Integration Tests** - Real MCP client → server → adapters (mock models)
3. **E2E Tests** - Full stack with local_models running

## Dependencies

- `black>=23.0.0` - Code formatting
- `radon>=6.0.0` - Complexity analysis
- `pytest` - For test framework support

## Timeline Estimate

- Test generation adapter: 2-3 hours
- Format adapter: 1-2 hours
- Complexity adapter: 1-2 hours
- MCP resources: 2 hours
- Dynamic prompts: 1-2 hours
- Docker optimization: 2 hours
- Tests: 2-3 hours
- Documentation: 1 hour

**Total**: ~12-15 hours (2 working days)

## Risks & Mitigations

- **Risk**: black/radon dependencies bloat Docker image
  - **Mitigation**: Multi-stage build, strip unnecessary files

- **Risk**: Test generation quality varies by model
  - **Mitigation**: Add validation, fallback templates

- **Risk**: Complexity metrics for non-Python code
  - **Mitigation**: Start Python-only, document limitations

### To-dos

- [ ] Create TestGenerationAdapter with pytest support
- [ ] Create FormatAdapter using black programmatically
- [ ] Create ComplexityAdapter using radon metrics
- [ ] Wire 3 new adapters through MCPApplicationAdapter
- [ ] Add 3 new @mcp.tool() definitions in server.py
- [ ] Add @mcp.resource() for prompts, config, templates
- [ ] Add @mcp.prompt() for code-review and test-generation
- [ ] Create multi-stage Dockerfile with optimized layers
- [ ] Enhance healthcheck to verify local_models connectivity
- [ ] Write unit tests for 3 new adapters
- [ ] Write MCP client → server integration tests
- [ ] Create README.phase2.md with usage examples
