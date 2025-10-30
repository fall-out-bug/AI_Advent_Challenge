import asyncio
import types
import pytest

try:
    from aiogram.types import CallbackQuery, Message, User, Chat
except Exception:
    pytest.skip("aiogram is required for menu tests", allow_module_level=True)

import src.presentation.bot.handlers.menu as menu_mod


class FakeMessage:
    def __init__(self) -> None:
        self.sent: list[str] = []

    async def answer(self, text: str) -> None:
        self.sent.append(text)


class FakeCall:
    def __init__(self, user_id: int) -> None:
        self.from_user = types.SimpleNamespace(id=user_id)
        self.message = FakeMessage()

    async def answer(self) -> None:  # noqa: D401 Dummy ack
        return None


@pytest.mark.asyncio
async def test_callback_summary_calls_mcp_and_replies(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        async def call_tool(self, tool_name: str, arguments: dict) -> dict:
            assert tool_name == "get_summary"
            assert isinstance(arguments.get("user_id"), int)
            return {"stats": {"total": 3, "completed": 1, "overdue": 1, "high_priority": 1}}

    monkeypatch.setattr(menu_mod, "MCPClient", lambda: FakeClient())

    call = FakeCall(user_id=123)
    await menu_mod.callback_summary(call)
    assert any("Summary" in s for s in call.message.sent)


@pytest.mark.asyncio
async def test_callback_digest_calls_mcp_and_replies(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        async def call_tool(self, tool_name: str, arguments: dict) -> dict:
            assert tool_name == "get_channel_digest"
            return {"digests": [{"channel": "news", "summary": "top story"}]}

    monkeypatch.setattr(menu_mod, "MCPClient", lambda: FakeClient())

    call = FakeCall(user_id=123)
    await menu_mod.callback_digest(call)
    assert any("📰" in s for s in call.message.sent)
