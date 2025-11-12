# Stage 06_03 · Automation & Quality Closure

## Goal
Automate shared infrastructure workflows, normalise CI/test baselines, and
retire provisional skips so the repository ships green by default.

## Checklist
- [ ] Implement shared infra bring-up automation for CI (e.g., scripts wrapping
  Mongo/Prometheus/LLM with credentials from `.env.infra`).
- [ ] Recalibrate MCP performance benchmarks and convert temporary `xfail` tests
  into passing checks or documented skips with metrics.
- [ ] Expand backoffice CLI integration tests to cover digest/homework flows.
- [ ] Update CI pipelines (`.github/workflows/…`) to include automation scripts
  and enforce revised gates.
- [ ] Document new automation in operations guides and maintainer playbook.

## Deliverables
- Shared infra automation scripts/config (e.g., `scripts/ci/start_shared_infra.py`)
  with usage documentation.
- Updated test suites with calibrated thresholds and reduced skips.
- CI workflow changes ensuring observability and shared infra checks run
  automatically.

## Metrics & Evidence
- CI history showing green builds with automation enabled.
- Test reports demonstrating passing benchmarks and CLI coverage.
- Documentation diffs covering operations guides and README updates.

## Dependencies
- Stage 06_02 repository layout (paths updated).
- Ops stakeholders for infra automation review.
- Access to shared infra credentials for CI environment.

## Exit Criteria
- CI passes without manual intervention or ad-hoc skips.
- Automation scripts documented and adopted in daily workflows.
- Remaining known issues triaged with owners/timelines or resolved.

## Open Questions
- Do we need feature flags to toggle automation in non-CI environments?
- Should we publish container images for shared infra to speed up automation?
