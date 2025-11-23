# AI Advent Challenge · Эра Альфреда

> 28 подряд завершённых дней сложились в Альфреда — единого God Agent’а в Telegram,
> который планирует, исполняет и отчитывается как персональный сотрудник.

## Статус проекта
- ✅ Все 28 ежедневных задач выполнены ([`docs/challenge_days.md`](docs/challenge_days.md))
- ✅ Оркестратор Alfred (эпик 28) в проде
- ✅ Бот-дворецкий (текст + голос) направляет каждое обращение в Alfred
- ✅ Инфраструктура полностью локальная (Mongo, Prometheus, Grafana, Qwen)

## Быстрый запуск
```bash
make install      # зависимости
make day-12-up    # Mongo, Prometheus, Grafana, Qwen
make run-bot      # Telegram Butler → Alfred
```
Детали развёртывания — в [`docs/FINAL_REPORT.md`](docs/FINAL_REPORT.md).

## Куда смотреть
| Документ | Зачем |
|----------|-------|
| [`docs/FINAL_REPORT.md`](docs/FINAL_REPORT.md) | Итог + инструкция по эксплуатации |
| [`docs/specs/epic_28/epic_28.md`](docs/specs/epic_28/epic_28.md) | Архитектура Alfred (роутер, планировщик, навыки) |
| [`docs/specs/epic_28/consensus/`](docs/specs/epic_28/consensus/) | Актуальные артефакты, сообщения и decision log |
| [`docs/roles/consensus_architecture.json`](docs/roles/consensus_architecture.json) + [`docs/roles/*/prompt.json`](docs/roles/) | Контракты и промпты агентов |
| [`docs/operational/shared_infra.md`](docs/operational/shared_infra.md) | Бутстрап общей инфраструктуры и наблюдаемость |

Все прежние гайды, API, справочники перенесены в
[`docs/reference/legacy/library/`](docs/reference/legacy/library/) — история
сохранена, но активный набор документов остаётся компактным.

## Структура репозитория
```
AI_Challenge/
├── src/                # Clean Architecture (domain/application/infrastructure/presentation)
├── docs/
│   ├── FINAL_REPORT.md
│   ├── challenge_days.md
│   ├── specs/epic_28/
│   ├── roles/
│   └── reference/legacy/library/
├── scripts/            # Скрипты для инфры и обслуживания
├── shared/             # Общие клиенты/SDK
└── tasks/, archive/…   # Исторические артефакты
```

## Ключевые вехи
- Персонализация Butler → Alfred (день 25): профили, память, настройка персоны
- Голос → текст (день 24): голосовые сообщения идут в тот же роутер
- Мультипроходный ревьюер, MCP-инструменты, автономный Test Agent (дни 14–26)
- Observability-first (день 23): метрики `god_agent_*`, Grafana/Loki
- Новый консенсус: JSON-инбоксы, компактные промпты, матрица ветo, только EN-выход

Полная хроника — в [`docs/challenge_days.md`](docs/challenge_days.md).

## Если нужен «олдскул»
- MCP-гиды, API, плейбуки деплоя → `docs/reference/legacy/library/`
- Там же лежат туториалы по дням (11–17, 19, 26 и т.д.)

## Полезно знать
- Контекст для AI-ассистентов: [`AI_CONTEXT.md`](AI_CONTEXT.md), [`docs/INDEX.md`](docs/INDEX.md)
- Правила/лицензия: [`CONTRIBUTING.md`](CONTRIBUTING.md), [`LICENSE`](LICENSE)

> «Альфред, мы дома» — финальная реплика
