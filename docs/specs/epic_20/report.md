# Stage 20_04 Report · RAG vs Non-RAG Answering Agent

## 1. Batch Run Summary
- **Date:** 2025-11-11 21:12–21:15 UTC
- **Command:**
  ```bash
  MONGODB_URL="mongodb://admin:***@127.0.0.1:27017/butler?authSource=admin" \
  LLM_URL="http://127.0.0.1:8000" \
  EMBEDDING_API_URL="http://127.0.0.1:8000" \
  poetry run python -m src.presentation.cli.backoffice.main \
    rag batch \
    --queries docs/specs/epic_20/queries.jsonl \
    --out results_stage20.jsonl
  ```
- **Input:** 15 curated Russian-language questions (architecture, MCP, benchmarking, indexing, lectures)
- **Outputs:**
  - `results_stage20.jsonl`
  - `results_with_labels.jsonl` (`rag_better`: 7, `non_rag_better`: 8)

## 2. Observations
1. **Retrieval**
   - Mongo auth в env → 100% queries получили контекст (1–5 чанков)
   - Источники соответствуют документации (`docs/specs/*.md`, lecture notes)
2. **LLM Stability**
   - Большинство запросов вернуло `200 OK`
   - Единичные сбои (`lect_002` RAG шаг → 400; fallback задействован автоматически)
   - Время отклика: 1.7–8.9 сек; объём токенов до ~640
3. **Ответы**
   - RAG добавляет ссылки/файлы (`arch_002`, `mcp_001`, `bench_001`, `lect_004`, `lect_006`)
   - Non-RAG выигрывает, когда RAG отвечает "информация не найдена" либо даёт более краткий ответ (например `mcp_002`, `lect_001`)

## 3. Quantitative Metrics
| Metric | Value |
|--------|-------|
| Queries processed | 15 |
| Chunks retrieved | 5→11 queries, 2→2, 1→1, 3→1 |
| RAG better | 7 |
| Non-RAG better | 8 |
| Both poor | 0 |
| Fallback occurrences | 1 (RAG для `lect_002`) |

## 4. Representative Comparisons
- **`arch_002`**
  - *Without RAG:* generic advice (Jira/Trello)
  - *With RAG:* ссылкует `docs/specs/progress.md` и описывает трекер эпиков
- **`mcp_002`**
  - *Without RAG:* подробные шаги получения дайджеста
  - *With RAG:* "В предоставленных документах информация не найдена" (контекст не попал в prompt)
- **`lect_004`**
  - *Without RAG:* общий обзор Spark RDD/DataFrame
  - *With RAG:* структурирует ответ по chunk'ам (RDD → DataFrame, use cases, cache)

## 5. Failure Analysis
- **RAG "контекст не найден"** — указывает на необходимость расширить набор chunk'ов или улучшить prompt инструкцию, особенно для вопросов из лекций, где слово "контекст" неясное.
- **Редкий 400 Bad Request** — вероятно, превышение лимитов (слишком длинное сообщение с chunk'ами). Стоит ограничить `max_context_tokens` или добавить контроль суммарной длины chunk'ов.
- **Производительность** — ответ RAG может занимать ~8 секунд; для демки приемлемо, но в будущем пригодятся async/pooling.

## 6. Recommendations
1. **Промпт/Chunk tuning**
   - Явно прописать, что если chunk'и пустые, нужно отвечать fallback'ом с объяснением.
   - Настроить фильтрацию chunk'ов для lecture-вопросов, чтобы ответы не уходили в "не найдено".
2. **Контроль длины**
   - Trim chunk'и (напр., первые 3–4) или переформатировать prompt, чтобы избежать 400.
3. **Manual evaluation**
   - Подтвердить лейблы (особенно borderline cases `mcp_002`, `lect_001`, `lect_003`).
4. **Demo**
   - В Demo показать контраст (`arch_002`, `mcp_002`) для выделения сильных/слабых сторон.

## 7. Next Steps
- Пересмотреть heuristic labels вручную
- Дополнить отчёт заметками по каждой категории вопросов
- Записать демо (index check → `rag:compare` для 2–3 запросов → `rag:batch` summary)

*Prepared: 2025-11-11 21:20 UTC · Tech Lead Agent*
