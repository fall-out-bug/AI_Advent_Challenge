# Phase 0: Code Quality Report

**Generated:** 2025-01-27  
**Scope:** Butler Agent refactoring baseline analysis

## Executive Summary

This report establishes a baseline for code quality metrics before Phase 1-7 refactoring. Current state shows significant technical debt in file sizes, complexity, and type coverage.

## Key Findings

### Critical Issues (Immediate Attention Required)

1. **Large Files (>150 lines):**
   - `src/domain/agents/mcp_aware_agent.py`: **696 lines** - Violates SRP
   - `src/presentation/bot/butler_bot.py`: **554 lines** - Needs handler extraction
   - `src/presentation/mcp/tools/pdf_digest_tools.py`: **406 lines** - Needs decomposition
   - Total: **3 files** exceed recommended size

2. **High Complexity Methods:**
   - `MCPAwareAgent._stage_execution`: **Complexity F** (354 lines)
   - `MCPAwareAgent._parse_response`: **Complexity C** (65 lines)
   - `ButlerBot._send_long_response_as_pdf`: **Complexity C**
   - `ButlerBot._handle_digest_intent`: **Complexity C**
   - `ButlerBot.handle_natural_language`: **Complexity C**

3. **Type Coverage:**
   - Current mypy errors: **150+ violations**
   - Critical issues:
     - Missing return type annotations: **20+ functions**
     - Returning Any type: **40+ functions**
     - No stub libraries: yaml, dateparser, pytz, radon

## Linter Results

### flake8 Results

```
Total violations: 2,649

Breakdown:
- E501: 1,151 violations (line too long >79 chars)
- W293: 877 violations (blank line contains whitespace)
- W291: 120 violations (trailing whitespace)
- W391: 120 violations (blank line at end of file)
- E402: 49 violations (module level import not at top)
- E128: 140 violations (continuation line under-indented)
- E128: 140 violations (continuation line under-indented)
- F401: 138 violations (imported but unused)
- E502: 1 violation (continuation line with same indent)
- E129: 2 violations (visually indented line)
- E203: 2 violations (whitespace before ':')
- E302: 5 violations (expected 2 blank lines)
- E303: 2 violations (too many blank lines)
- E305: 2 violations (expected 2 blank lines after class/function)
- E722: 2 violations (bare 'except')
- E741: 2 violations (ambiguous variable name 'l')
- F541: 4 violations (f-string missing placeholders)
- F811: 8 violations (redefinition of unused)
- F821: 3 violations (undefined name)
- F841: 21 violations (local variable assigned but never used)
```

### mypy Results

**Total Errors:** 150+ violations

**Top Categories:**
- Import-not-found: 10+ (shared_package, transformers)
- Missing stubs: 5+ (yaml, dateparser, pytz, radon)
- No-untyped-def: 30+ (missing return type annotations)
- No-any-return: 40+ (functions returning Any)
- Invalid type usage: 20+ (Using 'any' instead of Any)
- Assignment errors: 20+ (type mismatches)
- Attribute errors: 15+ (missing attributes)

**Files with Most Errors:**
1. `src/infrastructure/monitoring/logger.py`: 10+ errors
2. `src/domain/agents/base_agent.py`: 10+ errors
3. `src/infrastructure/config/model_selector.py`: 10+ errors
4. `src/domain/services/token_analyzer.py`: 5+ errors
5. `src/infrastructure/monitoring/prometheus_metrics.py`: 10+ errors

## Complexity Analysis

### Cyclomatic Complexity

**mcp_aware_agent.py:**
- `_stage_execution`: **F** (Very high - needs splitting)
- `_parse_response`: **C** (High - needs refactoring)
- Average complexity: **D** (29.0)

**butler_bot.py:**
- `_send_long_response_as_pdf`: **C**
- `_handle_digest_intent`: **C**
- `handle_natural_language`: **C**
- Average complexity: **C** (13.67)

### Function Length Analysis

**mcp_aware_agent.py** (696 lines, 14 methods):
- `process`: 135 lines - **VIOLATION** (>40 recommended)
- `_stage_execution`: 354 lines - **CRITICAL VIOLATION** (>150)
- `_stage_decision`: 30 lines ✓
- `_call_llm`: 45 lines - **VIOLATION**
- `_parse_response`: 65 lines - **VIOLATION**
- `_format_tool_result`: 11 lines ✓

**butler_bot.py** (554 lines):
- `handle_natural_language`: 80+ lines - **VIOLATION**
- `_handle_digest_intent`: 60+ lines - **VIOLATION**

## Architectural Smells

### 1. God Class: MCPAwareAgent

**Location:** `src/domain/agents/mcp_aware_agent.py`

**Responsibilities (SRP Violation):**
1. LLM communication (decision, calling)
2. MCP tool execution
3. Channel resolution
4. Parameter normalization
5. Response formatting
6. Error handling & metrics
7. Parsing (Russian, intent)
8. Tool validation
9. Tracing/debugging

**Recommendation:** Split into:
- `DecisionEngine` (LLM-based decision making)
- `ToolExecutor` (MCP tool execution)
- `ResponseFormatter` (formatting)
- `ParameterNormalizer` (parameter mapping)

### 2. Layer Violation: Domain → Infrastructure/Presentation

**Location:** `src/domain/agents/mcp_aware_agent.py`

**Imports from outer layers:**
```python
from src.presentation.mcp.tools_registry import MCPToolsRegistry
from src.presentation.mcp.client import MCPClientProtocol
from src.infrastructure.llm.openai_chat_client import OpenAIChatClient
from src.infrastructure.config.settings import get_settings
from src.infrastructure.monitoring.agent_metrics import AgentMetrics, LLMMetrics
```

**Impact:** Domain layer depends on infrastructure/presentation, violating Clean Architecture

**Recommendation:** Create abstractions/interfaces in domain layer

### 3. Long Parameter Lists

**Examples:**
- `_stage_execution(tool_name, tool_params, tools, user_id)` - 4 params ✓
- `process(request)` - OK via dataclass ✓

## Token Cost Estimation

Based on function lengths and complexity:

| File | Function | Lines | Est. Tokens | Risk |
|------|----------|-------|-------------|------|
| mcp_aware_agent.py | `_stage_execution` | 354 | ~8,000 | 🔴 High |
| mcp_aware_agent.py | `process` | 135 | ~3,500 | 🟡 Medium |
| mcp_aware_agent.py | `_parse_response` | 65 | ~1,500 | 🟡 Medium |
| butler_bot.py | `handle_natural_language` | 80 | ~2,000 | 🟡 Medium |

**Total Risk:** High token costs for large functions during AI-assisted refactoring.

## Priority Recommendations

### High Priority (Phase 1)

1. **Split `mcp_aware_agent.py`:**
   - Extract `_stage_execution` → `ToolExecutionService` (infrastructure)
   - Extract decision logic → `DecisionEngine` (domain)
   - Extract formatting → `ResponseFormatter` (domain)

2. **Fix architecture violations:**
   - Move abstractions to domain layer
   - Remove direct imports from infrastructure/presentation

3. **Reduce complexity:**
   - Refactor `_stage_execution` 354 lines → 5 methods of <40 lines
   - Extract channel resolution logic
   - Extract parameter normalization

### Medium Priority (Phase 2-3)

1. **Fix type annotations:**
   - Add return types to all functions
   - Install stub libraries: `types-yaml`, `types-dateparser`
   - Resolve `Any` return types

2. **Fix style violations:**
   - Fix 1,151 long lines (E501)
   - Remove 877 whitespace lines (W293)
   - Remove unused imports (F401)

### Low Priority (Phase 4-7)

1. **Code cleanup:**
   - Remove bare except blocks (E722)
   - Fix ambiguous variable names (E741)
   - Remove debug print statements

## Metrics Summary

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| Files >150 lines | 3 | 0 | 3 |
| Functions >40 lines | 8+ | 0 | 8+ |
| mypy errors | 150+ | 0 | 150+ |
| flake8 violations | 2,649 | <100 | 2,549 |
| Complexity (avg) | D | B | 2 levels |
| Type coverage | ~70% | 100% | 30% |

## Next Steps

1. Share findings with team for Phase 1 planning
2. Prioritize `mcp_aware_agent.py` refactoring
3. Create architectural diagrams for split strategy
4. Set up CI/CD checks for complexity and type coverage

## References

- [Python Zen](https://peps.python.org/pep-0020/)
- [Clean Code JavaScript](https://github.com/ryanmcdermott/clean-code-javascript) (applies to Python)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

