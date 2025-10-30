import asyncio
from typing import Any, Awaitable, Callable, Dict

import pytest

try:
    from aiogram.types import TelegramObject
except Exception:
    pytest.skip("aiogram is required for middleware tests", allow_module_level=True)

from src.presentation.bot.middleware.state_middleware import StatePersistenceMiddleware


class DummyEvent(TelegramObject):
    pass


@pytest.mark.asyncio
async def test_state_middleware_pass_through() -> None:
    """Middleware should invoke next handler and return its result."""

    called: Dict[str, Any] = {"hit": False}

    async def handler(evt: TelegramObject, data: Dict[str, Any]) -> str:  # type: ignore[override]
        called["hit"] = True
        # ensure data is the same mapping object
        assert data.get("foo") == "bar"
        return "ok"

    mw = StatePersistenceMiddleware()
    event = DummyEvent(event_id="1")
    data: Dict[str, Any] = {"foo": "bar"}

    result = await mw(handler, event, data)

    assert called["hit"] is True
    assert result == "ok"
