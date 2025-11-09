"""Conversation repository interface.

Following Clean Architecture principles and the Zen of Python:
- Simple is better than complex
- Explicit is better than implicit
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.conversation import Conversation


class ConversationRepository(ABC):
    """Abstract repository for conversations."""

    @abstractmethod
    async def save(self, conversation: Conversation) -> None:
        """
        Save or update conversation.

        Args:
            conversation: Conversation entity
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get conversation by ID.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Conversation entity or None
        """
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> List[Conversation]:
        """
        Get all conversations.

        Returns:
            List of conversations
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, conversation_id: str) -> bool:
        """
        Delete conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            True if deleted, False if not found
        """
        raise NotImplementedError

    @abstractmethod
    async def exists(self, conversation_id: str) -> bool:
        """
        Check if conversation exists.

        Args:
            conversation_id: Conversation identifier

        Returns:
            True if exists, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Add message to conversation.

        Args:
            conversation_id: Conversation identifier
            role: Message role
            content: Message content
            metadata: Optional metadata
        """
        raise NotImplementedError

    @abstractmethod
    async def get_recent_messages(
        self, conversation_id: str, limit: int = 5
    ) -> List[dict]:
        """
        Get recent messages from conversation.

        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of messages

        Returns:
            List of message dictionaries
        """
        raise NotImplementedError
