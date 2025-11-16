# Epic 24 Backlog · Repository Hygiene & De-Legacy

## Context
Legacy refactor clusters A–E (see `docs/specs/epic_23/legacy_refactor_proposal.md`) translate into the work items below. Each task references the corresponding mini-epic plan under `docs/specs/epic_23/mini_epics/`.

## Tasks
1. **Cluster A – Mongo & Async Infrastructure**
   - TL-00: Confirm fixture naming, repository inventory, and CI baseline.
   - TL-01: Implement `settings.mongodb_url/test_mongodb_url` + DI factory.
   - TL-02: Add shared Mongo pytest fixtures with per-test DB teardown.
   - TL-03: Remove legacy event-loop fixtures, set `pytest-asyncio` mode.
   - TL-04: Update docs (`README*`, testing guide) + record evidence in `work_log.md`.

2. **Cluster B – Summarization & Digest Use Cases**
   - TL-00: Approve async contract + `SummarizerService` spec.
   - TL-01: Implement service interface and default implementation using LLM adapter.
   - TL-02: Refactor use-cases, fix repo signatures, remove undefined variables.
   - TL-03: Refresh unit/integration tests to mock `SummarizerService`.
   - TL-04: Update docs/challenge days, worklog, acceptance matrix.

3. **Cluster C – Butler Orchestrator & MCP-Aware Agent**
   - TL-00: Define public API + identify legacy test touchpoints.
   - TL-01: Refactor orchestrator/agent to expose stable API, enforce DI.
   - TL-02: Implement legacy adapter if required by existing integrations.
   - TL-03: Align metrics/tests with new API and observability labels.
   - TL-04: Update docs (Days 14/18) + worklog.

4. **Cluster D – LLM Clients & Map-Reduce Summarizer**
   - TL-00: Approve `LLMClientProtocol` and settings layout.
   - TL-01: Implement protocol + refactor clients to consume settings.
   - TL-02: Introduce dataclass for map-reduce chunk params; refactor summarizer.
   - TL-03: Update client/summarizer tests with protocol mocks.
   - TL-04: Document LLM config + update challenge days references.

5. **Cluster E – Telegram Helpers & Workers**
   - TL-00: Confirm lowercase normalisation policy and affected modules.
   - TL-01: Implement Telegram adapter + DI wiring.
   - TL-02: Update ChannelNormalizer + CLI/backoffice helpers.
   - TL-03: Refactor PostFetcherWorker/tests to use adapter and domain-level assertions.
   - TL-04: Update docs (Days 1/11/17) + worklog entries.

## Dependencies / Notes
- Clusters can start once TL-00 scope confirmed; A should lead to unblock others.
- Ensure CI secrets (`.env.infra`) available before running Mongo/LLM tests.
- Acceptance matrices for each cluster live under `docs/specs/epic_23/mini_epics/legacy_cluster_*_acceptance_matrix.md`.
# Epic 24 Backlog · Repository Hygiene & De-Legacy

## Context
Legacy issues identified during Epic 23 (`legacy_refactor_proposal.md`) and full test runs must be addressed to keep the repository maintainable, testable, and aligned with current architecture and infrastructure baselines.

This backlog groups work into clusters A–E plus documentation/archive hygiene.

## Tasks

### Cluster A — Mongo Repositories & Async Infrastructure
1. **Unify Mongo configuration**
   - Ensure all repositories use `Settings`/DI (`mongodb_url`, `test_mongodb_url`).
   - Remove direct `MongoClient(...)` instantiations with inlined URLs.
2. **Standardise Mongo test fixtures**
   - Introduce `test_mongodb` fixture that provisions per-test database and handles cleanup.
   - Update integration tests (workers, channels, evaluation) to use the shared fixture.
3. **Fix async/event loop issues**
   - Adopt `pytest-asyncio` with `asyncio_mode = auto`.
   - Remove legacy event-loop fixtures causing `RuntimeError: Event loop is closed`.

### Cluster B — Summarisation & Digest Use Cases
4. **Clarify digest use case contract**
   - Decide and document whether digest use cases are async or sync.
   - Update implementations and tests accordingly.
5. **Fix obvious digest bugs**
   - Remove references to undefined variables (`posts`, etc.).
   - Align repository calls (parameters, return types) with test expectations.
6. **Introduce summariser service abstraction**
   - Create `SummarizerService` interface in domain/application.
   - Update use cases to depend on the service instead of raw LLM calls.

### Cluster C — Butler Orchestrator & MCP-Aware Agent
7. **Define public APIs**
   - Document and expose minimal public methods for `MCPAwareAgent` and `ButlerOrchestrator`.
   - Mark internal helpers as private and refactor tests to use public APIs only.
8. **Adapter for legacy tests**
   - Implement thin adapter/shim for any still-useful legacy behaviours required by tests.
9. **Align MCP metrics**
   - Ensure MCP-related metrics labels match `observability_labels.md`.
   - Update tests to assert on the canonical label set.

### Cluster D — LLM Clients & Map-Reduce Summariser
10. **Stabilise LLM client interface**
    - Define `LLMClient` adapter with explicit methods (`generate`, `chat`, etc.).
    - Replace hard-coded URL expectations in tests with config-driven assertions.
11. **Normalise map-reduce summariser**
    - Introduce parameter dataclass for chunk summarisation to avoid signature drift.
    - Update tests to rely on the dataclass/API instead of private methods.

### Cluster E — Telegram Helpers, Channel Normaliser & Workers
12. **Channel normalisation policy**
    - Decide on canonical channel name format (e.g. lowercase).
    - Update normaliser implementation and tests to reflect agreed policy.
13. **Telegram client adapter**
    - Wrap `telegram_utils` in an adapter that tests and workers can mock easily.
14. **Worker DI and domain-focussed tests**
    - Ensure workers depend on repositories and Telegram adapter via DI.
    - Update tests to assert on domain outcomes (saved posts, timestamps) rather than Mongo internals.

### Documentation & Archive Hygiene
15. **Challenge Days & user guide sync**
    - Re-verify `docs/challenge_days.md` and `docs/USER_GUIDE_MULTI_AGENT_WORKFLOW.md` against refactored code.
    - Fix or update any links that point to moved/archived modules.
16. **Archive outdated specs/tests**
    - Move outdated or superseded specs/tests to `archive/` with clear labels.
    - Update active docs to reference archive materials only when historically relevant.
17. **Progress tracker alignment**
    - Update `docs/specs/progress.md` to reflect the final status of EP19–EP23 and EP24 once refactors are complete.

## Done When
- Cluster A–E acceptance criteria in `legacy_refactor_proposal.md` are met and reflected in tests and CI.
- `make test` passes on the standard shared infra baseline.
- Documentation and progress trackers are consistent with the refactored codebase.
