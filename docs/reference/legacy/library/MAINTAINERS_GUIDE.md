# Maintainer Playbook

## Overview
The maintainer team keeps the repository healthy, enforces Clean Architecture, and
ensures CI pipelines ship green by default. This playbook covers daily routines,
automation touchpoints, and escalation paths introduced during Epic 06.

## Repo Layout
- `src/`: production code organised by architecture layers (`domain`, `application`,
  `infrastructure`, `presentation`).
- `tests/`: active suites (`unit`, `integration`, `legacy/src`) aligned with the new
  layout. Legacy tests remain under `tests/legacy/src/` for historical coverage.
- `scripts/`: operational tooling split into:
  - `scripts/ci/` for GitHub Actions bootstrap/cleanup helpers.
  - `scripts/infra/` for shared-infra compatibility shims.
  - `scripts/quality/` for smoke tests and diagnostics.
- `docs/`: reorganised into `docs/guides/`, `docs/reference/`, `docs/specs/`, and
  `docs/archive/` for bilingual contributor guidance.

## Automation & Scripts
- Shared infra bootstrap (CI/local parity):
  - `python scripts/ci/bootstrap_shared_infra.py --mongo-port 37017 --mock-port 19080`
  - `python scripts/ci/cleanup_shared_infra.py` (always run, even on failure)
  - Mock endpoints implemented in `scripts/ci/mock_shared_services.py`
- Repository hygiene:
  - `make repo-cleanup-dry-run` → preview plan in `docs/specs/epic_06/repo_cleanup_plan.json`
  - `make repo-cleanup-apply-git` → execute scripted moves with history retention
- Quality smoke checks:
  - `poetry run python scripts/quality/test_review_system.py --metrics`
  - `poetry run pytest tests/integration/presentation/cli/test_backoffice_cli.py -q`
  - `poetry run pytest tests/legacy/src/presentation/mcp/test_performance.py -q`
- Always update `docs/specs/epic_06/repo_cleanup_log.md` when running automated
  moves to preserve traceability.

## CI Gates
- Pipelines: `.github/workflows/ci.yml`, `python-ci.yml`, and `observability-checks.yml`.
- Required jobs: lint (Black, Flake8, MyPy), unit tests, integration tests, coverage (≥80 %),
  Docker image builds, and security scan.
- Shared infra steps:
  - `Bootstrap shared infrastructure` → exports `MONGODB_URL`, `LLM_URL`, `PROMETHEUS_URL`
  - `Cleanup shared infrastructure` → tears down containers/processes
- MCP latency guardrails (fail-fast thresholds):
  | Metric | Threshold (s) | Override |
  |--------|---------------|----------|
  | Discovery | 1.50 | `MCP_DISCOVERY_LATENCY_SEC` |
  | Calculator | 1.20 | `MCP_CALCULATOR_LATENCY_P95_SEC` |
  | Token counter (S/M/L) | 1.10 / 1.30 / 1.60 | `MCP_TOKEN_LATENCY_*` |
  | Model listing | 1.20 | `MCP_MODEL_LISTING_LATENCY_SEC` |
- Never add new `xfail` markers without documenting rationale in specs and the CI
  README; remove temporary skips as part of Stage endpoints.

## Escalation & Contacts
- Operational runbooks live in `docs/specs/operations.md` and
  `docs/specs/epic_03/alerting_runbook.md`.
- Escalation order: on-call engineer → EP03 tech lead → program coordination.
- Incident communications: `#ops-shared` Slack, on-call bridge, and incident tracker.
- Record automation regressions or flaky tests in the Epic 06 repo cleanup log
  with timestamps for visibility.

## Onboarding Checklist
- [ ] Review this playbook plus `docs/specs/operations.md`.
- [ ] Run CI parity tests locally (`bootstrap_shared_infra.py`, integration, MCP performance suites).
- [ ] Verify documentation links via `docs/INDEX.md` and migration guide.
- [ ] Update `docs/specs/epic_06/repo_cleanup_log.md` after any scripted moves.
- [ ] Confirm upcoming release window in programme tracker; coordinate with ops.

## Release Cadence
- Weekly maintenance window: Saturday 02:00–06:00 UTC (see operations guide).
- Tag releases after green CI plus manual smoke tests:
  1. `poetry run pytest -q`
  2. `poetry run python scripts/quality/test_review_system.py --metrics`
  3. `poetry run pytest tests/integration/presentation/cli/test_backoffice_cli.py -q`
  4. Update `CHANGELOG.md` with automation notes and benchmark deltas.
- For hotfixes, follow the escalation flow and document deviations in the next
  release bulletin.

## Краткое резюме (RU)
- Общая структура: код (`src/`), тесты (`tests/`), скрипты (`scripts/ci|infra|quality`),
  документация (`docs/guides|reference|specs|archive`).
- Автоматизация: запуск shared infra через `bootstrap_shared_infra.py`,
  очистка `cleanup_shared_infra.py`, диагностические тесты в `scripts/quality/`.
- CI-гейты: lint, unit/integration, покрытие ≥80 %, латентность MCP контролируется
  переменными `MCP_*_LATENCY_*`.
- Эскалация: см. `docs/specs/operations.md`, канал `#ops-shared`, дежурный EP03.
- Релизы: еженедельно после зелёного CI и smoke-тестов, результаты фиксируются в `CHANGELOG.md`.
