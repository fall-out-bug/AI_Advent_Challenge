from aiogram.fsm.state import State, StatesGroup


class TaskCreation(StatesGroup):
    """Conversation states for creating a task via natural language.

    Purpose:
        Defines FSM stages for collecting a task description and any
        follow-up clarifications required to complete task creation.

    States:
        waiting_for_task: Initial state where the bot expects user's task input.
        waiting_for_clarification: State for collecting answers to clarifying
            questions when the initial input is ambiguous or incomplete.

    Example:
        # Pseudocode usage in a handler
        # await state.set_state(TaskCreation.waiting_for_task)
        # await state.set_state(TaskCreation.waiting_for_clarification)
    """

    waiting_for_task = State()
    waiting_for_clarification = State()
