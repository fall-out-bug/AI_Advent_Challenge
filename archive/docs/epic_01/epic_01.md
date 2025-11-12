# Epic 01 · Modular Reviewer Hardening

## Purpose
Stabilise the modular reviewer as the canonical review engine by enforcing code
quality, coverage, and documentation standards across the package and its
integrations.

## Objectives
- Audit the reviewer package, shared SDK touchpoints, and consuming application
  services for test coverage, lint hygiene, and feature-flag usage.
- Remediate identified gaps, ensuring CI pipelines remain green on the mandatory
  baseline while staged linting enforcement is introduced safely.
- Publish updated documentation, release notes, and rollout guidelines for
  downstream consumers.

## Dependencies
- Stage 00 decisions and inventories (EP00) approved.
- Shared infrastructure available for integration tests.
- Coordination with EP02 for MCP tool contracts that depend on reviewer service
  endpoints.

## Stage Breakdown
| Stage | Scope | Key Deliverables | Exit Criteria |
|-------|-------|------------------|---------------|
| Stage 01_01 | Coverage & gap audit | Stage report summarising coverage, lint, feature flags; prioritised remediation backlog | Findings documented, remediation backlog approved by tech lead |
| Stage 01_02 | Remediation & CI hardening | Commits addressing agreed backlog, updated CI configs, staged lint enforcement plan | Baseline tests passing, linting gate defined, open issues tracked |
| Stage 01_03 | Documentation & release readiness | Updated docs, changelog, rollout checklist; stakeholder review sign-offs | Release artefacts published, hand-off checklist completed |

## Success Criteria
- `packages/multipass-reviewer` and shared SDK modules reach agreed coverage and
  lint thresholds without regressions.
- Feature flag defaults (`USE_MODULAR_REVIEWER`, related toggles) documented and
  validated.
- Consumers (application, MCP) receive an updated integration guide aligned with
  the hardened reviewer.

## Stakeholders
- Tech Lead Agent: to be assigned (owner of planning, reviews, sign-offs).
- Developer Agents: assigned per stage for remediation tasks.
- Architecture/QA: consulted for acceptance of coverage and lint thresholds.

## Risk & Mitigation Snapshot
- **Risk:** Lint enforcement blocks parallel epics.  
  **Mitigation:** Stage staged enforcement with allowlists during Stage 01_02.
- **Risk:** Shared SDK changes ripple into EP02.  
  **Mitigation:** Track interface updates in shared change log; communicate in
  weekly coordination notes.

## References
- `docs/specs/epic_00/stage_00_01.md` – Component inventory.
- `docs/specs/specs.md` – Functional/non-functional requirements.
- `docs/specs/operations.md` – Shared infra setup for integration testing.

