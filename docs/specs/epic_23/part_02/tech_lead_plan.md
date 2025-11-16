# Epic 24 · Tech Lead Implementation Plan  
_Repository Hygiene & De-Legacy · Day 24_

## 1. Metadata & Inputs
| Field | Value |
| --- | --- |
| Epic | EP24 |
| Tech Lead | cursor_tech_lead_v1 |
| Date | 2025-11-16 |
| Source Requirements | `docs/specs/epic_24/epic_24.md`, `docs/specs/epic_24/backlog.md` |
| Legacy Analysis | `docs/specs/epic_23/legacy_refactor_proposal.md` |
| Operational Guardrails | `docs/operational/context_limits.md`, `docs/operational/handoff_contracts.md`, `docs/operational/shared_infra.md` |

## 2. Planning Assumptions & Constraints
- Day 23 shared infra baseline (`make day-23-up/down`, `bootstrap_shared_infra.py --check`) is the reference environment for EP24 work.
- Clean Architecture boundaries must be preserved; refactors must not introduce new domain→infrastructure couplings.
- Existing production behaviour (bot, MCP tools, summarisation flows) must remain functionally equivalent; behavioural changes require explicit MADRs.
- Legacy test suites may be archived or rewritten, but not silently deleted; every removal must be justified in docs.

## 3. Stage Overview
| Stage ID | Objective | Owner(s) | Duration (days) | Dependencies | Evidence |
| --- | --- | --- | --- | --- | --- |
| TL24-00 | Finalise scope, MADRs, acceptance matrix | Tech Lead | 1 | — | `acceptance_matrix.md`, updated questions log |
| TL24-01 | Cluster A – Mongo & async infra | Infra + QA | 3–4 | TL24-00 | Green repo/worker/channel integration tests |
| TL24-02 | Cluster B – Summarisation & digests | Application + QA | 3 | TL24-00 | Digest use case tests green, clear async/sync contract |
| TL24-03 | Cluster C – Butler/MCP orchestration | Domain + Presentation | 3–4 | TL24-00 | Butler/MCP tests use public APIs only, metrics aligned |
| TL24-04 | Cluster D – LLM client & summariser | Infra + Application | 2–3 | TL24-00 | LLM/summariser tests pass via stable adapter |
| TL24-05 | Cluster E – Telegram & workers | Infra + Domain | 3–4 | TL24-01 | Worker/domain tests assert business outcomes |
| TL24-06 | Docs & archive hygiene | Docs Guild | 2 | TL24-01…24-05 | Updated docs, archive layout, progress tracker |

Parallelisation:
- TL24-01 (Mongo/async infra) should start first to stabilise test environment.
- TL24-02 and TL24-04 can run in parallel once TL24-01 fixtures/config are in place.
- TL24-03 and TL24-05 depend on a stable infra baseline but can overlap within that constraint.
- TL24-06 runs after core refactors to reconcile docs and archive.

## 4. Stage Details

### TL24-00 · Input Consolidation & Acceptance Matrix (Day 0–1)
**Scope:** Confirm legacy cluster scope (A–E), agree on priorities, and create EP24-specific acceptance matrix.  
**Tasks:**
1. Review `legacy_refactor_proposal.md` with Architect + Analyst; adjust cluster boundaries if needed.
2. Create `docs/specs/epic_24/acceptance_matrix.md` mapping backlog items (A–E tasks + docs hygiene) to stages TL24-01…TL24-06.
3. Capture any cross-epic impacts (EP19–EP21) as explicit notes instead of implicit assumptions.
4. Log risks and mitigations specific to EP24 in the risk register.
**Definition of Done:**
- Acceptance matrix created and signed by Tech Lead + Analyst + Architect.
- Cluster priorities and sequencing confirmed.
**CI Gates:** `make lint`, markdown link checker.

### TL24-01 · Cluster A – Mongo & Async Infrastructure (Days 1–4)
**Scope:** Unify Mongo configuration, fixtures, and async behaviour to remove auth and event-loop errors.  
**Tasks:**
0. **Verify shared infra baseline** — Run `make day-23-up` and `scripts/ci/bootstrap_shared_infra.py --check` to confirm Day 23 infra is ready.
1. **Create characterization tests** — Capture current repository/worker behavior before refactoring (per cluster characterization test requirements).
2. Inventory all direct `MongoClient(...)` usages and replace with DI-based configuration (`Settings.mongodb_url`, `Settings.test_mongodb_url`).
3. Implement shared `mongodb_client` (session-scoped) and `mongodb_database` (function-scoped) fixtures providing per-test DB with automatic teardown.
4. **Migrate tests in order:** repositories → workers → channels → evaluation (per migration order).
5. Remove legacy event-loop fixtures; adopt `pytest-asyncio` with `asyncio_mode = auto` for async tests.
6. **Run full test suite** after each migration batch to catch regressions.
**Definition of Done:**
- Characterization tests created and passing (capture current behavior before refactoring).
- Shared infra baseline verified (`make day-23-up` passes).
- No `OperationFailure: requires authentication` errors under standard Day 23 infra.
- No `RuntimeError: Event loop is closed` in infra-related tests.
- All repository/worker tests use the shared fixtures and DI-based configuration.
- Full test suite passes after each migration batch (no regressions).
**CI Gates:** `pytest tests/integration/shared_infra`, `pytest tests/infrastructure/repositories`, `mypy src/infrastructure`, `make lint`.

### TL24-02 · Cluster B – Summarisation & Digest Use Cases (Days 4–7)
**Scope:** Fix digest use case bugs and align summarisation with a clear contract.  
**Tasks:**
0. **Create characterization tests** — Capture current digest generation flow and summarization behavior before refactoring.
1. Decide and document whether digest use cases are async or sync, and adjust interfaces accordingly (confirmed: async `async def execute(...) -> DigestResult`).
2. Fix known bugs (`NameError`, parameter mismatches) in digest use cases and related repos.
3. Introduce `SummarizerService` abstraction in domain/application and refactor use cases to depend on it.
4. Update integration tests to mock `SummarizerService` instead of low-level clients.
**Definition of Done:**
- Characterization tests created and passing (capture current digest/summarization behavior before refactoring).
- Digest generation tests pass with clear async/sync expectations (`async def execute(...) -> DigestResult`).
- No use of undefined variables; summarisation flow covered by happy/edge-case tests.
- Summarisation logic injectable and testable in isolation.
**CI Gates:** `pytest tests/integration/summarization`, `pytest tests/unit/application/test_summarizer_service.py`, `mypy src/application`.

### TL24-03 · Cluster C – Butler Orchestrator & MCP-Aware Agent (Days 5–9)
**Scope:** Stabilise orchestrator/agent APIs and align tests/metrics with the new architecture.  
**Tasks:**
1. Define and document public API surface for `MCPAwareAgent` and `ButlerOrchestrator`.
2. Refactor tests to rely on public APIs only; remove direct access to private attributes.
3. Introduce adapter/shim where legacy behaviours remain valuable.
4. Align MCP-related metrics with `observability_labels.md` and adjust tests accordingly.
**Definition of Done:**
- Characterization tests created and passing (capture current Butler/MCP/agent behavior before refactoring).
- Butler/MCP tests pass using only public interfaces (`handle_message()`, `handle_tool_result()`, `handle_update()`).
- Prometheus label sets for MCP metrics match docs and CI checks.
- No new domain↔infrastructure violations introduced by adapters.
**CI Gates:** `pytest tests/domain/agents`, `pytest tests/integration/butler`, `pytest tests/integration/presentation/mcp`, `mypy src/domain src/presentation`.

### TL24-04 · Cluster D – LLM Clients & Map-Reduce Summariser (Days 6–8)
**Scope:** Normalise LLM client API and map-reduce summariser signatures.  
**Tasks:**
0. **Create characterization tests** — Capture current LLM client request/response patterns, map-reduce chunking behavior, and error/timeout handling before refactoring.
1. Define `LLMClient` adapter interface and refactor existing clients to implement it.
2. Replace URL string expectations in tests with config-driven checks (base URL, path).
3. Introduce parameter dataclass for summariser chunk operations and update implementations/tests to use it.
**Definition of Done:**
- Characterization tests created and passing (capture current LLM client/summarizer behavior before refactoring).
- LLM client tests verify behaviour via the adapter interface, not raw URLs.
- Map-reduce summariser tests pass with consistent signatures and no direct calls to internal/private methods.
**CI Gates:** `pytest tests/unit/infrastructure/llm`, `pytest tests/unit/infrastructure/llm/summarizers`, `mypy src/infrastructure/llm`.

### TL24-05 · Cluster E – Telegram Helpers & Workers (Days 8–11)
**Scope:** Align Telegram helpers, channel normaliser, and workers with domain rules and DI.  
**Tasks:**
0. **Create characterization tests** — Capture current worker execution flow, channel normalization edge cases, and Telegram message processing before refactoring.
1. Decide and document canonical channel normalisation policy (confirmed: lowercase without @ prefix, e.g. `"onaboka"`).
2. Wrap `telegram_utils` in a dedicated adapter interface and inject it into workers via DI.
3. Refactor worker tests to assert on domain-level outputs (saved posts, time ranges) rather than direct Mongo calls.
**Definition of Done:**
- Characterization tests created and passing (capture current worker/Telegram/channel behavior before refactoring).
- Channel normaliser tests pass with agreed policy (lowercase without @ prefix).
- Worker tests pass and assert on domain outcomes; no direct Mongo client usage.
**CI Gates:** `pytest tests/unit/domain/test_channel_normalizer.py`, `pytest tests/workers`, `mypy src/workers src/infrastructure/clients`.

### TL24-06 · Documentation & Archive Hygiene (Days 10–12)
**Scope:** Bring docs and archive in sync with refactored codebase.  
**Tasks:**
1. Review and update `docs/challenge_days.md` and `docs/USER_GUIDE_MULTI_AGENT_WORKFLOW.md` to reflect refactored modules and examples.
2. Move outdated specs/tests into `archive/` with clear labels; add references from active docs where historically useful.
3. Update `docs/specs/progress.md` to include EP24 status and any EP19–EP21 changes driven by this refactor.
**Definition of Done:**
- No active docs reference removed/renamed modules without pointing to archive.
- Progress tracker accurately reflects post-EP24 state.
**CI Gates:** doc link checker, `make lint`, optional `pytest` doc tests (if present).

## 5. CI/CD Gate Matrix
| Gate | Command | Applies To | Threshold | Blocking |
| --- | --- | --- | --- | --- |
| Lint | `make lint` | All stages | 0 errors | Yes |
| Typecheck | `mypy src/ --strict` | TL24-01…05 | 100% modules typed | Yes |
| Unit Tests | `pytest tests/unit` | All relevant clusters | 100% pass | Yes |
| Integration Tests | `pytest tests/integration` | TL24-01…05 | 100% pass | Yes |
| Coverage | `pytest --cov=src --cov-report=xml` | TL24-02…05 | ≥80% global | Yes |
| Shared Infra Smoke | `python scripts/ci/bootstrap_shared_infra.py --check` | TL24-01, TL24-05 | Exit 0 | Yes |

## 6. Traceability Map
To be populated in `docs/specs/epic_24/acceptance_matrix.md` once clusters and tasks are finalised. It should map:
- Cluster tasks (A–E, docs hygiene) → stages TL24-01…TL24-06 → evidence (tests, logs, doc diffs).

## 7. Risk Register (Initial)
| ID | Description | Impact | Likelihood | Owner | Mitigation |
| --- | --- | --- | --- | --- | --- |
| R24-1 | Refactors break existing production flows | High | Medium | Tech Lead | Use characterisation tests, small PRs, and staged rollout. |
| R24-2 | Timebox overrun for clusters A–E | Medium | Medium | Tech Lead | Prioritise A/B/C, defer low-impact items with explicit backlog entries. |
| R24-3 | Docs drift during refactor | Medium | Medium | Docs Guild | Enforce doc updates as part of DoD and run link checks in CI. |
| R24-4 | New architecture boundary violations | High | Low | Architect | Perform architecture-focused reviews; add simple static checks/grep rules. |

## 8. Next Steps
- [ ] Architect + Analyst review this plan and confirm cluster priorities.
- [ ] Create `acceptance_matrix.md` for EP24 and wire it into `work_log.md`.
- [ ] Kick off TL24-01 (Cluster A) as soon as environment baseline is confirmed.


