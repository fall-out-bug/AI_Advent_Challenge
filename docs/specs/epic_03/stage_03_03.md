# Stage 03_03 · Runbooks & CI Operations Checks

## Goal
Consolidate operational knowledge, automate health validations, and prepare
teams to operate the refactored system confidently.

## Checklist
- [ ] Update `docs/specs/operations.md` and related guides with new dashboards,
  alerts, and troubleshooting steps.
- [ ] Implement CI jobs/scripts that validate shared infra connectivity and
  health (e.g., Prometheus scrape, Mongo auth, LLM readiness).
- [ ] Provide onboarding/training material for operators (slides, recordings, or
  written walkthroughs).
- [ ] Document escalation paths and maintenance windows.
- [ ] Record lessons learned and backlog items for continuous improvement.

## Deliverables
- Revised operations documentation with cross-links to dashboards and alerts.
- CI pipeline updates demonstrating automated ops checks.
- Training artefacts stored in `docs/` or external knowledge base.
- Stage summary including stakeholder approvals.

## Metrics & Evidence
- CI run history showing successful ops checks.
- Documentation change log.
- Attendance/feedback notes from onboarding session (if conducted).

## Dependencies
- Completion of Stage 03_02 instrumentation work.
- Cooperation from operations/support stakeholders.
- Shared infra availability for CI validations.

## Exit Criteria
- Operations documentation approved by ops stakeholder(s).
- CI ops checks integrated into mandatory pipelines with green status.
- Handover complete with clear escalation process and backlog captured.

## Open Questions
- Do we automate runbook verification (e.g., doc tests) in future sprints?
- Should we schedule periodic disaster recovery drills post-epic?

