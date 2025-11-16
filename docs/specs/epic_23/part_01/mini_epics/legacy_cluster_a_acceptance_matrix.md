# Legacy Cluster A · Acceptance Matrix

| Task | Stage | Evidence | Owner | Status |
| --- | --- | --- | --- | --- |
| Confirm scope & fixture names | TL-00 | Plan + notes in worklog | Tech Lead | Pending |
| Add `settings.mongodb_url`/`test_mongodb_url` + factory | TL-01 | Settings diff, docs update | Dev A | Pending |
| Migrate repositories to DI | TL-01 | Code review checklist, grep showing no raw clients | Dev A | Pending |
| Introduce pytest fixtures (`mongodb_client`, `mongodb_database`) | TL-02 | `tests/conftest.py` diff, fixture docstrings | Dev B | Pending |
| Ensure per-test DB cleanup | TL-02 | Logs showing drop + helper tests | Dev B | Pending |
| Configure pytest asyncio mode & remove legacy loop fixtures | TL-03 | `pytest.ini` diff + removed fixtures | Dev B | Pending |
| Async repo/use-case methods consistent (`async def` + awaiting) | TL-03 | Unit test logs, code diff | QA | Pending |
| Targeted suites pass without `OperationFailure`/`RuntimeError` | TL-03 | Pytest log attached to worklog | QA | Pending |
| Smoke suite (repos + channels + workers) | TL-04 | Combined pytest log, CI link | Tech Lead | Pending |
| Docs updated (`README*`, new testing guide) | TL-04 | Doc diff references | Tech Lead | Pending |
| `challenge_days_gap_closure_plan.md` + `work_log.md` updated (impact) | TL-04 | Doc diff, worklog entry | Tech Lead | Pending |

Status legend: Pending / In Progress / Done / Blocked.

