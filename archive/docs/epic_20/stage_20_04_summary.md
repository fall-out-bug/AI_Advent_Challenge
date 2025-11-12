# Stage 20_04 Summary · Validation & Report

## Status: 🔄 In Progress

### Deliverables
- `results_stage20.jsonl` (latest run, 2025-11-11 21:12 UTC)
- `results_with_labels.jsonl` (updated labels: `rag_better` 7, `non_rag_better` 8)
- `report.md` (updated analysis of successes/failures)

### Highlights
- ✅ Retrieval активен для всех запросов (1–5 чанков)
- ✅ Большинство LLM-вызовов теперь успешны (`llm_unavailable` остался лишь для `lect_002` RAG шага)
- ✅ RAG победы: `arch_001`/`arch_002`/`arch_003`/`mcp_001`/`bench_001`/`lect_004`/`lect_006`
- ❌ Non-RAG выигрывает там, где RAG отвечает "контекст не найден" (`mcp_002`, `bench_002`, `lect_001`, `lect_003`, `lect_005`, `lect_007`, `index_001`, `lect_002` non-rag)
- ⏱️ Без ретраев отдельные ответы занимают до ~8s (но в пределах ожиданий)

### Remaining Tasks
- Ручной обзор (подтвердить/скорректировать labels, качественные заметки)
- Итоговый анализ (развернуть секцию успехов/регрессий в `report.md`)
- Демозапись (по `docs/specs/epic_20/demo_plan.md`)

**Last Updated:** 2025-11-11 21:20 UTC
**Owner:** Tech Lead Agent
