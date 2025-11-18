# Epic 24 · Cluster Dependency Matrix

**Epic:** EP24 – Repository Hygiene & De-Legacy
**Date:** 2025-11-16
**Purpose:** Explicitly track dependencies between clusters to guide sequencing and parallelisation

## Dependency Graph

```
TL24-01 (Cluster A: Mongo & Async Infrastructure)
  ├─> TL24-02 (Cluster B: Summarization & Digest)
  │   └─> Requires: Shared fixtures, DI-based Mongo config
  ├─> TL24-04 (Cluster D: LLM Clients & Map-Reduce)
  │   └─> Requires: Settings infrastructure (from A), SummarizerService spec (from B)
  ├─> TL24-03 (Cluster C: Butler/MCP Orchestration)
  │   └─> Requires: Stable infra baseline (A), LLM interface (D)
  └─> TL24-05 (Cluster E: Telegram & Workers)
      └─> Requires: DI-based Mongo access (A)

TL24-06 (Documentation & Archive)
  └─> Requires: All clusters (A, B, C, D, E) complete
```

## Detailed Dependencies

### Cluster A (TL24-01) – Foundation
**Depends on:** None (starts first)

**Provides to:**
- **Cluster B:** Shared `mongodb_database` fixture, DI-based Mongo config
- **Cluster D:** Settings infrastructure (`Settings.mongodb_url`, `Settings.test_mongodb_url`)
- **Cluster C:** Stable infra baseline (no auth errors, no event loop issues)
- **Cluster E:** DI-based Mongo access, shared fixtures

**Critical Deliverables:**
- `mongodb_client` (session-scoped) fixture
- `mongodb_database` (function-scoped) fixture
- `MongoClientFactory` or equivalent DI mechanism
- All repositories migrated to DI

---

### Cluster B (TL24-02) – Summarization & Digest
**Depends on:**
- **Cluster A:** Shared fixtures, DI-based Mongo config (for repository access)

**Provides to:**
- **Cluster D:** `SummarizerService` interface spec (for LLM client alignment)

**Critical Deliverables:**
- `SummarizerService` abstraction
- Async contract (`async def execute(...) -> DigestResult`)
- Fixed digest use cases (no undefined variables)

---

### Cluster D (TL24-04) – LLM Clients & Map-Reduce
**Depends on:**
- **Cluster A:** Settings infrastructure
- **Cluster B:** `SummarizerService` spec (to avoid duplicate abstractions)

**Provides to:**
- **Cluster C:** Stable LLM client interface (for MCP/Butler orchestration)

**Critical Deliverables:**
- `LLMClient` adapter interface
- Map-reduce summarizer parameter dataclass
- Config-driven client configuration

---

### Cluster C (TL24-03) – Butler/MCP Orchestration
**Depends on:**
- **Cluster A:** Stable infra baseline (no auth/loop errors)
- **Cluster D:** LLM client interface (for tool invocation)

**Provides to:**
- **None** (does not block other clusters)

**Critical Deliverables:**
- Public API documentation (`handle_message()`, `handle_tool_result()`, `handle_update()`)
- Legacy adapter (if needed)
- Metrics aligned with `observability_labels.md`

---

### Cluster E (TL24-05) – Telegram & Workers
**Depends on:**
- **Cluster A:** DI-based Mongo access, shared fixtures

**Provides to:**
- **None** (does not block other clusters)

**Critical Deliverables:**
- Channel normalization policy implementation (lowercase without @)
- `TelegramClientAdapter` interface
- Worker tests using domain assertions

---

### TL24-06 – Documentation & Archive
**Depends on:**
- **All Clusters:** A, B, C, D, E must be complete

**Provides to:**
- **None** (epic closure)

**Critical Deliverables:**
- Updated `challenge_days.md`
- Updated `USER_GUIDE_MULTI_AGENT_WORKFLOW.md`
- Archived legacy specs/tests
- Updated `progress.md`

## Parallelisation Strategy

### Phase 1: Foundation (Sequential)
- **TL24-01 (Cluster A)** — Must complete first
- **Outcome:** Stable test fixtures, DI-based Mongo access, async patterns fixed

### Phase 2: Parallel Refactoring (After A)
- **TL24-02 (Cluster B)** + **TL24-04 (Cluster D)** — Can run in parallel after Cluster A
  - **Note:** Cluster D needs `SummarizerService` spec from Cluster B, but can start interface design in parallel
- **Outcome:** SummarizerService, LLM client adapter, map-reduce normalisation

### Phase 3: Orchestration & Workers (After A + B/D)
- **TL24-03 (Cluster C)** + **TL24-05 (Cluster E)** — Can run in parallel after stable infra + LLM interface
  - **Cluster C** needs Cluster D's LLM interface
  - **Cluster E** only needs Cluster A
- **Outcome:** Public APIs defined, Telegram adapter, workers refactored

### Phase 4: Documentation (Sequential, After All)
- **TL24-06 (Documentation & Archive)** — Runs after all clusters
- **Outcome:** Docs updated, archive organised, progress.md updated

## Dependency Resolution Order

1. **TL24-01 (Cluster A)** — No dependencies, starts immediately
2. **TL24-02 (Cluster B)** — After A, provides SummarizerService spec
3. **TL24-04 (Cluster D)** — After A + B spec, provides LLM interface
4. **TL24-03 (Cluster C)** — After A + D, uses LLM interface
5. **TL24-05 (Cluster E)** — After A, can start in parallel with C
6. **TL24-06 (Documentation)** — After all clusters

---

**Dependency matrix maintained by:** cursor_dev_a_v1
**Reviewed by:** cursor_reviewer_v1
**Date:** 2025-11-16
