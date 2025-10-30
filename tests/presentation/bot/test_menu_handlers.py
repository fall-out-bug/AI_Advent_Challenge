import pytest

try:
    from aiogram import Router
    from aiogram.filters import Command
    from aiogram.types import CallbackQuery
except Exception:
    pytest.skip("aiogram is required for menu tests", allow_module_level=True)

from src.presentation.bot.handlers.menu import menu_router


def test_menu_router_is_router_instance() -> None:
    assert isinstance(menu_router, Router)


def test_menu_router_has_callbacks_registered() -> None:
    # ensure there are callback_query handlers
    cq_handlers = menu_router.callback_query.handlers
    assert any(callable(h.callback) for h in cq_handlers)
