"""Dialog DTOs for Butler conversational flows."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class DialogMode(Enum):
    """High-level Butler dialog modes."""

    TASK = "task"
    DATA = "data"
    HOMEWORK_REVIEW = "homework_review"
    IDLE = "idle"


class DialogState(Enum):
    """Fine-grained Butler dialog states."""

    IDLE = "idle"
    TASK_CREATE_TITLE = "task_create_title"
    TASK_CREATE_DESC = "task_create_desc"
    TASK_CONFIRM = "task_confirm"
    DATA_COLLECTING = "data_collecting"


@dataclass
class DialogContext:
    """Mutable dialog context shared across handlers."""

    state: DialogState
    user_id: str
    session_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    step_count: int = 0

    def transition_to(self, new_state: DialogState) -> None:
        """Transition to a new dialog state."""
        self.state = new_state
        self.step_count += 1

    def reset(self) -> None:
        """Reset context to initial IDLE state."""
        self.state = DialogState.IDLE
        self.data.clear()
        self.step_count = 0

    def update_data(self, key: str, value: Any) -> None:
        """Persist value in context storage."""
        self.data[key] = value
