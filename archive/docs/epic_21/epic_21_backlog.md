# Epic 21 · Backlog

## Legend
- **Status**: `todo`, `in-progress`, `blocked`, `done`
- **Stage**: 21_01 (Architecture), 21_02 (Quality), 21_03 (Guardrails)

## Work Items
| ID | Stage | Status | Title | Description | Owner | Links |
|----|-------|--------|-------|-------------|-------|-------|
| ARCH-21-01 | 21_01 | todo | Extract dialog context repository | Replace Mongo binding in `ButlerOrchestrator` with domain interface | Domain/App | `stage_21_01_dependency_audit.md` |
| ARCH-21-02 | 21_01 | todo | Introduce homework review service | Move HW checker access out of domain handler | Domain/App | `stage_21_01_dependency_audit.md` |
| ARCH-21-03 | 21_01 | todo | Abstract review archive storage | Inject storage adapter in API/use case layers | Application | `stage_21_01_dependency_audit.md` |
| ARCH-21-04 | 21_01 | todo | Decompose modular review orchestration | Split `ReviewSubmissionUseCase` responsibilities | Application | `epic_21.md` |
| CODE-21-01 | 21_02 | todo | Refactor oversized helpers | Introduce collaborators for log analysis, publishing, persistence | Application | `stage_21_02.md` |
| CODE-21-02 | 21_02 | todo | Rework review route pipeline | Separate validation, storage, and enqueue logic | Presentation | `stage_21_02.md` |
| CODE-21-03 | 21_02 | todo | Enforce docstring template | Apply standardized docstrings across modules | Docs Lead | `stage_21_02_docstring_plan.md` |
| CODE-21-04 | 21_02 | todo | Update lint toolchain | Configure pre-commit, `make lint`, CI parity | DevEx | `stage_21_02_tooling_rollout.md` |
| SEC-21-02 | 21_03 | todo | Harden archive storage | Add checksum, optional AV scan, env-configured paths | Infra | `stage_21_03.md` |
| TEST-21-01 | 21_03 | todo | Expand storage/orchestrator tests | Create targeted unit/integration suites | QA | `stage_21_03_test_matrix.md` |
| OBS-21-03 | 21_03 | todo | Refresh monitoring artefacts | Update Prometheus/Grafana for new services | DevOps | `stage_21_03_test_matrix.md` |
| OPS-21-04 | 21_03 | todo | Update operations docs | Reflect new guardrails in `operations.md` | Docs/DevOps | `stage_21_03_test_matrix.md` |

### New Preparatory Work
| ID | Stage | Status | Title | Description | Owner | Links |
|----|-------|--------|-------|-------------|-------|-------|
| PREP-21-01 | 21_00 | todo | Implementation roadmap | Author executable roadmap with code examples and migration steps | Tech Lead | `implementation_roadmap.md` |
| PREP-21-02 | 21_00 | todo | TDD characterization suites | Add baseline characterization tests before refactors | QA/Tech Lead | `stage_21_01.md` |
| PREP-21-03 | 21_00 | todo | Performance baselines | Capture latency/throughput/memory metrics pre-refactor | DevOps | `stage_21_03_test_matrix.md` |
| PREP-21-04 | 21_00 | todo | Risk register refresh | Enumerate data, performance, concurrency, external dependency risks | Tech Lead | `risk_register.md` |
| PREP-21-05 | 21_00 | completed | Team comms & training | Docstring FAQ, pre-commit plan, pytest markers delivered; schedule condensed into single-day intensive session | Tech Lead | `implementation_roadmap.md` |

## Milestones
- **M1: Architecture Baseline** — ARCH-21-01..04 completed; new interfaces merged; diagrams updated.
- **M2: Quality Gates Online** — CODE-21-01..04 delivered; lint/test pipelines green.
- **M3: Guardrails & Ops** — SEC-21-02, TEST-21-01, OBS-21-03, OPS-21-04 closed; ops sign-off obtained.

## Coordination
- Weekly sync with EP01/EP03 owners to avoid conflicting changes.
- Bi-weekly doc review to ensure specs stay synchronized with implementation progress.


