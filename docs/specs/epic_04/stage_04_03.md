# Stage 04_03 · Repository Hygiene & Sign-Off

## Goal
Finalise repository clean-up, update navigation artefacts, and capture lessons
learned to close the epic.

## Checklist
- [x] Update top-level README, documentation indices, and progress tracker to
  reflect the new canonical structure.
- [x] Review archive folders for completeness (README, metadata, access notes).
- [x] Perform final repository audit (lint, tests, doc links) to ensure no
  dangling references remain.
- [x] Compile closure report summarising work completed, remaining risks, and
  recommended follow-ups.
- [x] Obtain stakeholder sign-off (architecture, product, operations).
- [x] Publish disaster recovery drill schedule and ownership notes derived from
  EP03 follow-ups.
- [ ] Record known issues and deferred items in `docs/specs/epic_04/known_issues.md`.

## Deliverables
- Updated repository documentation and indices.
- Closure report stored under `docs/specs/epic_04/`.
- Signed-off checklist or meeting notes confirming acceptance.
- DR drill calendar and escalation summary linked from operations docs.

## Metrics & Evidence
- Automated doc link checker or manual verification logs.
- CI/lint reports confirming clean state post-cleanup.
- Summary of archived assets with final locations.

## Dependencies
- Completion of Stage 04_02 migrations.
- Availability of documentation maintainers and stakeholders.

## Exit Criteria
- Documentation merged, trackers updated, stakeholders approve closure.
- No outstanding TODOs or blockers tied to EP04; remaining items assigned to
  future epics if necessary.
- Lessons learned captured for future archival efforts.
- Disaster recovery drill cadence communicated and logged.

## Open Questions
- Should we schedule periodic audits to ensure archive remains tidy?
- Are there automation opportunities for archive inventory generation?

## Validation Summary
- ✅ Documentation refreshed (`README.md`, `docs/INDEX.md`, `docs/DOCS_OVERVIEW*.md`)
- ✅ Archive manifest and subfolder READMEs verified (`archive/ep04_2025-11/`)
- ✅ Full test suite with shared infra credentials:
  `MONGODB_URL="mongodb://admin:<pwd>@127.0.0.1:27017/butler_test?authSource=admin" poetry run pytest -q`
  → `429 passed / 2 xfailed` (latency benchmarks tracked as known issues)
  Evidence: `docs/specs/epic_04/evidence/test_summary_stage_04_03_final_2025-11-10T2358Z.txt`
