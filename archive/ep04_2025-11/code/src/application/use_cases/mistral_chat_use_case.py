"""Mistral chat use case following existing patterns.

Following Clean Architecture and Python Zen principles.
"""

import logging
from typing import Optional

from src.application.orchestrators.mistral_orchestrator import MistralChatOrchestrator
from src.domain.repositories.conversation_repository import ConversationRepository
from src.presentation.mcp.orchestrators.mcp_mistral_wrapper import MCPMistralWrapper

logger = logging.getLogger(__name__)


class MistralChatUseCase:
    """Use case for Mistral chat interactions."""

    def __init__(
        self,
        orchestrator: MistralChatOrchestrator,
        conversation_repo: ConversationRepository,
        mcp_wrapper: Optional[MCPMistralWrapper] = None,
    ):
        """Initialize use case.

        Args:
            orchestrator: Mistral orchestrator
            conversation_repo: Conversation repository
            mcp_wrapper: Optional MCP wrapper
        """
        self.orchestrator = orchestrator
        self.conversation_repo = conversation_repo
        self.mcp_wrapper = mcp_wrapper

    async def handle_chat_message(self, message: str, conversation_id: str) -> str:
        """Handle chat message.

        Args:
            message: User message
            conversation_id: Conversation identifier

        Returns:
            Response string

        Raises:
            ValueError: If message is empty
        """
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        logger.info(f"Handling message in conversation {conversation_id}")

        response = await self.orchestrator.handle_message(message, conversation_id)

        return response

    async def get_conversation_history(self, conversation_id: str, limit: int = 10):
        """Get conversation history.

        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of messages

        Returns:
            List of messages
        """
        return await self.conversation_repo.get_recent_messages(conversation_id, limit)
