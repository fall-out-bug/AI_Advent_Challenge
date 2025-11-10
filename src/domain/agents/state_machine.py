"""Dialog state machine for Butler Agent.

Following Python Zen:
- Simple is better than complex
- Explicit is better than implicit
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class DialogState(Enum):
    """Dialog state enumeration.

    Represents all possible states in a dialog conversation.
    Following Python Zen: Enum over string literals.
    """

    IDLE = "idle"
    TASK_CREATE_TITLE = "task_create_title"
    TASK_CREATE_DESC = "task_create_desc"
    TASK_CONFIRM = "task_confirm"
    DATA_COLLECTING = "data_collecting"


@dataclass
class DialogContext:
    """Dialog context with explicit state.

    Stores conversation state and data for FSM transitions.
    Following Python Zen: Explicit state over implicit tracking.

    Attributes:
        state: Current dialog state
        data: Dictionary for storing context data
        step_count: Number of steps in current conversation
        user_id: User identifier
        session_id: Session identifier

    Example:
        >>> context = DialogContext(
        ...     state=DialogState.IDLE,
        ...     user_id="123",
        ...     session_id="456"
        ... )
        >>> context.state
        <DialogState.IDLE: 'idle'>
    """

    state: DialogState
    user_id: str
    session_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    step_count: int = 0

    def transition_to(self, new_state: DialogState) -> None:
        """Transition to a new state.

        Args:
            new_state: Target state for transition

        Example:
            >>> context = DialogContext(
            ...     state=DialogState.IDLE,
            ...     user_id="123",
            ...     session_id="456"
            ... )
            >>> context.transition_to(DialogState.TASK_CREATE_TITLE)
            >>> context.state
            <DialogState.TASK_CREATE_TITLE: 'task_create_title'>
        """
        self.state = new_state
        self.step_count += 1

    def reset(self) -> None:
        """Reset context to initial IDLE state.

        Clears all data and resets step count.
        """
        self.state = DialogState.IDLE
        self.data.clear()
        self.step_count = 0

    def update_data(self, key: str, value: Any) -> None:
        """Update context data.

        Args:
            key: Data key
            value: Data value

        Example:
            >>> context = DialogContext(
            ...     state=DialogState.TASK_CREATE_TITLE,
            ...     user_id="123",
            ...     session_id="456"
            ... )
            >>> context.update_data("title", "My task")
            >>> context.data["title"]
            'My task'
        """
        self.data[key] = value
