# Stage 21_03 · Testing, Security & Observability Hardening

## Goal
Reinstate confidence in automated quality and operations guardrails by mapping
coverage gaps, tightening security posture, and aligning monitoring artefacts
with the operations specification.

## Current Findings
- Critical refactored areas (domain/application handlers, presentation routes)
  lack focused unit and integration tests, making regression detection difficult.
- File-system interactions in API routes and workers bypass centralised storage
  policies and lack explicit virus/size scanning hooks beyond simple thresholds.
- Observability artefacts (Prometheus alerts, Grafana dashboards) require updates
  to reflect new services introduced during Stage 21_01/21_02 refactors.

### Evidence Snapshot
- `tests/presentation` and `tests/application` contain legacy-focused suites;
  there are no direct tests covering `review_routes.create_review` or the modular
  reviewer orchestration path post-migration.
- `src/presentation/api/review_routes.py` writes archives to `review_archives/`
  synchronously, without checksum verification or configurable storage roots.
- Operations guide (`docs/specs/operations.md`) mandates Prometheus metrics and
  Grafana dashboards; existing configs will need updates after refactoring interfaces.

## Planned Workstreams
1. **Test Coverage Expansion**
   - Introduce unit tests for new application services and adapters created in
     Stage 21_01/21_02.
   - Add integration tests that exercise API → use case → repository flows using
     the shared infrastructure bootstrap scripts.
2. **Security & Storage Controls**
   - Provide configurable storage abstraction with allowance lists, checksum
     verification, and optional malware scanning hooks.
   - Audit secrets management to ensure new services read credentials via
     environment variables defined in ops guide.
3. **Observability Alignment**
   - Update Prometheus scrape configs, Alertmanager rules, and Grafana dashboards
     to cover decomposed services (e.g. review storage service, log analysis pipeline).
   - Ensure structured logging contexts survive the refactor and feed Loki dashboards.

## Backlog Draft
| ID | Impact | Action | Owner | Dependencies |
|----|--------|--------|-------|--------------|
| TEST-21-01 | High | Create unit/integration test suites for API storage service and modular review orchestrator | QA team | After Stage 21_01/21_02 |
| SEC-21-02 | High | Implement pluggable storage adapter with checksum & optional AV scan, update settings docs | Infra team | Depends on CODE-21-02 |
| OBS-21-03 | Medium | Refresh Prometheus/Grafana configs to monitor refactored services; document runbooks | DevOps | Needs Stage 21_01 output |
| OPS-21-04 | Medium | Update `docs/specs/operations.md` with new maintenance and alerting procedures | Docs/DevOps | After OBS-21-03 |

## Exit Criteria
- Test coverage report highlights ≥80% for affected modules, integrated into CI.
- Storage and publishing paths comply with security requirements (size, checksum,
  configurable directories, no plaintext secrets).
- Monitoring dashboards and alerts reflect the new architecture, and operations
  documentation is updated accordingly.
- Tech lead confirms guardrails, product owner approves readiness after analytics/architecture reviewers acknowledge updates.


