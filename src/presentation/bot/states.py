from aiogram.fsm.state import State, StatesGroup


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
