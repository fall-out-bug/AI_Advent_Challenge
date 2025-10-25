<!-- 5b21ae77-c059-45c6-b0dc-52fcbc5dadcc 8dfaa92f-7f23-4338-a16d-00c24fd53e93 -->
# Fix API Key & External API Tests

## Overview

Fix API key management and external API tests (22 failing tests) to establish stable foundation for SDK. This phase focuses on configuration and external service integration.

## Context from Previous Phases

- Phases 1-6: Completed agentic SDK architecture implementation
- SDK version 0.2.0 released with agents, orchestration, and configuration
- Current status: 171/223 tests passing (76.7%)
- Outstanding: 52 failing tests across 5 categories

## Phase 7: Fix API Key & External API Tests

### 1. Fix API Key Management Tests (12 failures)

**File**: `shared/tests/test_api_keys.py`

**Issues**: Tests failing due to import or implementation issues in API key utilities

**Tasks**:

- Review API key loading functions (`get_api_key`, `is_api_key_configured`)
- Fix `get_available_external_apis` helper function
- Ensure proper mocking of file system and environment variables
- Update test fixtures for consistent API key testing
- Verify priority order: file > environment variable

**Expected**: 12/12 tests passing

### 2. Fix External API Tests (10 failures)

**File**: `shared/tests/test_external_apis.py`

**Issues**: External API request handling and availability checks failing

**Tasks**:

- Fix `make_external_request` function for Perplexity and ChadGPT
- Implement proper error handling for missing API keys
- Fix response parsing for both external providers
- Update availability checking logic
- Ensure proper mocking of HTTP requests

**Expected**: 10/10 tests passing

### 3. Fix Model Configuration Tests (2 failures)

**File**: `shared/tests/test_models.py`

**Issues**: Model config structure or helper function issues

**Tasks**:

- Review `MODEL_CONFIGS` structure validation
- Fix `get_local_models` helper function
- Ensure all model types correctly identified
- Update assertions to match current config structure

**Expected**: 2/2 tests passing

### 4. Fix Orchestration Adapter Tests (6 failures)

**File**: `shared/tests/test_orchestration_adapters.py`

**Issues**: REST adapter implementation or test mocking issues

**Tasks**:

- Fix `RestAdapter.send_request` implementation
- Implement retry logic correctly
- Fix `is_available` method
- Update HTTP client mocking in tests
- Ensure proper error propagation

**Expected**: 6/6 tests passing

### 5. Fix Orchestration Pattern Tests (22 failures)

**File**: `shared/tests/test_orchestration_patterns.py`

**Issues**: Orchestrator implementations or adapter integration issues

**Tasks**:

- Fix `DirectAdapter` initialization and execution
- Fix `RestAdapter` execution with proper mocking
- Implement `SequentialOrchestrator` execution logic
- Implement `ParallelOrchestrator` with asyncio.gather
- Fix error handling and cancellation logic
- Implement proper statistics aggregation
- Update integration test workflows

**Expected**: 22/22 tests passing

### 6. Verify All Tests Pass

**Command**: `cd shared && python -m pytest tests/ -v --tb=short`

**Expected**: 223/223 tests passing (100%)

## Phase 8: Complete Day 08 Refactoring

### 1. Update Day 08 Generator Adapter

**File**: `day_08/agents/code_generator_adapter.py`

**Changes**:

- Remove day_07 dependency (imports on lines 15-31)
- Import from SDK: `from shared_package.agents import CodeGeneratorAgent, AgentRequest`
- Replace implementation with SDK agent wrapper
- Use `DirectAdapter` for async calls
- Keep public API unchanged for backward compatibility
- Update docstrings to reference SDK

### 2. Update Day 08 Reviewer Adapter

**File**: `day_08/agents/code_reviewer_adapter.py`

**Changes**:

- Remove day_07 dependency (imports on lines 16-32)
- Import from SDK: `from shared_package.agents import CodeReviewerAgent, AgentRequest`
- Replace implementation with SDK agent wrapper
- Maintain quality metrics interface
- Keep public API unchanged

### 3. Update Demo Scripts

**File**: `day_08/demo_enhanced.py`

**Changes**:

- Update agent initialization to use SDK agents directly
- Remove fallback logic for day_07 agents
- Add SDK agent configuration examples
- Improve error messages with SDK exceptions
- Add agent statistics display

**File**: `day_08/demo_model_switching.py`

**Changes**:

- Integrate SDK orchestration patterns if applicable
- Update agent creation to use SDK
- Maintain existing demo functionality

### 4. Update Model Switcher Orchestrator

**File**: `day_08/core/model_switcher.py`

**Changes**:

- Import SDK orchestration: `from shared_package.orchestration import SequentialOrchestrator`
- Use `SequentialOrchestrator` for generator→reviewer workflow
- Maintain existing `ModelSwitcherOrchestrator` API
- Add adapter configuration options
- Update to use SDK agent instances

### 5. Update Day 08 Configuration

**File**: `day_08/config/agent_config.py` (if exists)

**Changes**:

- Import SDK agent configurations
- Extend or override with day_08-specific settings
- Remove duplicate configuration
- Use SDK compatibility matrix

### 6. Update Day 08 Documentation

**File**: `day_08/README.md`

**Changes**:

- Add section on SDK integration
- Document migration from day_07 dependency
- Add examples of SDK agent usage
- Update architecture diagrams
- Reference SDK documentation

**File**: `day_08/CHANGELOG.md`

**Changes**:

- Add entry for SDK migration
- Document breaking changes (none expected)
- List new features from SDK integration
- Update version to reflect SDK usage

### 7. Update Day 08 Tests

**File**: `day_08/tests/test_agents.py` (and related test files)

**Changes**:

- Update mocks to use SDK agent schemas
- Test SDK agent integration
- Remove day_07 test dependencies
- Add tests for adapter usage
- Verify backward compatibility

### 8. Remove Day 07 Dependencies

**File**: `day_08/pyproject.toml` or `requirements.txt`

**Changes**:

- Remove any day_07 path dependencies
- Ensure SDK (shared_package) is properly referenced
- Verify all imports resolve correctly

### 9. Verification

**Tasks**:

- Run day_08 tests: `cd day_08 && python -m pytest tests/ -v`
- Run demo scripts: `python demo_enhanced.py --model qwen`
- Test model switching: `python demo_model_switching.py`
- Verify no day_07 imports remain: `grep -r "from day_07" day_08/`
- Verify day_07 still works independently

## Success Criteria

### Phase 7 Success Metrics

- ✅ 223/223 SDK tests passing (100% pass rate)
- ✅ All test categories fixed: API keys, external APIs, model config, orchestration
- ✅ No regressions in previously passing tests
- ✅ Test coverage maintained or improved

### Phase 8 Success Metrics

- ✅ Day 08 fully migrated to SDK agents
- ✅ No day_07 dependencies remaining
- ✅ All day_08 demos working with SDK agents
- ✅ Backward compatibility maintained
- ✅ Day 07 still functional (untouched)
- ✅ Documentation updated

## Testing Strategy

1. **Unit Tests**: Fix and verify each test file individually
2. **Integration Tests**: Verify day_08 works end-to-end with SDK
3. **Regression Tests**: Ensure day_07 remains unchanged and functional
4. **Manual Testing**: Run all demo scripts and verify output quality

## Deliverables

1. SDK with 100% test pass rate (223/223)
2. Day 08 fully refactored to use SDK agents
3. Updated documentation for both SDK and day_08
4. Migration guide for future projects
5. Clean, educational demonstration of agentic architecture

## Timeline Estimate

- Phase 7 (Fix tests): ~2-3 hours of focused work
- Phase 8 (Day 08 refactor): ~1-2 hours of focused work
- Testing & verification: ~1 hour
- Documentation: ~30 minutes

**Total**: 4-6 hours of development time

## Python Zen Compliance

- **Simple is better than complex**: Straightforward test fixes, minimal refactoring
- **Explicit is better than implicit**: Clear SDK imports, no hidden dependencies
- **Readability counts**: Clean migration, well-documented changes
- **There should be one obvious way**: Single source of truth in SDK
- **Now is better than never**: Complete the migration as planned

### To-dos

- [ ] Fix 12 API key management tests in test_api_keys.py
- [ ] Fix 10 external API tests in test_external_apis.py
- [ ] Fix 2 model configuration tests in test_models.py
- [ ] Fix 6 orchestration adapter tests in test_orchestration_adapters.py
- [ ] Fix 22 orchestration pattern tests in test_orchestration_patterns.py
- [ ] Verify all 223 SDK tests pass (100% pass rate)
- [ ] Refactor day_08 generator adapter to use SDK agents, remove day_07 dependency
- [ ] Refactor day_08 reviewer adapter to use SDK agents, remove day_07 dependency
- [ ] Update demo_enhanced.py and demo_model_switching.py to use SDK agents
- [ ] Update model_switcher.py to use SDK SequentialOrchestrator
- [ ] Update day_08 configuration to use SDK agent configs
- [ ] Update day_08 README.md and CHANGELOG.md for SDK integration
- [ ] Update day_08 tests to work with SDK agents and verify integration
- [ ] Run all day_08 tests and demos to verify successful SDK migration
- [ ] Verify day_07 remains functional and unchanged after day_08 migration