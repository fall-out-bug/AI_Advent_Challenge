# Architecture Feedback · 2025-11-11

## Overview
Принял документы Stage 21 — структура и детализация заметно улучшились. Ниже — замечания и вопросы, которые предлагаю обсудить до передачи плана в разработку.

## Findings & Questions

1. **Дублирование задач между стадиями**
   - В плане архитектурных работ Stage 21_01 фигурирует пункт про обновление докстрингов, хотя для этого уже есть отдельная программа в Stage 21_02.
   
```44:51:docs/specs/epic_21/stage_21_01.md
| ARCH-21-05 | Medium | Update docstring templates in domain/application modules to match required format | Doc lead | After module moves |
```
   
   **Вопрос:** переносим `ARCH-21-05` в Stage 21_02 (например, объединяем с `DOC-21-02-02`), или оставляем архитектурной команде частичную ответственность за шаблоны?

2. **Описание интерфейсов: конкретика по возвращаемым типам**
   - В дизайне `ReviewArchiveStorage` упомянут `StoredArtifact`, но нет определения структуры и требований к полям.
   - Приёмы `save_*` принимают полностью загруженные `bytes`, что может стать проблемой для больших архивов.
   
```41:54:docs/specs/epic_21/stage_21_01_interface_design.md
- **Interface Name**: `ReviewArchiveStorage`
...
  - `async def save_new(..., data: bytes) -> StoredArtifact`
```
   
   **Предложение:** описать `StoredArtifact` (например, dataclass с путём, размером, checksum) и добавить сценарий потоковой записи (пригодится для 100+ МБ архивов).

3. **Docstring Template: уточнить правила для edge-кейсов**
   - План Stage 21_02 требует раздел `Raises` всегда, но часть функций исключений не выбрасывает.
   - Нужен ответ на вопрос, что писать в `Example`, если функция чисто внутреннего использования.
   
```7:32:docs/specs/epic_21/stage_21_02_docstring_plan.md
- Adopt the docstring structure...
```
   
   **Вопрос:** допускаем ли «`Raises:` None»/опускаем секцию? Стоит описать в FAQ, чтобы избежать разночтений.

4. **Pre-commit нагрузка**
   - Подключение `mypy`, `bandit`, `markdownlint` на каждый коммит может серьёзно замедлить цикл.
   
```20:51:docs/specs/epic_21/stage_21_02_tooling_rollout.md
repos:
  - repo: https://github.com/pre-commit/mirrors-mypy
...
  - repo: https://github.com/PyCQA/bandit
```
   
   **Вопрос:** запускаем все хуки по умолчанию или добавим `manual: true` для тяжёлых, оставив автомат только для Black/isort/flake8? Я бы предложил staged rollout: обязательные быстрые хуки, а тяжёлые — как `pre-commit run --hook-stage manual`.

5. **Маркировка тестов**
   - Тестовая матрица Stage 21_03 использует маркер `pytest -m "storage or logs"`, но в репозитории таких меток пока нет.
   
```6:33:docs/specs/epic_21/stage_21_03_test_matrix.md
| Review archive storage service | ... | Unit tests for size/checksum validation |
...
1. Extend CI to run new unit/integration suites with `pytest -m "storage or logs"` markers.
```
   
   **Предложение:** заранее зафиксировать имена маркеров в `pytest.ini`, чтобы не расходиться между командами.

6. **Метрики и алерты**
   - Новые метрики для storage/pass4 потенциально пересекаются с существующими, нужно убедиться, что названия уникальны и соответствуют текущему namespace Prometheus.
   - Отлично, что есть чек-лист, но стоит добавить требование описать две вещи: где именно будут экспонироваться метрики (FastAPI endpoint? worker process?) и какие теги (labels) обязательны.
   
```8:37:docs/specs/epic_21/stage_21_03_observability_plan.md
- `review_storage_write_seconds` (histogram)
...
- Provide annotations for deployment windows
```
   
   **Вопрос:** какие label’ы хотим видеть (например, `backend="local_fs"` / `backend="s3"`)? Без этого риск получить несопоставимые метрики.

## Дополнительные рекомендации
- Зафиксировать, что техлид принимает критику и уточнения (это уже отражено в ролях — спасибо).
- Для интерфейсов добавить два примера использования (domain → application → infrastructure), можно коротко, чтобы аналитика и архитекторы видели целевую цепочку зависимостей.
- Подумать о шаблоне миграционных заметок: в Stage 21_01 упоминается, но нет места, куда их складывать; можно завести `docs/specs/epic_21/migrations/`.

Готов обсудить и скорректировать планы после ваших ответов.


