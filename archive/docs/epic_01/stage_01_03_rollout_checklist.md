# Stage 01_03 · Rollout Checklist

## 1. Operator Runbook

| Step | Command / Action | Notes |
|------|------------------|-------|
| 1 | `poetry install --with dev` | Ensure local venv has `multipass-reviewer==0.3.0`. |
| 2 | `make lint-allowlist` | Must pass without modifications. |
| 3 | `make review-test` | Reviewer smoke tests must pass. |
| 4 | `poetry run pytest packages/multipass-reviewer/tests` | Confirm package suite. |
| 5 | `poetry run pytest shared/tests/test_code_reviewer_agent.py` | Validate shared SDK integration. |
| 6 | `docker compose -f docker-compose.butler.yml up -d reviewer` | Deploy updated reviewer container. |
| 7 | `docker compose -f docker-compose.butler.yml ps reviewer` | Check container healthy. |
| 8 | Tail `docker compose logs reviewer -f` | Ensure no runtime errors. |
| 9 | Post-deploy: trigger sample review (`scripts/dev/run_modular_review.py`) | Validate end-to-end. |
| 10 | Rollback (if needed): `git checkout <prev-tag>` + redeploy | Use previous release tag (e.g., `v0.2.0`). |

### Rollback Trigger Criteria
- `make lint-allowlist` or `make review-test` fails post-deploy.
- Reviewer container emits fatal errors for multiple tasks.
- Prometheus `review_pass_failures_total` spikes above baseline.

## 2. Developer Migration Guide

1. Update dependency:
   ```toml
   multipass-reviewer = { git = "https://example.com/multipass-reviewer.git", tag = "v0.3.0" }
   ```
2. Remove references to `use_modular_reviewer` flag:
   - Delete env vars `USE_MODULAR_REVIEWER`.
   - Remove conditional checks in downstream services.
3. Re-run mypy/flake8 with stricter configuration provided by 0.3.0.
4. Replace ad-hoc reviewer stubs with adapters from `ModularReviewService`.
5. Update documentation references to the new version and mandatory reviewer path.

## 3. Pre-Flight Validation

- [ ] `make lint-allowlist`
- [ ] `make review-test`
- [ ] `poetry run pytest packages/multipass-reviewer/tests`
- [ ] `poetry run pytest shared/tests/test_code_reviewer_agent.py`
- [ ] Docker image rebuilt with `0.3.0` label
- [ ] Documentation diff reviewed (EN + RU guides, MCP API note)
- [ ] Release notes/changelog approved by tech lead

## 4. Stakeholder Sign-Off

| Stakeholder | Responsibility | Status | Notes |
|-------------|----------------|--------|-------|
| Architecture Lead | Confirms removal of legacy flag & DI impacts | ☐ | |
| QA Lead | Approves test evidence (`make review-test`, targeted pytest) | ☐ | |
| Operations Lead | Signs off runbook & monitoring steps | ☐ | |
| Product/Programme | Accepts release notes & communication plan | ☐ | |

## 5. Monitoring & Observability

Track the following Prometheus metrics after rollout:

- `review_pass_runtime_seconds` — ensure median stays within historical range.
- `review_pass_failures_total` — should not increase vs baseline.
- `llm_request_latency_seconds` — watch for regressions due to strict retries.
- `modular_reviewer_sessions_total` — verify steady throughput without dips.

Alerts (existing):
- `MCPReviewerJobFailuresHigh` (Alertmanager) — ensure clear post-deploy.
- `ModularReviewerLatencyHigh` — investigate if over thresholds.

## 6. Communication

- Notify stakeholders via Stage 01_03 comms plan (email + Slack + board update).
- Mention removal of `use_modular_reviewer` flag and mandatory adoption.
- Provide link to migration guide and release notes (`CHANGELOG.md`).

