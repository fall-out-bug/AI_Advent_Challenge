# Legacy Refactor Cluster B · Summarization & Digest Use Cases

## 1. Metadata
| Field | Value |
| --- | --- |
| Cluster | B |
| Scope | `GenerateChannelDigestByNameUseCase`, `GenerateChannelDigestUseCase`, summarizer integration |
| Epic | EP23 (sub-epic) |
| Tech Lead | cursor_tech_lead_v1 |
| Date | 2025-11-16 |
| References | `legacy_refactor_proposal.md` §Cluster B, `challenge_days_gap_closure_plan.md` (Days 3,5,6,15), TL plan |

## 2. Objectives
1. Определить и задокументировать async/ sync контракт для digest use-cases (решение: async).
2. Интегрировать новую `SummarizerService` (domain/application) вместо прямых LLM вызовов.
3. Исправить сигнатуры вызовов репозиториев (`post_repo`) и удалить undefined переменные.
4. Обновить тесты (unit + integration) так, чтобы они использовали mock SummarizerService, а не низкоуровневые LLM.

## 3. Challenge Day Impact
- **Day 3 (Stopping)** – CLI демо на обновлённых use-case’ах обеспечит корректное “остановись, когда ясно” поведение.
- **Day 5 (Model comparison)** – результаты бенчмарка будут ссылаться на исправленные summarizer’ы, что закрывает пробел в отчёте.
- **Day 6 (CoT)** – новая `SummarizerService` используется в тестах CoT vs non-CoT.
- **Day 15 (Compression)** – Digest pipeline демонстрирует работу с компрессией и ограничениями токенов.

## 4. Stages
| Stage | Цель | Owner | Duration | Dependencies | Evidence |
| --- | --- | --- | --- | --- | --- |
| TL-00 | Контракты + дизайн | Tech Lead + Architect | 1d | Cluster A (settings ready) | Design note, approved contract |
| TL-01 | SummarizerService + DI | Dev A | 2d | TL-00 | New domain service, DI wiring |
| TL-02 | Use-case refactor | Dev A + Dev B | 2d | TL-01 | Updated use cases, repository calls fixed |
| TL-03 | Tests & fixtures | QA + Dev B | 2d | TL-02 | Unit/integration tests green |
| TL-04 | Docs & Challenge Days updates | Tech Lead | 1d | TL-03 | Doc diffs, worklog entries |

## 5. Stage Details
### TL-00 · Contract Alignment
- Confirm `GenerateChannelDigestByNameUseCase.execute` and `GenerateChannelDigestUseCase.execute` are `async def`.
- Define interface for `SummarizerService` (methods, exceptions, type hints).
- Capture migration plan for repository signatures (channel_id, user_id, limit).
- Output: short design note appended to plan + architect acknowledgement.

### TL-01 · SummarizerService & DI
- Create `src/domain/services/summarizer.py` (interface) + `src/application/services/summarizer_service.py` (default impl using LLM adapter).
- Register service in DI container; ensure tests can inject fake summarizer.
- Provide stub/adapter for CLI demos (used later by Challenge Day tasks).
- Evidence: service module, DI wiring diff, docstrings.

### TL-02 · Use-Case Refactor
- Update use-cases to:
  - Accept injected `SummarizerService`.
  - Await async repository calls; remove undefined variables (e.g., `posts`).
  - Ensure `post_repo.get_posts_by_channel` signature matches implementation & tests.
- Add structured logging & error handling.
- Evidence: use-case files diff, type checking.

### TL-03 · Tests & Fixtures
- Update integration tests under `tests/integration/summarization/`.
- Add unit tests verifying fallback paths (no posts, summarizer exception).
- Replace direct LLM mocks with `SummarizerService` mocks.
- Ensure `tests/unit/cot/test_day06_cot_vs_nocot.py` reuses new service.
- Evidence: `pytest tests/integration/summarization tests/unit/cot` log, coverage report.

### TL-04 · Docs & Challenge Days
- Update `docs/challenge_days.md` (Days 3,5,6,15) referencing new demos/tests.
- Add developer note in `docs/guides/en/use_case_summarization.md` (new) covering async contract.
- Update `work_log.md` + acceptance matrix.

## 6. Acceptance Matrix
(See `legacy_cluster_b_acceptance_matrix.md`)

## 7. Risks / Dependencies
- Depends on Cluster A for stable Mongo fixtures (to avoid auth errors in integration tests).
- Requires coordination with Challenge Day deliverables (Day 3 demo uses new CLI).
- Ensure LLM adapters from Cluster D accept new service integration later (keep interfaces decoupled).

