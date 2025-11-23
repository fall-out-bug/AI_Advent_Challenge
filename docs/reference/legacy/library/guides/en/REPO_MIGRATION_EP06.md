# EP06 Repository Migration Guide

## Overview

Epic 06 reorganises repository assets so documentation, automation scripts, and
legacy tests follow the Clean Architecture layout. This guide explains the
changes, how to update local clones, and what scripts assist with future moves.

## Summary of Changes

- Documentation is grouped into:
  - `docs/guides/en` and `docs/guides/ru` for operational and how-to guides.
  - `docs/reference/en` and `docs/reference/ru` for API, architecture, and deep
    technical references.
  - `docs/archive/<year>-<theme>` for legacy material previously under `docs/`.
- Automation scripts are categorised under:
  - `scripts/infra/` for shared infrastructure helpers.
  - `scripts/maintenance/` for data maintenance utilities.
  - `scripts/quality/` for QA, benchmarking, and smoke tests (including new
    subfolders `analysis/`, `benchmark/`, `qa/`, `security/`, `validation/`).
- Reviewer prompt assets now live in `prompts/reviewer/`; the loader uses the
  `prompts.reviewer` package.
- Historical `src/tests/**` are preserved in `tests/legacy/src/**`; canonical
  suites remain in `tests/`.

## Required Developer Actions

1. Update documentation references:
   - Replace links such as `docs/ARCHITECTURE.md` with
     `docs/reference/en/ARCHITECTURE.md`.
   - Replace guider references `docs/DEPLOYMENT.md` with
     `docs/guides/en/DEPLOYMENT.md`.
   - Archive references should point to `docs/archive/<year>-<theme>/...`.
2. Refresh script pointers in READMEs, automation, and CI jobs:
   - Shared infra wrapper → `scripts/infra/start_shared_infra.sh`.
   - Review system smoke test → `scripts/quality/test_review_system.py`.
   - Benchmark exporters → `scripts/quality/analysis/export_*.py`.
3. When importing prompt resources programmatically, use the package name
   `prompts.reviewer` (see `PromptLoader.PROMPTS_PACKAGE`).
4. Test discovery defaults to `tests/`; run legacy suites via
   `pytest tests/legacy/src -q` when needed.
5. Regenerate links or notes that referenced `scripts/qa/` or root-level docs to
   avoid stale guidance.

## Tooling

- The migration script `tools/repo_cleanup.py` (invoked through
  `make repo-cleanup-dry-run` / `make repo-cleanup-apply`) performs deterministic
  moves. The plan file `docs/specs/epic_06/repo_cleanup_plan.json` is now empty
  to prevent accidental re-runs; clone it to craft future cleanups.
- Lints and tests expect the new paths; run:
  ```bash
  poetry run pytest tests/unit/tools/test_repo_cleanup.py -q
  ```
  to validate tooling after local adjustments.

## Checklist for Downstream Repositories

- [ ] Update documentation links to new `docs/guides/` and `docs/reference/`
      paths.
- [ ] Swap automation references to `scripts/infra/` or `scripts/quality/`.
- [ ] Ensure CI workflows call `pytest` from `tests/` (legacy suites optional).
- [ ] Bump dependencies if importing `PromptLoader` (new package path).
- [ ] Refresh onboarding docs to reference this guide.

## RU Summary (Краткое резюме)

- Документация разнесена по каталогам `docs/guides/*`, `docs/reference/*`,
  архив – в `docs/archive/…`.
- Скрипты распределены по `scripts/infra/`, `scripts/maintenance/`,
  `scripts/quality/…`.
- Промпты доступны через пакет `prompts.reviewer`.
- Исторические тесты лежат в `tests/legacy/src`.
- Обновите ссылки в документах и CI, используйте `tools/repo_cleanup.py` для
  последующих реорганизаций, запустите smoke-тесты (`scripts/quality/test_review_system.py`)
  после обновления.
