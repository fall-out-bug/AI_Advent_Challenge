# Stage 21_01 · Architecture & Layering Remediation

## Goal
Realign the codebase with Clean Architecture principles by eliminating cross-layer
dependencies, introducing explicit interfaces, and preparing migration steps that
support style, testing, and operations compliance in later stages.

## Current Findings
- Domain services depend directly on infrastructure clients (e.g. MongoDB, HW checker),
  violating the inward dependency rule and blocking isolated unit tests.
- Presentation routes and workers contain long, multi-responsibility functions
  that mix validation, persistence, file IO, and orchestration logic.
- Domain modules partially follow docstring requirements but lack the mandated
  `Purpose/Args/Returns/Example` sections, complicating future automation.

### Evidence Snapshot
- `src/domain/agents/butler_orchestrator.py` instantiates Mongo collections inside
  the domain layer, binding business logic to infrastructure persistence.
- `src/domain/agents/handlers/homework_handler.py` imports `src.infrastructure.hw_checker.client`
  and performs temp-file IO, mixing presentation formatting with integration code.
- `src/presentation/api/review_routes.py:create_review` orchestrates archive validation,
  disk writes, and use-case invocation in a single 120+ LOC coroutine.
- `src/application/use_cases/review_submission_use_case.py` holds several large methods
  (>40 LOC) covering rate limiting, log analysis, persistence, and publishing.

## Planned Workstreams
0. **Test-First Baseline**
   - Add characterization suites for current orchestrator/handler flows prior to refactor.
   - Mark tests with `epic21`, `stage_21_01`, and component markers for targeted runs.
   - Capture latency snapshots (dialog latency, review submission) before changes.
1. **Domain Layer Isolation**
   - Extract persistence, tool, and external-service dependencies behind
     protocol interfaces hosted in `src/domain/interfaces/`.
   - Introduce application-layer orchestrators that compose domain logic with
     infrastructure adapters, ensuring dependency injection is container-driven.
2. **Handler & Orchestrator Refactor**
   - Break down agent handlers into intent processing, data formatting, and
     external-call adapters to respect single-responsibility guidance.
   - Move Telegram/Markdown formatting helpers to presentation utilities.
3. **Route & Worker Decomposition**
   - Relocate file-system and validation logic from presentation routes into
     dedicated application services with configurable storage backends.
   - Apply consistent error handling and structured logging decorators.
4. **Documentation Alignment**
   - Author migration notes covering new interfaces, DI container updates, and
     testing strategies; ensure `.cursor` rules remain accurate post-refactor.

## Backlog Draft
| ID | Impact | Action | Owner | Dependencies |
|----|--------|--------|-------|--------------|
| ARCH-21-01 | High | Define `DialogContextRepository` protocol and move Mongo usage from `ButlerOrchestrator` into infrastructure adapter | Domain/App team | DI container update |
| ARCH-21-02 | High | Introduce `HomeworkReviewService` in application layer; refactor `HomeworkHandler` to call service via interface | Domain/App team | ARCH-21-01 |
| ARCH-21-03 | Medium | Split `review_routes.create_review` into validator, storage service, and enqueue command objects | Presentation team | Storage path config |
| ARCH-21-04 | Medium | Decompose `ReviewSubmissionUseCase` into smaller collaborators (rate limiter, log pipeline, publisher) | Application team | ARCH-21-02 |

## Exit Criteria
- Characterization suites in `tests/epic21/` cover current flows and pass before refactors.
- No domain module imports `src.infrastructure.*` or third-party clients.
- Presentation layer delegates persistence/IO to injected services.
- Updated dependency diagram documented in `docs/specs/epic_21/stage_21_01.md`.
- Refactor backlog reviewed and accepted by tech lead (AI assistant), product owner, and architecture/analytics reviewers.
