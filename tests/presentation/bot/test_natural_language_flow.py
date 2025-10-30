import types
import pytest

try:
    from aiogram.fsm.context import FSMContext
    from aiogram.types import Message
except Exception:
    pytest.skip("aiogram is required for NL flow tests", allow_module_level=True)

import src.presentation.bot.handlers.tasks as tasks_mod
from src.domain.entities.intent import IntentParseResult
from src.presentation.bot.states import TaskCreation


class FakeState:
    def __init__(self) -> None:
        self.state = None
        self.data = {}

    async def set_state(self, s) -> None:  # noqa: D401
        self.state = s

    async def update_data(self, **kwargs) -> None:
        self.data.update(kwargs)

    async def get_data(self):
        return dict(self.data)

    async def clear(self) -> None:
        self.state = None
        self.data = {}


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
async def test_nl_flow_clear_intent(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeOrch:
        def parse_task_intent(self, text: str, context: dict) -> IntentParseResult:
            return IntentParseResult(
                title="Buy milk",
                description=None,
                deadline_iso="2025-12-01T10:00:00",
                priority="high",
                tags=[],
                needs_clarification=False,
                questions=[],
            )

    monkeypatch.setattr(tasks_mod, "IntentOrchestrator", FakeOrch)

    state = FakeState()
    msg = FakeMessage(text="Buy milk tomorrow at 10 high")

    await tasks_mod.handle_task_input(msg, state)  # type: ignore[arg-type]

    assert state.state is None  # cleared on completion
    assert any("✅ Task added" in s for s in msg.sent)


@pytest.mark.asyncio
async def test_nl_flow_needs_clarification(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeOrch:
        def parse_task_intent(self, text: str, context: dict) -> IntentParseResult:
            return IntentParseResult(
                title="Call mom",
                description=None,
                deadline_iso=None,
                priority="medium",
                tags=[],
                needs_clarification=True,
                questions=["When is the deadline?"],
            )

    monkeypatch.setattr(tasks_mod, "IntentOrchestrator", FakeOrch)

    state = FakeState()
    msg = FakeMessage(text="Remind me to call mom")

    await tasks_mod.handle_task_input(msg, state)  # type: ignore[arg-type]

    assert state.state == TaskCreation.waiting_for_clarification
    assert any("When is the deadline?" in s for s in msg.sent)


@pytest.mark.asyncio
async def test_nl_flow_error_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeOrch:
        def parse_task_intent(self, text: str, context: dict) -> IntentParseResult:
            raise RuntimeError("LLM unavailable")

    monkeypatch.setattr(tasks_mod, "IntentOrchestrator", FakeOrch)

    state = FakeState()
    msg = FakeMessage(text="Create task")

    await tasks_mod.handle_task_input(msg, state)  # type: ignore[arg-type]

    # State remains asking for task; error message sent
    assert state.state == TaskCreation.waiting_for_task
    assert any("temporarily unavailable" in s.lower() for s in msg.sent)
