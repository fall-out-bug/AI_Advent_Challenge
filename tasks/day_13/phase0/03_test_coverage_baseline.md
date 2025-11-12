# Phase 0: Test Coverage Baseline

**Generated:** 2025-01-27
**Scope:** Butler Agent test coverage analysis for Phase 1-7 refactoring

## Executive Summary

Current test coverage is **40.10%**, well below the 80% target. This report analyzes test distribution, identifies gaps, and provides a roadmap to achieve comprehensive coverage across unit, integration, and e2e tests.

## Coverage Metrics

### Overall Coverage

**Current:** 40.10%
**Target:** 80%+
**Gap:** -39.90%

**Breakdown:**
- Total lines: **8,573**
- Covered lines: **5,135** (59.90%)
- Missing lines: **3,438** (40.10%)

### Test Results Summary

```
Tests run: 446 total
- ✅ Passed: 358 (80.3%)
- ❌ Failed: 20 (4.5%)
- ⚠️  Errors: 68 (15.2%)
```

### Test Distribution

**By Type:**
- Unit tests: **6 files** (target: 30+)
- Integration tests: **11 files**
- E2E tests: **3 files**

**Total Test Files:** 54

## Coverage Gaps by Layer

### Domain Layer Coverage

**Current Status:** Unknown (requires detailed report)

**Critical Files Needing Tests:**

1. **`src/domain/agents/mcp_aware_agent.py`** (696 lines)
   - Coverage: Likely low (complex, hard to test)
   - Priority: 🔴 HIGH
   - Estimated gaps: 200+ lines

2. **`src/domain/agents/base_agent.py`**
   - Coverage: Needs verification
   - Priority: 🟡 MEDIUM

3. **`src/domain/services/token_analyzer.py`** (314 lines)
   - Coverage: Likely moderate
   - Priority: 🟡 MEDIUM

### Application Layer Coverage

**Current Status:** Moderate

**Existing Tests:**
- ✅ `test_intent_orchestrator.py`
- ⚠️  Failures present: 2

**Coverage Gaps:**
- `intent_validator.py`: Needs unit tests
- `intent_clarification.py`: Needs unit tests
- `intent_fallback.py`: Needs unit tests

**New Use Cases (Phase 1):**
- `create_task_usecase.py`: Not yet created
- `collect_data_usecase.py`: Not yet created
- Target coverage: 90%+

### Infrastructure Layer Coverage

**Current Status:** Mixed

**Existing Tests:**
- ✅ `test_mcp_client_robust.py`
- ✅ `test_dialog_manager.py`
- ⚠️  `test_prometheus_metrics.py`: 3 failures
- ❌ `test_summarizer.py`: 2 failures (transformers missing)

**Coverage Gaps:**
- `mcp_client_robust.py`: Likely OK
- `dialog_manager.py`: Likely OK
- `monitoring/`: Needs more tests
- `config/settings.py`: Needs tests

### Presentation Layer Coverage

**Current Status:** Low

**Existing Tests:**
- ✅ Basic handlers tested
- ❌ `test_api.py`: Errors (from_env issues)
- ❌ `test_digest_tools.py`: 8 errors (event loop)
- ❌ `test_pdf_digest_tools.py`: 12 errors (event loop)

**Coverage Gaps:**
- `butler_bot.py`: 554 lines, needs comprehensive tests
- `handlers/tasks.py`: Needs unit tests
- `handlers/channels.py`: Needs unit tests
- `handlers/menu.py`: Needs unit tests

## Test Quality Analysis

### Unit Tests

**Current: 6 files identified**

**Strengths:**
- Test structure follows pytest conventions ✓
- Mocking in place for external dependencies ✓
- Test names are descriptive ✓

**Weaknesses:**
- Low coverage (estimated 30-40%)
- Missing tests for complex logic
- No tests for new files (phase 1-7)

**Recommendations:**
1. Add tests for all domain services
2. Test error paths extensively
3. Test edge cases
4. Mock properly (avoid integration in unit tests)

### Integration Tests

**Current: 11 files identified**

**Strengths:**
- Good coverage of MCP integration ✓
- PDF generation flows tested ✓
- Database interactions tested ✓

**Weaknesses:**
- Event loop errors: 20+ tests failing
- MongoDB connection issues: Several tests failing
- Performance tests failing (timeouts)

**Recommendations:**
1. Fix async/event loop issues
2. Use pytest-asyncio fixtures correctly
3. Mock MongoDB for unit tests
4. Separate integration from unit tests clearly

### E2E Tests

**Current: 3 files identified**

**Strengths:**
- Full workflow tests present ✓
- Edge case scenarios covered ✓

**Weaknesses:**
- 8 tests with MongoDB connection errors
- Telegram bot tests failing (token issues)
- Event loop issues persist

**Recommendations:**
1. Use test containers for E2E (docker-compose.test.yml)
2. Mock Telegram API for tests
3. Fix async cleanup

## Critical Test Gaps

### Phase 1 Priorities

**Domain Layer:**
1. **MCPAwareAgent** (696 lines)
   - Test `process` method with mocked LLM
   - Test `_stage_decision` with various inputs
   - Test `_stage_execution` with tool calls
   - Test error handling paths

2. **DecisionEngine** (new, Phase 1)
   - Test LLM decision-making
   - Test fallback logic
   - Test parameter extraction

3. **ToolExecutor** (new, Phase 1)
   - Test tool discovery
   - Test tool calling
   - Test error handling

4. **ResponseFormatter** (new, Phase 1)
   - Test markdown formatting
   - Test PDF generation
   - Test edge cases (empty results, etc.)

**Application Layer:**
5. **CreateTaskUseCase**
   - Test happy path
   - Test clarification flow
   - Test validation errors

6. **CollectDataUseCase**
   - Test channel digest flow
   - Test error handling
   - Test limits enforcement

**Infrastructure Layer:**
7. **MCP Client Implementation**
   - Test retry logic
   - Test timeout handling
   - Test connection failures

### Testing Infrastructure Needs

**Missing:**
1. Test fixtures for MCP client mocking
2. Test fixtures for LLM mocking
3. Test database (MongoDB test instance)
4. Test configuration (separate from prod)

**Existing:**
- ✅ `conftest.py` with some fixtures
- ✅ pytest-asyncio configured
- ✅ Coverage reporting configured

## Test Quality Metrics

### Code Quality

**Issues Found:**
- ❌ **68 errors** (event loops, import issues)
- ❌ **20 failures** (test logic issues)
- ⚠️  Bare except blocks in some tests
- ⚠️  Missing assertions in some tests

**Recommendations:**
1. Fix all test errors (priority: HIGH)
2. Add assertions to all tests
3. Improve test isolation
4. Use pytest fixtures correctly

### Test Maintainability

**Good Practices:**
- ✅ Tests in separate `tests/` directory
- ✅ Proper test naming (`test_*.py`)
- ✅ Docstrings in some tests

**Weaknesses:**
- ⚠️  Some tests too long (>50 lines)
- ⚠️  Duplication in test setup
- ⚠️  Hard-coded values in tests

**Recommendations:**
1. Extract common fixtures
2. Use parametrize for similar tests
3. Move constants to conftest or separate config

## Coverage by Priority

### High Priority Files (80%+ Target)

| File | Lines | Est. Coverage | Target | Gap |
|------|-------|---------------|--------|-----|
| mcp_aware_agent.py | 696 | 20% | 90% | 70% |
| butler_bot.py | 554 | 30% | 85% | 55% |
| intent_orchestrator.py | 155 | 50% | 90% | 40% |
| mcp_client_robust.py | 254 | 60% | 90% | 30% |
| dialog_manager.py | 200 | 70% | 90% | 20% |

### Medium Priority Files (80% Target)

| File | Lines | Est. Coverage | Target | Gap |
|------|-------|---------------|--------|-----|
| token_analyzer.py | 314 | 50% | 80% | 30% |
| pdf_digest_tools.py | 406 | 40% | 80% | 40% |
| handlers/*.py | 200 | 40% | 80% | 40% |

## Test Strategy for Phase 1-7

### Phase 1: Domain Layer Tests

**Goal:** 80% coverage for domain

**Actions:**
1. Unit tests for all domain services
2. Mock infrastructure dependencies
3. Test all error paths
4. Property-based tests for edge cases

**Target Files:**
- `decision_engine.py`: 100% coverage
- `tool_executor.py`: 100% coverage
- `response_formatter.py`: 100% coverage
- `mcp_aware_agent.py`: 85% coverage

### Phase 2: Infrastructure Tests

**Goal:** 80% coverage for infrastructure

**Actions:**
1. Unit tests for MCP client
2. Integration tests for LLM
3. Test retry/timeout logic
4. Test error handling

**Target Files:**
- `mcp_client_robust.py`: 90% coverage
- `dialog_manager.py`: 90% coverage
- `monitoring/`: 80% coverage

### Phase 3: Application Tests

**Goal:** 85% coverage for application

**Actions:**
1. Unit tests for use cases
2. Integration tests for orchestrators
3. Test error scenarios
4. Test edge cases

**Target Files:**
- `butler_orchestrator.py`: 90% coverage
- `create_task_usecase.py`: 90% coverage
- `collect_data_usecase.py`: 90% coverage

### Phase 4-7: Presentation & E2E

**Goal:** 70% coverage for presentation, 100% for critical paths

**Actions:**
1. Unit tests for handlers
2. E2E tests for workflows
3. Fix async issues
4. Add performance tests

## CI/CD Test Requirements

### Pre-commit Checks

**Requirements:**
```bash
# Run on each commit
pytest tests/unit/ --cov=src/domain
pytest tests/unit/ --cov=src/application

# Coverage thresholds
coverage >= 80% for domain
coverage >= 80% for application
```

### Pull Request Checks

**Requirements:**
```bash
# Full test suite
pytest tests/ --cov=src/

# Coverage thresholds
coverage >= 75% overall
no decrease in coverage
```

### Release Checks

**Requirements:**
```bash
# Full suite + integration
pytest tests/ --cov=src/ --cov-report=html

# Coverage thresholds
coverage >= 80% overall
all tests passing
```

## Recommendations

### Immediate Actions (Phase 0 → Phase 1)

1. **Fix existing test errors** (68 errors)
   - Event loop issues (highest priority)
   - Import errors
   - MongoDB connection issues

2. **Add domain tests**
   - DecisionEngine unit tests
   - ToolExecutor unit tests
   - ResponseFormatter unit tests

3. **Set up test infrastructure**
   - MongoDB test container
   - Mock LLM client
   - Mock MCP server

### Phase 1-3 Actions

4. **Achieve 80% domain coverage**
5. **Achieve 80% infrastructure coverage**
6. **Achieve 85% application coverage**

### Phase 4-7 Actions

7. **Achieve 70% presentation coverage**
8. **100% E2E coverage for critical paths**
9. **Add performance tests**
10. **Add chaos/error injection tests**

## Tools & Configuration

### Current Setup

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["src/tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
asyncio_mode = "auto"

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
```

### Recommended Additions

```toml
# Add coverage thresholds
[tool.coverage.report]
fail_under = 80

# Add coverage paths per-module
[tool.coverage.paths]
source = ["src"]
omit = ["*/tests/*", "*/migrations/*"]
```

## Metrics Summary

| Metric | Current | Target Phase 1 | Target Phase 7 |
|--------|---------|----------------|----------------|
| Overall coverage | 40.10% | 60% | 80% |
| Domain coverage | 30% | 80% | 90% |
| Application coverage | 45% | 70% | 85% |
| Infrastructure coverage | 50% | 70% | 80% |
| Presentation coverage | 30% | 50% | 70% |
| E2E coverage | 40% | 60% | 100% |
| Passing tests | 80.3% | 95% | 100% |

## References

- [pytest Best Practices](https://docs.pytest.org/en/stable/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Test-Driven Development](https://martinfowler.com/bliki/TestDrivenDevelopment.html)
- [Property-Based Testing](https://hypothesis.readthedocs.io/)
