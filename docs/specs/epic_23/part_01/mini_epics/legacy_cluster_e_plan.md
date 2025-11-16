# Legacy Refactor Cluster E · Telegram Helpers & Workers

## 1. Metadata
| Field | Value |
| --- | --- |
| Cluster | E |
| Scope | Channel normalizer, Telegram utils, post fetcher worker |
| Epic | EP23 (sub-epic) |
| Tech Lead | cursor_tech_lead_v1 |
| Date | 2025-11-16 |
| References | `legacy_refactor_proposal.md` §Cluster E, Challenge Day plan (Days 11,17), `docs/specs/epic_23/work_log.md` |

## 2. Objectives
1. Определить единую политику нормализации каналов (решение: lowercase) и привести все вызовы/тесты к ней.
2. Ввести `TelegramClientAdapter` (DI), оборачивающий `telegram_utils`.
3. Обновить `PostFetcherWorker` и связанные tests на использование адаптера + DI, с доменными проверками.

## 3. Challenge Day Impact
- **Day 1 (Basic agent demo):** унифицированный normalizer избавит от сюрпризов в hello-world скрипте.
- **Day 11 (Scheduler):** расписание/воркеры получают документированный адаптер и становятся демонстрацией “24/7 summary”.
- **Day 17 (Pipeline):** PostFetcherWorker после рефактора служит примером mini pipeline (ingest→save) для учебных материалов.

## 4. Stages
| Stage | Цель | Owner | Duration | Dependencies | Evidence |
| --- | --- | --- | --- | --- | --- |
| TL-00 | Channel normalization decision + checklist | Tech Lead + Analyst | 1d | Challenge Day plan | Decision note |
| TL-01 | Adapter + DI | Dev D | 2d | TL-00 | Adapter module, DI wiring |
| TL-02 | Channel normalizer refactor | Dev D | 1d | TL-01 | Normalizer code diff |
| TL-03 | Worker refactor + tests | Dev E + QA | 3d | TL-02 | Worker/test diffs, pytest log |
| TL-04 | Docs + Challenge Day updates | Tech Lead | 1d | TL-03 | Doc diff, worklog |

## 5. Stage Details
### TL-00 · Policy & Alignment
- Confirm lowercase canonical form with Analyst/Architect (ties into Challenge Day 1 + 11).
- List all modules touching channel names (normalizer, CLI, worker, docs).
- Capture migration impacts (DB fields? analytics?).

### TL-01 · Adapter Introduction
- Create `src/infrastructure/clients/telegram_adapter.py` with interface `TelegramClientAdapter`.
- Wrap existing `telegram_utils` functions; ensure adapter methods return domain types.
- Register adapter via DI; update worker/service constructors.

### TL-02 · Channel Normalizer Refactor
- Update `ChannelNormalizer` in domain layer to enforce lowercase; provide docstring.
- Adjust tests (`tests/unit/domain/test_channel_normalizer.py`).
- Add `normalize_channel_name` helper for CLI/backoffice reuse.

### TL-03 · Worker & Test Alignment
- Refactor `PostFetcherWorker` to use adapter + repositories via DI.
- Update tests: assert domain-level outcomes (posts saved count, timestamps).
- Remove direct Mongo mocks; use repository/adapter mocks.
- Ensure E2E Telegram tests (if active) align with new behaviour.

### TL-04 · Documentation & Challenge Days
- Update `docs/challenge_days.md` (Days 11 & 17) to describe scheduler/pipeline using new adapter.
- Update developer guide for Telegram integration (existing doc or new `docs/guides/en/telegram_adapter.md`).
- Fill `work_log.md` + acceptance matrix; mark relevant rows in Challenge Day gap table.

## 6. Acceptance Matrix
`legacy_cluster_e_acceptance_matrix.md`

## 7. Risks / Notes
- Need to confirm whether DB documents require migration (if stored names change). If yes, plan migration script or compatibility shim.
- Ensure no domain → infrastructure leakage: adapter interfaces live in domain/application.

