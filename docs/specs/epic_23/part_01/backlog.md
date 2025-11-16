# Epic 23 Backlog · Benchmark Data Seeding

## Context
Live benchmark runs for Stage 05 require fresh datasets populated in shared
Mongo collections (`digests`, `review_reports`). Current environment does not
contain the expected artefacts, so automation halts at export stage.

### Architect Confirmations (2025-11-15)
- Product owner provides **exactly five RU Telegram channels**; scope limited to
  observability & benchmark enablement (payment examples removed).
- Collect posts for the **latest 30 calendar days** per channel.
- **Minimum dataset requirement:** ≥30 daily digests (or equivalent exporter
  records) per channel; use this floor for validation thresholds.
- Continue storing data as MongoDB JSON documents; reference exporter outputs
  (`scripts/quality/analysis/export_digests.py`,
  `scripts/quality/analysis/export_review_reports.py`) instead of duplicating
  schemas in specs.
- Stack runs on a single Ryzen 5800 / 128 GB RAM / RTX 3070 Ti host; DR drill is
  explicitly out of scope for Epic 23.
- RAG++ feature flag remains owner-only; document the limitation in Analyst and
  downstream packages.

## Tasks
1. **Seed digest samples for benchmarking**
   - Populate `butler.digests` with RU channel digest documents (24h/7d
     coverage).
   - Ensure each entry contains summary, raw posts, feature flags, latency.
   - **Validation:** each of the five channels must have ≥30 daily digests
     covering the last 30 calendar days (fail task if any channel <30 records).
   - Owner: Data services.

2. **Seed reviewer report samples**
   - Populate `butler.review_reports` with modular reviewer outputs (passes,
     synthesis, metadata).
   - Include judge scores / latency for baseline comparisons.
   - Reuse the exporter structure documented in
     `scripts/quality/analysis/export_review_reports.py` (schema reference).

3. **Verify exporters**
   - Re-run `scripts/quality/analysis/export_digests.py` and
     `scripts/quality/analysis/export_review_reports.py` against populated DB.
   - Confirm JSONL samples match Stage 05 schema.
   - Capture validation link to sample outputs instead of duplicating schema
     snippets in docs.

4. **Trigger live benchmarks**
   - Execute `scripts/benchmark/run_benchmark.py --scenario channel_digest_ru`
     without `--dry-run` and capture metrics.
   - Update `docs/reference/en/PERFORMANCE_BENCHMARKS.md` with live results and adjust
     thresholds if necessary.
5. **Run Stage 05_03 Pilot**
   - Once datasets are seeded, execute fine-tuning pilot per
     `docs/specs/epic_05/stage_05_03_runbook.md`.
   - Record evaluation results and complete governance sign-off.
   - **Acceptance tests (owner)**:
     - `scripts/quality/analysis/export_digests.py --output sample.jsonl`
       produces 30+ entries per channel with RU content.
     - `scripts/quality/benchmark/run_benchmark.py --scenario channel_digest_ru`
       completes on target hardware without exceeding latency threshold.
     - Manual spot-check: digest Markdown contains localized headings, latency
       field present, and feature flags match exporter reference.
6. **Complete RU localisation review for MCP/Bot docs**
   - Review RU copy updates introduced in Stage 02_03; ensure Telegram flows,
     CLI backoffice docs, and README.ru reflect final scope.
7. **Purge legacy assets from deployment artefacts**
   - Confirm container images / deployment bundles no longer include archived
     reminder/task modules; update automation scripts if needed.
8. **Automate shared infra bring-up for CI**
   - Implement scripts/workflow that start Mongo/Prometheus/LLM services with
     `.env.infra` credentials and integrate into GitHub Actions.
9. **Grafana IaC & Loki alert extensions**
   - Codify dashboards introduced in EP03 via IaC; expand Loki alert rules per
     Stage 03_03 follow-up and validate via CI observability checks.
10. **Schedule and document DR drill**
    - Plan the first disaster recovery drill for the observability stack, run it,
      and store outcomes in operations docs.
11. **Expand backoffice CLI integration coverage**
    - Add tests covering digest export, channels refresh, and error handling to
      replace archived MCP E2E flows.
12. **Нормализовать линтеры для `shared/tests`**
    - Убрать предупреждения `E501/W293/F401` в модуле `shared/tests`.
    - Актуализировать фикстуры/утилиты, чтобы pre-commit проходил без
      массового автоформатирования.
13. **Привести YAML/JSON к валидному виду**
    - Исправить `config/mcp_config.yaml`, `archive/docker-compose/docker-compose.yml`
      и `tests/e2e/telegram/fixtures/test_messages.json`, чтобы pre-commit
      `check-yaml`/`check-json` проходил без ошибок.
14. **Оптимизировать большие JSONL артефакты**
    - Сжать или перенести `results_stage20.jsonl` и `results_with_labels.jsonl`
      под лимит 500 KB (использовать сжатие, разбивку на части или синтетические
      выборки) и документировать процесс.
15. **Перенести устаревшие асинхронные тесты в Stage 21 refactor backlog**
    - Зафиксировать пакеты, использующие `LegacyDialogContextAdapter`, старый DI-контейнер
      и инфраструктурные фикстуры (Airflow, MCP, post-fetcher).
    - Подготовить план восстановления/архивации в рамках Epic 23.
16. **RAG++ расширения из Epic 21**
    - Документировать и внедрить стратегию регулярного тюнинга промптов для LLM-reranker (скрипты + гайд).
    - Добавить поддержку `seed` и контроль воспроизводимости для LLM-клиентов/конфигурации.
    - Расширить метрики: измерение межзапусковой вариации (cross-run variance) и аналитика.
    - Исследовать/реализовать адаптивные пороги (learned thresholds) после аблаций Stage 21_04.
    - Проработать постепенный rollout (canary percentage) для feature flag `rag_plus_plus`.

## Dependencies
- Shared infra credentials (`.env.infra`)
- Access to production-like data dumps or synthetic generator

## Done When
- Export scripts produce non-empty datasets.
- Live benchmark run completes with metrics stored in Prometheus.
- Stage 05 performance scoreboard updated with real measurements.
