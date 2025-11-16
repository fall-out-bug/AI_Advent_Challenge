# TL24-00 · Scope Confirmation & Priorities

**Epic:** EP24 – Repository Hygiene & De-Legacy  
**Stage:** TL24-00  
**Date:** 2025-11-16  
**Owner:** Dev A (cursor_dev_a_v1)

## Scope Confirmation

### Cluster Boundaries (from `legacy_refactor_proposal.md`)

#### Cluster A – Mongo & Async Infrastructure ✅ Confirmed
- **Scope:** Mongo repositories, test fixtures, async infrastructure
- **Priority:** **HIGHEST** (must start first to stabilise test environment)
- **Dependencies:** None (starts first)
- **Impact:** Unblocks all other clusters

#### Cluster B – Summarization & Digest Use Cases ✅ Confirmed
- **Scope:** `GenerateChannelDigestByNameUseCase`, `GenerateChannelDigestUseCase`, summarizer integration
- **Priority:** **HIGH** (can run in parallel with D after A)
- **Dependencies:** Cluster A (for shared fixtures)
- **Impact:** Fixes undefined variables, establishes SummarizerService abstraction

#### Cluster C – Butler Orchestrator & MCP-Aware Agent ✅ Confirmed
- **Scope:** Butler orchestrator, MCP-aware agent, metrics alignment
- **Priority:** **HIGH** (can run in parallel with E after stable infra)
- **Dependencies:** Cluster A (for stable infra), Cluster D (for LLM interface)
- **Impact:** Defines public APIs, aligns metrics with observability_labels.md

#### Cluster D – LLM Clients & Map-Reduce Summarizer ✅ Confirmed
- **Scope:** LLM client adapters, map-reduce summarizer
- **Priority:** **HIGH** (can run in parallel with B after A)
- **Dependencies:** Cluster A (for settings), Cluster B (for SummarizerService spec)
- **Impact:** Stabilises LLM client interface, normalises summarizer signatures

#### Cluster E – Telegram Helpers & Workers ✅ Confirmed
- **Scope:** Channel normalizer, Telegram utils, post fetcher worker
- **Priority:** **MEDIUM** (can run in parallel with C after stable infra)
- **Dependencies:** Cluster A (for DI-based Mongo access)
- **Impact:** Canonical channel policy, Telegram adapter, domain-focused tests

#### TL24-06 – Documentation & Archive Hygiene ✅ Confirmed
- **Scope:** Challenge Days docs, USER_GUIDE, archive outdated specs/tests, progress.md
- **Priority:** **MEDIUM** (runs after all clusters)
- **Dependencies:** All clusters (A–E)
- **Impact:** Documentation aligned with refactored codebase

## Fixture Naming Conventions

Based on Epic 23 patterns and cluster plans:

### Mongo Fixtures
- **`mongodb_client`** — Session-scoped fixture providing authenticated `MongoClient` instance
- **`mongodb_database`** — Function-scoped fixture providing per-test database with automatic cleanup
- **Rationale:** Consistent with `test_mongodb` mentioned in cluster plans, but explicit naming clarifies scope

### Alternative Names Considered
- `test_mongodb` / `test_mongodb_db` — Less explicit about scope
- `mongo_client` / `mongo_database` — Shorter but less descriptive
- **Decision:** Use `mongodb_client` and `mongodb_database` for clarity

## Cluster Sequencing & Parallelisation

### Phase 1: Foundation (Days 1–4)
- **TL24-01 (Cluster A)** — Must complete first
- **Outcome:** Stable test fixtures, DI-based Mongo access, async patterns fixed

### Phase 2: Parallel Refactoring (Days 4–8)
- **TL24-02 (Cluster B)** + **TL24-04 (Cluster D)** — Can run in parallel after Cluster A
- **Outcome:** SummarizerService, LLM client adapter, map-reduce normalisation

### Phase 3: Orchestration & Workers (Days 5–11)
- **TL24-03 (Cluster C)** + **TL24-05 (Cluster E)** — Can run in parallel after stable infra
- **Outcome:** Public APIs defined, Telegram adapter, workers refactored

### Phase 4: Documentation (Days 10–12)
- **TL24-06 (Documentation & Archive)** — Runs after all clusters
- **Outcome:** Docs updated, archive organised, progress.md updated

## Cross-Epic Impacts

### EP19 (Document Embedding Index)
- **Impact:** Cluster A (Mongo fixtures) and Cluster D (LLM client) may affect embedding index
- **Mitigation:** Use shared fixtures from Cluster A, coordinate LLM client changes
- **Notes:** Embedding index repository may need updates to use new fixtures

### EP20 (RAG Comparison)
- **Impact:** Cluster D (LLM client adapter) may affect RAG comparison demos
- **Mitigation:** Ensure backward compatibility or provide migration guide
- **Notes:** RAG demos should continue working with new LLM client adapter

### EP21 (Multi-Pass Code Review)
- **Impact:** Cluster C (Butler/MCP APIs) may affect code review orchestration
- **Mitigation:** Public API changes documented, legacy adapter if needed
- **Notes:** Code review tool uses Butler/MCP orchestrator

### EP23 (Observability & Benchmark)
- **Impact:** Cluster A builds on EP23 shared infra (`make day-23-up/down`), Cluster C aligns metrics
- **Mitigation:** Ensure EP24 refactors respect EP23 observability instrumentation
- **Notes:** Metrics must remain compatible with EP23 observability_labels.md

## Open Questions for Architect & Analyst

### For Architect — ✅ ANSWERED (2025-11-16)
1. **Fixture Naming:** ✅ **Confirmed** — `mongodb_client` (session scope) and `mongodb_database` (function scope) as standard names. Already referenced in Cluster A documentation.
2. **Async Strategy:** ✅ **Confirmed** — All digest use cases must be async. This aligns with I/O operations (repositories/LLM). In TL-00 Cluster B, document `async def execute(...)` for both use cases and update tests/docs accordingly.
3. **Channel Normalization:** ✅ **Confirmed** — Fully lowercase policy. `ChannelNormalizer` normalizes names to lowercase, and CLI/backoffice/worker/tests must expect this format.
4. **Public API Surface:** ✅ **Confirmed** — For `MCPAwareAgent`/`ButlerOrchestrator`, public methods are high-level: `run()`, `handle_message()`, `resolve_intent()` (agent) and `execute()`/`dispatch()` (orchestrator). Internal helpers (channel normalization, FSM transitions) marked as private. Tests/integrations rely only on public methods or thin legacy adapter (if needed for compatibility).
5. **LLM Client Interface:** ⏳ Deferred — To be addressed during Cluster D design phase.

### For Analyst — ✅ ANSWERED (2025-11-16)
1. **Channel Policy:** ✅ **Confirmed** — Lowercase policy aligns with business requirements (Architect confirmation).
2. **Summarization Contract:** ✅ **Confirmed** — Async contract confirmed (Architect confirmation).
3. **Legacy E2E Tests:** ✅ **Confirmed** — Critical E2E tests:
   - Butler/MCP dialog (minimal scenario)
   - PostFetcherWorker (Telegram ingest) with adapter/DI
   - Summarization pipeline (digest generation) after Cluster B
   - Other legacy E2E (especially tied to outdated adapters or Airflow) can be archived after fixing working integration tests/examples.
4. **Documentation Priorities:** ⏳ To be refined during TL24-06 planning.

## Acceptance Matrix Status

- ✅ **Acceptance Matrix Created:** `docs/specs/epic_24/acceptance_matrix.md` (v1.0)
  - 32 tasks mapped across 7 stages (TL24-00 through TL24-06)
  - All clusters (A–E) and documentation tasks included
  - Detailed breakdown by sub-tasks (A.1–A.7, B.1–B.5, etc.)

- ✅ **Work Log Created:** `docs/specs/epic_24/work_log.md`
  - Initial entries for TL24-00 kickoff
  - Decisions section populated
  - Cross-epic impacts documented

- ✅ **Risk Register Created:** `docs/specs/epic_24/risk_register.md`
  - 8 risks identified with mitigation strategies
  - Risk review schedule defined

## Sign-Offs Required

| Role | Sign-Off Status | Date | Notes |
| --- | --- | --- | --- |
| Tech Lead | ⏳ Pending | — | Review scope, priorities, and fixture naming |
| Architect | ⏳ Pending | — | Review API boundaries, async strategy, channel policy |
| Analyst | ⏳ Pending | — | Review channel policy, summarization contract, E2E priorities |

## Next Steps (Post TL24-00)

1. **Architect + Analyst Review:** Confirm cluster boundaries and open questions
2. **Fixture Naming Confirmation:** Finalise `mongodb_client` / `mongodb_database` naming
3. **Sign-Off on Acceptance Matrix:** Get Tech Lead + Analyst + Architect approval
4. **Kick Off TL24-01:** Begin Cluster A (Mongo & Async Infrastructure) implementation

---

_Scope confirmed by cursor_dev_a_v1 · 2025-11-16_

