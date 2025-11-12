# Repository Cleanup Log (EP06)

| Date | Change | Script/Command | Notes | PR/Commit |
|------|--------|----------------|-------|-----------|
| 2025-11-10 | Stage 06_01 backlog refreshed with EP01–EP04 follow-ups; repository audit captured in `stage_06_01.md`. | Manual triage | Referenced source specs in backlog notes; pending Stage 06_02 execution. | TBC |
| 2025-11-11 | Authored `tools/repo_cleanup.py` with dry-run/git support; wired make targets and unit tests. | `poetry run pytest tests/unit/tools/test_repo_cleanup.py` | Enables scripted moves per RFC with reusable plan file (`repo_cleanup_plan.json`). | TBC |
| 2025-11-11 | Executed Stage 06_02 repo reorg: moved docs into `docs/guides/`, `docs/reference/`, reorganised scripts under `scripts/infra|maintenance|quality`, archived legacy demos, relocated `prompts/v1` to `prompts/reviewer`, migrated `src/tests` to `tests/legacy/src`. | `poetry run python -m tools.repo_cleanup --config docs/specs/epic_06/repo_cleanup_plan.json --execute --use-git` | Followed by manual moves for untracked analysis/benchmark scripts and path updates across README, indices, Makefile, pytest config. | TBC |

_Record each directory/file move, including before/after paths and automation used.
Attach evidence (CI run links, screenshots) where relevant._
