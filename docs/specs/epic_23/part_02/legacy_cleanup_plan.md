# Epic 24 · Legacy Code Cleanup Plan

**Purpose:**  
Document the strategy and process for archiving or removing legacy code as part of Epic 24 refactoring.

**Status:** Draft  
**Owner:** Tech Lead  
**Date:** 2025-11-17

---

## 1. Overview

Epic 24 refactoring will introduce new patterns (DI, shared fixtures, SummarizerService, etc.). Legacy code that doesn't align with these patterns should be archived or removed following a clear process.

**Key Principles:**
1. **Archive, don't delete** — Legacy code provides historical context and may be needed for reference.
2. **Clear labeling** — All archived code must have clear metadata explaining why it was archived and when.
3. **Active docs reference** — If archived code is referenced in active documentation, add pointers to the archive.
4. **Test coverage** — Before archiving, ensure new tests cover the same functionality.

---

## 2. Legacy Code Categories

### 2.1. Legacy Test Suites

**Location:** `tests/legacy/`

**Criteria for Archival:**
- Tests that depend on deprecated patterns (e.g., direct `get_db()` calls, global clients).
- Tests that duplicate coverage provided by new characterization/integration tests.
- Tests that verify behavior now covered by public API tests.

**Process:**
1. Verify new tests cover the same behavior (characterization tests + integration tests).
2. Move test files to `archive/tests/legacy/YYYY-MM-DD_epic24_<reason>/`
3. Add `ARCHIVE_REASON.md` in the archive directory explaining what was replaced.
4. Update active test docs to reference archive if needed.

**Examples:**
- `tests/legacy/src/e2e/` — E2E tests using old adapters
- `tests/legacy/src/infrastructure/test_task_repository.py` — Uses old patterns
- `tests/legacy/epic21/` — Epic 21-specific tests (some may be rewritten)

### 2.2. Deprecated Infrastructure Code

**Location:** Various `src/infrastructure/` modules

**Criteria:**
- Code replaced by new abstractions (e.g., direct `MongoClient` usage → `MongoClientFactory`).
- Code using deprecated patterns (e.g., global state, hardcoded URLs).

**Process:**
1. **Don't archive yet** — Keep for now if it's still in use.
2. **Mark as deprecated** — Add deprecation warnings to code that will be removed.
3. **Plan removal** — After Cluster refactoring is complete, evaluate removal.

**Note:** Most infrastructure code will be refactored, not archived. Only truly unused code should be archived.

### 2.3. Outdated Specifications/Documentation

**Location:** `docs/specs/epic_*/`, `docs/roles/*/`

**Criteria:**
- Specifications superseded by Epic 24 refactoring.
- Documentation referencing removed/renamed modules.

**Process:**
1. Review docs during TL24-06 (Documentation & Archive Hygiene).
2. Move outdated specs to `archive/docs/specs/epic_*/YYYY-MM-DD_epic24_superseded/`
3. Update active docs to reference archive or new locations.

---

## 3. Archive Structure

```
archive/
├── README.md                          # Archive index and policies
├── tests/
│   ├── legacy/
│   │   ├── YYYY-MM-DD_epic24_<reason>/
│   │   │   ├── ARCHIVE_REASON.md      # Why archived, what replaced it
│   │   │   └── <test_files>           # Original test files
│   │   └── ...
├── docs/
│   └── specs/
│       └── epic_*/
│           └── YYYY-MM-DD_epic24_superseded/
│               ├── ARCHIVE_REASON.md
│               └── <doc_files>
└── code/
    └── (only if truly unused code - most will be refactored, not archived)
```

---

## 4. Archive Metadata Template

Every archive directory must contain `ARCHIVE_REASON.md`:

```markdown
# Archive Reason

**Date:** YYYY-MM-DD  
**Epic:** EP24  
**Archive Reason:** [Brief description]

**What Was Archived:**
- List of files/modules

**Why It Was Archived:**
- Explanation (e.g., "Replaced by new SummarizerService abstraction", "Covered by characterization tests")

**What Replaces It:**
- Links to new tests/implementations
- References to relevant Epic 24 tasks

**Migration Notes:**
- How to port functionality if needed
- Breaking changes

**Reference:**
- Epic 24 acceptance matrix task
- Work log entry
```

---

## 5. Execution Plan by Cluster

### Cluster C (TL24-03) — Butler/MCP

**Legacy Code to Address:**
- Old MCP adapter tests using private APIs
- Butler orchestrator tests accessing internal state

**Action:**
- Refactor tests to use public APIs (C.2)
- Archive tests that can't be refactored (after C.5 verification)

### Cluster D (TL24-04) — LLM Clients

**Legacy Code to Address:**
- Tests with hardcoded URLs
- Map-reduce tests using private methods

**Action:**
- Refactor tests to use adapter interface (D.1-D.4)
- Archive tests that verify deprecated behavior (after D.5 verification)

### Cluster E (TL24-05) — Telegram & Workers

**Legacy Code to Address:**
- Worker tests with direct Mongo calls
- Tests using old channel normalization patterns

**Action:**
- Refactor tests to use DI and domain assertions (E.4-E.5)
- Archive tests that can't be migrated (after E.5 verification)

### TL24-06 — Documentation & Archive Hygiene

**Tasks:**
1. Review all legacy test suites — identify candidates for archival.
2. Verify new tests cover archived functionality — create mapping.
3. Move legacy tests to archive — follow structure above.
4. Update active docs — add archive references where needed.
5. Create archive index — update `archive/README.md`.

---

## 6. Verification Checklist

Before archiving any code:

- [ ] New tests cover the same functionality (characterization + integration)
- [ ] New implementation is stable and tested
- [ ] Archive reason documented (`ARCHIVE_REASON.md`)
- [ ] Active docs updated (references to archive or new location)
- [ ] Work log updated with archival decision
- [ ] Acceptance matrix reflects archival

---

## 7. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Archive code needed later | Medium | Keep archive well-documented with migration notes |
| Breaking active references | High | Review all docs/specs before archiving; update links |
| Test coverage gaps | High | Require characterization tests before archival |

---

## 8. Next Steps

1. **During Cluster refactoring (C, D, E):** Identify legacy code as we refactor.
2. **After each cluster:** Document what can be archived (after new tests pass).
3. **TL24-06:** Execute archival process and update documentation.

---

**See also:**
- `docs/specs/epic_24/architect_decisions.md` — Legacy test archival policy
- `docs/specs/epic_23/legacy_refactor_proposal.md` — Original legacy analysis
- `docs/specs/epic_24/tech_lead_plan.md` — TL24-06 tasks

