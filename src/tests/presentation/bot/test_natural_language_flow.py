from typing import Any, List

import pytest


@pytest.mark.asyncio
async def test_handle_any_message_routes_to_orchestrator():
    from aiogram.types import User

    from src.presentation.bot.handlers.butler_handler import (
        handle_any_message,
        setup_butler_handler,
    )

    class StubOrchestrator:
        def __init__(self) -> None:
            self.calls: List[dict[str, Any]] = []

        async def handle_user_message(
            self,
            user_id: str,
            message: str,
            session_id: str,
            force_mode: Any = None,
        ) -> str:
            self.calls.append(
                {
                    "user_id": user_id,
                    "message": message,
                    "session_id": session_id,
                    "force_mode": force_mode,
                }
            )
            return "✅ Task added successfully!"

    orchestrator = StubOrchestrator()
    setup_butler_handler(orchestrator)  # type: ignore[arg-type]

    class DummyMessage:
        def __init__(self) -> None:
            self.text = "создай задачу купить молоко"
            self.from_user = User(id=123, is_bot=False, first_name="Tester")
            self.message_id = 42
            self.sent: List[str] = []

        async def answer(self, text: str, **kwargs: Any) -> None:
            self.sent.append(text)

    msg = DummyMessage()
    await handle_any_message(msg)

    assert orchestrator.calls, "Orchestrator should receive the message"
    assert "✅ Task added" in msg.sent[-1]
