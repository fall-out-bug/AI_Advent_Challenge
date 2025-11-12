# Pytest Markers · Epic 21

**Purpose**: Fixed marker names for consistent test organization and CI matrix.

**Status**: Ready for implementation (Stage 21_00)

---

## pytest.ini Configuration

```ini
# pytest.ini (add to root of repository)

[pytest]
# Minimum version
minversion = 7.0

# Test discovery
python_files = test_*.py
python_classes = Test*
python_functions = test_*

testpaths = tests

# --- Epic 21 Markers ---
markers =
    # Epic/Stage markers
    epic21: Tests related to Epic 21 refactoring
    stage_21_00: Stage 21_00 (Preparation)
    stage_21_01: Stage 21_01 (Architecture & Layering)
    stage_21_02: Stage 21_02 (Code Quality)
    stage_21_03: Stage 21_03 (Testing & Observability)
    
    # Component markers
    dialog_context: Dialog context repository tests
    homework_service: Homework review service tests
    storage: Storage adapter tests
    logs: Log analysis tests
    use_case: Use case decomposition tests
    
    # Test type markers (Epic 21)
    characterization: Tests capturing current behavior before refactoring
    performance: Performance/latency tests with SLO validation
    security: Security-focused tests (checksum, AV scan, path traversal)
    
    # Existing markers (for reference)
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (shared infra required)
    e2e: End-to-end tests (full stack)
    smoke: Smoke tests (critical paths only)
    slow: Tests that take >5 seconds
    
    # Infrastructure markers
    requires_mongo: Test requires MongoDB connection
    requires_redis: Test requires Redis connection
    requires_llm: Test requires LLM API access

# Coverage configuration
addopts =
    --strict-markers
    --tb=short
    --cov-report=term-missing
    --cov-report=html
    --cov-report=json
    
    # Warnings
    -W error::DeprecationWarning
    -W ignore::pytest.PytestUnraisableExceptionWarning
```

---

## Usage Examples

### Run All Epic 21 Tests

```bash
pytest -m epic21 -v
```

### Run Specific Stage Tests

```bash
# Stage 21_01 tests only
pytest -m stage_21_01 -v

# Stage 21_03 tests only
pytest -m stage_21_03 -v
```

### Run Component-Specific Tests

```bash
# Storage adapter tests
pytest -m storage -v

# Log analysis tests
pytest -m logs -v

# Combined (storage OR logs)
pytest -m "storage or logs" -v
```

### Run by Test Type

```bash
# Characterization tests (before refactoring)
pytest -m characterization -v

# Performance tests with timing
pytest -m performance -v --durations=10

# Security tests
pytest -m security -v
```

### Combined Queries

```bash
# Epic 21 unit tests only
pytest -m "epic21 and unit" -v

# Epic 21 integration tests (not e2e)
pytest -m "epic21 and integration and not e2e" -v

# Storage tests (unit + integration)
pytest -m "storage and (unit or integration)" -v

# All fast Epic 21 tests (exclude slow)
pytest -m "epic21 and not slow" -v
```

### CI Matrix (as per Stage 21_03)

```bash
# As suggested by Tech Lead
pytest -m "storage or logs" -v
```

---

## Marking Tests

### Example 1: Component Test

```python
# tests/unit/infrastructure/repositories/test_mongo_dialog_context_repository.py

import pytest


@pytest.mark.unit
@pytest.mark.epic21
@pytest.mark.stage_21_01
@pytest.mark.dialog_context
@pytest.mark.asyncio
async def test_repository_saves_context(mongo_client):
    """Unit: Repository saves DialogContext to MongoDB."""
    repo = MongoDialogContextRepository(mongo_client=mongo_client)
    context = DialogContext(session_id="s1", user_id="alice", turn=1)
    
    await repo.save(context)
    
    # Verify in DB
    doc = await mongo_client.butler.dialog_contexts.find_one({"session_id": "s1"})
    assert doc["user_id"] == "alice"
```

### Example 2: Characterization Test

```python
# tests/characterization/test_butler_orchestrator_dialog_context.py

import pytest


@pytest.mark.characterization
@pytest.mark.epic21
@pytest.mark.stage_21_01
@pytest.mark.dialog_context
@pytest.mark.integration
@pytest.mark.requires_mongo
@pytest.mark.asyncio
async def test_orchestrator_saves_and_retrieves_context(mongo_db):
    """Characterization: ButlerOrchestrator saves/retrieves dialog contexts."""
    # Capture current behavior before refactoring
    orchestrator = ButlerOrchestrator(mongodb=mongo_db)
    session_id = "test_session_123"
    
    # Act: Save context
    await orchestrator.save_context(session_id, {"user_id": "alice", "turn": 1})
    
    # Assert: Retrieve returns same data
    context = await orchestrator.get_context(session_id)
    assert context["user_id"] == "alice"
    assert context["turn"] == 1
```

### Example 3: Performance Test

```python
# tests/performance/test_dialog_context_repository_latency.py

import pytest
import time


@pytest.mark.performance
@pytest.mark.epic21
@pytest.mark.stage_21_03
@pytest.mark.dialog_context
@pytest.mark.requires_mongo
@pytest.mark.asyncio
async def test_repository_latency(mongo_dialog_context_repo):
    """Performance: Repository operations complete within 100ms."""
    context = DialogContext(session_id="perf_test", user_id="alice")
    
    # Test save latency
    start = time.perf_counter()
    await mongo_dialog_context_repo.save(context)
    save_duration = time.perf_counter() - start
    
    # Test get latency
    start = time.perf_counter()
    await mongo_dialog_context_repo.get_by_session("perf_test")
    get_duration = time.perf_counter() - start
    
    # Assert SLO
    assert save_duration < 0.1, f"Save took {save_duration:.3f}s, expected <0.1s"
    assert get_duration < 0.1, f"Get took {get_duration:.3f}s, expected <0.1s"
```

### Example 4: Security Test

```python
# tests/security/test_storage_path_traversal.py

import pytest


@pytest.mark.security
@pytest.mark.epic21
@pytest.mark.stage_21_01
@pytest.mark.storage
@pytest.mark.asyncio
async def test_storage_blocks_path_traversal(local_storage):
    """Security: Storage blocks path traversal attempts."""
    # Attempt path traversal
    with pytest.raises(StorageSecurityError):
        await local_storage.save_new(
            student_id="../../etc",
            assignment_id="passwd",
            filename="evil.txt",
            data=b"malicious content"
        )
```

---

## CI Integration

### GitHub Actions Matrix

```yaml
# .github/workflows/ci.yml

test:
  strategy:
    matrix:
      test-suite:
        - unit
        - integration
        - characterization
        - performance
        - security
      python-version: ['3.11']
  
  steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Bootstrap shared infra
      run: poetry run python scripts/ci/bootstrap_shared_infra.py --mongo-port 37017
    
    - name: Run ${{ matrix.test-suite }} tests
      run: |
        poetry run pytest -m "${{ matrix.test-suite }}" \
          --cov=src/ \
          --cov-report=json \
          --cov-report=term \
          -v
    
    - name: Upload coverage
      if: matrix.test-suite == 'unit'
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.json
        flags: epic21,${{ matrix.test-suite }}

# Epic 21 specific job
epic21-tests:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Run all Epic 21 tests
      run: |
        poetry run pytest -m epic21 \
          --cov=src/ \
          --cov-fail-under=85 \
          -v
```

---

## Marker Validation

### Pre-commit Hook (Optional)

```yaml
# .pre-commit-config.yaml (add to hooks)

- repo: local
  hooks:
    - id: check-pytest-markers
      name: Validate pytest markers
      entry: python scripts/quality/check_pytest_markers.py
      language: system
      pass_filenames: false
      files: ^tests/.*\.py$
```

### Validation Script

```python
# scripts/quality/check_pytest_markers.py

"""Validate that all test files use Epic 21 markers."""

import ast
import sys
from pathlib import Path

REQUIRED_MARKERS = {"epic21", "unit", "integration", "e2e"}

def check_file(filepath: Path) -> list[str]:
    """Check test file for Epic 21 markers."""
    tree = ast.parse(filepath.read_text())
    errors = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            decorators = [d.attr for d in node.decorator_list if hasattr(d, "attr")]
            if "epic21" in str(filepath) and "epic21" not in decorators:
                errors.append(f"{filepath}::{node.name} missing @pytest.mark.epic21")
    
    return errors

def main():
    errors = []
    for test_file in Path("tests").rglob("test_*.py"):
        if "epic21" in str(test_file) or "characterization" in str(test_file):
            errors.extend(check_file(test_file))
    
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    print("✅ All tests properly marked")

if __name__ == "__main__":
    main()
```

---

## Adding New Markers

### Process

1. **Propose marker** in Epic 21 planning doc
2. **Add to pytest.ini** with description
3. **Update this doc** with usage examples
4. **Notify team** in standup/Slack

### Template

```ini
# pytest.ini additions

markers =
    new_marker: Description of what this marker represents and when to use it
```

---

## Acceptance Criteria

- [ ] `pytest.ini` updated with all Epic 21 markers
- [ ] CI matrix uses markers correctly
- [ ] All new tests properly marked
- [ ] Team trained on marker usage (30 min session)

---

**Document Owner**: EP21 QA Lead  
**Status**: Ready for Stage 21_00  
**Last Updated**: 2025-11-11

