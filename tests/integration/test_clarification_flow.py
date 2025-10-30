import pytest
import types

try:
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.types import Message
except Exception:
    pytest.skip("aiogram is required for integration tests", allow_module_level=True)

from src.presentation.bot.states import TaskCreation
from src.application.orchestration.intent_orchestrator import IntentOrchestrator
from src.domain.entities.intent import IntentParseResult
import src.presentation.bot.handlers.tasks as tasks_mod


class FakeStorage:
    def __init__(self) -> None:
        self.data: dict = {}

    async def set_state(self, key, state) -> None:
        self.data[f"{key}_state"] = state

    async def update_data(self, key, data) -> None:
        if key not in self.data:
            self.data[key] = {}
        self.data[key].update(data)

    async def get_data(self, key) -> dict:
        return self.data.get(key, {})

    async def clear(self, key) -> None:
        self.data.pop(key, None)


class FakeState:
    def __init__(self, storage: FakeStorage, user_id: int) -> None:
        self.storage = storage
        self.key = (user_id, 1)
        self.data: dict = {}

    async def set_state(self, state) -> None:
        await self.storage.set_state(self.key, state)

    async def update_data(self, **kwargs) -> None:
        self.data.update(kwargs)
        await self.storage.update_data(self.key, self.data)

    async def get_data(self) -> dict:
        return dict(self.data)

    async def clear(self) -> None:
        self.data = {}
        await self.storage.clear(self.key)


class FakeMessage:
    def __init__(self, text: str, user_id: int = 1) -> None:
        self.text = text
        self.chat = types.SimpleNamespace(id=1)
        self.from_user = types.SimpleNamespace(id=user_id)
        self.bot = types.SimpleNamespace(send_chat_action=lambda *args, **kwargs: None)
        self.sent: list[str] = []

    async def answer(self, text: str) -> None:
        self.sent.append(text)


@pytest.mark.asyncio
async def test_clarification_flow_moves_states_correctly() -> None:
    """Full flow: user input → intent parsing → clarifying questions → task creation."""
    storage = FakeStorage()
    state = FakeState(storage, user_id=123)
    msg = FakeMessage("Remind me to call mom")

    # Simulate orchestrator detecting need for clarification
    original_parse = IntentOrchestrator.parse_task_intent

    def mock_parse(self, text: str, context: dict) -> IntentParseResult:
        if "clarification" in context.get("_pending", []):
            return IntentParseResult(
                title="Call mom",
                deadline_iso="2025-12-01T15:00:00",
                priority="medium",
                needs_clarification=False,
                questions=[],
            )
        return IntentParseResult(
            title="Call mom",
            deadline_iso=None,
            priority="medium",
            needs_clarification=True,
            questions=["When is the deadline?"],
        )

    import unittest.mock
    with unittest.mock.patch.object(IntentOrchestrator, "parse_task_intent", mock_parse):
        # First message: needs clarification
        await tasks_mod.handle_task_input(msg, state)  # type: ignore[arg-type]
        assert state.storage.data.get(f"{state.key}_state") == TaskCreation.waiting_for_clarification
        assert any("deadline" in s.lower() for s in msg.sent)

        # Second message: provides clarification
        msg2 = FakeMessage("2025-12-01 15:00", user_id=123)
        state2 = FakeState(storage, user_id=123)
        state2.data = state.data  # Restore context
        await state2.update_data(_pending=["clarification"])

        await tasks_mod.handle_clarification(msg2, state2)  # type: ignore[arg-type]
        assert state2.data == {}  # cleared
        assert any("✅ Task added" in s for s in msg2.sent)


@pytest.mark.asyncio
async def test_bot_mcp_integration_with_mocked_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bot handlers calling MCP tools with error handling."""
    import src.presentation.bot.handlers.menu as menu_mod

    call_count = {"count": 0}

    class FakeClient:
        async def call_tool(self, tool_name: str, arguments: dict) -> dict:
            call_count["count"] += 1
            if tool_name == "get_summary":
                return {
                    "stats": {"total": 3, "completed": 1, "overdue": 1, "high_priority": 1},
                    "tasks": [],
                }
            return {}

    monkeypatch.setattr(menu_mod, "MCPClient", FakeClient)

    async def fake_answer(msg_text: str = "") -> None:
        pass

    call = types.SimpleNamespace(
        from_user=types.SimpleNamespace(id=123),
        message=types.SimpleNamespace(answer=fake_answer),
        answer=fake_answer,
    )

    await menu_mod.callback_summary(call)  # type: ignore[arg-type]

    assert call_count["count"] == 1

