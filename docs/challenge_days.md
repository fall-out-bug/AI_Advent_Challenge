# Daily Challenges Overview (Days 1–25)

This document provides a concise bilingual overview of all 25 daily challenges in the AI Advent Challenge project.

## English Summary

| Day | Focus Area | Short Description | Key Docs / Implementation |
|-----|------------|-------------------|---------------------------|
| 1 | Basic chat interface | First LLM chat over HTTP | Legacy day-1 example (now superseded by later architecture) |
| 2 | JSON structured responses | Strict JSON outputs from LLM | DTOs and schema-based responses in application layer |
| 3 | Advisor mode | Multi-turn advisor with session state | Session patterns reused in Butler and reviewer flows |
| 4 | Temperature control | Creative vs deterministic sampling | Temperature patterns used across prompts and evaluators |
| 5 | Local models | Run local LLMs in Docker | Early local stack, now archived in `archive/legacy/local_models/` |
| 6 | Testing framework | Systematic tests & reports | pytest-based quality pipeline, test fixtures and reports |
| 7 | Multi-agent systems | Orchestrating multiple agents | Multi-agent orchestrator and patterns used in reviewer/Butler |
| 8 | Token analysis | Token budgeting and limits | Context compression & token strategies (see analyst day docs) |
| 9 | MCP integration | First MCP server & tools | MCP HTTP server, tool catalogue, basic tool usage |
| 10 | Production MCP system | Production-ready MCP with orchestration, caching, streaming | `tasks/day_10/README.md` + MCP tools and benchmark scripts |
| 11 | Butler Bot FSM | 24/7 Telegram butler with FSM & digests | `tasks/day_11/README.md`, Butler bot, workers, MCP integration |
| 12 | PDF Digest System | PDF digest generation and delivery | Day-12 PDF pipeline (now integrated into Butler stack) |
| 13 | Butler Agent Refactoring | Clean refactor into use cases & phases | `tasks/day_13/` Phases 0–5, modular Butler use cases & tests |
| 14 | Multi-Pass Code Review | Multi-pass homework/code review | Multipass reviewer package, MCP homework review tools |
| 15 | Quality Assessment & Fine-tuning | LLM-as-Judge and fine-tune governance | Benchmarks & fine-tuning flows reused in Epic 23 |
| 16 | External memory | Persistent external memory for sessions/requirements | Mongo-based external memory; see analyst day-16 capability |
| 17 | Code Review Platform & MCP Publishing | Full code review platform with MCP publishing | Day-17 platform, contracts, static analysis & log diagnostics |
| 18 | Foundation Summary (Epics 00–06) | Consolidate early clean-up epics | `docs/specs/epic_18/epic_18.md` |
| 19 | Document Embedding Index | Ingest → chunk → embed → store pipeline | `docs/specs/epic_19/epic_19.md` |
| 20 | RAG vs Non‑RAG Answering Agent | Compare plain LLM vs RAG answers | `docs/specs/epic_20/epic_20.md` |
| 21 | RAG++ Refactor & Clean Architecture | Repository refactor and RAG reranking | `docs/specs/epic_21/epic_21.md` |
| 22 | RAG Citations & Source Attribution | Answers with explicit sources | Analyst day-22 docs + RAG citation tests |
| 23 | Observability & Benchmark Enablement | Metrics, logs, traces, benchmarks | `docs/specs/epic_23/part_01/epic_23_part_01.md`, `epic_23_completion_summary.md` |
| 24 | Voice Commands Integration | Voice→text→command via Whisper STT | `docs/specs/epic_24/README.md`, `epic_24.md`, `epic_closure.md` |
| 25 | Personalised Butler | Profiles, memory, interest-aware persona | `docs/specs/epic_25/README.md`, `EPIC_COMPLETION.md`, `FINAL_REPORT.md` |

---

## Краткое резюме по-русски

| День | Фокус | Краткое описание | Основные документы |
|------|-------|------------------|--------------------|
| 1 | Базовый чат-интерфейс | Первый LLM-чат по HTTP | Легаси-пример (заменён текущей архитектурой) |
| 2 | JSON-структурированные ответы | Строгие JSON-ответы от модели | DTO и схемы в слое application |
| 3 | Режим советника | Многошаговый советник с состоянием сессии | Паттерны сессий, переиспользуемые в Butler и ревьюере |
| 4 | Контроль температуры | Креативные vs детерминированные режимы | Температурные режимы во всех промптах и оценках |
| 5 | Локальные модели | Запуск локальных LLM в Docker | Ранний локальный стек (архив `archive/legacy/local_models/`) |
| 6 | Тестовый фреймворк | Тесты и отчёты | pytest-пайплайн качества и фикстуры |
| 7 | Мультиагентные системы | Оркестрация нескольких агентов | Multi-agent orchestrator, паттерны для ревьюера и Butler |
| 8 | Анализ токенов | Бюджет токенов и лимиты | Стратегии контекстной компрессии (см. day_capabilities аналитика) |
| 9 | Интеграция MCP | Первый MCP-сервер и инструменты | MCP HTTP сервер, каталог инструментов |
| 10 | Production-Ready MCP | Продовый MCP с оркестрацией, кешированием, стримингом | `tasks/day_10/README.md` и MCP-инструменты |
| 11 | Butler Bot FSM | 24/7 Telegram-бот с FSM и дайджестами | `tasks/day_11/README.md`, Butler-бот и воркеры |
| 12 | Система PDF-дайджестов | Генерация и доставка PDF | Дневные спеки Day 12, интегрированы в текущий стек |
| 13 | Рефакторинг Butler Agent | Фазовый рефакторинг на use cases | `tasks/day_13/` (Phases 0–5) |
| 14 | Multi-Pass Code Review | Многопроходное ревью кода/домашек | Multipass reviewer и MCP-инструменты ревью |
| 15 | Оценка качества и файнтюнинг | LLM-as-Judge и процессы файнтюнинга | Бенчмарки и пайплайны, используемые в Epic 23 |
| 16 | Внешняя память | Внешняя память для требований/сессий | Mongo-хранилище; см. Day 16 в `day_capabilities` аналитика |
| 17 | Платформа code review и MCP-публикация | Полноценная платформа ревью | Платформа Day 17, контракты и статический анализ |
| 18 | Сводка Epics 00–06 | Консолидация фундаментальных эпиков | `docs/specs/epic_18/epic_18.md` |
| 19 | Индексация документов | Конвейер эмбеддингов | `docs/specs/epic_19/epic_19.md` |
| 20 | Агент RAG vs Non‑RAG | Сравнение ответов RAG и чистого LLM | `docs/specs/epic_20/epic_20.md` |
| 21 | RAG++ и рефакторинг репозитория | Clean Architecture и reranking | `docs/specs/epic_21/epic_21.md` |
| 22 | RAG‑цитаты и источники | Ответы с обязательными ссылками | Документы по Day 22 для аналитика и RAG |
| 23 | Observability & Benchmarks | Метрики, логи, трейсы, бенчмарки | `docs/specs/epic_23/part_01/epic_23_part_01.md`, `epic_23_completion_summary.md` |
| 24 | Голосовой агент | Голос → текст → команда (Whisper STT) | `docs/specs/epic_24/README.md`, `epic_24.md`, `epic_closure.md` |
| 25 | Персонализированный Butler | Профили, память, интересы, "Alfred-style дворецкий" | `docs/specs/epic_25/README.md`, `EPIC_COMPLETION.md`, `FINAL_REPORT.md` |

---

### Notes

- For detailed implementation notes per day, see the corresponding epic specs and `docs/roles/analyst/day_capabilities.md`.
- This file is the canonical high-level overview of Days 1–25; for status and quick links also see the tables in `README.md` and `README.ru.md`.
