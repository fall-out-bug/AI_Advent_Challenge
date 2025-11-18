# Legacy Refactor Cluster A · Mongo & Async Infrastructure

## 1. Metadata
| Field | Value |
| --- | --- |
| Cluster | A |
| Scope | Mongo repositories, test fixtures, async infra |
| Epic | EP23 (sub-epic) |
| Tech Lead | cursor_tech_lead_v1 |
| Date | 2025-11-16 |
| References | `legacy_refactor_proposal.md` §Cluster A, `challenge_days_gap_closure_plan.md`, `docs/operational/context_limits.md` |

## 2. Objectives
1. Все Mongo репозитории используют DI и `settings.mongodb_url`/`settings.test_mongodb_url` (без прямых `MongoClient(...)`).
2. Тесты используют унифицированную фикстуру `mongodb_database` c пер-тестовой БД + автоматическим teardown.
3. Async тесты больше не падают на `RuntimeError: Event loop is closed`; используется `pytest-asyncio` (`asyncio_mode = auto`).
4. Никаких `OperationFailure: requires authentication` при наличии переменных окружения.

## 3. Challenge Day Impact
- **Day 13 (Environment)** – кластер даёт минимальную “одну команду” инструкцию для локальной Mongo (через новые фикстуры и `make day-23-up`), закрывая пробел из `challenge_days_gap_closure_plan.md`.
- **Day 16 (External memory)** – унификация репозиториев демонстрирует, как используется внешняя память (Mongo) в актуальном виде.
- **Day 17 (Pipelines)** – очищенные репозитории/фикстуры становятся основой для ETL/benchmark сценариев.

## 4. Stages (TL-00…TL-04)
| Stage | Цель | Owner | Duration | Dependencies | Evidence |
| --- | --- | --- | --- | --- | --- |
| TL-00 | Планирование + вопросы | Tech Lead | 1d | — | Updated proposal, accepted scope |
| TL-01 | DI + Settings | Dev A | 2d | TL-00 | Settings diff, repos migrated |
| TL-02 | Pytest фикстуры & cleanup | Dev B | 2d | TL-01 | New fixtures, docstrings, tests |
| TL-03 | Async стабилизация | Dev B + QA | 2d | TL-02 | pytest.ini updated, async tests green |
| TL-04 | Smoke suite & docs | Tech Lead | 1d | TL-03 | Test report, docs update |

## 5. Stage Details
### TL-00 · Scope & Contracts
- Review `legacy_refactor_proposal.md` + confirm cluster ordering.
- Decide final naming for fixtures (`mongodb_database`, `mongodb_client`, etc.).
- Capture open questions for architect (e.g., default lowercase normalization tie-in).
- Output: TL plan (this file) + updated `challenge_days_gap_closure_plan.md` link, `legacy_cluster_a_acceptance_matrix.md`.

### TL-01 · DI + Settings
- Add `settings.mongodb_url` and `settings.test_mongodb_url` if not present; wire through `pydantic-settings`.
- Introduce `MongoClientFactory` or similar helper returning client per env (prod/test).
- Update repositories: `post_repository`, `mongo_dialog_context_repository`, etc., to consume factory/DI.
- Remove direct `MongoClient("mongodb://localhost")` usages.
- Evidence: repository diffs, unit tests adjusted, docs snippet describing env vars.

### TL-02 · Pytest Fixtures & Cleanup
- Create fixtures in `tests/conftest.py` (or dedicated module):
  - `mongodb_client` (singleton per session) opening auth’d connection.
  - `mongodb_database` (function-scoped) generating db name via uuid/test name, ensuring cleanup after tests.
- Update tests to request fixtures instead of constructing clients manually.
- Add helper `drop_database_if_exists(client, name)` with logging.
- Evidence: fixture module, updated tests (no inline Mongo).

### TL-03 · Async Stabilization
- Configure `pytest.ini`: `asyncio_mode = auto`, ensure `pytest-asyncio` imported.
- Remove legacy event-loop fixtures; replace with `asyncio` fixtures from library when needed.
- Audit async repos/use-cases: ensure methods declared `async def` and awaited in tests.
- Run targeted suites: `tests/infrastructure/repositories`, `tests/integration/channels`, `tests/integration/workers`, confirm no `RuntimeError`/`OperationFailure`.
- Evidence: pytest logs attached to worklog entry.

### TL-04 · Smoke & Docs
- Run `pytest tests/infrastructure/repositories tests/integration/channels tests/integration/workers`.
- Update `README.md` / `README.ru.md` (if needed) with Mongo env variables for developers.
- Document fixtures + instructions in `docs/guides/en/testing_mongo.md` (new) or similar.
- Update `work_log.md` (Cluster A section) and `challenge_days_gap_closure_plan.md` (impact on Days 11, 17).

## 6. Acceptance Matrix (excerpt)
| Task | DoD Evidence | Status |
| --- | --- | --- |
| Settings expose Mongo URLs | Settings diff, env doc updated | Pending |
| Repos use DI (no raw client) | grep check + code review | Pending |
| Fixtures manage per-test DB | Fixture module + sample logs | Pending |
| Async tests stable | pytest log attached | Pending |
| Docs updated | README & testing guide diff | Pending |

Full matrix in `mini_epics/legacy_cluster_a_acceptance_matrix.md`.

## 7. Dependencies / Risks
- Needs `.env.infra` secrets for Mongo auth in CI (coordinate with DevOps).
- CI runners must run `bootstrap_shared_infra.py --check` or run standalone Mongo container for tests; plan TL-05 ensures this.
- Risk: time sink if cluster A touches too many modules at once; mitigate by incremental PRs per repo/test group.

## 8. Reporting
- Track progress in `work_log.md` under “Legacy Cluster A”.
- Each PR references this plan and updates acceptance matrix row.
- After TL-04, notify architect for review before moving to Cluster B.
