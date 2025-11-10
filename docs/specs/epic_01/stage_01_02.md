# Stage 01_02 · Remediation & CI Hardening

## Goal
Execute the remediation backlog, enforce agreed quality gates, and stabilise CI
pipelines for the modular reviewer and shared dependencies.

## Checklist
- [ ] Implement fixes covering the prioritised backlog from Stage 01_01.
- [ ] Update or create tests to restore coverage to the agreed threshold.
- [ ] Introduce staged lint enforcement (e.g., selective directories, fail-on-new
  violations policy).
- [ ] Adjust CI configuration to run the mandatory baseline test suites and
  collect artefacts (coverage, lint reports).
- [ ] Document any exceptions or deferred items with rationale and follow-up
  owners.

## Deliverables
- Code changes merged (or ready for review) addressing backlog items.
- Updated CI/CD configurations reflecting new gates.
- Coverage and lint reports attached to stage summary.
- Exception log for deferred tasks with new target dates/stages.

## Metrics & Evidence
- Coverage percentage meeting or exceeding target (≥ agreed baseline).
- CI history showing consecutive green runs with new gates enabled.
- Lint violation trend demonstrating reduction or zero new violations.

## Dependencies
- Developer agents assigned to remediation tasks.
- CI infrastructure access to adjust pipelines.
- Coordination with EP02/EP03 for shared components touched by fixes.

## Exit Criteria
- Mandatory baseline suites pass consistently with new gates enabled.
- Tech lead approves remediation outcomes and signs off on exception list.
- Updated documentation (inline or README snippets) for any new workflows.

## Open Questions
- Which lint rules become mandatory now versus future stages?
- Do any fixes require coordinated releases with downstream consumers?

