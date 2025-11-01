"""Dialog Manager for MongoDB storage.

Following Python Zen:
- Simple is better than complex
- Explicit is better than implicit
- Readability counts
"""

import logging
from typing import List, Optional
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.infrastructure.dialogs.schemas import DialogMessage
from src.infrastructure.dialogs.history_compressor import HistoryCompressor
from src.infrastructure.utils.path_utils import ensure_shared_in_path

ensure_shared_in_path()

from shared_package.clients.unified_client import UnifiedModelClient

logger = logging.getLogger(__name__)


class DialogManager:
    """Manages dialog history in MongoDB.
    
    Purpose:
        Store and retrieve dialog messages with automatic compression
        when token limit is exceeded.
    
    Example:
        >>> from src.infrastructure.dialogs.dialog_manager import DialogManager
        >>> from src.infrastructure.database.mongo import get_db
        >>>
        >>> mongodb = await get_db()
        >>> manager = DialogManager(mongodb=mongodb)
        >>> await manager.add_message("session_123", "user", "Hello!")
        >>> context = await manager.get_context("session_123", max_tokens=1000)
    """
    
    COMPRESSION_THRESHOLD = 8000  # Tokens
    MAX_CONTEXT_TOKENS = 8000
    
    def __init__(
        self,
        mongodb: AsyncIOMotorDatabase,
        llm_client: Optional[UnifiedModelClient] = None
    ):
        """Initialize dialog manager.
        
        Args:
            mongodb: MongoDB database instance
            llm_client: Optional LLM client for compression
        """
        self.mongodb = mongodb
        self.collection = mongodb.dialogs
        self.compressor = None
        if llm_client:
            self.compressor = HistoryCompressor(llm_client)
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> None:
        """Add message and check compression.
        
        Args:
            session_id: Session ID
            role: Message role
            content: Message content
        """
        tokens = self._estimate_tokens(content)
        message = DialogMessage(
            role=role,
            content=content,
            tokens=tokens
        )
        
        await self._save_to_mongo(session_id, message)
        
        if await self._should_compress(session_id):
            await self._compress_history(session_id)
    
    async def get_context(
        self,
        session_id: str,
        max_tokens: int = MAX_CONTEXT_TOKENS
    ) -> str:
        """Get dialog context respecting token limit.
        
        Args:
            session_id: Session ID
            max_tokens: Maximum tokens to return
        
        Returns:
            Formatted context string
        """
        messages = await self._fetch_from_mongo(session_id)
        return self._format_context(messages, max_tokens)
    
    async def _save_to_mongo(
        self,
        session_id: str,
        message: DialogMessage
    ) -> None:
        """Save message to MongoDB.
        
        Args:
            session_id: Session ID
            message: Message to save
        """
        doc = {
            "session_id": session_id,
            "messages": [message.model_dump()],
            "token_count": message.tokens,
            "updated_at": datetime.utcnow()
        }
        
        await self.collection.update_one(
            {"session_id": session_id},
            {
                "$push": {"messages": message.model_dump()},
                "$inc": {"token_count": message.tokens},
                "$set": {"updated_at": datetime.utcnow()},
                "$setOnInsert": {"created_at": datetime.utcnow()}
            },
            upsert=True
        )
    
    async def _fetch_from_mongo(self, session_id: str) -> List[DialogMessage]:
        """Fetch messages from MongoDB.
        
        Args:
            session_id: Session ID
        
        Returns:
            List of messages
        """
        doc = await self.collection.find_one({"session_id": session_id})
        if not doc:
            return []
        
        messages = doc.get("messages", [])
        return [DialogMessage(**msg) for msg in messages]
    
    async def _should_compress(self, session_id: str) -> bool:
        """Check if compression is needed.
        
        Args:
            session_id: Session ID
        
        Returns:
            True if compression needed
        """
        doc = await self.collection.find_one({"session_id": session_id})
        if not doc:
            return False
        
        token_count = doc.get("token_count", 0)
        return token_count > self.COMPRESSION_THRESHOLD
    
    async def _compress_history(self, session_id: str) -> None:
        """Compress dialog history.
        
        Args:
            session_id: Session ID
        """
        if not self.compressor:
            logger.warning("No compressor available, skipping compression")
            return
        
        messages = await self._fetch_from_mongo(session_id)
        if len(messages) < 10:
            return  # Don't compress if too few messages
        
        summary = await self.compressor.compress(session_id, messages)
        summary_message = DialogMessage(
            role="system",
            content=f"[Сжато] {summary}",
            tokens=self._estimate_tokens(summary)
        )
        
        await self.collection.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "messages": [summary_message.model_dump()],
                    "token_count": summary_message.tokens,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    def _format_context(
        self,
        messages: List[DialogMessage],
        max_tokens: int
    ) -> str:
        """Format messages into context string.
        
        Args:
            messages: List of messages
            max_tokens: Maximum tokens
        
        Returns:
            Formatted context
        """
        formatted = []
        total_tokens = 0
        
        for msg in reversed(messages):
            msg_tokens = msg.tokens or self._estimate_tokens(msg.content)
            if total_tokens + msg_tokens > max_tokens:
                break
            formatted.insert(0, f"{msg.role}: {msg.content}")
            total_tokens += msg_tokens
        
        return "\n".join(formatted)
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation).
        
        Args:
            text: Text to estimate
        
        Returns:
            Estimated token count
        """
        return int(len(text.split()) * 1.3)  # Rough approximation

