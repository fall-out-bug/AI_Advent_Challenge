# Stage 04_03 · Sign-off Checklist

Date circulated: 2025-11-10
Requested sign-off deadline: 2025-11-13 (async)

## Instructions
1. Review the following artefacts:
   - `docs/specs/epic_04/epic_04_closure_report.md`
   - `docs/specs/epic_04/stage_04_03.md`
   - `docs/specs/epic_04/known_issues.md`
   - `archive/ep04_2025-11/ARCHIVE_MANIFEST.md`
  - Test evidence: `docs/specs/epic_04/evidence/test_summary_stage_04_03_final_2025-11-10T2358Z.txt` (run with `MONGODB_URL="mongodb://admin:<pwd>@127.0.0.1:27017/butler_test?authSource=admin"`)
2. Confirm there are no blocking issues in your domain.
3. Approve via PR comment or message (recorded in `signoff_log.md`).

## Stakeholder Checklist

| Stakeholder | Scope | Items to Confirm | Status | Notes |
|-------------|-------|------------------|--------|-------|
| EP01 Tech Lead | Modular reviewer tooling | Homework MCP replacement, prompts archived, latency xfail documented | ☐ |  |
| EP02 Tech Lead | MCP & bot consolidation | CLI/backoffice coverage, reminder workflows removed, tests updated | ☐ |  |
| EP03 Tech Lead | Observability & operations | Prometheus/LLM test guards, performance xfail rationale, DR drill follow-up | ☐ |  |
| Application Lead | Butler use cases | `use_cases/` migration complete, fossil imports removed | ☐ |  |
| Workers Lead | Schedulers & workers | `message_sender.py` archival, summary worker ownership documented | ☐ |  |
| Documentation Owner | Docs convergence | README/INDEX/Overview updated, legacy docs archived | ☐ |  |
| Operations Owner | Shared infra | `scripts/start_shared_infra.sh`, `shared_infra_cutover.md`, Mongo auth notes | ☐ |  |
| QA Lead | Test coverage | Skipped/XFailed suites logged, new CLI/E2E coverage in place | ☐ |  |

## Approval Log

Update `docs/specs/epic_04/signoff_log.md` with date + confirmation link for each stakeholder.

---

Questions? Contact the Stage 04_03 owner (Assistant) or leave comments on the closure PR.
