# RFC · Repository Reorganisation (EP06)

## Context
Following EP01–EP04, the repository contains legacy directories (`docs/legacy`,
`scripts/day*`, deprecated tests) interleaved with active assets. Contributors
report difficulty locating canonical docs, and automation scripts remain spread
across multiple folders. EP06 aims to streamline layout without breaking history.

## Goals
- Provide intuitive top-level structure aligned with Clean Architecture.
- Separate active documentation from archives; enforce bilingual parity.
- Group automation scripts by purpose (CI, infra, tooling).
- Ensure migration plan preserves git history and minimises merge conflicts.

## Current Layout Audit
- **Docs:** Active specs live under `docs/specs/`, but API and guide content is
  scattered at the root (`API_*.md`, `DOCS_OVERVIEW*.md`, `MODULAR_REVIEWER_*`).
  `docs/archive/` stores historical material; top-level `archive/` is empty.
- **Scripts:** Mixture of legacy entry points (`day12_run.py`,
  `mcp_comprehensive_demo.py`) and partially grouped folders (`analysis/`,
  `maintenance/`, `quality/`). CI helpers reside under `scripts/ci/`, but shared
  infra bootstraps appear at the root.
- **Prompts:** Only `prompts/v1/` exists; reviewer and summarisation prompts need
  distinct homes, with deprecated variants archived.
- **Tests:** Duplicate hierarchies (`tests/`, `src/tests/`) complicate ownership
  and break clean layering; fixtures in `tests/fixtures/` power integration/e2e
  flows and must remain accessible.
- **Evidence bundles:** `docs/specs/epic_04/evidence/` and similar folders provide
  sign-off provenance; moves must retain references until archival manifests are
  regenerated.

## Non-Goals
- Full rewrite of documentation content (only reorganisation and targeted updates).
- Large-scale refactor of application code beyond path updates.
- Deletion of historical artefacts without archival replacements.

## Proposed Structure (Target)
```
docs/
  README.md
  specs/
    epic_XX/
    reference/
    operations/
    playbooks/
  guides/
    en/
    ru/
  archive/
    <year>-<theme>/
scripts/
  ci/
  infra/
  maintenance/
  quality/
archive/
  legacy/
    <timestamp>/
tests/
  unit/
  integration/
  e2e/
  legacy/ (optional, clearly marked)
prompts/
  reviewer/
  summarisation/
  archive/
```

## Migration Plan
1. **Preparation**
   - Freeze merges touching `docs/`, `scripts/`, `archive/` during execution window.
   - Communicate plan via Slack/email and progress tracker.
   - Tag baseline commit for potential rollback.
2. **Scripted Moves**
   - Use `python tools/repo_cleanup.py` (to be authored) for deterministic moves.
   - Leverage `git mv` to preserve history.
   - Moves aligned with buckets: docs → `docs/guides/en|ru/`, scripts → `scripts/<bucket>/`,
     prompts → `prompts/<category>/`, tests → canonicalised `tests/`.
3. **Reference Updates**
   - Run search-and-replace for old paths (`rg` validation).
   - Update import paths, docs links, automation scripts.
4. **Verification**
   - Execute CI (lint/tests/link checks, observability verification).
   - Manual spot-check navigation docs (EN/RU) against new index.
   - Validate prompt registry against new layout; ensure CLI/backoffice docs resolve.
5. **Communication**
   - Publish migration guide summarising new layout and how to update forks.

## Rollout Considerations
- Branch-based rollout to allow smoke testing before merge.
- Align with Stage 06_02 deliverables; Stage 06_03 automation must respect new paths.
- Coordinate with doc translation workflow to rename RU files simultaneously.

## Validation & Tooling
- `scripts/tools/repo_cleanup.py` to emit dry-run summary, archive manifests, and
  JSON changelog for evidence.
- Add CI guard (Stage 06_03) running doc link checker, prompt registry validator,
  and directory placement lint.
- Ensure `make lint-allowlist` and `make test` cover relocated paths before merge.

## Communication Plan
- Share RFC via repo PR and progress tracker entry; optional heads-up in shared
  `#ops-shared` channel once execution window is fixed.
- Update `docs/INDEX.md` and `docs/DOCS_OVERVIEW*.md` in the same change set to
  avoid broken navigation between approvals and rollout.

## Approvals
| Stakeholder | Decision | Date | Notes |
|-------------|----------|------|-------|
| Architecture | ☐ |  | Pending review of Stage 06_02 execution plan. |
| Documentation | ☐ |  | Requires guide/index parity check (EN/RU). |
| Operations | ☐ |  | Confirm scripts and infra automation entry points remain stable. |
| QA | ☐ |  | Validate test relocation strategy and CI coverage. |

## Follow-up
- Document recurrence cadence (quarterly hygiene check).
- Evaluate adding CI guard to ensure new files follow directory conventions.
