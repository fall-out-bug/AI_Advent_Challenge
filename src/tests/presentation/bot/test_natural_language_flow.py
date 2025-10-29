import pytest


class DummyMCP:
    async def call_tool(self, name: str, args: dict):  # noqa: D401
        if name == "parse_task_intent":
            return {
                "title": "Buy milk",
                "description": "2L",
                "deadline": None,
                "priority": "medium",
                "tags": [],
                "needs_clarification": False,
                "questions": [],
            }
        if name == "add_task":
            return {"status": "created", "task_id": "t1"}
        return {}


@pytest.mark.asyncio
async def test_bot_handles_nl_and_creates_task(monkeypatch):
    from aiogram.types import User
    from src.presentation.bot.butler_bot import ButlerBot

    bot = ButlerBot(token="TEST_TOKEN")
    # Inject dummy MCP client
    bot._mcp = DummyMCP()  # type: ignore[attr-defined]

    class DummyMessage:
        def __init__(self):
            self.text = "buy milk"
            self.from_user = User(id=1, is_bot=False, first_name="x")
            self.sent = []

        async def answer(self, text: str, **kwargs):
            self.sent.append(text)

    msg = DummyMessage()
    await bot.handle_natural_language(msg)
    assert any("Task added" in s for s in msg.sent)


