# Epic 21 · Testing Strategy

**Purpose**: Define test-first approach and coverage requirements for Epic 21 refactoring.

**Principle**: *"Never implement a feature without a corresponding test"* (repo rules)

---

## Overview

Epic 21 refactors critical components (dialog context, homework handling, storage, use case
orchestration). Testing strategy ensures:

1. **No regressions** in existing functionality
2. **Confidence** in new interfaces
3. **TDD compliance** (tests before implementation)
4. **Measurable coverage** (≥80% for refactored modules, ≥85% for critical paths)

---

## Test-First Workflow

### Phase 1: Characterization Tests (Capture Current Behavior)

Before refactoring any component, write tests that **document existing behavior**.

**Purpose**:
- Lock down current functionality
- Detect unintended changes during refactor
- Serve as acceptance criteria (if characterization tests pass, refactor is correct)

**Example Workflow for ARCH-21-01 (Dialog Context Repository)**:

```python
# Step 1: Write characterization tests BEFORE extracting interface
# tests/characterization/test_butler_orchestrator_dialog_context.py

import pytest
from src.domain.agents.butler_orchestrator import ButlerOrchestrator

@pytest.mark.asyncio
async def test_dialog_context_save_and_retrieve(mongo_db):
    """Characterization: ButlerOrchestrator saves/retrieves dialog contexts."""
    # Arrange
    orchestrator = ButlerOrchestrator(mongodb=mongo_db, ...)
    session_id = "test_session_123"
    
    # Act: Save context
    await orchestrator.save_context(session_id, {"user_id": "alice", "turn": 1})
    
    # Assert: Retrieve returns same data
    context = await orchestrator.get_context(session_id)
    assert context["user_id"] == "alice"
    assert context["turn"] == 1

@pytest.mark.asyncio
async def test_dialog_context_not_found_returns_none(mongo_db):
    """Characterization: Non-existent context returns None."""
    orchestrator = ButlerOrchestrator(mongodb=mongo_db, ...)
    context = await orchestrator.get_context("nonexistent")
    assert context is None

# ... more characterization tests covering edge cases
```

**Run characterization tests** (should pass with current code):
```bash
pytest tests/characterization/ -v
# Expected: All pass (baseline established)
```

### Phase 2: Refactor with Tests Passing

After characterization tests pass:

1. Extract interface (`DialogContextRepository`)
2. Create adapter (`MongoDialogContextRepository`)
3. Update orchestrator to use interface (behind feature flag)
4. **Run characterization tests again**
   - If pass → refactor correct
   - If fail → fix implementation or update tests (if behavior intentionally changed)

### Phase 3: Unit Tests for New Components

Write unit tests for newly created interfaces/adapters:

```python
# tests/unit/infrastructure/repositories/test_mongo_dialog_context_repository.py

@pytest.mark.asyncio
async def test_repository_saves_context(mongo_db):
    """Unit: Repository saves DialogContext to MongoDB."""
    repo = MongoDialogContextRepository(mongo_client=mongo_db)
    context = DialogContext(session_id="s1", user_id="alice", turn=1)
    
    await repo.save(context)
    
    # Verify in DB
    doc = await mongo_db.dialog_contexts.find_one({"session_id": "s1"})
    assert doc["user_id"] == "alice"

@pytest.mark.asyncio  
async def test_repository_returns_none_for_missing_context(mongo_db):
    """Unit: Repository returns None for non-existent session."""
    repo = MongoDialogContextRepository(mongo_client=mongo_db)
    context = await repo.get_by_session("nonexistent")
    assert context is None
```

### Phase 4: Integration Tests (End-to-End)

Validate wiring of interfaces through DI container:

```python
# tests/integration/test_butler_orchestrator_with_repository.py

@pytest.mark.asyncio
async def test_orchestrator_uses_repository_via_di(di_container):
    """Integration: ButlerOrchestrator uses DialogContextRepository via DI."""
    orchestrator = di_container.butler_orchestrator
    
    # Act
    await orchestrator.handle_message(user_id="alice", message="Hello")
    
    # Assert: Context saved via repository (not direct Mongo)
    repo = di_container.dialog_context_repo
    context = await repo.get_by_session(orchestrator.current_session_id)
    assert context.user_id == "alice"
```

---

## Test Pyramid for Epic 21

```
         ╱╲
        ╱  ╲         E2E (5%)
       ╱────╲        - Full workflow tests (API → use case → DB)
      ╱      ╲       - Smoke tests with feature flags
     ╱────────╲      
    ╱          ╲     Integration (20%)
   ╱────────────╲    - DI container wiring
  ╱              ╲   - Cross-layer validation
 ╱────────────────╲  
╱                  ╲ Unit (75%)
────────────────────  - Interface implementations
                      - Domain logic
                      - Adapters (mocked dependencies)
```

### Target Distribution

| Test Type | Count (estimated) | Coverage Target | Execution Time |
|-----------|------------------|-----------------|----------------|
| Unit | ~120 tests | 90% of domain/application logic | <10s |
| Integration | ~30 tests | 80% of infrastructure adapters | <30s |
| E2E | ~10 tests | Critical user flows (review, dialog) | <2min |
| Characterization | ~40 tests | 100% of refactored components | <20s |

**Total**: ~200 tests, <3 minutes execution time

---

## Stage-by-Stage Test Requirements

### Stage 21_00: Preparation

**Goal**: Establish test infrastructure and baselines

**Deliverables**:
- [ ] Test fixtures for DI container
- [ ] Mock implementations of interfaces (in-memory fakes)
- [ ] Baseline coverage report (current state)
- [ ] CI test matrix updated

**Test Script**:
```bash
# Collect baseline coverage
poetry run pytest tests/ --cov=src/ --cov-report=json -q
cp coverage.json docs/specs/epic_21/architect/baseline_coverage.json

# Measure test execution time
poetry run pytest tests/ --durations=0 > docs/specs/epic_21/architect/baseline_test_durations.txt
```

**Exit Criteria**:
- [ ] Baseline coverage ≥70% (current state documented)
- [ ] Test suite runs in <5 minutes
- [ ] Shared infra bootstrap script working in CI

---

### Stage 21_01a: Dialog Context Repository

**Test Checklist**:

#### Characterization Tests (Write First)
- [ ] `test_butler_orchestrator_saves_context`
- [ ] `test_butler_orchestrator_retrieves_context`
- [ ] `test_butler_orchestrator_handles_missing_context`
- [ ] `test_butler_orchestrator_updates_existing_context`
- [ ] `test_butler_orchestrator_deletes_context`

#### Unit Tests (New Components)
- [ ] `test_dialog_context_repository_interface` (protocol compliance)
- [ ] `test_mongo_dialog_context_repository_save`
- [ ] `test_mongo_dialog_context_repository_get_by_session`
- [ ] `test_mongo_dialog_context_repository_delete`
- [ ] `test_mongo_dialog_context_repository_handles_connection_errors`

#### Integration Tests
- [ ] `test_butler_orchestrator_with_real_repository` (feature flag on)
- [ ] `test_butler_orchestrator_with_old_mongo_access` (feature flag off)
- [ ] `test_di_container_injects_correct_repository_implementation`

#### Test Doubles (Fakes for Other Tests)
- [ ] `InMemoryDialogContextRepository` (for fast unit tests)

**Coverage Target**: ≥85% for:
- `src/domain/interfaces/dialog_context_repository.py`
- `src/infrastructure/repositories/mongo_dialog_context_repository.py`
- `src/domain/agents/butler_orchestrator.py` (context-related methods)

**Exit Criteria**:
- [ ] All characterization tests pass with old code
- [ ] All characterization tests pass with new code (feature flag on)
- [ ] Unit tests cover happy path + 3 error scenarios
- [ ] Integration tests validate DI wiring

---

### Stage 21_01b: Homework Review Service

**Test Checklist**:

#### Characterization Tests
- [ ] `test_homework_handler_lists_recent_commits`
- [ ] `test_homework_handler_requests_review`
- [ ] `test_homework_handler_handles_api_timeout`
- [ ] `test_homework_handler_handles_api_error`

#### Unit Tests
- [ ] `test_homework_review_service_interface`
- [ ] `test_hw_checker_service_adapter_list_recent`
- [ ] `test_hw_checker_service_adapter_request_review`
- [ ] `test_hw_checker_service_adapter_translates_errors` (domain exceptions)
- [ ] `test_hw_checker_service_adapter_caching` (future enhancement)

#### Integration Tests
- [ ] `test_homework_handler_with_real_service` (feature flag on)
- [ ] `test_homework_handler_with_mock_hw_checker` (for fast tests)

#### Test Doubles
- [ ] `FakeHomeworkReviewService` (returns predictable data)
- [ ] `FailingHomeworkReviewService` (simulates errors)

**Coverage Target**: ≥85% for homework handler + service adapter

**Exit Criteria**:
- [ ] External API mocked in tests (no real HW checker calls)
- [ ] Error translation tested (HW checker errors → domain exceptions)
- [ ] Timeout handling validated

---

### Stage 21_01c: Storage Abstraction

**Test Checklist** (⚠️ Critical: Storage affects data integrity):

#### Characterization Tests
- [ ] `test_review_routes_saves_new_submission_archive`
- [ ] `test_review_routes_saves_previous_submission_archive`
- [ ] `test_review_routes_saves_logs_archive`
- [ ] `test_review_routes_handles_oversized_file` (>100MB)
- [ ] `test_review_routes_handles_invalid_archive_format`

#### Unit Tests (Security Focus)
- [ ] `test_storage_adapter_validates_file_size`
- [ ] `test_storage_adapter_calculates_checksum`
- [ ] `test_storage_adapter_rejects_mismatched_checksum`
- [ ] `test_storage_adapter_calls_av_scan_hook` (if enabled)
- [ ] `test_storage_adapter_creates_directories_if_missing`
- [ ] `test_storage_adapter_handles_disk_full_error`

#### Integration Tests
- [ ] `test_review_routes_with_real_storage_adapter` (temp directory)
- [ ] `test_storage_adapter_with_s3_backend` (mocked boto3)
- [ ] `test_storage_adapter_with_feature_flag_off` (old behavior)

#### Security Tests
- [ ] `test_storage_rejects_path_traversal_attempt` (e.g., `../../etc/passwd`)
- [ ] `test_storage_enforces_allowed_extensions` (`.zip`, `.tar.gz`)
- [ ] `test_storage_logs_security_events` (failed checksum, AV reject)

#### Test Doubles
- [ ] `InMemoryReviewArchiveStorage` (for fast tests)
- [ ] `FailingReviewArchiveStorage` (simulates disk errors)

**Coverage Target**: ≥90% (critical path, security-sensitive)

**Exit Criteria**:
- [ ] Checksum validation tested with known-good and corrupted files
- [ ] Path traversal attempts blocked
- [ ] Disk full scenario handled gracefully
- [ ] All security events logged

---

### Stage 21_01d: Use Case Decomposition

**Test Checklist**:

#### Characterization Tests (Comprehensive)
- [ ] `test_review_submission_use_case_full_pipeline`
- [ ] `test_review_submission_use_case_rate_limiting`
- [ ] `test_review_submission_use_case_log_analysis_appended`
- [ ] `test_review_submission_use_case_report_persisted`
- [ ] `test_review_submission_use_case_report_published`

#### Unit Tests (New Collaborators)
- [ ] `test_rate_limiter_enforces_limit`
- [ ] `test_rate_limiter_allows_under_limit`
- [ ] `test_log_analysis_pipeline_parses_logs`
- [ ] `test_log_analysis_pipeline_handles_malformed_logs`
- [ ] `test_report_publisher_publishes_to_mongo`
- [ ] `test_report_publisher_handles_publish_failure`

#### Integration Tests
- [ ] `test_decomposed_use_case_with_all_collaborators` (feature flag on)
- [ ] `test_monolithic_use_case_still_works` (feature flag off)

**Coverage Target**: ≥85% for use case + collaborators

**Exit Criteria**:
- [ ] Each collaborator tested independently
- [ ] Collaborators composed correctly in use case
- [ ] Error handling in one collaborator doesn't break pipeline

---

### Stage 21_02: Code Quality

**Test Checklist**:

#### Regression Tests (After Function Decomposition)
- [ ] Run full test suite after each function split
- [ ] Ensure no new lint errors introduced
- [ ] Validate docstrings examples are runnable

#### Docstring Tests (New)
- [ ] `test_docstring_examples_are_valid_python` (extract and exec)
- [ ] `test_all_public_functions_have_docstrings` (custom linter)

**Example Docstring Test**:
```python
import ast
import inspect

def test_docstring_examples_runnable():
    """Validate that all docstring examples are valid Python."""
    from src.domain.agents import butler_orchestrator
    
    for name, obj in inspect.getmembers(butler_orchestrator, inspect.isfunction):
        if obj.__doc__ and "Example:" in obj.__doc__:
            # Extract example code
            example = extract_example(obj.__doc__)
            # Validate syntax
            try:
                ast.parse(example)
            except SyntaxError as e:
                pytest.fail(f"{name} docstring example has syntax error: {e}")
```

**Coverage Target**: Maintain ≥85% after function splits

**Exit Criteria**:
- [ ] No test failures after decomposition
- [ ] All new helper functions have unit tests
- [ ] Docstring examples validated

---

### Stage 21_03: Guardrails

**Test Checklist**:

#### Performance Tests (New)
- [ ] `test_dialog_context_repository_latency` (<100ms)
- [ ] `test_homework_review_service_latency` (<2s)
- [ ] `test_storage_adapter_write_latency` (<500ms for 10MB file)
- [ ] `test_review_submission_use_case_end_to_end_latency` (<30s)

**Example Performance Test**:
```python
import pytest
import time

@pytest.mark.performance
@pytest.mark.asyncio
async def test_dialog_context_repository_latency(mongo_dialog_context_repo):
    """Performance: Repository operations complete within 100ms."""
    context = DialogContext(session_id="perf_test", user_id="alice")
    
    start = time.perf_counter()
    await mongo_dialog_context_repo.save(context)
    duration = time.perf_counter() - start
    
    assert duration < 0.1, f"Save took {duration:.3f}s, expected <0.1s"
```

#### Security Tests (Comprehensive)
- [ ] `test_storage_adapter_blocks_path_traversal`
- [ ] `test_storage_adapter_enforces_file_size_limit`
- [ ] `test_storage_adapter_validates_checksums`
- [ ] `test_no_secrets_logged` (scan logs for API keys, passwords)

**Coverage Target**: ≥80% overall (Epic 21 complete)

**Exit Criteria**:
- [ ] All performance tests pass in CI
- [ ] Security tests cover OWASP Top 10 relevant issues
- [ ] Coverage report shows ≥85% for refactored modules

---

## Test Fixtures & Test Doubles

### Shared Fixtures (tests/conftest.py)

```python
import pytest
from src.infrastructure.di.container import DIContainer

@pytest.fixture
async def mongo_db():
    """Provide MongoDB connection for tests."""
    # Use bootstrap script from operations.md
    from scripts.ci.bootstrap_shared_infra import bootstrap_mongo
    mongo_url = await bootstrap_mongo(port=37017)
    yield mongo_url
    # Cleanup after test

@pytest.fixture
def di_container(mongo_db):
    """Provide DI container with test dependencies."""
    container = DIContainer(config=test_settings)
    container.mongo_client = mongo_db
    return container

@pytest.fixture
def in_memory_dialog_context_repo():
    """Fast in-memory repository for unit tests."""
    return InMemoryDialogContextRepository()
```

### Test Doubles (Fakes, Mocks, Stubs)

#### In-Memory Dialog Context Repository
```python
# tests/doubles/in_memory_dialog_context_repository.py

class InMemoryDialogContextRepository:
    """Fake repository for testing without Mongo."""
    
    def __init__(self):
        self._store: dict[str, DialogContext] = {}
    
    async def get_by_session(self, session_id: str) -> DialogContext | None:
        return self._store.get(session_id)
    
    async def save(self, context: DialogContext) -> None:
        self._store[context.session_id] = context
    
    async def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)
```

#### Fake Homework Review Service
```python
class FakeHomeworkReviewService:
    """Predictable service for testing."""
    
    async def list_recent_commits(self, days: int) -> HomeworkCommitList:
        return HomeworkCommitList(commits=[
            Commit(hash="abc123", date="2025-11-10", student="alice"),
            Commit(hash="def456", date="2025-11-11", student="bob"),
        ])
    
    async def request_review(self, commit_hash: str) -> ReviewResult:
        return ReviewResult(status="success", review_id="test_review_1")
```

---

## CI Integration

### GitHub Actions Test Matrix

```yaml
# .github/workflows/ci.yml (updated for Epic 21)

test:
  strategy:
    matrix:
      test-suite:
        - unit
        - integration
        - characterization
        - performance
      python-version: ['3.11']
  
  steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Bootstrap shared infra
      run: poetry run python scripts/ci/bootstrap_shared_infra.py --mongo-port 37017
    
    - name: Run ${{ matrix.test-suite }} tests
      run: poetry run pytest tests/${{ matrix.test-suite }}/ --cov=src/ -v
    
    - name: Upload coverage
      if: matrix.test-suite == 'unit'
      uses: codecov/codecov-action@v3
```

### Test Markers

```python
# pytest.ini (add Epic 21 markers)

[pytest]
markers =
    epic21: Tests related to Epic 21 refactoring
    characterization: Tests capturing current behavior
    performance: Performance/latency tests
    security: Security-focused tests
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (shared infra required)
    e2e: End-to-end tests (full stack)
```

### Running Tests Locally

```bash
# All Epic 21 tests
pytest -m epic21 -v

# Only characterization tests (before refactoring)
pytest -m characterization -v

# Performance tests (with timing output)
pytest -m performance -v --durations=10

# Security tests
pytest -m security -v

# Fast unit tests only
pytest -m "unit and epic21" -v
```

---

## Coverage Requirements

### Minimum Coverage by Layer

| Layer | Minimum Coverage | Critical Modules (90%+) |
|-------|-----------------|------------------------|
| Domain | 90% | `butler_orchestrator.py`, `homework_handler.py` |
| Application | 85% | `review_submission_use_case.py`, all service adapters |
| Infrastructure | 80% | Repositories, storage adapters |
| Presentation | 75% | Route handlers (higher in integration tests) |

### Exemptions

- **Scripts** (`scripts/`): No coverage requirement (operational helpers)
- **Tests** (`tests/`): No self-coverage requirement
- **Migrations** (`scripts/migrations/`): Manual validation instead of automated tests

### Coverage Enforcement in CI

```yaml
# .github/workflows/ci.yml

- name: Check coverage
  run: |
    poetry run pytest tests/ --cov=src/ --cov-report=term --cov-fail-under=80
    # Fail if coverage drops below 80%
```

---

## Test Performance Budget

### Execution Time Targets

| Test Suite | Target Time | Max Allowed | Action if Exceeded |
|------------|------------|-------------|-------------------|
| Unit tests | <10s | <20s | Optimize slow tests (use fakes, not mocks) |
| Integration tests | <30s | <60s | Parallelize or move to E2E |
| E2E tests | <2min | <5min | Run nightly instead of per-commit |
| Full suite | <3min | <6min | Split into fast/slow suites |

### Slow Test Detection

```bash
# Identify slow tests
pytest tests/ --durations=10

# Expected output:
# 1.23s call tests/integration/test_review_submission_flow.py::test_full_pipeline
# 0.89s call tests/integration/test_storage_adapter.py::test_large_file_upload
# ...
```

If any test >5s → investigate:
- Are external services mocked?
- Can fixtures be reused?
- Should this be E2E instead of integration?

---

## Acceptance Criteria for Testing Strategy

- [ ] All stages have characterization tests defined before implementation starts
- [ ] Test doubles (fakes, mocks) created for all new interfaces
- [ ] CI runs full test matrix on every commit
- [ ] Coverage reports generated and stored in Epic 21 artifacts
- [ ] Performance tests included with latency thresholds
- [ ] Security tests cover path traversal, checksum validation, size limits
- [ ] Rollback drills include test execution validation

---

## References

- **TDD Rules**: Repo rules (`.cursorrules-guide.md`)
- **Shared Infra Bootstrap**: `docs/specs/operations.md` §2.1
- **Coverage Tools**: `pytest-cov`, `coverage.py`
- **Performance Testing**: `pytest-benchmark` (consider adding)
- **Security Testing**: `bandit` (static analysis), custom tests for runtime validation

---

**Document Owner**: QA Lead + EP21 Tech Lead  
**Last Updated**: 2025-11-11  
**Next Review**: After Stage 21_00 completion

