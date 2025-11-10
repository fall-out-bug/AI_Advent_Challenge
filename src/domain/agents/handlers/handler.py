"""Base handler interface for Butler Agent modes.

Following Python Zen:
- Simple is better than complex
- Explicit is better than implicit
"""

from abc import ABC, abstractmethod

from src.domain.agents.state_machine import DialogContext


class Handler(ABC):
    """Base interface for mode handlers.

    All mode handlers (Task, Data, Reminders, Chat) must implement
    this interface. Following SOLID: Interface Segregation Principle.

    Methods:
        handle: Process user message in handler's mode
    """

    @abstractmethod
    async def handle(self, context: DialogContext, message: str) -> str:
        """Handle user message in specific mode.

        Args:
            context: Dialog context with state and data
            message: User message text

        Returns:
            Response text to send to user

        Raises:
            Exception: If handling fails
        """
