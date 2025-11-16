# Epic 24 · Pre-Start Review Report

**Reviewer:** cursor_reviewer_v1
**Date:** 2025-11-16
**Status:** ✅ **APPROVED WITH RECOMMENDATIONS**

## Executive Summary

Epic 24 plan is **well-structured and ready for execution** with minor recommendations for risk mitigation and clarity improvements. The plan correctly identifies legacy technical debt clusters (A–E) and provides a clear roadmap for refactoring. All critical architectural decisions have been confirmed (TL24-00 completed).

## Strengths

1. ✅ **Clear scope definition** — Legacy clusters A–E are well-defined with specific acceptance criteria
2. ✅ **Architectural decisions confirmed** — TL24-00 completed with all key decisions documented
3. ✅ **Proper sequencing** — Cluster A (Mongo/async infra) correctly identified as foundation
4. ✅ **Risk awareness** — Risk register identifies key concerns (regressions, timebox, docs drift)
5. ✅ **CI gates defined** — Clear quality gates for each stage

## Recommendations & Potential Issues

### 🔴 Critical (Address Before Start)

**None identified** — Plan is ready for execution.

### 🟡 High Priority (Address Early)

#### 1. **Test Coverage Baseline Missing**
**Issue:** No baseline test count/metrics documented before refactoring starts.
**Impact:** Difficult to measure progress and ensure no test loss during refactors.
**Recommendation:**
- Document current test counts per cluster (A–E) in `work_log.md` before TL24-01 starts
- Track test count changes per cluster to ensure no silent test removal
- Example: "Cluster A: 45 tests before, 48 tests after (3 new fixtures tests added)"

#### 2. **Characterization Tests Not Explicitly Required**
**Issue:** Plan mentions "characterisation tests" in risk mitigation but doesn't require them as DoD.
**Impact:** Risk R24-1 (refactors break production flows) may not be fully mitigated.
**Recommendation:**
- Add explicit DoD item for each cluster: "Characterisation tests capture current behaviour before refactor"
- Example for Cluster B: "Capture current digest output format/behaviour in test before refactoring SummarizerService"

#### 3. **Shared Fixture Migration Strategy Unclear**
**Issue:** TL24-01 migrates tests to shared fixtures, but migration order/strategy not specified.
**Impact:** Potential conflicts if multiple developers work on different test suites simultaneously.
**Recommendation:**
- Define migration order: repositories → workers → channels → evaluation
- Add DoD item: "All tests in migration order use shared fixture, verified via grep"

### 🟢 Medium Priority (Nice to Have)

#### 4. **Legacy Test Archive Policy Unclear**
**Issue:** Plan mentions archiving legacy tests but doesn't specify what gets archived vs. rewritten.
**Impact:** Inconsistent decisions across clusters.
**Recommendation:**
- Add explicit policy: "Tests referencing removed/renamed modules → archive. Tests with wrong contracts → rewrite. Tests with infra issues → fix."
- Document in `architect_decisions.md` or `tl24_00_scope_confirmation.md`

#### 5. **Cross-Cluster Dependencies Not Explicitly Tracked**
**Issue:** Some clusters may share modules (e.g., both B and D touch summarization).
**Impact:** Potential merge conflicts or duplicate work.
**Recommendation:**
- Add dependency matrix in TL24-00: "Cluster B depends on Cluster D for LLM client interface"
- Or explicitly state: "Clusters B and D can run in parallel if LLMClientProtocol is defined first (TL24-04.1)"

#### 6. **CI Bootstrap Check Timing**
**Issue:** `bootstrap_shared_infra.py --check` is required for TL24-01 and TL24-05, but timing not specified.
**Impact:** Tests may fail if infra not ready.
**Recommendation:**
- Add explicit step in TL24-01: "Verify `make day-23-up` and `bootstrap_shared_infra.py --check` pass before starting"
- Document in DoD: "Shared infra smoke test passes before repository fixture migration"

### 🔵 Low Priority (Optional Improvements)

#### 7. **Documentation Update Scope Could Be More Specific**
**Issue:** TL24-06 mentions updating docs but doesn't list specific files/sections.
**Impact:** Risk of missing doc updates.
**Recommendation:**
- Add checklist: "Update `docs/challenge_days.md` sections: Day 1 (Telegram), Day 11 (workers), Day 17 (ETL)"
- Reference specific sections that will change per cluster

#### 8. **Progress Tracker Update Timing**
**Issue:** `progress.md` update is in TL24-06, but intermediate status updates might be useful.
**Impact:** Less visibility during execution.
**Recommendation:**
- Consider updating `progress.md` after each cluster completion (not just at TL24-06)
- Or document: "Progress tracker updated incrementally in work_log.md, final update in TL24-06"

## Architecture Review

### ✅ Clean Architecture Boundaries
- Plan correctly emphasizes preserving boundaries
- No new domain→infrastructure violations expected
- Adapter pattern correctly identified for legacy behaviours

### ✅ Dependency Injection
- DI correctly identified as key pattern (Mongo, Telegram, LLM clients)
- Settings-based configuration aligns with Epic 23 baseline

### ✅ Test Strategy
- Shared fixtures approach is sound
- Domain-level assertions correctly prioritized over low-level checks

## Risk Assessment

### Existing Risks (from risk_register.md)
All identified risks are reasonable and have mitigations:
- ✅ R24-1: Refactors break production — Mitigation: characterisation tests, small PRs
- ✅ R24-2: Timebox overrun — Mitigation: prioritize A/B/C, defer low-impact
- ✅ R24-3: Docs drift — Mitigation: DoD includes doc updates
- ✅ R24-4: Architecture violations — Mitigation: architecture reviews

### Additional Risk Identified
**R24-5: Test Suite Regression During Migration**
- **Description:** Migrating tests to shared fixtures may introduce subtle bugs (fixture scope, cleanup order)
- **Impact:** Medium
- **Likelihood:** Medium
- **Mitigation:**
  - Run full test suite after each fixture migration batch
  - Add smoke test that verifies fixture cleanup (no DB leakage between tests)
  - Document in DoD: "Full test suite passes 3× consecutively after fixture migration"

## Acceptance Matrix Review

### ✅ Structure
- Matrix correctly maps backlog items to stages
- DoD evidence requirements are specific and measurable
- Sign-off process is clear

### ⚠️ Minor Issue
- Some DoD items reference "diffs" but don't specify what to diff against
- **Recommendation:** Add baseline references, e.g., "Code diff against `main` branch showing DI migration"

## CI/CD Gates Review

### ✅ Coverage
- All critical gates present (lint, typecheck, unit tests, integration tests, coverage)
- Shared infra smoke test correctly included

### ⚠️ Potential Gap
- No gate for verifying no new architecture violations (R24-4 mitigation)
- **Recommendation:** Consider adding static check or grep-based gate:
  ```bash
  # Example: Check for forbidden imports
  grep -r "from src.infrastructure import" src/domain/ || echo "OK"
  ```

## Timeline & Parallelization

### ✅ Sequencing
- Cluster A correctly identified as foundation
- Parallelization strategy is reasonable (B and D can overlap after A)

### ⚠️ Potential Bottleneck
- TL24-01 (Cluster A) is critical path — if it overruns, all other clusters are blocked
- **Recommendation:** Consider splitting TL24-01 into smaller sub-stages if it's taking too long:
  - TL24-01a: Settings + factory (1 day)
  - TL24-01b: Fixtures (1 day)
  - TL24-01c: Migration (1–2 days)

## Final Verdict

**Status:** ✅ **APPROVED FOR EXECUTION**

The plan is **production-ready** with the following action items:

### Before Starting TL24-01:
1. ✅ Document test baseline (counts per cluster)
2. ✅ Verify shared infra baseline (`make day-23-up`, `bootstrap_shared_infra.py --check`)
3. ✅ Add characterization test requirement to Cluster B DoD
4. ✅ Define migration order for test fixtures

### During Execution:
1. Monitor test counts per cluster to ensure no silent test loss
2. Run full test suite after each fixture migration batch
3. Update progress tracker incrementally (not just at TL24-06)

### Optional Enhancements:
1. Add static check for architecture violations to CI
2. Create dependency matrix for cross-cluster dependencies
3. Add specific doc update checklist to TL24-06

---

**Overall Quality Score:** 0.88/1.0
**Risk Level:** Low-Medium (mitigated)
**Confidence in Success:** High

The plan demonstrates strong understanding of legacy technical debt and provides a clear, executable roadmap. Minor recommendations above will further reduce execution risk.
