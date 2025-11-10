"""JSON-based conversation repository implementation.

Following existing repository patterns and Python Zen.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.domain.entities.conversation import Conversation, ConversationMessage
from src.domain.repositories.conversation_repository import ConversationRepository


class JsonConversationRepository(ConversationRepository):
    """JSON file-based conversation repository."""

    def __init__(self, storage_path: Path) -> None:
        """
        Initialize repository.

        Args:
            storage_path: Path to JSON storage file
        """
        self.storage_path = storage_path
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory and file exist."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self.storage_path.write_text("{}")

    async def save(self, conversation: Conversation) -> None:
        """
        Save or update conversation.

        Args:
            conversation: Conversation entity
        """
        data = self._load_data()
        data[conversation.conversation_id] = self._serialize_conversation(conversation)
        self._save_data(data)

    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get conversation by ID.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Conversation entity or None
        """
        data = self._load_data()
        conv_data = data.get(conversation_id)
        if not conv_data:
            return None
        return self._deserialize_conversation(conv_data)

    async def get_all(self) -> List[Conversation]:
        """
        Get all conversations.

        Returns:
            List of conversations
        """
        data = self._load_data()
        return [
            self._deserialize_conversation(conv_data) for conv_data in data.values()
        ]

    async def delete(self, conversation_id: str) -> bool:
        """
        Delete conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            True if deleted, False if not found
        """
        data = self._load_data()
        if conversation_id not in data:
            return False
        del data[conversation_id]
        self._save_data(data)
        return True

    async def exists(self, conversation_id: str) -> bool:
        """
        Check if conversation exists.

        Args:
            conversation_id: Conversation identifier

        Returns:
            True if exists, False otherwise
        """
        data = self._load_data()
        return conversation_id in data

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
        conversation = await self.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        conversation.add_message(role, content, metadata)
        await self.save(conversation)

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
        conversation = await self.get_by_id(conversation_id)
        if not conversation:
            return []
        messages = conversation.get_recent_messages(limit)
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata,
            }
            for msg in messages
        ]

    def _load_data(self) -> Dict[str, Any]:
        """Load data from JSON file."""
        if not self.storage_path.exists():
            return {}
        content = self.storage_path.read_text()
        if not content.strip():
            return {}
        return json.loads(content)

    def _save_data(self, data: Dict[str, Any]) -> None:
        """Save data to JSON file."""
        self.storage_path.write_text(json.dumps(data, indent=2, default=str))

    def _serialize_conversation(self, conversation: Conversation) -> Dict[str, Any]:
        """Serialize conversation to dictionary."""
        return {
            "conversation_id": conversation.conversation_id,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata,
                }
                for msg in conversation.messages
            ],
            "context": conversation.context,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
        }

    def _deserialize_conversation(self, data: Dict[str, Any]) -> Conversation:
        """Deserialize conversation from dictionary."""
        from datetime import datetime

        messages = [
            ConversationMessage(
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                metadata=msg_data.get("metadata", {}),
            )
            for msg_data in data.get("messages", [])
        ]

        return Conversation(
            conversation_id=data["conversation_id"],
            messages=messages,
            context=data.get("context", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
