# Cluster C Legacy Adapter Analysis

**Date:** 2025-11-17
**Epic:** EP24 — Repository Hygiene & De-Legacy
**Cluster:** C.3 — Legacy Adapter (if needed)

## Purpose

Определить, нужен ли legacy adapter для `ButlerOrchestrator` и `MCPAwareAgent`, и что должно в него войти.

## Current State Analysis

### Production Code Usage ✅

**Все production код использует публичный API:**

1. **`src/presentation/bot/factory.py`** — создает `ButlerOrchestrator` через DI
2. **`src/presentation/bot/butler_bot.py`** — использует `ButlerOrchestrator` через конструктор (DI)
3. **`src/presentation/bot/handlers/butler_handler.py`** — использует `ButlerOrchestrator.handle_user_message()` (публичный метод)

**Вывод:** Production код не использует приватные атрибуты напрямую ✅

### Test Code Usage ⚠️

**Интеграционные тесты (`tests/integration/butler/`):**
- ✅ Все рефакторированы на публичный API (C.2 complete)
- Используют `force_mode`, фикстуры, публичный API

**E2E тесты (`tests/e2e/telegram/test_butler_e2e.py`):**
- ⚠️ Используют приватные атрибуты:
  - `orchestrator.mode_classifier.llm_client.make_request`
  - `orchestrator.task_handler.intent_orchestrator.parse_task_intent`
  - `orchestrator.task_handler.tool_client.call_tool`
  - `orchestrator.data_handler.tool_client.call_tool`
  - `orchestrator.chat_handler.llm_client.make_request`

**Вывод:** E2E тесты нуждаются в рефакторинге (C.5)

## Legacy Adapter Design (If Needed)

### Когда нужен Legacy Adapter?

1. **Если есть внешний код** (не тесты), который использует приватные атрибуты
2. **Если есть старые тесты**, которые сложно рефакторить
3. **Если нужна постепенная миграция** (поэтапный переход)

### Что может войти в Legacy Adapter?

#### Вариант 1: Thin Wrapper (Рекомендуется)

```python
class ButlerOrchestratorLegacyAdapter:
    """Legacy adapter for backward compatibility.

    Purpose:
        Provides public access to internal components for gradual migration.
        Should be removed after all code is migrated to public API.

    Deprecated: Use public API (handle_user_message with force_mode) instead.
    """

    def __init__(self, orchestrator: ButlerOrchestrator):
        """Initialize adapter with orchestrator instance."""
        self._orchestrator = orchestrator

    @property
    def mode_classifier(self) -> ModeClassifier:
        """Get mode classifier (deprecated - use force_mode parameter)."""
        warnings.warn(
            "mode_classifier access is deprecated. Use handle_user_message(force_mode=...) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self._orchestrator._mode_classifier

    @property
    def task_handler(self) -> Handler:
        """Get task handler (deprecated - use public API)."""
        warnings.warn(
            "task_handler access is deprecated. Use handle_user_message(force_mode=DialogMode.TASK) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self._orchestrator._handlers[DialogMode.TASK]

    @property
    def data_handler(self) -> Handler:
        """Get data handler (deprecated - use public API)."""
        warnings.warn(
            "data_handler access is deprecated. Use handle_user_message(force_mode=DialogMode.DATA) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self._orchestrator._handlers[DialogMode.DATA]

    @property
    def chat_handler(self) -> Handler:
        """Get chat handler (deprecated - use public API)."""
        warnings.warn(
            "chat_handler access is deprecated. Use handle_user_message(force_mode=DialogMode.IDLE) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self._orchestrator._handlers[DialogMode.IDLE]

    async def classify_mode(self, message: str) -> DialogMode:
        """Classify message mode (deprecated - use handle_user_message without force_mode)."""
        warnings.warn(
            "classify_mode is deprecated. Use handle_user_message() which classifies internally.",
            DeprecationWarning,
            stacklevel=2
        )
        return await self._orchestrator._mode_classifier.classify(message)
```

#### Вариант 2: Публичные Properties (Не рекомендуется)

Добавить публичные properties в сам `ButlerOrchestrator`:

```python
@property
def mode_classifier(self) -> ModeClassifier:
    """Get mode classifier (deprecated - use force_mode parameter)."""
    warnings.warn("Use handle_user_message(force_mode=...) instead.", DeprecationWarning)
    return self._mode_classifier
```

**Проблема:** Размывает границы публичного API, усложняет поддержку.

### Для MCPAwareAgent

Аналогично, если нужен доступ к внутренним компонентам:

```python
class MCPAwareAgentLegacyAdapter:
    """Legacy adapter for MCPAwareAgent backward compatibility."""

    def __init__(self, agent: MCPAwareAgent):
        self._agent = agent

    @property
    def tool_trace(self) -> List[ToolCall]:
        """Get tool execution trace (deprecated)."""
        warnings.warn("Use handle_message() which returns AgentResponse with trace.", DeprecationWarning)
        return self._agent._tool_trace
```

## Recommendation

### ❌ Legacy Adapter НЕ НУЖЕН

**Причины:**

1. **Production код уже использует публичный API** — нет внешних зависимостей от приватных атрибутов
2. **E2E тесты можно рефакторить** — применить тот же паттерн, что и для интеграционных тестов:
   - Использовать `force_mode` вместо мокирования `mode_classifier.classify()`
   - Мокировать handlers через фикстуры
   - Проверять поведение через публичный API
3. **Проще рефакторить тесты**, чем поддерживать adapter:
   - Адаптер добавляет сложность и технический долг
   - Тесты уже рефакторились успешно (13 тестов в C.2)
   - E2E тесты используют тот же паттерн, что и интеграционные

### План действий

**C.3: Legacy Adapter — SKIP**

- ✅ **Status:** NOT NEEDED
- ✅ **Rationale:** Production код использует публичный API, тесты можно рефакторить
- ✅ **Action:** Рефакторить E2E тесты в C.5 вместо создания adapter

**C.5: Verify Butler/MCP tests use public interfaces**

- Рефакторить `tests/e2e/telegram/test_butler_e2e.py` (8 тестов)
- Рефакторить `tests/e2e/butler/test_channel_operations.py` (если использует приватные атрибуты)
- Применить тот же паттерн: `force_mode`, фикстуры, публичный API

## Alternative: Если все-таки нужен Adapter

Если в процессе рефакторинга E2E тестов обнаружатся случаи, когда adapter действительно нужен (например, сложная логика, которую нельзя выразить через публичный API), то:

1. **Создать минимальный adapter** только для необходимых случаев
2. **Добавить deprecation warnings**
3. **Задокументировать план удаления** adapter после миграции
4. **Ограничить scope** — только для критических E2E тестов

## Conclusion

**Legacy adapter не нужен** для текущего состояния кодовой базы. Все использование можно мигрировать на публичный API. Рекомендуется пропустить C.3 и продолжить с C.5 (рефакторинг E2E тестов).
