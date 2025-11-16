# Epic 23 · Stage 23_02 · Repository Hygiene & De-Legacy (Day 24 Continuation)

## Context
- Stage 23_01 (Epic 23) delivered observability and benchmark enablement plus Challenge Days 1–22 gap closure.
- This stage (23_02) focuses on removing legacy technical debt that still slows down CI, tests, and onboarding, effectively acting as the "second half" of Epic 23 / Day 24.
- `docs/specs/epic_23/legacy_refactor_proposal.md` identified five refactor clusters (Mongo/async, summarisation, Butler/MCP, LLM clients, Telegram/worker), which now form the backbone of this stage.

## Goals
1. Unify MongoDB access, fixtures, and async patterns so test suites run without authentication or event-loop errors.
2. Stabilise summarization/digest use-cases through a dedicated `SummarizerService`, replacing brittle LLM mocks.
3. Finalise Butler/MCP-aware agent APIs with clear public interfaces and observability-compliant metrics.
4. Consolidate LLM clients and map-reduce summarizer interfaces for reuse across RAG, benchmarking, and demos.
5. Standardise Telegram helpers, channel normalisation, and post-fetcher workers to match Challenge Day pipelines.

## Success Metrics
- `pytest tests/infrastructure/repositories tests/integration/channels tests/integration/workers` passes without `OperationFailure` or `RuntimeError` for 3 consecutive runs.
- Summarization suites run with async contracts and do not rely on undefined variables or direct LLM mocks.
- Butler/MCP integration tests reference only public APIs; `/metrics` conforms to `docs/operational/observability_labels.md`.
- LLM client + map-reduce summarizer tests pass with protocol-based mocks and no hard-coded URLs.
- Telegram/worker suites verify domain-level outcomes; channel names remain consistent (lowercase) across CLI, docs, and DB.
- Acceptance matrices for clusters A–E fully signed off and linked from `work_log.md`.

## Scope
### Must Have
- Implement TL-00…TL-04 stages for clusters A–E (see `docs/specs/epic_23/mini_epics/legacy_cluster_*_plan.md`).
- Update CI configuration (where applicable) to use new fixtures/settings.
- Document any migrations (channel naming, adapter changes) and update Challenge Day references if behaviour changes.

### Should Have
- Backfill additional regression tests uncovered during refactors (e.g., summarizer failure modes, Telegram adapter error handling).
- Add developer guides for new adapters/services (LLM, Telegram, Mongo fixtures).

### Out of Scope
- New business features unrelated to Day 24.
- Expanding MCP tooling beyond what is needed to support refactors.
- Rewriting long-term legacy E2E suites beyond what is necessary to stabilise CI (non-critical suites may remain archived).

## Workstreams & Requirements
### 1. Cluster A – Mongo & Async Infrastructure
- **Requirements:** inject `settings.mongodb_url`/`settings.test_mongodb_url`, add shared Mongo fixtures, stabilise async behaviour.
- **Acceptance:** targeted test suites run without auth/loop errors; docs describe new fixtures.
- **References:** `mini_epics/legacy_cluster_a_plan.md`, `mini_epics/legacy_cluster_a_acceptance_matrix.md`.

### 2. Cluster B – Summarization & Digest Use Cases
- **Requirements:** implement `SummarizerService`, make use-cases async, fix repository signatures, update tests/docs.
- **Acceptance:** summarization integration/unit tests green; Challenge Days 3/5/6/15 reference new CLI/examples.
- **References:** `mini_epics/legacy_cluster_b_plan.md`, `mini_epics/legacy_cluster_b_acceptance_matrix.md`.

### 3. Cluster C – Butler Orchestrator & MCP-Aware Agent
- **Requirements:** define public API, optional legacy adapter, align MCP metrics and tests.
- **Acceptance:** Butler/MCP tests only touch public interfaces; metrics follow observability labels; docs for Days 14/18 updated.
- **References:** `mini_epics/legacy_cluster_c_plan.md`, `mini_epics/legacy_cluster_c_acceptance_matrix.md`.

### 4. Cluster D – LLM Clients & Map-Reduce Summarizer
- **Requirements:** design `LLMClientProtocol`, add settings, refactor summarizer with dataclass, refresh tests, document config.
- **Acceptance:** LLM/summarizer tests pass with protocol mocks; docs for Days 4/5/6/20/21 mention new interface.
- **References:** `mini_epics/legacy_cluster_d_plan.md`, `mini_epics/legacy_cluster_d_acceptance_matrix.md`.

### 5. Cluster E – Telegram Helpers & Workers
- **Requirements:** confirm lowercase channel policy, add Telegram adapter, refactor worker/tests, update docs.
- **Acceptance:** worker tests assert domain outcomes, CLI uses adapter, Challenge Days 1/11/17 highlight new behaviour.
- **References:** `mini_epics/legacy_cluster_e_plan.md`, `mini_epics/legacy_cluster_e_acceptance_matrix.md`.

## Dependencies
- `.env.infra` secrets for Mongo/LLM endpoints (already used by EP23).
- DevOps support for CI updates (`bootstrap_shared_infra.py --check`, new fixtures).
- Analyst/Architect confirmation on channel naming policy and E2E prioritisation.
- RAG/LLM teams for protocol alignment (Cluster D) and Challenge Day documentation.

## Risks & Mitigations
| Risk | Mitigation |
| --- | --- |
| Fixture rollout causes CI instability | Introduce feature flags / staged rollout; run smoke suites per PR. |
| Channel naming change requires data migration | Provide compat shim + migration script; communicate to doc owners. |
| Refactors span too many modules per PR | Enforce cluster-specific PRs; use acceptance matrix as scope guard. |
| Legacy E2E suites still flaky | Archive non-critical suites, add slimmed regression tests aligned with new architecture. |

## Deliverables
- Updated code for clusters A–E with passing tests.
- Documentation updates (`docs/challenge_days.md`, new guides for fixtures/adapters/LLM clients).
- Signed acceptance matrices per cluster.
- `work_log.md` entries reflecting each TL stage completion + evidence links.
- Updated `docs/specs/progress.md` row for EP24 once implementation phases complete.
# Epic 24 · Repository Hygiene & De-Legacy (Day 24)

## Context
- Epic 23 delivered observability, benchmark enablement, and Challenge Days 1–22 gap closure at the **process/usage** level.
- Full test runs during Epic 23 revealed legacy modules, tests, and docs that no longer align with the current Clean Architecture, async patterns, or shared infrastructure baseline.
- `docs/specs/epic_23/legacy_refactor_proposal.md` groups problematic areas into clusters A–E (Mongo/async infra, summarisation, Butler/MCP orchestration, LLM clients/summariser, Telegram/worker utilities).

Day 24 focuses on turning that proposal into concrete implementation work to bring the repository to a clean, current state.

## Goals
1. Reduce legacy technical debt by refactoring clusters A–E to comply with Clean Architecture, async, and observability standards.
2. Align tests and infrastructure with the Day 23 baseline (shared infra, metrics, CI bootstrap) and restore a reliable `make test` for the supported stack.
3. Clean up and re-structure documentation so that active specs, guides, and challenge materials reflect the current codebase and archive outdated content.

## Success Metrics
- ✅ `make test` passes on the standard Day 23 environment (shared infra via `make day-23-up`) with no unexpected Mongo/auth/async errors; any remaining legacy tests are explicitly archived or skipped with rationale.
- ✅ No direct `MongoClient(...)` calls with hard-coded URLs; all Mongo access flows through settings/DI and shared fixtures.
- ✅ Butler/MCP orchestration tests exercise only public APIs and pass with metrics aligned to `docs/operational/observability_labels.md`.
- ✅ Summarisation/digest use cases have a clear async/sync contract and pass all integration tests.
- ✅ LLM client and map-reduce summariser tests pass via a stable adapter interface; URL/path expectations are configuration-driven.
- ✅ Telegram utilities and workers use well-defined adapters and DI; channel normalisation policy is documented and enforced in tests.
- ✅ Documentation (`docs/challenge_days.md`, `USER_GUIDE_MULTI_AGENT_WORKFLOW.md`, `docs/specs/progress.md`) contains no unlabelled references to archived/removed code paths.

## Scope

### In Scope (Must)
- Implement refactors for legacy clusters defined in `legacy_refactor_proposal.md`:
  - **Cluster A:** Mongo repositories & async infrastructure.
  - **Cluster B:** Summarisation & digest use cases.
  - **Cluster C:** Butler orchestrator & MCP-aware agent.
  - **Cluster D:** LLM clients & map-reduce summariser.
  - **Cluster E:** Telegram helpers, channel normaliser, post-fetcher worker.
- Normalise test fixtures and CI behaviour with respect to shared infra:
  - Standard `MONGODB_URL`, `TEST_MONGODB_URL`, `LLM_URL`, `PROMETHEUS_URL` usage.
  - Clear marking of infra-dependent tests and legacy suites.
- Documentation hygiene for:
  - Challenge Days (ensure they reference active examples).
  - Multi-agent workflow/user guide.
  - Epic progress overview.

### In Scope (Should)
- Introduce mini-epic plans and acceptance matrices per cluster (A–E) to keep work bounded and traceable.
- Consolidate educational examples (Days 1–22) under `examples/` and link them from a single index doc.
- Improve archive structure by moving old specs and tests under `archive/` with explicit “historical” labels.

### Out of Scope
- New business features (new MCP tools, new services, new user-facing flows).
- New model families or major RAG architecture changes beyond what is required to stabilise existing tests and configs.

## Workstreams & Requirements

See `docs/specs/epic_24/backlog.md` for detailed tasks. High-level workstreams:

1. **Legacy Infrastructure & Mongo (Cluster A)**
   - Unify Mongo configuration and test fixtures.
   - Eliminate direct, unauthenticated Mongo usage in tests.
   - Resolve legacy async/event loop issues in infra tests.

2. **Summarisation & Digests (Cluster B)**
   - Fix use case bugs and define async/sync contract.
   - Introduce summariser service abstraction.
   - Align tests with new contracts.

3. **Butler/MCP Orchestration (Cluster C)**
   - Define public APIs for orchestrator/agent.
   - Introduce adapters for necessary legacy behaviours.
   - Align metrics and tests.

4. **LLM Client & Summariser (Cluster D)**
   - Stabilise LLM client interface and configuration.
   - Normalise map-reduce summariser signatures.
   - Remove brittle URL/string expectations from tests.

5. **Telegram & Workers (Cluster E)**
   - Agree and enforce channel normalisation policy.
   - Wrap Telegram helpers into adapters.
   - Make workers use DI and focus tests on domain behaviours.

6. **Documentation & Archive Hygiene**
   - Review and update challenge, user guide, and progress docs.
   - Move outdated docs/tests to archive with clear labelling.

## Acceptance Checklist
- [ ] All cluster A–E acceptance criteria from `legacy_refactor_proposal.md` are satisfied and marked as completed in their respective matrices.
- [ ] `make test` passes on the standard environment, with any skipped legacy tests documented and justified.
- [ ] No new violations of Clean Architecture boundaries introduced by refactors.
- [ ] Documentation cross-links (challenge days, user guide, epic specs, progress tracker) Are consistent and up-to-date.
- [ ] Deprecated modules and tests are either removed or moved to `archive/` with explanatory notes.

## Dependencies
- Existing Epic 23 shared infra and metrics:
  - `docs/specs/epic_23/shared_infra_restart.md`
  - `docs/operational/shared_infra.md`
  - `docs/operational/observability_labels.md`
- Legacy refactor analysis:
  - `docs/specs/epic_23/legacy_refactor_proposal.md`
- Gap closure and challenge day mapping:
  - `docs/specs/epic_23/challenge_days_alignment.md`
  - `docs/specs/epic_23/challenge_days_gaps.md`
  - `docs/specs/epic_23/challenge_days_gap_closure_plan.md`

## Risks & Mitigations
- **Risk:** Refactors introduce regressions in production flows.  
  **Mitigation:** Characterisation tests before refactor, small-scoped PRs per cluster, strict TDD and CI gates.

- **Risk:** Timebox overrun for clusters A–E.  
  **Mitigation:** Prioritise clusters impacting most tests (A, B, C first), explicitly track any deferred sub-tasks into follow-up backlog items.

- **Risk:** Documentation drift during refactor.  
  **Mitigation:** Require doc updates as part of DoD for each cluster; enforce link checks and doc linting.

- **Risk:** Clean Architecture boundaries accidentally violated.  
  **Mitigation:** Architecture review for refactor PRs; add simple static checks or grep-based CI guardrails for forbidden imports.

## Deliverables
- `docs/specs/epic_24/epic_24.md` (this spec).
- `docs/specs/epic_24/backlog.md` with detailed tasks per cluster and docs cleanup.
- Cluster-specific mini-epic plans and acceptance matrices (if created) under `docs/specs/epic_24/mini_epics/`.
- Updated tests, fixtures, and infrastructure scripts ensuring a clean, stable repo for future epics.


