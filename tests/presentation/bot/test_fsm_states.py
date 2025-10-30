import pytest

try:
    from aiogram.fsm.state import State
    from aiogram.fsm.state import StatesGroup
except Exception as exc:  # pragma: no cover
    pytest.skip("aiogram is required for FSM tests", allow_module_level=True)

from src.presentation.bot.states import TaskCreation


def test_task_creation_states_exist() -> None:
    """Ensure TaskCreation FSM has required states with correct types."""
    assert hasattr(TaskCreation, "waiting_for_task")
    assert hasattr(TaskCreation, "waiting_for_clarification")

    assert isinstance(TaskCreation.waiting_for_task, State)
    assert isinstance(TaskCreation.waiting_for_clarification, State)


def test_task_creation_state_names_are_readable() -> None:
    """State names should be explicit and stable for persistence."""
    assert TaskCreation.waiting_for_task.state == "TaskCreation:waiting_for_task"
    assert (
        TaskCreation.waiting_for_clarification.state
        == "TaskCreation:waiting_for_clarification"
    )
