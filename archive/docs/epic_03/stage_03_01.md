# Stage 03_01 · Observability Gap Analysis

## Goal
Produce an actionable inventory of observability gaps across metrics, logging,
tracing (if applicable), and operational automation.

## Checklist
- [ ] Review current Prometheus scrape targets, exported metrics, and dashboard
  coverage.
- [ ] Audit structured logging usage across application, MCP, CLI, and worker
  components.
- [ ] Catalogue existing alerts and SLOs; identify missing coverage.
- [ ] Assess CI pipelines for operational checks (health probes, connectivity
  tests).
- [ ] Prioritise gaps into a remediation backlog for Stage 03_02.

## Deliverables
- Observability gap report with prioritised backlog entries.
- Updated risk register entries for critical gaps.
- Recommendations for SLOs/SLIs per component.

## Metrics & Evidence
- Current list of Prometheus jobs and metrics exported.
- Logging samples showcasing presence/absence of structured context.
- CI job summary highlighting ops-related tests.

## Dependencies
- Access to Prometheus/Grafana instances and configuration files.
- Collaboration with EP01/EP02 leads to understand upcoming instrumentation.
- Shared infra availability for validation.

## Exit Criteria
- Gap report approved by EP03 tech lead and shared with coordination board.
- Remediation backlog scoped and scheduled for Stage 03_02.
- No outstanding unknowns blocking instrumentation rollout.

## Open Questions
- Do we introduce tracing (e.g., OpenTelemetry) within this epic or defer?
- Are there compliance or audit logging requirements not yet captured?

