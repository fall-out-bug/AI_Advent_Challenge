# Обзор документации (RU)

Репозиторий поддерживает двуязычную структуру документации. Данный индекс
помогает быстро находить актуальные материалы.

## 1. Спецификации (основной источник)

| Путь | Описание |
|------|----------|
| `docs/specs/epic_00/` | Артефакты аудита (Эпик 0) |
| `docs/specs/epic_04/` | План архивации, лог миграции, финализация Эпика 04 |
| `docs/specs/epic_06/` | Гигиена репозитория (текущий эпик) |
| `docs/specs/architecture.md` | Целевая архитектура |
| `docs/specs/operations.md` | Инфраструктура и runbook'и |
| `docs/specs/specs.md` | Сводная системная спецификация |
| `docs/specs/progress.md` | Трекер эпиков и стадий |

## 2. API и CLI (EN/RU пары)

| EN | RU | Тематика |
|----|----|----------|
| `docs/reference/en/API_REVIEWER.md` | `docs/reference/ru/API_REVIEWER.ru.md` | Модульный ревьюер и MCP-инструмент |
| `docs/reference/en/API_MCP.md` | `docs/reference/ru/API_MCP.ru.md` | Доступные MCP-инструменты (каналы, дайджесты, NLP) |
| `docs/reference/en/API_BOT_BACKOFFICE.md` | `docs/reference/ru/API_BOT_BACKOFFICE.ru.md` | Команды CLI backoffice |
| `docs/reference/en/API_DOCUMENTATION.md` | — | Общий API/CLI обзор (только EN) |

Планируемые пары:

- `guides/en/USER_GUIDE.md` / `guides/ru/AGENT_INTEGRATION.ru.md`
- `guides/en/DEVELOPMENT.md` / _(перевод в планах)_
- Новые гайды в рамках Stage 00_02.

## 3. Руководства и операции

| Путь | Примечания |
|------|------------|
| `docs/guides/en/USER_GUIDE.md` | Настройка окружения, бенчмарки |
| `docs/guides/en/DEVELOPMENT.md` | Dev-контейнер и рабочий процесс |
| `docs/guides/en/TROUBLESHOOTING.md` | Решение частых проблем (Mongo, LLM, Prometheus) |
| `docs/guides/en/shared_infra_cutover.md` | Описание внешней инфраструктуры |
| `docs/MAINTAINERS_GUIDE.md` | Плейбук мейнтейнеров, CI-гейты, автоматизация (EN + краткое резюме RU) |
| `docs/reference/en/PERFORMANCE_BENCHMARKS.md` | Последние метрики ревьюера |
| `docs/guides/en/MODULAR_REVIEWER_INTEGRATION_GUIDE.md` | Интеграция пакета в сторонние проекты |
| `docs/guides/en/observability_operations_guide.md` | Операционные процедуры по наблюдаемости |
| `scripts/ci/bootstrap_shared_infra.py` | CI/локальный бутстрап одноразовой инфраструктуры (парный cleanup-скрипт) |
| `scripts/infra/start_shared_infra.sh` | Скрипт запуска общей инфраструктуры (исполняется из корня репо) |

## 4. Легаси / Архив

- `docs/archive/` — исторические day-спецификации (Day 11, Day 12 и т.д.).
- `docs/reference/en/API_MCP_TOOLS.md`, `docs/reference/en/API.md` — старые версии API-доков (останутся до завершения миграции).

## 5. Политика локализации

- Спецификации ведутся на английском; пользовательские тексты (бот, CLI) локализуются на русский.
- API/CLI-материалы поддерживаются в виде пар EN/RU; изменения вносятся синхронно.
- При добавлении новых гайдов создавайте обе версии или фиксируйте задачу на перевод в Stage 00_02.
