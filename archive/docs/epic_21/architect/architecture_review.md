# Epic 21 · Architecture Review & Recommendations

**Reviewer**: Architecture & Analytics Role  
**Date**: 2025-11-11  
**Epic**: Epic 21 — Repository Refactor for Rule Compliance  
**Status**: 🟡 Requires Critical Changes Before Implementation

---

## Executive Summary

Epic 21 presents a **well-structured plan** to align the repository with Clean Architecture
and unified Cursor rules. However, **critical gaps** in TDD compliance, deployment strategy,
and risk mitigation must be addressed before implementation begins.

### Overall Assessment

| Aspect | Rating | Status |
|--------|--------|--------|
| **Architecture Alignment** | 🟡 Partial | Interface design correct, layer placement needs clarification |
| **TDD Compliance** | 🔴 Non-compliant | Tests scheduled after refactoring (violates red-green-refactor) |
| **Operations Readiness** | 🔴 Missing | No deployment/rollback strategy, monitoring gaps |
| **Security Compliance** | 🟢 Good | Checksum, AV scan, env variables addressed |
| **Documentation Quality** | 🟡 Partial | Docstring plan exists, quality checklist missing |
| **Risk Management** | 🔴 Insufficient | Performance, data migration, rollback risks not covered |

---

## Critical Issues (Blockers)

### 1. TDD Violation: Tests After Implementation

**Severity**: 🔴 Critical  
**Impact**: High risk of breaking existing functionality without detection

**Problem**:
- Stage 21_03 (testing) scheduled **after** Stage 21_01 (architecture) and 21_02 (quality)
- Violates repository rule: *"Write test first, then the implementation (red-green-refactor)"*
- No characterization tests to capture current behavior before refactoring

**Evidence from Specs**:
```markdown
From specs.md §2:
> Reliability: Critical tests (review pipeline integration, shared infra
> connectivity) must pass before release

From repo rules (TDD Rules):
> Write test first, then the implementation (red-green-refactor).
> Never implement a feature without a corresponding test.
```

**Recommendation**:
1. Add **characterization tests** before each ARCH-* task
2. Restructure Stage 21_01 to include test-first approach:
   ```
   ARCH-21-01a: Write integration tests for ButlerOrchestrator (current behavior)
   ARCH-21-01b: Extract DialogContextRepository interface
   ARCH-21-01c: Migrate ButlerOrchestrator to use interface
   ARCH-21-01d: Validate all tests still pass
   ```
3. Create `stage_21_00_preparation.md` for test infrastructure setup

**Action Items**:
- [ ] Create `testing_strategy.md` with characterization test approach
- [ ] Update Stage 21_01 backlog to include test-first tasks
- [ ] Add test coverage baseline metrics before starting

---

### 2. Missing Deployment & Rollback Strategy

**Severity**: 🔴 Critical  
**Impact**: Cannot safely deploy to production without rollback capability

**Problem**:
- No feature flags for gradual rollout of new interfaces
- No rollback procedures if issues arise post-deployment
- No backward compatibility strategy during migration
- Deployment windows not aligned with `operations.md` schedule

**Evidence from Operations Guide**:
```markdown
From operations.md §5.1:
> Primary window: Saturday 02:00–06:00 UTC (low traffic, coordinated with support)
> Emergency maintenance: coordinate via ops chat (#ops-shared)

From operations.md §5.3:
> Pre-maintenance: announce window, snapshot configs, verify rollback plan
```

**Recommendation**:
1. Create **Stage 21_00 (Preparation)** with:
   - Feature flags: `USE_NEW_DIALOG_CONTEXT_REPO`, `USE_NEW_STORAGE_ADAPTER`
   - Rollback procedures for each stage
   - Configuration snapshot automation
2. Add deployment windows to Epic 21 timeline
3. Document emergency rollback triggers and owners

**Action Items**:
- [ ] Create `rollback_plan.md` with stage-by-stage procedures
- [ ] Create `deployment_checklist.md` aligned with ops maintenance template
- [ ] Add feature flag inventory to Epic 21 backlog
- [ ] Define rollback authority (EP21 tech lead or on-call engineer)

---

### 3. Overly Broad Scope for Stage 21_01

**Severity**: 🟠 High  
**Impact**: Difficult to isolate issues if multiple components change simultaneously

**Problem**:
ARCH-21-01 through ARCH-21-04 modify **4 critical components** in parallel:
- ButlerOrchestrator (dialog context persistence)
- HomeworkHandler (external API integration)
- ReviewRoutes (file system storage)
- ReviewSubmissionUseCase (orchestration logic)

**Risk Analysis**:
- If any component breaks, blast radius affects multiple workflows
- Integration testing becomes complex with 4 moving parts
- Rollback requires coordinating multiple interface changes

**Recommendation**:
Split Stage 21_01 into **sequential sub-stages**:

```markdown
## Revised Stage 21_01 Structure

### Stage 21_01a: Dialog Context Repository (Isolated)
- Extract DialogContextRepository interface
- Migrate ButlerOrchestrator
- **Reason**: Most isolated component, lowest risk
- **Duration**: 1 week

### Stage 21_01b: Homework Review Service
- Extract HomeworkReviewService interface  
- Migrate HomeworkHandler
- **Reason**: External API, independent of storage
- **Duration**: 1 week

### Stage 21_01c: Storage Abstraction
- Extract ReviewArchiveStorage interface
- Migrate ReviewRoutes
- **Reason**: Critical path, requires careful validation
- **Duration**: 2 weeks (includes security hardening)

### Stage 21_01d: Use Case Decomposition
- Refactor ReviewSubmissionUseCase
- **Reason**: Depends on 21_01c completion
- **Duration**: 1 week
```

**Action Items**:
- [ ] Update `stage_21_01.md` with sub-stage breakdown
- [ ] Create separate merge requests for each sub-stage
- [ ] Add validation gates between sub-stages

---

## Architecture Issues

### 4. Dependency Injection Strategy Unclear

**Severity**: 🟡 Medium  
**Impact**: Inconsistent wiring may lead to maintenance burden

**Problem**:
- "DI container" mentioned but no concrete implementation specified
- No examples of how presentation layer wires interfaces
- Unclear whether using library (dependency-injector) or manual factories

**From architecture.md §4**:
> Infra via Adapters: Use dependency injection to bridge between application
> services and external systems

**Current State in Specs**:
- `stage_21_01_interface_design.md` describes interfaces
- No wiring examples or container configuration

**Recommendation**:

Add DI wiring section to `stage_21_01_interface_design.md`:

```python
# Suggested Approach: Lightweight Manual DI

# src/infrastructure/di/container.py
class DIContainer:
    """Dependency injection container."""
    
    def __init__(self, config: Settings):
        self.config = config
        self._instances: dict[str, Any] = {}
    
    @cached_property
    def dialog_context_repo(self) -> DialogContextRepository:
        return MongoDialogContextRepository(
            mongo_client=self.mongo_client
        )
    
    @cached_property
    def butler_orchestrator(self) -> ButlerOrchestrator:
        return ButlerOrchestrator(
            context_repo=self.dialog_context_repo,  # ← interface injection
            llm_client=self.llm_client
        )

# src/presentation/api/dependencies.py
def get_container() -> DIContainer:
    """FastAPI dependency."""
    return DIContainer(config=get_settings())

# src/presentation/api/routes.py
@router.post("/dialog")
async def handle_dialog(
    container: DIContainer = Depends(get_container)
):
    orchestrator = container.butler_orchestrator
    ...
```

**Action Items**:
- [ ] Choose DI approach (manual vs dependency-injector library)
- [ ] Add wiring examples to interface_design.md
- [ ] Document test double injection strategy

---

### 5. Interface Layer Placement Inconsistency

**Severity**: 🟡 Medium  
**Impact**: Breaks Clean Architecture dependency rules if misplaced

**Problem**:
Interfaces proposed in different layers:
- `DialogContextRepository` → `src/domain/interfaces/` ✅
- `HomeworkReviewService` → `src/application/interfaces/` ⚠️
- `ReviewArchiveStorage` → `src/application/interfaces/` ⚠️

**Clean Architecture Principle**:
> Domain layer defines **all** interfaces it needs.
> Outer layers implement them (Dependency Inversion Principle).

**Analysis**:

| Interface | Used By | Correct Location |
|-----------|---------|------------------|
| `DialogContextRepository` | `ButlerOrchestrator` (domain) | `src/domain/interfaces/` ✅ |
| `HomeworkReviewService` | `HomeworkHandler` (domain) | **Should be** `src/domain/interfaces/` |
| `ReviewArchiveStorage` | `ReviewSubmissionUseCase` (application) | `src/application/interfaces/` ✅ |

**Recommendation**:
1. Move `HomeworkReviewService` interface to `src/domain/interfaces/`
2. Keep implementation in `src/application/services/homework_review_service.py`
3. Update dependency_audit.md with corrected layer diagram

**Action Items**:
- [ ] Audit all interfaces for correct layer placement
- [ ] Update `stage_21_01_interface_design.md` with layer rules
- [ ] Add layer dependency diagram to epic

---

### 6. Missing Architecture Diagrams

**Severity**: 🟡 Medium  
**Impact**: Difficult to visualize changes and communicate to stakeholders

**Problem**:
- Stage 21_01 exit criteria mentions "Updated dependency diagram"
- No actual diagrams exist in current spec files
- Hard to review architecture changes without visual representation

**Recommendation**:
Create `architecture_diagrams.md` with Mermaid diagrams:

1. **Current State**: Showing violated dependencies
2. **Target State**: Clean architecture with interfaces
3. **Migration Path**: Stage-by-stage transformation

See attached `architecture_diagrams.md` for examples.

**Action Items**:
- [ ] Create architecture_diagrams.md (done in this review)
- [ ] Add to Stage 21_01 deliverables
- [ ] Include in tech lead review meeting

---

## Operations & Security Issues

### 7. Monitoring Metrics Not Specified

**Severity**: 🟠 High  
**Impact**: Cannot detect regressions or measure success of refactor

**Problem**:
- OBS-21-03 mentions "refresh Prometheus/Grafana"
- No specific new metrics defined
- Existing metrics may break after interface changes

**From operations.md §4**:
> Metrics exported via Prometheus client; structured logger attaches
> contextual fields (e.g., trace_id)

**Recommendation**:

Define new metrics in `stage_21_03.md`:

```prometheus
# Dialog Context Repository
dialog_context_repository_operations_total{operation="get|save|delete", status="success|error"}
dialog_context_repository_latency_seconds{operation="get|save|delete"}

# Homework Review Service  
homework_review_service_requests_total{operation="list|review", status="success|error"}
homework_review_service_latency_seconds{operation="list|review"}

# Storage Adapter
review_archive_storage_bytes_written{backend="local|s3"}
review_archive_storage_checksum_failures_total
review_archive_storage_operations_total{operation="save|open|purge", status="success|error"}

# Use Case Decomposition
review_submission_rate_limit_hits_total
review_submission_log_analysis_duration_seconds
```

**Action Items**:
- [ ] Add metrics specification to `stage_21_03_observability_plan.md`
- [ ] Create Grafana dashboard templates
- [ ] Update alerting rules in coordination with EP03

---

### 8. Security: Credential Handling Unclear

**Severity**: 🟡 Medium  
**Impact**: Risk of hardcoded secrets in new adapters

**Problem**:
- Interface design doesn't specify how credentials flow to implementations
- No guidance on environment variable naming conventions
- Missing from security checklist

**From operations.md §2**:
> Credentials sourced from ~/work/infra/.env.infra

**Recommendation**:

Add security section to each interface:

```python
class ReviewArchiveStorage(Protocol):
    """Abstract storage for review archives.
    
    Security Requirements:
        - Credentials MUST be sourced from environment variables
        - For S3: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
        - For local: REVIEW_ARCHIVE_ROOT_PATH (default: ./review_archives)
        - Never log file contents or checksums
        - Apply size limits from operations.md (max 100MB per archive)
    
    Example:
        >>> storage = S3ReviewArchiveStorage(
        ...     bucket=os.getenv("S3_REVIEW_BUCKET"),
        ...     credentials_from_env=True  # ← explicit flag
        ... )
    """
```

**Action Items**:
- [ ] Add security requirements to all interface docstrings
- [ ] Update SEC-21-02 to include credential audit
- [ ] Document environment variables in operations.md

---

### 9. Performance Regression Risk

**Severity**: 🟡 Medium  
**Impact**: DI overhead may violate MCP latency SLOs

**Problem**:
- Adding interface layers + DI may increase latency
- No performance benchmarks planned
- MCP tools have strict latency thresholds (operations.md §4)

**From operations.md §4**:
```
| Tool discovery | 1.50s |
| Calculator tool | 1.20s |
```

**Recommendation**:
1. Add performance tests to TEST-21-01:
   ```python
   @pytest.mark.benchmark
   def test_dialog_context_repository_latency():
       """Ensure repository operations < 100ms."""
       assert repo.get_by_session("test") < 0.1  # seconds
   ```

2. Benchmark before/after for hot paths:
   - Dialog context retrieval (called on every message)
   - Review submission (called on every homework upload)

3. Add to risk register:
   ```markdown
   | Performance overhead from DI | Medium | Benchmark hot paths, add caching if needed |
   ```

**Action Items**:
- [ ] Add performance benchmarks to testing_strategy.md
- [ ] Define latency SLOs for new interfaces
- [ ] Include in Stage 21_03 exit criteria

---

### 10. Data Migration Strategy Missing

**Severity**: 🟠 High  
**Impact**: Changing DialogContext structure may break existing sessions

**Problem**:
- `DialogContextRepository` introduces abstraction layer
- May require schema changes in MongoDB
- No migration script planned for existing documents

**Risk Scenario**:
1. Deploy new `DialogContextRepository`
2. Old documents use different field names
3. Active user sessions break
4. Emergency rollback required

**Recommendation**:

Add to ARCH-21-01:

```markdown
### ARCH-21-01-DATA: Dialog Context Data Migration

**Purpose**: Ensure backward compatibility during repository migration.

**Tasks**:
1. Add `schema_version` field to all dialog_contexts documents
2. Support reading both old and new formats during transition period
3. Create migration script: `scripts/migrations/migrate_dialog_contexts.py`
4. Schedule migration during maintenance window (Saturday 02:00 UTC)
5. Monitor migration progress via Prometheus metrics

**Rollback Plan**:
- Keep old field names until 100% of documents migrated
- Dual-write to both old and new fields for 2 weeks
- Remove old fields only after validation period
```

**Action Items**:
- [ ] Create data migration task in backlog
- [ ] Add to rollback_plan.md
- [ ] Coordinate with DBA/ops for validation

---

## Documentation Issues

### 11. Docstring Quality Validation

**Severity**: 🟡 Medium  
**Impact**: Incomplete docstrings slip through automated checks

**Problem**:
- DOC-21-02-01 proposes pydocstyle for format checking
- No validation that examples are **runnable**
- No check for semantic completeness of `Purpose` sections

**From repo rules (Documentation Requirements)**:
> Every public function/class must have a docstring in English.
> Docstring structure: Purpose, Args, Returns, Exceptions, Example.

**Recommendation**:

Add docstring quality checklist to `stage_21_02_docstring_plan.md`:

```markdown
## Docstring Quality Gates

### Automated Checks (CI)
- [ ] pydocstyle: All sections present (Purpose, Args, Returns, Example)
- [ ] Type hints match Args documentation
- [ ] Example code syntax-highlighted correctly

### Manual Review Checklist
- [ ] Brief summary ≤ 1 line, no period
- [ ] Purpose explains "why", not just "what"
- [ ] Args include semantic meaning (not just type)
- [ ] Returns describes structure/semantics
- [ ] Example is copy-paste runnable (or marked as pseudo-code)
- [ ] Raises documents all exceptions
```

**Action Items**:
- [ ] Add docstring quality checklist to stage_21_02_docstring_plan.md
- [ ] Create custom linter for example runnability
- [ ] Include in CODE-21-03 acceptance criteria

---

### 12. Function Size Baseline Missing

**Severity**: 🟡 Medium  
**Impact**: Cannot measure progress on decomposition goals

**Problem**:
- CODE-21-01 targets "≤15 lines where practical, ≤40 lines absolute"
- No baseline metrics for current state
- No definition of "where practical"

**From repo rules (Clean Code Practices)**:
> Functions must be no longer than 15 lines where possible.
> One responsibility per function/method.

**Recommendation**:

Add metrics baseline to Epic 21 success criteria:

```markdown
## Function Size Metrics

| Metric | Baseline (pre-Epic 21) | Target (post-Epic 21) |
|--------|------------------------|----------------------|
| Functions >40 lines | 47 (measured via radon) | 0 |
| Functions 15-40 lines | 183 | <50 (acceptable for complex orchestration) |
| Average function length | 18.3 lines | <12 lines |

### Measurement Command
```bash
radon cc src/ -s -a --no-assert | grep "M " | wc -l  # >40 lines
radon cc src/ -s -a --no-assert | grep "F " | wc -l  # 15-40 lines
```

### Exemptions
- Test fixture setup functions (may exceed 15 lines)
- FastAPI dependency chains (acceptable if well-documented)
```

**Action Items**:
- [ ] Run baseline measurement before starting Epic 21
- [ ] Add to `metrics_baseline.md`
- [ ] Update CODE-21-01 with specific reduction targets

---

## Recommendations Summary

### Must-Have Before Starting (Blockers)

1. **Create Stage 21_00 (Preparation)** ← 🔴 Critical
   - Feature flags for gradual rollout
   - Rollback procedures
   - Test infrastructure setup
   - Baseline metrics collection

2. **Restructure Stage 21_01** ← 🔴 Critical
   - Add characterization tests before each ARCH-* task
   - Split into sub-stages (21_01a through 21_01d)
   - Include data migration planning

3. **Create Missing Documents** ← 🔴 Critical
   - `rollback_plan.md`
   - `testing_strategy.md` (with test-first approach)
   - `deployment_checklist.md`
   - `architecture_diagrams.md`

4. **Clarify DI Strategy** ← 🟠 High
   - Choose DI approach (manual vs library)
   - Add wiring examples to interface_design.md
   - Document test double injection

### Should-Have for Quality

5. **Define Monitoring Metrics** ← 🟠 High
   - Specify new Prometheus metrics
   - Create Grafana dashboard templates
   - Update alerting rules

6. **Add Performance Benchmarks** ← 🟡 Medium
   - Benchmark hot paths (dialog context, review submission)
   - Define latency SLOs for interfaces
   - Include in testing strategy

7. **Enhance Documentation Validation** ← 🟡 Medium
   - Docstring quality checklist
   - Function size baseline metrics
   - Security requirements in interfaces

### Nice-to-Have for Polish

8. **Architecture Diagrams Automation**
9. **Migration Script Templates**
10. **Communication Plan for Stakeholders**

---

## Alignment with Existing Epics

### Dependencies Confirmed

| Epic | Relationship | Coordination Notes |
|------|-------------|-------------------|
| **EP01** (Reviewer Hardening) | Shared components | Sync on repository interface changes |
| **EP03** (Observability) | Monitoring updates | Coordinate Prometheus/Grafana changes |
| **EP05** (Summarisation) | Reviewer inputs | Sequence refactors that affect summarization pipeline |

### Patterns from Previous Epics

Based on Epic 01, 02, 03, 04, 05, 06 structure:

✅ **Good Practices to Continue**:
- Stage breakdown (01/02/03)
- Backlog tracking
- Worklog updates
- Exit criteria per stage
- Signoff checklists

⚠️ **Missing from Epic 21**:
- Feature flag inventory (present in Epic 01)
- Rollout checklist (present in Epic 01)
- Risk register (present in Epic 03)
- Communication plan (present in Epic 04)
- Coordination logs (present in Epic 04)

**Recommendation**: Adopt best practices from previous epics.

---

## Revised Epic 21 Timeline

### Original Plan (from epic_21.md)
```
Stage 21_01: Architecture → Stage 21_02: Quality → Stage 21_03: Testing
```

### Recommended Plan

```
Stage 21_00: Preparation (NEW)
├── Feature flags setup
├── Baseline metrics collection
├── Test infrastructure
└── Rollback procedures documented
Duration: 1 week

Stage 21_01: Architecture (SPLIT)
├── 21_01a: Dialog Context Repository
├── 21_01b: Homework Review Service
├── 21_01c: Storage Abstraction
└── 21_01d: Use Case Decomposition
Duration: 5 weeks (1 week per sub-stage + 1 buffer)

Stage 21_02: Quality (ENHANCED)
├── Function decomposition (after 21_01)
├── Docstring compliance
└── Lint toolchain updates
Duration: 3 weeks

Stage 21_03: Guardrails (INTEGRATED THROUGHOUT)
├── Tests written alongside 21_01 (TDD)
├── Security hardening in 21_01c
└── Monitoring updates after each sub-stage
Duration: Parallel with 21_01-21_02, +1 week for final validation
```

**Total Duration**: ~9 weeks (vs original ~6 weeks)
**Rationale**: Test-first approach + sub-stages + preparation adds time but dramatically reduces risk.

---

## Decision Points for Tech Lead

### Immediate Decisions Required

1. **DI Approach**: Manual factories or dependency-injector library?
   - Recommendation: Manual (lower complexity, easier to debug)
   - Rationale: Project size doesn't justify library overhead

2. **Stage 21_01 Sequencing**: Parallel or sequential sub-stages?
   - Recommendation: Sequential (21_01a → 21_01b → 21_01c → 21_01d)
   - Rationale: Reduces blast radius, easier rollback

3. **Test Coverage Target**: 80% or higher?
   - Recommendation: 85% for refactored modules, 80% overall
   - Rationale: Higher confidence in critical paths

4. **Feature Flag Strategy**: Percentage rollout or binary on/off?
   - Recommendation: Binary for initial release, percentage in Stage 21_02
   - Rationale: Simpler to manage during architecture changes

### Questions for Stakeholders

1. **Operations**: Can we schedule 4 deployment windows (one per sub-stage)?
2. **QA**: Capacity for writing characterization tests before Stage 21_01?
3. **DevOps**: Prometheus/Grafana change approval process?
4. **Security**: AV scanning requirement mandatory or optional?

---

## Final Verdict

### 🟡 Conditional Approval with Required Changes

Epic 21 is **architecturally sound** but **operationally incomplete**.

**Approve for implementation ONLY AFTER**:
1. ✅ Stage 21_00 (Preparation) created with feature flags + rollback plan
2. ✅ Stage 21_01 restructured with test-first approach and sub-stages
3. ✅ Missing documents created (rollback, testing strategy, deployment checklist)
4. ✅ DI strategy clarified with wiring examples
5. ✅ Monitoring metrics specified

**Estimated Review Effort**: 2-3 days to address all recommendations.

**Next Steps**:
1. Tech lead reviews this architecture assessment
2. Create Stage 21_00 specification
3. Update Stage 21_01 with sub-stages
4. Schedule kickoff meeting with stakeholders
5. Begin Stage 21_00 implementation

---

**Reviewer Signature**: Architecture & Analytics Role  
**Review Date**: 2025-11-11  
**Next Review**: After Stage 21_00 completion

