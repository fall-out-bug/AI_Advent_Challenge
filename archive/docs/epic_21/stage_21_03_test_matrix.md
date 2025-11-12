# Stage 21_03 · Test & Guardrail Matrix

## Purpose
Establish targeted test coverage and operational guardrails for refactored components.

## Performance Baselines
- Dialog interaction latency: **p95 < 100 ms**, **p99 < 200 ms**.
- Review submission pipeline: **p95 < 30 s**, **p99 < 45 s**.
- Worker memory footprint: **< 500 MB** steady-state.
- Concurrent sessions supported: **≥100** simultaneous dialog contexts.
- Storage writes: **p95 latency < 2 s**, checksum failure rate **0** in steady-state.

## Test Coverage Matrix
| Component | Current Coverage | Required Tests | Notes |
|-----------|-----------------|----------------|-------|
| Review archive storage service | None (new) | Unit tests for size/checksum validation, error handling | Mock filesystem/S3 backends |
| Modular review orchestrator | Integration via `ReviewSubmissionUseCase`, limited unit coverage | Unit tests for collaborator interactions; integration test using shared infra bootstrap | Coordinate with Stage 21_01 decompositions |
| Presentation API storage workflow | Integration tests exist (`tests/integration/api/test_multipart_review.py`) but rely on in-function IO | Update tests to target new storage adapter; add failure-path scenarios (oversize, checksum mismatch) | Requires new DI pattern |
| Log analysis pipeline | Covered indirectly | Add regression tests for `_append_log_analysis` replacement components | Use synthetic logs fixtures |
| Alerting/metrics exporters | Manual verification | Add smoke tests for Prometheus metrics endpoints; ensure configs validated in CI | Could leverage `scripts/ci/bootstrap_shared_infra.py` |

## Security & Storage Controls
- Implement checksum verification before persisting archives.
- Provide pluggable antivirus hook (optional, default no-op) with documented interface.
- Ensure directories configurable via environment variables referenced in `operations.md` §2.

## Observability Checklist
- Update Prometheus scrape configs and alert thresholds for new services.
- Sync Grafana dashboards with revised metrics (`review_pipeline_duration`, storage errors).
- Validate structured logging includes `trace_id`, `task_id`, `student_id` after refactor.

## CI Integration
1. Extend CI to run new unit/integration suites with `pytest -m "storage or logs"` markers.
2. Add coverage reporting to enforce ≥80% (Stage 21_03 exit criterion).
3. Run `scripts/ci/bootstrap_shared_infra.py` within pipeline to exercise integration tests.

## Deliverables
- Updated `tests/` modules with new suites and fixtures.
- Refresh `docs/specs/operations.md` and relevant runbooks post-monitoring updates.
- Incident response appendix reflecting new alert sources and remediation steps.
- Performance validation report comparing baseline vs post-refactor metrics.


