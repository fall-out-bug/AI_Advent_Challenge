# Epic 24 · Architect & Analyst Decisions

**Epic:** EP24 – Repository Hygiene & De-Legacy  
**Date:** 2025-11-16  
**Architect:** cursor_architect_v1  
**Analyst:** cursor_analyst_v1

## Decisions & Confirmations

### 1. Fixture Naming Convention ✅
**Question:** Confirm fixture naming convention for Mongo test fixtures.

**Decision:** Use standard names:
- **`mongodb_client`** — Session-scoped fixture providing authenticated `MongoClient`/`AsyncIOMotorClient` instance
- **`mongodb_database`** — Function-scoped fixture providing per-test database with automatic cleanup (database name derived from test node ID)

**Rationale:** Already referenced in Cluster A documentation, consistent with pytest fixture scoping conventions.

**Implementation Requirements:**
- Both fixtures use `Settings.test_mongodb_url` (no hardcoded URLs)
- In tests, **prioritize `mongodb_database`** (use by default)
- Use `mongodb_client` only when client-level operations are actually needed
- Cluster A (TL24-01) must implement these fixtures in `tests/conftest.py` or dedicated module

**Analyst Note:** Standardized approach ensures consistent test isolation and configuration management.

---

### 2. Async Strategy for Digest Use Cases ✅
**Question:** Should all digest use cases be async by default?

**Decision:** **Yes, all digest use cases must be async.**

**Business Contract:**
- `async def execute(...) -> DigestResult` — Standard async contract for all digest use cases
- Synchronous facades (CLI/scripts) are allowed **only as thin wrappers** over async implementations

**Implementation Requirements:**
- `GenerateChannelDigestByNameUseCase.execute(...)` → `async def execute(...) -> DigestResult`
- `GenerateChannelDigestUseCase.execute(...)` → `async def execute(...) -> DigestResult`
- All repository calls must be awaited
- All LLM client calls must be awaited
- Tests must use `pytest-asyncio` with `asyncio_mode = auto`
- CLI/script wrappers must use `asyncio.run()` or equivalent to invoke async use cases

**Rationale:** Digest use cases involve I/O operations (repository access, LLM calls) → this is I/O-bound work that benefits from async patterns.

**Analyst Note:** Business contract explicitly defines return type (`DigestResult`) and allows thin synchronous facades for CLI convenience without breaking async contract.

**Documentation:** In Cluster B TL-00, document `async def execute(...) -> DigestResult` contract and update all tests/docs accordingly.

---

### 3. Channel Normalization Policy ✅
**Question:** Confirm channel normalization policy (lowercase vs title-case).

**Decision:** **Canonical form: lowercase, without @ prefix.**

**Canonical Form (Domain):**
- Internal format: `lowercase`, **no @ prefix**
- Example: `"onaboka"` (not `"@onaboka"` or `"Onaboka"`)
- Used in: database keys, indexes, domain logic, internal lookups

**Edge Formatting (Presentation):**
- On edges (CLI, Telegram UI, reports), **@ prefix can be added** for display
- Example: `"@onaboka"` in CLI output or Telegram messages
- **But**: Database, indexes, and keys always use canonical form (lowercase, no @)

**Implementation Requirements:**
- `ChannelNormalizer` normalizes channel names to **lowercase without @**
- Database keys/indexes use canonical form (lowercase, no @)
- CLI/backoffice can format with @ for display, but store/query using canonical form
- Workers use canonical form for all internal operations
- Tests must **explicitly assert** canonical form (lowercase, no @)

**Rationale:** Canonical form prevents duplication and matching issues. Display formatting is separate from internal representation.

**Analyst Note:** Clear separation between canonical domain form (lowercase, no @) and presentation formatting (with @) ensures consistency in storage while allowing flexible UI formatting.

**Migration:** Cluster E (TL24-05) must ensure all components (CLI, backoffice, workers, tests) align with canonical form policy and explicitly test normalization behavior.

---

### 4. Public API Boundaries for MCPAwareAgent/ButlerOrchestrator ✅
**Question:** Define public API surface for `MCPAwareAgent` and `ButlerOrchestrator`.

**Decision:** Public API (what tests and integrations can rely on):

#### MCPAwareAgent — Public Methods
- `handle_message(context, message) -> AgentResponse` — Message handling entry point
- `handle_tool_result(context, tool_result) -> AgentResponse` — Tool result handling (if tool orchestration is used)

#### ButlerOrchestrator — Public Methods
- `handle_update(update) -> None / Response` — **Single entry point** from bot layer for handling Telegram updates

**Private Methods (Internal Helpers — Tests Must Not Touch):**
- `_resolve_channel_username()` — Channel normalization helpers
- FSM transition helpers
- Task handler internals (e.g., `mode_classifier`, `task_handler`)
- Internal state management attributes
- Any method/attribute with leading underscore `_`

**Implementation Requirements:**
- Mark internal helpers as private (leading underscore `_`)
- Tests must use **only public methods** or thin legacy adapter (if needed for compatibility)
- **No direct access to private attributes** in tests (`_field`, `_method()`, etc.)
- If legacy behavior is needed, add thin adapter with explicit contract
- Legacy adapter can be implemented if some legacy behaviours remain valuable

**Rationale:** Clear API boundaries enable stable testing and prevent coupling to implementation details. Single entry point (`handle_update`) simplifies bot integration.

**Analyst Note:** Public API focuses on external-facing methods that tests/integrations can rely on. Internal state machines and helpers are explicitly private to allow implementation flexibility.

**Documentation:** Cluster C (TL24-03) must document public API (including method signatures) and create legacy adapter if needed.

---

### 5. Legacy E2E Test Priorities & Archival Policy ✅
**Question:** Which E2E suites are critical and must remain active?

**Decision:** Critical E2E tests (cover actual user scenarios):

1. **Telegram Flow (Homework/Review)** — `tests/e2e/telegram/*` scenarios that match current bot behavior (if actually used in production)
2. **CLI Backoffice Core Commands:**
   - Digest generation (`digest` command)
   - Indexing operations
   - RAG comparison
   - Health checks
3. **Shared Infrastructure / Bootstrap / Health** — E2E that participate in **CI gates** (e.g., `make day-23-up/down`, bootstrap validation)
4. **MCP Performance/Latency Guardrails** — If included in current SLO requirements

**Non-Critical E2E Tests (Can Be Archived or Migrated):**
- Tests tied to outdated adapters (e.g., `LegacyDialogContextAdapter`)
- Tests tied to deprecated infrastructure (e.g., Airflow)
- Historical EP21 scenarios that don't match current architecture
- Tests replaced by integration tests with similar coverage

**Migration Options:**
1. **Archive to `tests/legacy/...`** — With explicit labels and descriptions in backlog (for historical reference)
2. **Rewrite on New Public APIs** — If scenario is still business-significant but needs refactoring to use public APIs

**Archival Process:**
- After fixing working integration tests/examples, archive non-critical E2E tests
- Move to `archive/tests/e2e/legacy/` or `tests/legacy/` with explanatory notes
- Update active docs to reference archived tests only when historically relevant

**Implementation:** Cluster refactoring must ensure critical E2E tests remain functional. TL24-06 handles archival and migration decisions.

**Analyst Note:** Critical E2E focuses on user-facing flows (Telegram bot, CLI commands) and CI gate reliability (shared infra, health checks). Legacy adapter tests can be archived or migrated based on business significance.

### Legacy Test Archival Policy

**Archive Location:**
- Non-critical legacy tests → `tests/legacy/...` or `archive/tests/e2e/legacy/...`
- Archived specs/docs → `archive/docs/...`

**Archival Criteria:**
1. Tests tied to outdated adapters (e.g., `LegacyDialogContextAdapter`)
2. Tests tied to deprecated infrastructure (e.g., Airflow)
3. Historical scenarios that don't match current architecture (e.g., EP21-specific)
4. Tests replaced by integration tests with similar coverage

**Archival Process:**
1. **Verify replacement exists** — Ensure integration tests or refactored E2E tests provide equivalent coverage
2. **Create archive directory** — Use `tests/legacy/<component>` or `archive/tests/e2e/legacy/<component>`
3. **Add explanatory README** — Document what was archived, why, and where to find replacement tests
4. **Update active docs** — Reference archived tests only when historically relevant
5. **Update CI** — Remove archived tests from CI runs (if they were flaky)

**Documentation Requirements:**
- Archive README must include:
  - **What:** Description of archived tests/specs
  - **Why:** Reason for archival (outdated adapter, replaced by X, etc.)
  - **When:** Date of archival
  - **Replacement:** Link to replacement tests/specs (if applicable)
  - **Historical Value:** When/why to reference archived tests (if applicable)

**Example Archive Structure:**
```
tests/legacy/
├── README.md                          # Archive index
├── dialog_context_adapter/
│   ├── test_legacy_adapter.py        # Archived tests
│   └── README.md                      # Component-specific notes
└── airflow/
    └── test_airflow_integration.py   # Archived tests
```

**Implementation:** TL24-06 (Documentation & Archive Hygiene) handles archival execution and documentation.

---

## Impact on Cluster Implementation

### Cluster A (TL24-01)
- ✅ Use `mongodb_client` and `mongodb_database` fixture names
- ✅ Implement session-scoped and function-scoped fixtures

### Cluster B (TL24-02)
- ✅ All digest use cases must be `async def execute(...)`
- ✅ Document async contract in TL-00 design phase
- ✅ Update all tests to use async/await
- ✅ Ensure critical summarization pipeline E2E remains functional

### Cluster C (TL24-03)
- ✅ Define and document public API (`run()`, `handle_message()`, `resolve_intent()`, `execute()`, `dispatch()`)
- ✅ Mark internal helpers as private
- ✅ Implement legacy adapter if needed for compatibility
- ✅ Ensure critical Butler/MCP dialog E2E remains functional

### Cluster E (TL24-05)
- ✅ Enforce lowercase channel normalization policy
- ✅ Update CLI/backoffice/workers/tests to expect lowercase
- ✅ Ensure critical PostFetcherWorker E2E remains functional

### TL24-06 (Documentation)
- ✅ Archive non-critical legacy E2E tests after integration tests fixed
- ✅ Update docs to reference archived tests only when historically relevant

---

## Sign-Off

**Architect:** ✅ _cursor_architect_v1 (2025-11-16)_  
**Analyst:** ✅ _cursor_analyst_v1 (2025-11-16)_

All decisions documented and confirmed with detailed clarifications. Ready to proceed with cluster implementation.

---

_Decisions documented by cursor_dev_a_v1 · 2025-11-16 · Architect & Analyst confirmations received_

