"""Base handler protocol for Butler bot modes."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.application.dtos.butler_dialog_dtos import DialogContext


class Handler(ABC):
    """Abstract base for mode handlers."""

    @abstractmethod
    async def handle(self, context: DialogContext, message: str) -> str:
        """Process incoming message and return bot response."""
        raise NotImplementedError
