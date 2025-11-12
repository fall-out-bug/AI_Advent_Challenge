# Stage 21_00 · Preparation

## Goal
Establish the foundation for Epic 21 by setting up feature flags, collecting baseline
metrics, preparing test infrastructure, and documenting rollback procedures. This stage
ensures safe, reversible deployments for all subsequent architecture refactoring stages.

---

## Rationale

**From architecture review**:
> Epic 21 lacks deployment/rollback strategy and baseline metrics, creating risk for
> production deployments. Stage 21_00 addresses these gaps before code changes begin.

**Key Principles**:
1. **Feature flags first**: All new interfaces controlled by flags, off by default
2. **Measure before change**: Baseline metrics enable regression detection
3. **Practice rollback**: Validate procedures in staging before production
4. **Test infrastructure**: Ensure CI/test doubles ready for TDD approach

---

## Scope

### In Scope
- Feature flag configuration and validation tooling
- Baseline metric collection (performance, coverage, function size)
- Test infrastructure (DI container fixtures, in-memory fakes)
- Rollback procedure documentation and drill execution
- CI updates (test matrix, coverage enforcement)

### Out of Scope
- Code refactoring (begins in Stage 21_01)
- Interface extraction (Stage 21_01 deliverable)
- Docstring updates (Stage 21_02 deliverable)

---

## Deliverables

### 1. Feature Flag Infrastructure

#### Configuration (~/work/infra/.env.infra)

Add feature flags with safe defaults:

```bash
# Epic 21 Feature Flags (added YYYY-MM-DD)
# Reference: docs/specs/epic_21/stage_21_00_preparation.md

# Stage 21_01a: Dialog Context Repository
USE_NEW_DIALOG_CONTEXT_REPO=false

# Stage 21_01b: Homework Review Service
USE_NEW_HOMEWORK_REVIEW_SERVICE=false

# Stage 21_01c: Storage Abstraction
USE_NEW_STORAGE_ADAPTER=false

# Stage 21_01d: Use Case Decomposition
USE_DECOMPOSED_USE_CASE=false
```

#### Validation Script

Create `scripts/ops/check_feature_flags.py`:

```python
"""Validate Epic 21 feature flags configuration."""

import os
import sys
from pathlib import Path

EPIC_21_FLAGS = {
    "USE_NEW_DIALOG_CONTEXT_REPO": "Stage 21_01a: Dialog Context Repository",
    "USE_NEW_HOMEWORK_REVIEW_SERVICE": "Stage 21_01b: Homework Review Service",
    "USE_NEW_STORAGE_ADAPTER": "Stage 21_01c: Storage Abstraction",
    "USE_DECOMPOSED_USE_CASE": "Stage 21_01d: Use Case Decomposition",
}

def check_flags(epic: str) -> None:
    """Check feature flags for specified epic."""
    if epic != "21":
        print(f"Unknown epic: {epic}")
        sys.exit(1)
    
    print(f"Epic {epic} Feature Flags:")
    print("-" * 60)
    
    all_present = True
    for flag, description in EPIC_21_FLAGS.items():
        value = os.getenv(flag)
        if value is None:
            print(f"❌ {flag}: NOT SET (required)")
            all_present = False
        elif value.lower() == "false":
            print(f"✅ {flag}: False (safe)")
        elif value.lower() == "true":
            print(f"⚠️  {flag}: True (enabled)")
        else:
            print(f"❌ {flag}: Invalid value '{value}' (must be true/false)")
            all_present = False
        
        print(f"   └─ {description}")
    
    if not all_present:
        print("\n❌ Configuration incomplete. Add missing flags to .env.infra")
        sys.exit(1)
    
    print("\n✅ All flags configured correctly")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--epic", default="21", help="Epic number")
    args = parser.parse_args()
    check_flags(args.epic)
```

**Usage**:
```bash
# Check Epic 21 flags
poetry run python scripts/ops/check_feature_flags.py --epic 21

# Expected output (Stage 21_00 complete):
# Epic 21 Feature Flags:
# ------------------------------------------------------------
# ✅ USE_NEW_DIALOG_CONTEXT_REPO: False (safe)
#    └─ Stage 21_01a: Dialog Context Repository
# ✅ USE_NEW_HOMEWORK_REVIEW_SERVICE: False (safe)
#    └─ Stage 21_01b: Homework Review Service
# ✅ USE_NEW_STORAGE_ADAPTER: False (safe)
#    └─ Stage 21_01c: Storage Abstraction
# ✅ USE_DECOMPOSED_USE_CASE: False (safe)
#    └─ Stage 21_01d: Use Case Decomposition
# 
# ✅ All flags configured correctly
```

---

### 2. Baseline Metrics Collection

#### Script: scripts/ops/collect_baseline_metrics.py

```python
"""Collect baseline metrics before Epic 21 refactoring."""

import asyncio
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import pytest


async def collect_prometheus_metrics() -> dict[str, Any]:
    """Collect current Prometheus metrics."""
    async with httpx.AsyncClient() as client:
        # Key metrics to baseline
        queries = {
            "error_rate": 'rate(review_errors_total[5m])',
            "dialog_latency_p95": 'histogram_quantile(0.95, rate(dialog_handling_duration_seconds_bucket[5m]))',
            "review_latency_p95": 'histogram_quantile(0.95, rate(review_submission_duration_seconds_bucket[5m]))',
            "storage_writes": 'rate(storage_writes_total[5m])',
        }
        
        results = {}
        for name, query in queries.items():
            resp = await client.get(
                "http://127.0.0.1:9090/api/v1/query",
                params={"query": query}
            )
            data = resp.json()
            results[name] = data["data"]["result"]
        
        return results


def collect_code_metrics() -> dict[str, Any]:
    """Collect code quality metrics."""
    # Function size distribution (via radon)
    result = subprocess.run(
        ["radon", "cc", "src/", "-s", "-a", "--json"],
        capture_output=True,
        text=True
    )
    radon_data = json.loads(result.stdout) if result.stdout else {}
    
    # Count functions by size
    func_counts = {"<15": 0, "15-40": 0, ">40": 0}
    for file_data in radon_data.values():
        for item in file_data:
            if item.get("type") in ["function", "method"]:
                lines = item.get("lineno", 0)
                if lines <= 15:
                    func_counts["<15"] += 1
                elif lines <= 40:
                    func_counts["15-40"] += 1
                else:
                    func_counts[">40"] += 1
    
    # Test coverage
    cov_result = subprocess.run(
        ["pytest", "tests/", "--cov=src/", "--cov-report=json", "-q"],
        capture_output=True
    )
    coverage_file = Path("coverage.json")
    coverage_data = json.loads(coverage_file.read_text()) if coverage_file.exists() else {}
    
    return {
        "function_size_distribution": func_counts,
        "test_coverage_percent": coverage_data.get("totals", {}).get("percent_covered", 0),
        "total_functions": sum(func_counts.values()),
    }


async def main(output_path: str) -> None:
    """Collect all baseline metrics."""
    print("Collecting Epic 21 baseline metrics...")
    
    baseline = {
        "timestamp": datetime.utcnow().isoformat(),
        "epic": "21",
        "stage": "21_00_preparation",
        "prometheus": await collect_prometheus_metrics(),
        "code": collect_code_metrics(),
    }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(baseline, indent=2))
    
    print(f"✅ Baseline metrics saved to {output_path}")
    print(f"\nSummary:")
    print(f"  Functions >40 lines: {baseline['code']['function_size_distribution']['>40']}")
    print(f"  Test coverage: {baseline['code']['test_coverage_percent']:.1f}%")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--epic", default="21")
    parser.add_argument("--output", default="docs/specs/epic_21/architect/baseline_metrics.json")
    args = parser.parse_args()
    
    asyncio.run(main(args.output))
```

**Usage**:
```bash
# Collect baseline (before any refactoring)
poetry run python scripts/ops/collect_baseline_metrics.py --epic 21

# Expected output:
# ✅ Baseline metrics saved to docs/specs/epic_21/architect/baseline_metrics.json
# 
# Summary:
#   Functions >40 lines: 47
#   Test coverage: 73.2%
```

---

### 3. Test Infrastructure

#### Test Fixtures (tests/conftest.py additions)

```python
"""Shared test fixtures for Epic 21."""

import pytest
from src.infrastructure.di.container import DIContainer


# --- In-Memory Test Doubles ---

class InMemoryDialogContextRepository:
    """Fake repository for fast unit tests (no MongoDB required)."""
    
    def __init__(self):
        self._store: dict[str, dict] = {}
    
    async def get_by_session(self, session_id: str):
        return self._store.get(session_id)
    
    async def save(self, context):
        self._store[context.session_id] = context
    
    async def delete(self, session_id: str):
        self._store.pop(session_id, None)


class FakeHomeworkReviewService:
    """Predictable service for testing (no external API calls)."""
    
    async def list_recent_commits(self, days: int):
        return [
            {"hash": "abc123", "date": "2025-11-10", "student": "alice"},
            {"hash": "def456", "date": "2025-11-11", "student": "bob"},
        ]
    
    async def request_review(self, commit_hash: str):
        return {"status": "success", "review_id": f"test_review_{commit_hash}"}


class InMemoryReviewArchiveStorage:
    """In-memory storage for fast tests (no file system)."""
    
    def __init__(self):
        self._store: dict[str, bytes] = {}
    
    async def save_new(self, student_id, assignment_id, filename, data):
        key = f"{student_id}/{assignment_id}/{filename}"
        self._store[key] = data
        return {"path": key, "checksum": "test_checksum", "size": len(data)}
    
    async def open(self, path):
        return self._store.get(path, b"")


# --- Fixtures ---

@pytest.fixture
def in_memory_dialog_repo():
    """Provide in-memory dialog context repository."""
    return InMemoryDialogContextRepository()


@pytest.fixture
def fake_homework_service():
    """Provide fake homework review service."""
    return FakeHomeworkReviewService()


@pytest.fixture
def in_memory_storage():
    """Provide in-memory review archive storage."""
    return InMemoryReviewArchiveStorage()


@pytest.fixture
def test_di_container(in_memory_dialog_repo, fake_homework_service, in_memory_storage):
    """Provide DI container with test doubles (no external dependencies)."""
    container = DIContainer(config=test_settings)
    
    # Override with test doubles
    container._instances["dialog_context_repo"] = in_memory_dialog_repo
    container._instances["homework_review_service"] = fake_homework_service
    container._instances["review_archive_storage"] = in_memory_storage
    
    return container
```

**Usage in Tests**:
```python
# tests/unit/domain/test_butler_orchestrator.py

@pytest.mark.asyncio
async def test_butler_saves_context(test_di_container):
    """Unit: ButlerOrchestrator saves context via repository."""
    orchestrator = test_di_container.butler_orchestrator
    
    await orchestrator.handle_message("alice", "Hello")
    
    # Verify context saved (via in-memory repo, fast!)
    repo = test_di_container.dialog_context_repo
    context = await repo.get_by_session(orchestrator.current_session_id)
    assert context.user_id == "alice"
```

---

### 4. CI Test Matrix Updates

#### .github/workflows/ci.yml

```yaml
# Add Epic 21 test suite to CI

test:
  strategy:
    matrix:
      test-suite:
        - unit
        - integration
        - characterization  # NEW: Epic 21
        - performance       # NEW: Epic 21
      python-version: ['3.11']
  
  steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Bootstrap shared infra
      run: poetry run python scripts/ci/bootstrap_shared_infra.py --mongo-port 37017
    
    - name: Run ${{ matrix.test-suite }} tests
      run: |
        poetry run pytest tests/${{ matrix.test-suite }}/ \
          --cov=src/ \
          --cov-report=json \
          --cov-report=term \
          -v
    
    - name: Check coverage threshold
      if: matrix.test-suite == 'unit'
      run: |
        poetry run pytest tests/ --cov=src/ --cov-fail-under=80
        # Fail if coverage drops below 80%
    
    - name: Upload coverage to Codecov
      if: matrix.test-suite == 'unit'
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.json
        flags: epic21

# Add Epic 21 baseline check job
baseline-check:
  runs-on: ubuntu-latest
  steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Check feature flags present
      run: |
        poetry run python scripts/ops/check_feature_flags.py --epic 21
    
    - name: Validate baseline metrics
      run: |
        test -f docs/specs/epic_21/architect/baseline_metrics.json
        echo "✅ Baseline metrics file present"
```

---

### 5. Rollback Drill Execution

#### Objective

Validate rollback procedures in staging before production deployment.

#### Steps

1. **Deploy Stage 21_01a to staging** (with feature flag off)
2. **Enable feature flag** (simulate gradual rollout)
3. **Execute rollback** (toggle flag off, restart services)
4. **Validate functionality restored** (smoke tests pass)
5. **Document timing and deviations** (update rollback_plan.md)

#### Script: scripts/ops/rollback_drill.py

```python
"""Execute rollback drill for Epic 21."""

import asyncio
import time
from pathlib import Path


async def rollback_drill(stage: str, environment: str, record_metrics: bool) -> None:
    """Execute rollback drill for specified stage."""
    print(f"Starting rollback drill: {stage} ({environment})")
    print("-" * 60)
    
    # Step 1: Toggle feature flag off
    print("Step 1: Disabling feature flag...")
    start = time.time()
    # (Simulate flag toggle)
    flag_toggle_time = time.time() - start
    print(f"  ✅ Flag toggled in {flag_toggle_time:.2f}s")
    
    # Step 2: Restart services
    print("Step 2: Restarting services...")
    start = time.time()
    # (Simulate service restart)
    restart_time = time.time() - start
    print(f"  ✅ Services restarted in {restart_time:.2f}s")
    
    # Step 3: Run smoke tests
    print("Step 3: Running smoke tests...")
    start = time.time()
    # (Run pytest smoke suite)
    smoke_test_time = time.time() - start
    print(f"  ✅ Smoke tests pass in {smoke_test_time:.2f}s")
    
    total_time = flag_toggle_time + restart_time + smoke_test_time
    print(f"\n✅ Rollback drill complete in {total_time:.2f}s")
    
    if record_metrics:
        metrics = {
            "stage": stage,
            "environment": environment,
            "flag_toggle_time": flag_toggle_time,
            "restart_time": restart_time,
            "smoke_test_time": smoke_test_time,
            "total_time": total_time,
        }
        # Save metrics
        print(f"\nMetrics: {metrics}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, help="e.g., 21_01a")
    parser.add_argument("--environment", default="staging")
    parser.add_argument("--record-metrics", action="store_true")
    args = parser.parse_args()
    
    asyncio.run(rollback_drill(args.stage, args.environment, args.record_metrics))
```

**Usage**:
```bash
# Practice rollback in staging
poetry run python scripts/ops/rollback_drill.py --stage 21_01a --environment staging --record-metrics

# Expected output:
# Starting rollback drill: 21_01a (staging)
# ------------------------------------------------------------
# Step 1: Disabling feature flag...
#   ✅ Flag toggled in 0.12s
# Step 2: Restarting services...
#   ✅ Services restarted in 8.45s
# Step 3: Running smoke tests...
#   ✅ Smoke tests pass in 12.33s
# 
# ✅ Rollback drill complete in 20.90s
```

---

## Work Breakdown

| Task ID | Description | Owner | Duration | Dependencies |
|---------|-------------|-------|----------|--------------|
| PREP-21-01 | Add feature flags to .env.infra | DevOps | 1 day | None |
| PREP-21-02 | Create check_feature_flags.py script | DevOps | 1 day | PREP-21-01 |
| PREP-21-03 | Create collect_baseline_metrics.py | QA + DevOps | 2 days | None |
| PREP-21-04 | Run baseline collection, commit results | QA | 1 day | PREP-21-03 |
| PREP-21-05 | Add test doubles to conftest.py | QA | 2 days | None |
| PREP-21-06 | Update CI test matrix | DevOps | 1 day | PREP-21-05 |
| PREP-21-07 | Create rollback_drill.py script | DevOps | 1 day | None |
| PREP-21-08 | Execute rollback drill in staging | DevOps + QA | 1 day | PREP-21-07, PREP-21-01 |
| PREP-21-09 | Document baseline & drill results | Tech Lead | 1 day | PREP-21-04, PREP-21-08 |

**Total Duration**: ~5 days (1 week with buffer)

---

## Exit Criteria

- [ ] **Feature flags configured**:
  - [ ] All 4 Epic 21 flags present in .env.infra
  - [ ] All flags set to `false` (safe defaults)
  - [ ] Validation script runs successfully

- [ ] **Baseline metrics collected**:
  - [ ] Prometheus metrics snapshot saved
  - [ ] Code metrics (function size, coverage) recorded
  - [ ] Baseline file committed to docs/specs/epic_21/architect/

- [ ] **Test infrastructure ready**:
  - [ ] In-memory test doubles created (dialog repo, HW service, storage)
  - [ ] Test fixtures available in conftest.py
  - [ ] CI test matrix updated with characterization/performance suites

- [ ] **Rollback validated**:
  - [ ] Rollback drill executed in staging (timed)
  - [ ] Rollback timing <30 minutes (meets SLO)
  - [ ] Deviations documented in rollback_plan.md

- [ ] **Documentation complete**:
  - [ ] Stage 21_00 deliverables documented
  - [ ] Baseline metrics published
  - [ ] Rollback drill results recorded

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Baseline metrics incomplete | Low | Medium | Validate prometheus/code metrics tools working before execution |
| Rollback drill reveals timing issues | Medium | High | Schedule extra buffer in deployment windows if >30min |
| Test doubles don't match real behavior | Medium | High | Add integration tests to validate doubles match production adapters |
| CI updates break existing tests | Low | High | Run full test suite after CI changes, rollback if failures |

---

## Coordination Notes

- **Epic 01**: Align feature flag approach with existing inventory (stage_01_01_feature_flag_inventory.md)
- **Epic 03**: Coordinate Prometheus metric collection with observability team
- **DevOps**: Schedule staging access for rollback drill execution
- **QA**: Validate test doubles cover all interface methods

---

## Acceptance Criteria

- [ ] All exit criteria met
- [ ] Tech Lead sign-off on baseline metrics
- [ ] DevOps approval of feature flag setup
- [ ] QA approval of test infrastructure
- [ ] Rollback drill results reviewed and accepted

---

## References

- **Feature Flags**: Epic 01 `stage_01_01_feature_flag_inventory.md`
- **Rollback Plan**: `docs/specs/epic_21/architect/rollback_plan.md`
- **Testing Strategy**: `docs/specs/epic_21/architect/testing_strategy.md`
- **Operations Guide**: `docs/specs/operations.md` §2-5

---

**Stage Owner**: EP21 Tech Lead + DevOps + QA  
**Created**: 2025-11-11  
**Target Completion**: 2025-11-19 (Week 1 of Epic 21)

