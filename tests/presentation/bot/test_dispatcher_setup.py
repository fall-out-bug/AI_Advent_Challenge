import pytest

try:
    from aiogram import Dispatcher
    from aiogram.fsm.storage.memory import MemoryStorage
except Exception:
    pytest.skip("aiogram is required for dispatcher tests", allow_module_level=True)

from src.presentation.bot.butler_bot import create_dispatcher
from src.presentation.bot.middleware.state_middleware import StatePersistenceMiddleware


def test_create_dispatcher_registers_storage_and_middleware() -> None:
    """create_dispatcher should attach MemoryStorage and register StatePersistenceMiddleware."""
    dp = create_dispatcher()

    assert isinstance(dp, Dispatcher)
    assert isinstance(dp.storage, MemoryStorage)

    manager = dp.update.outer_middleware
    assert hasattr(manager, "_middlewares")
    assert any(isinstance(m, StatePersistenceMiddleware) for m in manager._middlewares)
