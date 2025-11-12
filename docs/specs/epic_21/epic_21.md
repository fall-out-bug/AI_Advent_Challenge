# Epic 21 · Summary

## Goals
- Выровнять кодовую базу под требования `.cursor/rules/cursorrules-unified.md`, `architecture.md`, `specs.md` и `operations.md`.
- Изолировать доменную логику от инфраструктуры, устранив прямые зависимости и технический долг (длинные функции, отсутствие типов, хаотичный I/O).
- Восстановить доверие к качественным гейтам: линтеры, тесты, безопасность, мониторинг.

## Принятые архитектурные решения
- Sequential rollout подэтапов Stage 21_01 с feature-flag контролем: `DialogContextRepository`, `HomeworkReviewService`, `ReviewArchiveStorage`, декомпозиция `ReviewSubmissionUseCase`.
- Ручной DI с протоколами в доменном слое и адаптерами в инфраструктуре; миграции с возможностью отката.
- Стандарт документирования Option B, staged pre-commit (быстрые хуки авто, тяжёлые manual/CI), единая система pytest-маркеров.
- Единый пакет метрик/лейблов для Prometheus, обновлённые алерты и дашборды, обязательные SLO (dialog p95 < 100 мс, review p95 < 30 с).

## Работы и их реализация
- Подготовка (Stage 21_00): базовые метрики, characterization-тесты, DI scaffolding, rollback скрипты, тренинги команды.
- Stage 21_01: внедрение интерфейсов и адаптеров, перенос логики в новые сервисы, покрытие тестами до/после каждого шага.
- Stage 21_02: массовое обновление docstring’ов и типизации, функция ≤15 строк, pre-commit и CI parity, обновлённый CONTRIBUTING.
- Stage 21_03: расширенные тесты для storage/log pipeline, security guardrails (checksum, AV hook), наблюдаемость и runbooks.
- Все изменения развернуты по feature flag’ам, прошли регресcию и удержали заявленные SLO; результаты задокументированы в финальном отчёте.
