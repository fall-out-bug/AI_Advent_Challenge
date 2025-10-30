import pytest
import types

try:
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage
except Exception:
    pytest.skip("aiogram is required for E2E tests", allow_module_level=True)

from src.presentation.bot.states import TaskCreation
from src.application.orchestration.intent_orchestrator import IntentOrchestrator
import src.presentation.bot.handlers.tasks as tasks_mod


class FakeMessage:
    def __init__(self, text: str, user_id: int = 1) -> None:
        self.text = text
        self.chat = types.SimpleNamespace(id=1)
        self.from_user = types.SimpleNamespace(id=user_id)
        self.bot = types.SimpleNamespace(send_chat_action=lambda *args, **kwargs: None)
        self.sent: list[str] = []

    async def answer(self, text: str) -> None:
        self.sent.append(text)


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


@pytest.mark.asyncio
async def test_task_creation_journey_with_complete_intent() -> None:
    """E2E: User sends task → Bot parses → Confirms creation."""
    state = FakeState()
    msg = FakeMessage("Call mom on 2025-12-01 15:00 high")

    await tasks_mod.handle_task_input(msg, state)  # type: ignore[arg-type]

    # Bot should confirm task creation
    assert any("✅ Task added" in s for s in msg.sent)
    assert state.state is None  # cleared after completion


@pytest.mark.asyncio
async def test_task_creation_journey_with_clarification() -> None:
    """E2E: User sends incomplete task → Bot asks → User answers → Task created."""
    orchestrator = IntentOrchestrator()

    # First message: ambiguous
    state1 = FakeState()
    msg1 = FakeMessage("Remind me to call mom")
    result1 = orchestrator.parse_task_intent(msg1.text or "", {})
    
    if result1.needs_clarification:
        await tasks_mod.handle_task_input(msg1, state1)  # type: ignore[arg-type]
        assert state1.state == TaskCreation.waiting_for_clarification
        assert any("deadline" in s.lower() or "when" in s.lower() for s in msg1.sent)

        # Second message: provides clarification
        state2 = FakeState()
        state2.data = state1.data  # Restore context
        msg2 = FakeMessage("2025-12-01 15:00")
        await tasks_mod.handle_clarification(msg2, state2)  # type: ignore[arg-type]
        assert any("✅ Task added" in s for s in msg2.sent)

