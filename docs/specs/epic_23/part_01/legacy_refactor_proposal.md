# Legacy Modules Refactor Proposal · Handoff to Architect & Tech Lead

## 1. Purpose & Scope

**Purpose:** Describe a structured refactor plan for legacy modules discovered while running full test suites during Epic 23 (Day 23).
**Scope:** Focus on modules and tests that are clearly out of sync with the current Clean Architecture, rely on legacy async patterns, or assume infrastructure that is no longer the default baseline. The work described here is intended to be executed **within Epic 23** as far as capacity allows (prioritised clusters), with any remaining tail explicitly rolled into future epics if needed.

This document is intended as a handoff to the Architect and Tech Lead to:
- Prioritise legacy refactor work,
- Decide on new epics or sub-epics,
- Align contracts for domain/application/infrastructure layers before implementation.

## 2. Current State (From `make test`)

Running `make test` with Epic 23 changes (snapshot as of 2025-11-16) yields:

- **Totals:** ~715 tests passing, 12 skipped, **70 failing**, **84 errors**.
- **Patterns in failures:**
  - **Infrastructure / env issues:**
    - MongoDB authentication errors (`Command insert/createIndexes/dropDatabase requires authentication`).
    - Shared infra connectivity issues (LLM health and Prometheus metrics not reachable when Day 23 stack is not running).
    - E2E fixtures using `ScopeMismatch` (session vs function scoped).
    - Legacy async tests still triggering `RuntimeError: Event loop is closed`.
  - **Code vs test contract drift:**
    - Summarization/digest use cases (`GenerateChannelDigestByNameUseCase`, `GenerateChannelDigestUseCase`).
    - Legacy Butler orchestration (`ButlerOrchestrator`, `MCPAwareAgent`, `IntentOrchestrator`).
    - LLM client and summarizer interfaces (`MistralClient`, map-reduce summarizer).
    - Telegram helpers and channel normalizer behaviour.

Epic 23 code paths (benchmarking, observability, RAG++) are covered and passing; the bulk of failures comes from **older integration/E2E tests and modules that pre-date the fully stabilised Clean Architecture**.

## 3. Refactor Cluster Overview

To make the work tractable, the proposal groups changes into five clusters. Each cluster can be implemented as a small epic or sub-epic with its own acceptance matrix.

### Cluster A — Mongo Repositories & Async Infrastructure

**Goal:** Normalise MongoDB access and async repository behaviour; remove ad-hoc connections and legacy event-loop issues.

- **Primary modules:**
  - `src/infrastructure/repositories/post_repository.py`
  - `src/infrastructure/repositories/mongo_dialog_context_repository.py`
  - Related tests:
    - `tests/infrastructure/repositories/test_post_repository.py`
    - `tests/integration/workers/test_post_fetcher_deduplication.py`
    - `tests/integration/channels/test_post_collection.py`
    - `tests/integration/evaluation/test_evaluation_flow.py`
    - `tests/integration/test_channel_digest_time_filtering.py`

- **Issues:**
  - Direct use of `MongoClient` with hardcoded URLs, no shared settings.
  - Tests rely on `dropDatabase` and implicit auth-less Mongo.
  - Event loop problems (`RuntimeError: Event loop is closed`) in async tests.

- **Proposed actions:**
  1. **Unify configuration:**
     - All Mongo access goes through `Settings`/DI (`settings.mongodb_url`, `settings.test_mongodb_url`), reusing Day 21/23 patterns.
  2. **Repository API normalisation:**
     - Encapsulate index creation and cleanup in repository methods (`ensure_indexes`, `drop_test_database`) with logging and explicit usage in tests.
  3. **Test fixtures:**
     - Introduce a single `real_mongodb`/`test_mongodb` fixture that creates per-test-database (name derived from test id) and handles cleanup.
     - Remove legacy event-loop fixtures and rely on `pytest-asyncio` with `asyncio_mode = auto`.

- **Acceptance criteria:**
  - No `OperationFailure: requires authentication` in repos/worker/channel integration tests when `MONGODB_URL`/`TEST_MONGODB_URL` are configured.
  - No `RuntimeError: Event loop is closed` in repository integration tests.
  - All repository tests use DI-based Mongo access (no inline `MongoClient(...)`).

### Cluster B — Summarization & Digest Use Cases

**Goal:** Align summarisation use cases and tests with the current domain/application boundaries; fix obvious logic bugs.

- **Primary modules:**
  - `src/application/use_cases/generate_channel_digest_by_name.py`
  - `src/application/use_cases/generate_channel_digest.py`
  - Related tests:
    - `tests/integration/summarization/test_digest_generation.py`
    - `tests/integration/summarization/test_summary_truncation.py`
    - `tests/integration/summarization/test_use_cases.py`

- **Issues:**
  - `NameError: name 'posts' is not defined` in `GenerateChannelDigestByNameUseCase`.
  - Mixed sync/async semantics: tests call `await use_case.execute(...)` while the implementation currently behaves like a synchronous use case.
  - Mismatched signatures between `post_repo.get_posts_by_channel(...)` and test side_effects (missing `user_id` argument).

- **Proposed actions:**
  1. **Clarify UseCase interface:**
     - Decide and document whether `GenerateChannelDigestByNameUseCase.execute` is async (recommended) or sync, and enforce this consistently.
  2. **Fix implementation bugs:**
     - Remove references to undefined variables such as `posts`.
     - Normalise parameters for `post_repo` calls to match repository contracts and test fixtures.
  3. **Extract summarizer service:**
     - Introduce a `SummarizerService` interface in the domain/application layer used by the use cases.
     - Update tests to mock `SummarizerService` instead of low-level LLM calls to reduce coupling.

- **Acceptance criteria:**
  - Digest summarization tests pass with a clear async/sync contract.
  - No use of undefined variables; summarization flow is covered with positive and negative test cases.
  - Summarization logic is injected as a dependency (testable in isolation).

### Cluster C — Butler Orchestrator & MCP-Aware Agent

**Goal:** Finish migration from legacy orchestration to the current FSM/intent-based architecture, while restoring a stable contract for tests.

- **Primary modules:**
  - Domain: `src/domain/agents/*` (especially `MCPAwareAgent`, `IntentOrchestrator`, `ButlerOrchestrator`).
  - Presentation: `src/presentation/bot/butler_bot.py`, dispatcher and handlers.
  - Related tests:
    - `tests/domain/agents/test_mcp_aware_agent.py`
    - `tests/agents/test_mcp_aware_agent_normalization.py`
    - `tests/agents/test_mcp_aware_agent_pipeline.py`
    - `tests/integration/butler/test_*`

- **Issues:**
  - Tests expect internal methods/fields (`_resolve_channel_username`, `mode_classifier`, `task_handler`), which no longer exist or were renamed.
  - Several tests fail with `ValueError: Incorrect label names` due to metric label changes in MCP-aware agent integration.

- **Proposed actions:**
  1. **Define explicit public API for `MCPAwareAgent` and `ButlerOrchestrator`:**
     - Mark internal helpers as private, expose minimal stable methods for tests.
     - Update tests to use the public API only.
  2. **Introduce adapter layer:**
     - If some legacy tests require behaviour that is still useful, implement a thin adapter (or shim) that maps old-style calls to the new architecture.
  3. **Metrics alignment:**
     - Ensure Prometheus labels for MCP-aware agent metrics (`mcp_requests_total`, etc.) match both observability expectations and test assertions.

- **Acceptance criteria:**
  - Butler/MCP integration tests use only public interfaces (no direct access to private attributes).
  - MCP metrics tests pass and align with `observability_labels.md`.
  - No new coupling from domain to infrastructure layers (respecting Clean Architecture boundaries).

### Cluster D — LLM Clients & Map-Reduce Summarizer

**Goal:** Consolidate LLM client interfaces and map-reduce summarizer into a coherent, testable API.

- **Primary modules:**
  - `src/infrastructure/llm/mistral_client.py`
  - `src/infrastructure/llm/summarizers/map_reduce_summarizer.py`
  - Related tests:
    - `tests/llm/test_llm_client.py`
    - `tests/unit/infrastructure/llm/summarizers/test_map_reduce_summarizer.py`

- **Issues:**
  - URL expectations in tests (`http://localhost:8000/chat` vs current base URL paths).
  - `MapReduceSummarizer._summarize_chunk` signature diverges from what tests expect (unexpected keyword arguments).

- **Proposed actions:**
  1. **Stabilise LLM client adapter:**
     - Define a single `LLMClient` interface with explicit methods (`generate`, `chat`, etc.).
     - Use configuration (`settings.llm_url`, path suffixes) instead of hard-coded URLs in tests.
  2. **Refactor map-reduce summarizer:**
     - Introduce a dataclass for chunk summarization parameters to avoid positional/keyword mismatches.
     - Align tests to that dataclass and avoid direct access to private methods where possible.

- **Acceptance criteria:**
  - LLM client tests assert behaviour via the adapter interface, not string comparison of URLs.
  - Map-reduce summarizer tests pass with consistent signatures and clear separation of responsibilities.

### Cluster E — Telegram Helpers, Channel Normalizer & Workers

**Goal:** Bring Telegram utilities, channel normalisation, and post-fetcher worker in line with domain rules and test expectations.

- **Primary modules:**
  - `src/infrastructure/clients/telegram_utils.py`
  - Channel normalizer in domain layer.
  - `src/workers/post_fetcher_worker.py`
  - Related tests:
    - `tests/unit/domain/test_channel_normalizer.py`
    - `tests/unit/infrastructure/test_digest_time_filtering.py`
    - `tests/workers/test_post_fetcher_worker.py`
    - E2E Telegram tests.

- **Issues:**
  - Channel normaliser now returns capitalised transliterations (`Naboka` vs expected `naboka`).
  - `telegram_utils` changed its API; tests still rely on old free functions.
  - Post fetcher worker tests observe that no posts are fetched or updated because mocks and worker implementation diverged.

- **Proposed actions:**
  1. **Define channel normalisation policy:**
     - Decide on canonical form (lowercase vs title-case) and update both implementation and tests accordingly.
  2. **Introduce Telegram client adapter:**
     - Wrap existing helpers in an adapter interface that tests can mock.
  3. **Align worker behaviour with domain expectations:**
     - Ensure the worker uses repositories and Telegram adapter through DI.
     - Update tests to check domain-level outcomes (e.g. number of saved posts, updated timestamps) rather than low-level Mongo calls.

- **Acceptance criteria:**
  - Channel normaliser tests reflect the agreed policy and pass.
  - Worker tests pass with meaningful domain assertions and no direct dependency on Mongo internals.

## 4. Proposed Execution Strategy

1. **Stabilise environment baseline (building on Epic 23):**
   - Use Day 23 shared infra baseline as the canonical setup:
     - `MONGODB_URL`, `TEST_MONGODB_URL`, `LLM_URL`, `PROMETHEUS_URL`, shared infra via `make day-23-up` / `make day-23-down` and `docs/specs/epic_23/shared_infra_restart.md`.
   - Ensure tests that require shared infra either:
     - Use that baseline end-to-end, or
     - Are explicitly marked as requiring it (and can be skipped/xfail when infra is not running).

2. **Refactor by cluster with mini-epics:**
   - Create one mini-epic per cluster (A–E) with its own acceptance matrix and work log.
   - For each cluster:
     - Freeze current behaviour (where possible) with characterisation tests.
     - Refactor towards the target architecture.
     - Update or replace tests to reflect the new contracts.

3. **Guardrails & tracking:**
   - Maintain Clean Architecture boundaries throughout (no new domain → infrastructure imports).
   - Require TDD for new or significantly changed behaviour.
   - Keep each cluster’s PRs focused (avoid mixing multiple clusters in a single change set).
   - Track cluster progress and decisions in `docs/specs/epic_23/work_log.md` and any future epic-specific acceptance matrices.

## 5. Questions for Architect & Tech Lead

Before implementation, the following decisions are needed:

1. **Scope & Prioritisation:**
   - Which cluster(s) should be tackled first (A–E)?
   - Are there any Day-specific constraints (e.g., tie Mongo/worker refactor to a future “Day 24” epic)?

2. **Async Strategy:**
   - Should all new use cases (e.g. summarization/digest) be async by default where IO is involved?
   - Do we enforce a strict pattern for async repositories across the codebase?

3. **Legacy E2E Tests:**
   - Which E2E suites are still considered critical?
   - Are some E2Es candidates for archiving (similar to `tests/legacy/epic21/*`) with a new, slimmer E2E suite built on top of the refactored modules?

4. **LLM & RAG++ Ownership:**
   - Should LLM client and RAG++ config ownership move to a dedicated “ML Platform” role, with clear contracts for application layer, or remain purely within the current repo?

Once these decisions are made, this proposal can be converted into one or more epics with concrete TL-00…TL-XX stages, similar to Epic 23.
