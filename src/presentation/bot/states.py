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


class ChannelSearchStates(StatesGroup):
    """Conversation states for channel search and confirmation.

    Purpose:
        Defines FSM stages for channel search flow:
        1. Waiting for user confirmation of found channel
        2. Waiting for user action choice (subscribe or subscribe-and-digest)

    States:
        waiting_confirmation: Waiting for user to confirm found channel (Yes/No)
        waiting_action_choice: Waiting for user to choose action (Subscribe/Subscribe-and-digest)

    Example:
        # Pseudocode usage in a handler
        # await state.set_state(ChannelSearchStates.waiting_confirmation)
        # await state.set_state(ChannelSearchStates.waiting_action_choice)
    """

    waiting_confirmation = State()  # Waiting for user to confirm found channel
    waiting_action_choice = State()  # Waiting for subscribe/subscribe-and-digest choice
