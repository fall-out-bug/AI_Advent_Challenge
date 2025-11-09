# EP01 Stage 01_01 · Shared SDK Governance & Coverage Plan

## 1. Coverage & Typing Targets

- Maintain ≥90% coverage (CI threshold) with sub-targets:
  - Agents module (code/reviewer): ≥92%
  - Orchestration modules: ≥90%
  - Clients module: ≥92%
- Strict mypy on clients + agents; staged rollout to orchestration by Stage 02_01.

## 2. Ownership Model (Joint EP01 & EP02)

### RACI Matrix

| Task | EP01 Tech Lead | EP02 Tech Lead | Shared SDK Maintainers | QA/Release |
|------|----------------|----------------|------------------------|------------|
| Define SDK roadmap & quality gates | **R** | **R** | C | I |
| Prioritise remediation backlog | **A** | **A** | C | I |
| Implement coverage/lint fixes | C | C | **R** | I |
| Approve PRs touching reviewer-facing SDK surfaces | **A** | **A** | R | C |
| Monitor coverage & lint metrics | **R** | **R** | C | **A** |
| Coordinate cross-epic impacts | **A** | **A** | C | I |

Legend: **R** = Responsible, **A** = Accountable, C = Consulted, I = Informed.

## 3. Workflow

- Shared Kanban lane (board: `EP01-EP02 Shared SDK`) with weekly sync.
- Each Stage 01_02/02_01 sprint must allocate capacity for SDK lint/coverage tasks.
- Integrate SDK lint allowlist into Stage 01_02 CI to avoid regressions.
- Track coverage deltas via `make test-coverage` reports (export HTML diff).

## 4. Immediate Actions

1. Nominate SDK maintainers (two engineers representing EP01/EP02).
2. Populate Kanban with R1 items: mypy fixes (48 errors), flake8 cleanup, coverage gaps.
3. Add SDK governance summary to Stage 01_02 plan & communication deck.

