# Stage 02_02 · CLI Backoffice Delivery

## Goal
Implement and document the CLI backoffice commands that provide deterministic
operations for channel management, digest generation, and optional NLP checks.

## Checklist
- [ ] Finalise command design (flags, output formats, error handling) aligned
  with Stage 02_01 tool contracts.
- [ ] Implement CLI commands in `src/presentation/cli/backoffice/`.
- [ ] Write unit/integration tests invoking application services and shared infra
  stubs/mocks where needed.
- [ ] Update operator documentation (`API_BOT_BACKOFFICE.md`) with usage
  examples, prerequisites, and troubleshooting tips.
- [ ] Provide release notes and onboarding instructions for operators.

## Deliverables
- Working CLI command set with tests and CI coverage.
- Documentation updates merged and cross-referenced from specs.
- Demo or screencast notes illustrating typical workflows (optional but
  recommended).

## Metrics & Evidence
- Test suite results for CLI commands (unit + integration).
- Manual verification logs capturing representative command outputs.
- Documentation diff summary.

## Dependencies
- Stage 02_01 tool contracts and registry updates.
- Shared infra credentials for integration testing (Mongo, LLM).
- Coordination with EP03 for logging/metrics hooks if CLI emits telemetry.

## Exit Criteria
- CLI commands pass automated tests and manual smoke checks.
- Operator documentation approved by tech lead and operations stakeholder.
- Backlog items for any deferred enhancements created with owners/dates.

## Open Questions
- Should CLI support both JSON and table output in this stage or a follow-up?
- Do we integrate CLI telemetry into observability stack now or defer to EP03?

