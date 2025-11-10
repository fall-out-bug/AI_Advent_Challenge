# Stage 01_01 · Coverage & Gap Audit Report

## Executive Summary

- The reviewer ecosystem (main application + shared SDK) is far from CI-ready: `make lint`, `make test-coverage`, and `make review-test` all fail deterministically. Coverage for the core application sits at **21.07%**, breaching the 80% policy.
- The shared SDK—consumed by the reviewer—fails the 90% coverage gate (currently **89%**) and carries 48 strict mypy errors plus extensive flake8 drift, undermining reviewer integration safety.
- Feature flag hygiene is uneven: critical toggles such as `use_modular_reviewer` are defined but unused, while others lack documentation or validation tests.
- A prioritised remediation backlog (`docs/specs/epic_01/stage_01_01_backlog.md`) enumerates 10 tickets grouped by theme with P0/P1 focus areas for Stage 01_02.

## 1. Coverage Analysis

### Multipass Reviewer Package (`packages/multipass-reviewer`)

- Coverage run succeeded with **94.64%** overall (target ≥90%).
- Gaps concentrate in infrastructure checkers:
  - `infrastructure/checkers/python_style.py` – 88%
  - `infrastructure/checkers/spark_airflow.py` – 89%
  - `infrastructure/checkers/linter.py` – 94% (small delta)
- Application layer (`application/config.py`, `application/orchestrator.py`) sits at 92% but missing branches relate to runtime error paths. These are candidates for focused unit tests.

### Shared SDK (`shared/`)

- Total coverage **89.21%** (below 90% threshold). Modules with material gaps:
  - `agents/code_generator.py` – 82%
  - `agents/code_reviewer.py` – 79%
  - `config/__init__.py` – 71%
  - `orchestration/parallel.py` – 76%
  - `validation/models.py` – 91% (fine) but other validator helpers <70%.
- Lack of reviewer-specific tests in SDK raises regression risk whenever reviewer consumes orchestration helpers.

### Main Application (`src/`)

- Total coverage **21.07%**. Reviewer-critical modules with poor or zero coverage:
  - `application/services/modular_review_service.py` – 33%
  - `application/use_cases/review_submission_use_case.py` – 22.8%
  - `domain/agents/*` (numerous files ≤30%)
  - `infrastructure/clients/llm_client.py` – 8.66%
  - `presentation/mcp/tools/channels/channel_digest.py` – 5.03%
- Several reviewer integrations (MCP, Telegram handlers) have **0%** coverage, leaving production flows untested.
- Evidence: `ci_run1_test.log` (and repeated runs) shows coverage failures due to test collection errors plus unmet threshold.

## 2. Lint Catalogue

### Multipass Reviewer

- **mypy** (strict): 6 errors across `domain/passes/base_pass.py` and `application/orchestrator.py` (incorrect return typing, `Mapping` vs `dict`).
- **flake8**: 5 E501 violations within `infrastructure/checkers/*`.
- **black/isort**: One file (`domain/interfaces/review_logger.py`) needs reformatting; isort clean.

### Shared SDK

- **mypy**: 48 errors across 9 files (config, agents, orchestration). Themes: missing type annotations, `Any` leakage, incompatible call signatures.
- **flake8**: Hundreds of spacing/line-length issues (predominantly W293, E501) plus unused imports and unused variables in agents/orchestration modules.
- **black/isort**: 19 files require formatting; 18 fail isort.

### Main Application

- **flake8 `make lint`**: Tens of thousands of E501 long lines, numerous F821, F841, E402. Run logs (`ci_run1_lint.log` .. `ci_run3_lint.log`) confirm deterministic failure.
- **mypy**: 1,202 errors in 196 files (lack of typing across logging, infrastructure, presentation modules).
- **bandit**: 1,069 B101 warnings (use of `assert` in tests) plus 17 medium, 2 high findings. Logs show no allowlist in place.

## 3. Feature Flag Inventory

| Flag | Default | Consumers | Documentation | Notes |
|------|---------|-----------|---------------|-------|
| `use_modular_reviewer` | `True` | **None found** | Mentioned in high-level docs only | Flag defined in `Settings` but never read; risk that toggling has no effect. |
| `enable_log_analysis` | `True` | `review_submission_use_case`, `ReviewConfig` builder | Not documented | Controls Pass 4 behaviour; lacking doc & dedicated tests. |
| `parser_strict_mode` | `False` | `domain/agents/mcp_aware_agent` | No | Toggles strict JSON parsing; needs documentation & test coverage. |
| `use_new_summarization` | `False` | `presentation/mcp/tools/channels/channel_digest.py`, `reminder_tools.py` | Only referenced in `docs/specs/architecture.md` | Drives Phase 6 summarizer; requires rollout guide. |
| `enable_quality_evaluation` | `True` | `generate_channel_digest_by_name.py` | No | Should be covered by acceptance tests. |
| `enable_auto_finetuning` | `True` | `summarization_evaluation_repository`, `finetuning_worker.py` | No | Critical for ensuring worker gating. |
| `enable_async_long_summarization` | `True` | `workers/summary_worker.py` | No | Async flow toggled but untested; add validation. |
| `bot_api_fallback_enabled` | `True` | `infrastructure/clients/telegram_utils.py` | No | Document fallback preconditions. |
| `llm_fallback_enabled` | `False` | `infrastructure/clients/telegram_utils.py` | No | Ensure safe default remains. |
| `enable_llm_rerank` | `True` | `domain/services/channel_resolver.py` | No | Needs tests to confirm branch coverage. |
| `hw_checker_mcp_enabled` | `True` | `workers/summary_worker.py` | Documented in changelog | Good doc coverage. |
| `external_api_enabled` | `False` | `summary_worker.py`, review pipeline tests | Documented (`TECHNICAL_DESIGN.ru.md`) | Ensure secrets gating documented in English. |

Key actions: wire unused flags (`use_modular_reviewer`) into DI, produce documentation for absent entries, and add tests verifying toggled behaviour.

## 4. CI Pipeline Assessment

| Target | Run 1 | Run 2 | Run 3 | Notes |
|--------|-------|-------|-------|-------|
| `make lint` | Fail | Fail | Fail | Identical failures; dominated by E501/F821 across `src/` and shared SDK. |
| `make test-coverage` | Fail (12 collection errors, coverage 21.07%) | Fail (same) | Fail (same) | Root causes: indentation error (`tests/e2e/test_digest_pdf_button.py`), missing Airflow dependency, duplicate module names causing import mismatch, absent review tests. |
| `make review-test` | Fail (glob missing) | Fail | Fail | Target references `tests/unit/domain/test_review*.py` which no longer exists; zero tests executed. |

Log references: `ci_run1_lint.log`, `ci_run2_lint.log`, `ci_run3_lint.log`, `ci_run1_test.log`–`ci_run3_test.log`, `ci_run1_review.log`–`ci_run3_review.log`.

## 5. Remediation Backlog

See `docs/specs/epic_01/stage_01_01_backlog.md` for the full table (10 items). Headlines:

- **P0 blockers**: unblock coverage suite, fix review-test glob, add reviewer-focused coverage.
- **P1 items**: shared SDK lint/coverage debt, activate `use_modular_reviewer`, staged lint allowlist.
- **P2 items**: feature flag documentation & phased lint strategy for monorepo.

## 6. Risk Register Updates

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Reviewer rollout proceeds without working tests (`make review-test` empty) | High | High | EP01-S01-CI-002 (fix target) before Stage 01_02 development. |
| Feature flags drift from implementation (`use_modular_reviewer` unused) | High | Medium | EP01-S01-FLAG-001 to wire or deprecate; add integration tests. |
| Shared SDK regressions propagate to reviewer | Medium | High | EP01-S01-COV-002 & EP01-S01-LINT-001 to raise coverage/lint gate. |
| CI remains red due to lint noise | Medium | High | EP01-S01-LINT-003: introduce allowlists/segment targets so reviewer scope can be enforced. |

## 7. Recommendations & Next Steps

1. **Triage P0 backlog tickets immediately** (Stage 01_02 kickoff). Without fixing test collection issues we cannot measure improvements or enforce coverage.
2. **Assign owners for shared SDK remediation**; split mypy/flake8 cleanup into manageable PRs aligned with backlog IDs.
3. **Introduce reviewer-focused smoke tests** covering `modular_review_service`, channel digest flows, and flag toggles; gate `use_modular_reviewer` toggling with automated checks.
4. **Document and validate feature flags**: update relevant docs (`docs/reference/en/API_REVIEWER.md`, architecture notes) and add unit tests ensuring toggles flip behaviour.
5. **Plan lint enforcement**: adopt allowlist strategy so reviewer-critical modules (`packages/multipass-reviewer`, `shared_package`, reviewer-related `src` paths) can be held to strict lint/mypy without waiting for full repo cleanup.

## 8. Supporting Artifacts

- `docs/specs/epic_01/stage_01_01_backlog.md` – prioritised remediation tickets.
- `docs/specs/epic_01/stage_01_01_questions_backlog.md` – open questions routed through EP01 Tech Lead.
- `docs/specs/epic_01/stage_01_01_feature_flag_inventory.md` – full flag reader inventory and decision options.
- `docs/specs/epic_01/stage_01_01_comms_plan.md` – stakeholder contact sheet and notification templates.
- `docs/specs/epic_01/stage_01_01_airflow_test_strategy.md` – CI options matrix for Airflow-dependent tests.
- `docs/specs/epic_01/stage_01_01_lint_allowlist_plan.md` – staged lint enforcement strategy.
- `docs/specs/epic_01/stage_01_01_shared_sdk_governance.md` – RACI and coverage targets for shared SDK.
- `scripts/quality/list_skipped_tests.py` – pytest skip inventory tool.

---

Prepared by: Stage 01_01 Tech Lead (Assistant)
Date: 2025-11-09
