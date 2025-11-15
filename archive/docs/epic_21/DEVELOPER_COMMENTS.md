# Epic 21 · Developer Comments (Final Fixes)

Audience: Developer
Status: Ship‑ready; apply minor edits below

---

## Required Final Edits (Must)

1) Docs sync: variance semantics (per‑run across chunks)
- What to change: Replace “variance across repeated runs (same query)” → “variance across chunks in a single run”.
- Where:
  - `docs/specs/epic_21/OPERATIONS_RUNBOOK.md` (metrics table, troubleshooting section)
  - `docs/specs/epic_21/DEVELOPER_IMPLEMENTATION_SPEC.md` (metrics list/description)
- Rationale: Code exports `rag_rerank_score_variance` as spread across chunk scores per run.

2) Docs cleanup: remove `seed` from MVP
- What to change: Drop seed from config snippets and guidance; keep only `RAG_RERANK_TEMPERATURE` as debug override.
- Where:
  - `OPERATIONS_RUNBOOK.md` (config block and tuning table)
  - `DEVELOPER_IMPLEMENTATION_SPEC.md` (decisions snapshot, config section)
- Note: Seed can be referenced as future enhancement (Epic 22), not part of MVP.

3) Demo artifacts per `DEMO_TASK.md`
- Add file: `docs/specs/epic_21/demo_queries.jsonl` with 10 questions (из задания).
- Make targets (in `Makefile`):
  - `day_21_batch`: batch‑прогон 10 вопросов → `var/results_ep21.jsonl`.
  - `day_21_metrics`: печать выдержки rag_* метрик из `/metrics`.
  - (optional) `day_21_rollback_drill`: enable→run→disable flag, в одном шоте.
- Add doc: `docs/specs/epic_21/DEMO.md` — краткий сценарий, команды, пример вывода, как включить fallback/rollback.

4) Defaults consistency (threshold)
- Ensure все документы используют дефолт `score_threshold: 0.30` (как в конфиге).
- Любые упоминания 0.35 оставить как “вариант для повышения precision”, не как дефолт/рекомендованный по умолчанию.

5) CLI precedence banner
- Вставить явное примечание “CLI > YAML > ENV > Defaults” в `DEMO.md` и/или `rag_commands` help, показать один пример переопределения.

---

## Optional Polish (Nice‑to‑have)
- В `DEMO.md` добавить “быстрые команды”:
  - `make day_21_demo`
  - `make day_21_batch`
  - `make day_21_metrics | rg 'rag_'`
- Зафиксировать модель LLM в демо‑инструкции (для повторяемости).
- Привести пример grep для variance/fallback: `curl :8000/metrics | rg 'rag_rerank_(score_variance|fallback_total)'`.

---

## Verification Checklist
- [ ] В `OPERATIONS_RUNBOOK.md` и `DEVELOPER_IMPLEMENTATION_SPEC.md` обновлена семантика variance (per‑run across chunks); изъяты упоминания seed.
- [ ] Добавлен `demo_queries.jsonl` (10 вопросов из `DEMO_TASK.md`).
- [ ] Добавлены цели `day_21_batch`, `day_21_metrics` (и по желанию rollback) в `Makefile`.
- [ ] Создан `DEMO.md` с сценарием и командами; показан пример CLI‑override.
- [ ] Везде согласован дефолт threshold=0.30.

---

## References
- `docs/specs/epic_21/DEMO_TASK.md`
- `docs/specs/epic_21/OPERATIONS_RUNBOOK.md`
- `docs/specs/epic_21/DEVELOPER_IMPLEMENTATION_SPEC.md`
- `docs/specs/epic_21/ARCHITECT_FINAL_SIGNOFF.md`
- `scripts/rag/day_21_demo.py`
