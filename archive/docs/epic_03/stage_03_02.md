# Stage 03_02 · Instrumentation Rollout

## Goal
Implement the prioritised observability improvements: Prometheus/Grafana wiring,
structured logging enhancements, and alerting/SLO definitions.

## Checklist
- [ ] Update Prometheus scrape configs and exporters to include all targeted
  services (reviewer, MCP, CLI, workers).
- [ ] Build or refresh Grafana dashboards showcasing key metrics and SLOs.
- [ ] Standardise structured logging (fields, trace IDs, correlation IDs) across
  components; update logging utilities as required.
- [ ] Define and configure alerting rules based on agreed SLOs/thresholds.
- [ ] Document instrumentation changes and provide quick validation steps.

## Deliverables
- Prometheus configuration updates committed with documentation.
- Grafana dashboard JSON exported/backed up and linked from docs.
- Logging guidelines and updated utilities in `src/infrastructure/logging/`.
- Alerting runbook covering escalation paths and noise mitigation.

## Metrics & Evidence
- Prometheus `/-/ready` checks succeeding for new targets.
- Grafana screenshot or dashboard link demonstrating metrics visibility.
- Sample logs verifying structured context fields exist.
- Alert simulation results recorded during testing.

## Dependencies
- Stage 03_01 backlog and prioritisation.
- Access to infrastructure repositories/configuration files.
- Coordination with ops stakeholders for dashboard/alert review.

## Exit Criteria
- Instrumentation changes merged and validated in shared infra environment.
- Stakeholders approve dashboards and alerting strategy.
- Follow-up items (if any) recorded with owners and target dates.

## Open Questions
- Should we automate dashboard provisioning (e.g., via IaC) now or later?
- Are additional exporters required for external dependencies (Kafka, Redis)?

