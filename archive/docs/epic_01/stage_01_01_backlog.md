# Stage 01_01 · Remediation Backlog

| ID | Theme | Priority | Scope | Summary | Effort | Notes |
|----|-------|----------|-------|---------|--------|-------|
| EP01-S01-CI-001 | CI | P0 | `tests/e2e/test_digest_pdf_button.py`, Airflow fixtures, `tests/unit/*` | Unblock `make test-coverage`: fix indentation error, provide Airflow guard/mocks, and reconcile duplicate module names causing pytest import mismatches. | Large | Test suite cannot run; affects coverage and Stage 01_02 readiness. |
| EP01-S01-CI-002 | CI | P0 | `Makefile` (`review-test` target) | Update review-test target to point at real reviewer unit tests and add smoke coverage for `src/application/services/modular_review_service.py`. | Medium | Current target references non-existent glob and exits with error 4. |
| EP01-S01-COV-001 | Coverage | P0 | `src/application/services/modular_review_service.py`, `src/domain/agents/*`, `src/infrastructure/clients/*` | Establish reviewer-focused integration/unit tests to lift application coverage (current 21.07%) and exercise critical reviewer paths. | Large | Blocker for confidence in modular reviewer rollout. |
| EP01-S01-COV-002 | Coverage | P1 | `shared_package/agents/*`, `shared_package/config/*`, `shared_package/orchestration/*` | Add shared SDK unit tests to raise package coverage from 89% to ≥90% (per policy). | Medium | Modules used by reviewer pipeline lack coverage; prioritize agents/orchestration. |
| EP01-S01-LINT-001 | Lint | P1 | `shared_package/*` | Resolve 48 mypy errors, flake8 violations, and isort/black drift in shared SDK. | Large | Blocks stricter CI; high leverage for reviewer stability. |
| EP01-S01-LINT-002 | Lint | P1 | `multipass_reviewer/*` | Fix strict mypy failures and formatting issues (review logger, checkers) to keep package green. | Small | Maintains package contract before further remediation. |
| EP01-S01-LINT-003 | Lint | P2 | `src/*` | Define staged lint plan (line-length waivers, module-by-module cleanup) to handle >1k flake8 errors and 1202 mypy issues. | Large | Requires phased execution; produce proposal in Stage 01_02. |
| EP01-S01-FLAG-001 | Feature Flags | P1 | `src/application/*`, `src/infrastructure/config/settings.py` | Wire `use_modular_reviewer` flag into DI/application flows or deprecate; ensure defaults enforced and tested. | Medium | Flag currently defined but unused—risk of silent regressions. |
| EP01-S01-FLAG-002 | Feature Flags | P2 | Flags: `enable_context_aware_parsing`, `enable_async_long_summarization`, `enable_llm_rerank`, docs | Document flag behaviour, add assertion tests, and remove dead toggles lacking consumers. | Medium | Many toggles lack documentation/validation; track for post-blocker cleanup. |
| EP01-S01-CI-003 | CI | P1 | `make lint`, `.pre-commit-config.yaml` (if available) | Introduce lint allowlist or segmented targets to make `make lint` actionable; break out reviewer-critical modules for focused linting. | Medium | Needed to prevent 30k+ lint violations from masking regressions. |

**Priority Legend**

- **P0** – Critical blocker for Stage 01_02; address immediately.
- **P1** – High priority within Stage 01_02 scope.
- **P2** – Important but may spill into later milestones if capacity constrained.

