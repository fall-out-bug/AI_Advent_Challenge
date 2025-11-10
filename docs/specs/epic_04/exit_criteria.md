# Stage 04_01 · Exit Criteria Check

| Criterion | Status | Evidence | Notes |
|-----------|--------|----------|-------|
| Archive scope document approved by tech lead and coordination board | Complete | `archive_scope.md`, `signoff_log.md` | Approved by user on 2025-11-09 |
| No outstanding blockers preventing migration (or blockers recorded with plan) | Complete | `dependency_map.md`, `remediation_plan.md` | Blockers captured with remediation waves |
| Communication plan scheduled with responsible owners | Complete | `communication_plan.md` | Timeline and stakeholder matrix prepared |
| Archive folder structure validated | Complete | `archive/ep04_2025-11/ARCHIVE_MANIFEST.md` + subfolder READMEs | Manifest and naming conventions established |
| Evidence bundle prepared | Complete | `docs/specs/epic_04/evidence/` | Search logs and test baselines recorded |

## Summary

Stage 04_01 complete — approvals captured and blockers documented. Proceed with Stage 04_02 remediation waves.

---

# Stage 04_02 · Exit Criteria Check

| Criterion | Status | Evidence | Notes |
|-----------|--------|----------|-------|
| Scoped assets migrated/removed with sign-offs captured | Complete | `archive/ep04_2025-11/ARCHIVE_MANIFEST.md`, `signoff_log.md` | Waves 0–4 recorded; sign-offs tracked |
| CI/tests green post-migration | Complete | `MONGODB_URL="mongodb://admin:<pwd>@127.0.0.1:27017/butler_test?authSource=admin" poetry run pytest -q` → `docs/specs/epic_04/evidence/test_summary_stage_04_03_final_2025-11-10T2358Z.txt` | Shared infra + credentials required (see README Quick Start) |
| No unresolved references/import errors | Complete | `dependency_map.md`, smoke tests | Butler presentation/MCP suites updated for new handlers and digest flow |
| Migration log stored with archive README | Complete | `stage_04_02.md` migration log updated | Final validation summary appended |
| Observability follow-ups (Grafana IaC, Loki alerts) | Pending | – | Scheduled for later waves |

## Notes

- Wave 0 completed (docs + scripts archived); user approval recorded 2025-11-09.
- CLI digest export (`digest:export`) available; PDF MCP tool scheduled for archival in Wave 1.
- Shared infra connectivity tests now require running services with credentials (`./scripts/infra/start_shared_infra.sh` + `MONGODB_URL`).
- Latency benchmarks remain xfail pending recalibration (tracked in Stage 04_03 known issues).

---

# Stage 04_03 · Exit Criteria Check

| Criterion | Status | Evidence | Notes |
|-----------|--------|----------|-------|
| Documentation and indices refreshed (README, INDEX, DOCS_OVERVIEW, known issues) | Complete | `README.md`, `docs/INDEX.md`, `docs/DOCS_OVERVIEW*.md`, `docs/specs/epic_04/known_issues.md` | Reflects shared infra flow, Stage 04_03 scope |
| Critical test regressions resolved or triaged | Complete | `MONGODB_URL="mongodb://admin:<pwd>@127.0.0.1:27017/butler_test?authSource=admin" poetry run pytest -q` | Full suite green (429 passed / 2 xfail); latency benchmarks tracked in known issues |
| Closure report prepared | Complete | `docs/specs/epic_04/epic_04_closure_report.md` | Summarises deliverables, metrics, lessons |
| Stakeholder sign-offs captured | Pending | `docs/specs/epic_04/signoff_log.md`, `stage_04_03_signoff_checklist.md` | Await async approvals |
| DR drill schedule published | Pending | – | To be coordinated with EP03 follow-up |

## Notes

- Known issues documented for Stage 04_03 handover (`docs/specs/epic_04/known_issues.md`).
- Sign-off checklist distributed with 3-day async window.
- Final evidence stored in `docs/specs/epic_04/evidence/test_summary_stage_04_03_final_2025-11-10T2358Z.txt`.
