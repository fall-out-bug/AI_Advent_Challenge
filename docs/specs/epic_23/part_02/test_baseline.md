# Epic 24 · Test Baseline

**Epic:** EP24 – Repository Hygiene & De-Legacy
**Date:** 2025-11-16
**Purpose:** Establish baseline metrics before refactoring to track regression and progress

## Test Collection Summary

**Total Test Files:** 167+
**Total Test Functions:** ~881 (collected via `pytest --collect-only`)
**Test Collection Errors:** 7 (expected due to missing dependencies in some tests)

## Cluster-Specific Test Baseline

### Cluster A – Mongo & Async Infrastructure
**Test Files:**
- Repository tests: 4+ files (e.g., `test_post_repository.py`, `test_mongo_*_repository.py`)
- Mongo-related tests: ~10+ files across infrastructure/integration tests

**Known Issues:**
- Direct `MongoClient(...)` instantiations causing authentication failures
- Event loop issues in async tests (`RuntimeError: Event loop is closed`)
- Missing shared fixtures causing test isolation problems

**Baseline Metrics:**
- Repository tests: ~30+ test functions
- Integration tests using Mongo: ~50+ test functions
- Total Cluster A related: ~80+ test functions

### Cluster B – Summarization & Digest Use Cases
**Test Files:**
- Digest use case tests: 3+ files (e.g., `test_subscribe_and_digest.py`, `test_digest_*.py`)
- Summarization tests: ~10+ files (e.g., `test_summarizer*.py`, `test_map_reduce_summarizer.py`)
- Worker tests related to digest: 1+ file (`test_post_fetcher_worker.py` with 9+ tests)

**Known Issues:**
- `NameError: name 'posts' is not defined` in digest use cases
- Parameter mismatches in repository calls
- Missing async/sync contract clarity

**Baseline Metrics:**
- Digest use case tests: ~15+ test functions
- Summarization tests: ~30+ test functions
- Total Cluster B related: ~45+ test functions

### Cluster C – Butler Orchestration & MCP-Aware Agent
**Test Files:**
- Butler bot tests: ~15+ files (e.g., `test_butler_bot*.py`, `test_butler_handler.py`)
- MCP tests: ~10+ files (e.g., `test_mcp*.py`, `test_homework_review_tool.py`)
- Agent tests: ~5+ files (e.g., `test_agent*.py`, `test_mode_classifier*.py`)

**Known Issues:**
- Private attribute access in tests (`mode_classifier`, `task_handler`, etc.)
- Missing public API boundaries
- Metrics misalignment with `observability_labels.md`

**Baseline Metrics:**
- Butler/MCP tests: ~50+ test functions
- Agent orchestration tests: ~30+ test functions
- Total Cluster C related: ~80+ test functions

### Cluster D – LLM Clients & Map-Reduce Summarizer
**Test Files:**
- LLM client tests: ~8+ files (e.g., `test_llm_client.py`, `test_resilient_client.py`)
- Summarizer tests: ~6+ files (e.g., `test_llm_summarizer.py`, `test_map_reduce_summarizer.py`)

**Known Issues:**
- Hardcoded URLs in tests
- Inconsistent client interface usage
- Map-reduce summarizer parameter mismatches

**Baseline Metrics:**
- LLM client tests: ~25+ test functions
- Summarizer tests: ~20+ test functions
- Total Cluster D related: ~45+ test functions

### Cluster E – Telegram & Workers
**Test Files:**
- Worker tests: 1+ file (`test_post_fetcher_worker.py` with 9+ tests)
- Telegram utils tests: ~3+ files
- Channel normalizer tests: 1+ file (implicit in domain tests)

**Known Issues:**
- Direct Mongo usage in worker tests
- Channel normalization policy unclear
- Missing Telegram adapter interface

**Baseline Metrics:**
- Worker tests: ~15+ test functions
- Telegram/Channel tests: ~10+ test functions
- Total Cluster E related: ~25+ test functions

### Shared / Cross-Cluster Tests
**Test Files:**
- Integration tests: ~20+ files (e.g., `test_*_integration.py`)
- E2E tests: ~5+ files (e.g., `test_*_e2e.py`)
- Benchmark tests: ~3+ files

**Baseline Metrics:**
- Integration tests: ~40+ test functions
- E2E tests: ~15+ test functions
- Total Shared: ~55+ test functions

## Test Execution Baseline

**Last Full Run:** Pre-Epic 24 baseline (2025-11-16)

**Expected Issues Before Refactoring:**
- Authentication errors: ~20+ tests (Mongo auth)
- Event loop errors: ~15+ tests (async fixtures)
- Undefined variables: ~5+ tests (digest use cases)
- Attribute errors: ~10+ tests (private attribute access)

**Total Expected Failures:** ~50+ tests (before refactoring)

## Characterization Test Requirements

Before refactoring each cluster, **characterization tests must be created** to capture current behavior:

### Cluster A Characterization Tests
- Repository CRUD operations (create, read, update, delete)
- Database connection patterns (sync vs async)
- Transaction behavior (if applicable)

### Cluster B Characterization Tests
- Digest generation flow (end-to-end)
- Summarization quality/output format
- Error handling in digest pipeline

### Cluster C Characterization Tests
- Butler message handling flow
- MCP tool invocation patterns
- Agent state transitions

### Cluster D Characterization Tests
- LLM client request/response patterns
- Map-reduce summarizer chunking behavior
- Error/timeout handling

### Cluster E Characterization Tests
- Worker execution flow
- Channel normalization edge cases
- Telegram message processing

## Migration Order for Test Fixtures

**Priority Order:**
1. **Repositories** (Cluster A foundation)
2. **Workers** (depends on repositories)
3. **Channels** (depends on repositories + workers)
4. **Evaluation** (depends on all above)

**Rationale:** Repositories are the foundation for all other components. Workers depend on repositories. Channels depend on both. Evaluation depends on all.

---

**Baseline established by:** cursor_dev_a_v1
**Reviewed by:** cursor_reviewer_v1
**Date:** 2025-11-16
