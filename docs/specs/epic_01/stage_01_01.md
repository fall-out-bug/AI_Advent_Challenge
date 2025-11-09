# Stage 01_01 · Coverage & Gap Audit

## Goal
Establish a definitive view of modular reviewer quality gaps across code,
coverage, linting, and feature flag usage to inform remediation work.

## Checklist
- [ ] Capture current coverage reports for `packages/multipass-reviewer` and
  shared SDK modules used by the reviewer.
- [ ] Catalogue lint violations and classify them by severity and effort.
- [ ] Inventory feature flags/toggles affecting reviewer behaviour; verify
  defaults and documentation.
- [ ] Assess CI pipeline outputs (tests, lint, type checking) for flaky or
  skipped suites relevant to reviewer flows.
- [ ] Produce remediation backlog with prioritised tickets grouped by theme.

## Deliverables
- Stage report summarising findings, metrics, and recommended priorities.
- Backlog entries (tickets or tasks) mapped to EP01 Stage 01_02 scope.
- Updated risk register entries for any newly discovered blockers.

## Metrics & Evidence
- Coverage percentage per module/package.
- Count of lint violations by category (error/warning/info).
- List of feature flags with default values and consumers.
- CI history snapshot (last three runs) highlighting failures/skips.

## Dependencies
- Access to CI pipeline artefacts and coverage reports.
- Shared infrastructure (Mongo, LLM) when reproducing integration tests.
- Coordination with EP02 lead for any MCP-dependent findings.

## Exit Criteria
- Findings document approved by EP01 tech lead and shared with cross-epic
  coordination channel.
- Remediation backlog agreed and scheduled for Stage 01_02.
- No unanswered questions blocking remediation.

## Open Questions
- Do we re-enable any currently skipped tests within Stage 01_02 or defer to
  later epics?
- Are there external consumers requiring notification about upcoming changes?

