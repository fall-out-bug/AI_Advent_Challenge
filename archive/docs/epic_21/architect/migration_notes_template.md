# Migration Notes Template · Epic 21

**Purpose**: Standard template for documenting architectural migrations.

**Usage**: Copy this template for each Stage 21_01 sub-stage migration.

---

## Template

```markdown
# Migration: [COMPONENT_NAME] · Stage [STAGE_ID]

**Component**: [e.g., Dialog Context Repository]  
**Stage**: [e.g., 21_01a]  
**Date**: [YYYY-MM-DD]  
**Owner**: [Name]  
**Status**: [Planning | In Progress | Complete]

---

## Summary

[2-3 sentence overview of what is being migrated and why]

**Example**:
> Migrate ButlerOrchestrator from direct MongoDB access to DialogContextRepository
> interface. This isolates domain logic from infrastructure, enables testing with
> in-memory fakes, and supports future storage backend changes (Redis, etc.).

---

## Motivation

**Problem**: [What issue are we solving?]

**Current State**: [Brief description of current implementation]

**Target State**: [Brief description of desired state]

---

## Breaking Changes

### For Developers

- [ ] **API Changes**
  - [List any changed function signatures]
  - [List any removed/deprecated methods]
  
- [ ] **Import Changes**
  - Old: `from src.domain.agents.butler_orchestrator import ButlerOrchestrator`
  - New: `from src.infrastructure.di.container import DIContainer`

- [ ] **Configuration Changes**
  - [List any new environment variables]
  - [List any changed config keys]

### For Operations

- [ ] **Deployment Requirements**
  - [List any new dependencies]
  - [List any infrastructure changes]

- [ ] **Rollback Procedure**
  - Feature flag: `USE_NEW_[COMPONENT]=false`
  - [Additional rollback steps if needed]

---

## Migration Steps (Developer Guide)

### Step 1: Update Imports

**Before**:
```python
from src.domain.agents.butler_orchestrator import ButlerOrchestrator

orchestrator = ButlerOrchestrator(mongodb=mongo_client.butler)
```

**After**:
```python
from src.infrastructure.di.container import DIContainer

container = DIContainer(settings=get_settings())
orchestrator = container.butler_orchestrator  # ← DI injected
```

### Step 2: Update Tests

**Before**:
```python
@pytest.fixture
def orchestrator(mongo_db):
    return ButlerOrchestrator(mongodb=mongo_db)
```

**After**:
```python
@pytest.fixture
def orchestrator(test_di_container):
    return test_di_container.butler_orchestrator  # Uses in-memory repo
```

### Step 3: [Additional Steps...]

[Continue with detailed migration steps]

---

## Code Examples

### Example 1: [Use Case]

**Before**:
```python
# [Old code]
```

**After**:
```python
# [New code]
```

### Example 2: [Another Use Case]

[More examples as needed]

---

## Testing Migration

### Characterization Tests (Run Before)

```bash
# Capture current behavior
pytest tests/characterization/test_[component]_*.py -v

# Expected: All pass (baseline established)
```

### Validation Tests (Run After)

```bash
# Validate new implementation
pytest tests/characterization/test_[component]_*.py -v

# Expected: All pass (behavior unchanged)
```

### New Unit Tests

```bash
# Test new interface/adapter
pytest tests/unit/[component]/ -v
```

---

## Rollback Procedure

### If Issues Found Within 1 Hour of Deployment

1. **Disable feature flag**:
   ```bash
   sed -i 's/USE_NEW_[COMPONENT]=true/USE_NEW_[COMPONENT]=false/' ~/work/infra/.env.infra
   make day-12-restart-[service]
   ```

2. **Validate rollback**:
   ```bash
   poetry run pytest tests/smoke/ -v
   curl -s http://127.0.0.1:9090/api/v1/targets  # Check Prometheus
   ```

3. **Communicate**:
   - Post to `#ops-shared`
   - Update incident log
   - Schedule post-mortem

### If Issues Found >1 Hour After Deployment

[Follow full rollback plan from `docs/specs/epic_21/architect/rollback_plan.md`]

---

## Monitoring & Validation

### Key Metrics to Watch

| Metric | Baseline | Target | Alert Threshold |
|--------|----------|--------|-----------------|
| [Metric 1] | [Value] | [Value] | [Value] |
| [Metric 2] | [Value] | [Value] | [Value] |

**Example**:
| Metric | Baseline | Target | Alert Threshold |
|--------|----------|--------|-----------------|
| Dialog context latency (p95) | 80ms | <100ms | >150ms |
| Error rate | 0.1% | <0.5% | >1.0% |

### Prometheus Queries

```promql
# [Metric 1 query]
rate(dialog_context_repository_operations_total{status="error"}[5m])

# [Metric 2 query]
histogram_quantile(0.95, rate(dialog_context_repository_latency_seconds_bucket[5m]))
```

### Grafana Dashboard

- **Dashboard**: [Name/Link]
- **Panels**: [List key panels]

---

## Known Issues

### Issue 1: [Brief Description]

**Impact**: [Who/what is affected]  
**Workaround**: [Temporary fix]  
**Fix ETA**: [Date or "In backlog"]  
**Tracking**: [Jira ticket or GitHub issue]

### Issue 2: [Another Issue]

[Continue as needed]

---

## Data Migration (if applicable)

### Schema Changes

**Before**:
```json
{
  "session_id": "s1",
  "user_id": "alice",
  "turn": 1
}
```

**After**:
```json
{
  "session_id": "s1",
  "user_id": "alice",
  "turn": 1,
  "schema_version": 2  // ← Added
}
```

### Migration Script

```bash
# Run migration
poetry run python scripts/migrations/migrate_[component].py --dry-run

# Verify results
poetry run python scripts/migrations/verify_[component]_migration.py

# Apply for real
poetry run python scripts/migrations/migrate_[component].py --apply
```

### Rollback Data Migration

```bash
# Revert schema changes
poetry run python scripts/migrations/migrate_[component].py --rollback
```

---

## Acceptance Criteria

- [ ] Feature flag configured (`USE_NEW_[COMPONENT]=false` by default)
- [ ] Characterization tests pass (before migration)
- [ ] New unit tests written and passing
- [ ] Integration tests updated
- [ ] Code deployed to staging
- [ ] Feature flag enabled in staging
- [ ] Smoke tests pass in staging
- [ ] Monitoring dashboards updated
- [ ] Rollback procedure validated in staging
- [ ] Documentation updated (this file)
- [ ] Team notified (Slack/email)
- [ ] Ready for production deployment

---

## Timeline

| Date | Milestone | Status |
|------|-----------|--------|
| [YYYY-MM-DD] | Planning complete | ✅ Done |
| [YYYY-MM-DD] | Characterization tests written | 🔄 In Progress |
| [YYYY-MM-DD] | Interface extracted | ⏳ Pending |
| [YYYY-MM-DD] | Implementation complete | ⏳ Pending |
| [YYYY-MM-DD] | Staging deployment | ⏳ Pending |
| [YYYY-MM-DD] | Production deployment | ⏳ Pending |

---

## Communication Log

### [YYYY-MM-DD] Planning Kickoff
- **Attendees**: [Names]
- **Decisions**: [Key decisions]
- **Action Items**: [Who does what]

### [YYYY-MM-DD] Staging Deployment
- **Result**: [Success/Issues]
- **Metrics**: [Performance data]
- **Next Steps**: [Plan for production]

### [YYYY-MM-DD] Production Deployment
- **Result**: [Success/Issues]
- **Rollback**: [Yes/No]
- **Follow-up**: [Any issues to address]

---

## References

- **Epic 21 Plan**: `docs/specs/epic_21/epic_21.md`
- **Stage Plan**: `docs/specs/epic_21/stage_21_01.md`
- **Interface Design**: `docs/specs/epic_21/architect/interface_design_v2.md`
- **Rollback Plan**: `docs/specs/epic_21/architect/rollback_plan.md`
- **Testing Strategy**: `docs/specs/epic_21/architect/testing_strategy.md`

---

**Document Owner**: [Name]  
**Last Updated**: [YYYY-MM-DD]  
**Status**: [Planning | In Progress | Complete]
```

---

## Usage Instructions

### Creating New Migration Notes

1. **Copy template**:
   ```bash
   cp docs/specs/epic_21/architect/migration_notes_template.md \
      docs/specs/epic_21/migrations/21_01a_dialog_context_repo.md
   ```

2. **Fill in sections**:
   - Replace `[PLACEHOLDERS]` with actual values
   - Delete sections not applicable (e.g., Data Migration if no schema changes)
   - Add component-specific details

3. **Review checklist**:
   - [ ] Summary explains "what" and "why"
   - [ ] Breaking changes documented
   - [ ] Migration steps are actionable
   - [ ] Rollback procedure is clear
   - [ ] Acceptance criteria complete

4. **Commit**:
   ```bash
   git add docs/specs/epic_21/migrations/
   git commit -m "docs: add migration notes for [component]"
   ```

---

## Example (Filled Template)

See `docs/specs/epic_21/migrations/21_01a_dialog_context_repo.md` for completed example.

---

**Document Owner**: EP21 Architect  
**Status**: Ready for Stage 21_01  
**Last Updated**: 2025-11-11

