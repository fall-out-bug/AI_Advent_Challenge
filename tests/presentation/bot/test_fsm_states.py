import pytest

try:
    from aiogram.fsm.state import State
    from aiogram.fsm.state import StatesGroup
except Exception as exc:  # pragma: no cover
    pytest.skip("aiogram is required for FSM tests", allow_module_level=True)

from types import ModuleType

from src.presentation.bot import states as bot_states


def test_task_creation_states_removed() -> None:
    """Task creation state machine must be removed in Stage 02_03 scope."""
    assert isinstance(bot_states, ModuleType)
    assert not hasattr(bot_states, "TaskCreation")
