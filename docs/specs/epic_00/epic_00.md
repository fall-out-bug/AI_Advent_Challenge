# Epic 00 · Repository Alignment

## Purpose
Establish a single source of truth for the current repository state and define
the recovery roadmap. Epic 00 consolidates requirements, documents architectural
decisions, and enumerates follow-up epics for execution.

## Objectives
- Inventory the codebase against historical day-by-day specifications.
- Decide which components remain first-class, which move to `archive/`, and
  which require redesign.
- Capture operating procedures for shared infrastructure and developer
  workflows.
- Publish a tracked backlog (Epic 01+) with clear acceptance criteria.

## Success Criteria
- `docs/specs/` contains Architecture, Operations, and System Specification
  documents reflecting the desired target state.
- All modules are tagged as **Keep / Archive / Rework** in Stage documents.
- `progress.md` lists approved epics with current status and owners.
- Day-specific specs are linked to the new documents for traceability.

## Dependencies
- Access to historical day specs (e.g. `docs/day11`, `docs/day12`, …).
- Current infra credentials (Mongo, Prometheus, LLM) to validate operational
  expectations.
- SME availability for MCP/Bot flows to confirm intent of legacy tests.

## Deliverables
1. `docs/specs/specs.md` – consolidated functional and non-functional
   requirements.
2. `docs/specs/architecture.md` – target architecture and dependency rules.
3. `docs/specs/operations.md` – infra topology, environment variables,
   observability, and runbooks.
4. Stage notes (`stage_00_01.md`, `stage_00_02.md`, …) documenting the audit
   trail and decisions.
5. `docs/specs/progress.md` – backlog view with epics, stages, and status.

## Exit Criteria
- All deliverables above reviewed and accepted.
- Follow-up epics agreed upon by engineering and product stakeholders.
- Outstanding risks captured in `progress.md` with mitigation plan.
