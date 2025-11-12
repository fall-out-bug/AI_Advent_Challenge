# Epic 03 · Observability & Operations

## Purpose
Upgrade observability, logging, and operational hygiene to support the refactored
reviewer, MCP, and bot ecosystem while keeping shared infrastructure as the
single source of truth.

## Objectives
- Catalogue current monitoring/logging gaps and establish target metrics for the
  modular reviewer stack.
- Implement Prometheus/Grafana wiring, structured logging patterns, and CI
  operations checks that validate environment health.
- Expand and maintain operations documentation, runbooks, and onboarding flows.

## Dependencies
- EP01 instrumentation hooks (e.g., reviewer metrics/logging output).
- EP02 CLI telemetry requirements where applicable.
- Access to shared infra (Prometheus, Grafana, Mongo, LLM) for validation.

## Stage Breakdown
| Stage | Scope | Key Deliverables | Exit Criteria |
|-------|-------|------------------|---------------|
| Stage 03_01 | Observability gap analysis | Metrics/logging inventory, prioritised backlog | Gap report approved, backlog scheduled |
| Stage 03_02 | Instrumentation rollout | Prometheus/Grafana configs, structured logging updates, alerts | Metrics visualised, alerts validated, logging guidelines published |
| Stage 03_03 | Runbooks & CI ops checks | Updated operations guide, automated health checks, training notes | Docs merged, CI ops jobs green, stakeholders sign off |

## Success Criteria
- Prometheus scrapes all critical services with documented dashboards.
- Structured logging guidelines adopted across application, MCP, and CLI layers.
- Operations guide includes up-to-date runbooks, escalation paths, and health
  check automation.

## Stakeholders
- Tech Lead Agent: to be assigned (planning, reviews).
- Developer/Infra Agents: implement instrumentation and automation tasks.
- Ops/Support: primary reviewers of runbooks and dashboard usability.

## Risk & Mitigation Snapshot
- **Risk:** Alert fatigue from noisy metrics.  
  **Mitigation:** Stage 03_02 to include SLO definition and alert tuning.
- **Risk:** CI environment diverges from shared infra config.  
  **Mitigation:** Introduce configuration validation scripts and document
  differences explicitly.

## References
- `docs/specs/operations.md` – current operations baseline.
- `docs/specs/epic_00/stage_00_01.md` – notes on existing logging/metrics gaps.
- `scripts/quality/` – existing automation to extend or replace.

