"""History compressor for dialog compression.

Following Python Zen: "Simple is better than complex".
"""

import logging
from typing import List

from src.infrastructure.dialogs.schemas import DialogMessage
from src.infrastructure.utils.path_utils import ensure_shared_in_path

ensure_shared_in_path()

from shared_package.clients.unified_client import UnifiedModelClient

logger = logging.getLogger(__name__)


class HistoryCompressor:
    """Compresses dialog history using LLM.
    
    Purpose:
        Reduce dialog history size by creating summaries
        when token limit is exceeded.
    
    Example:
        >>> from src.infrastructure.dialogs.history_compressor import HistoryCompressor
        >>> from shared_package.clients.unified_client import UnifiedModelClient
        >>>
        >>> llm_client = UnifiedModelClient()
        >>> compressor = HistoryCompressor(llm_client=llm_client)
        >>> summary = await compressor.compress("session_123", messages)
    """
    
    # Compression configuration constants
    DEFAULT_MODEL_NAME = "mistral"
    COMPRESSION_MAX_TOKENS = 200
    COMPRESSION_TEMPERATURE = 0.3
    
    COMPRESSION_PROMPT = """Создай краткое резюме следующего диалога, сохранив ключевую информацию и контекст.

Диалог:
{messages}

Резюме должно быть кратким (максимум 200 токенов) и содержать:
1. Основную тему диалога
2. Ключевые решения и действия
3. Важный контекст для продолжения диалога

Резюме:"""
    
    def __init__(self, llm_client: UnifiedModelClient, model_name: str = DEFAULT_MODEL_NAME):
        """Initialize compressor.
        
        Args:
            llm_client: LLM client for compression
            model_name: Model name to use
        """
        self.llm_client = llm_client
        self.model_name = model_name
    
    async def compress(
        self,
        session_id: str,
        messages: List[DialogMessage]
    ) -> str:
        """Create summary of messages.
        
        Args:
            session_id: Session ID
            messages: List of messages to compress
        
        Returns:
            Summary text
        
        Raises:
            Exception: If compression fails
        """
        formatted_messages = self._format_messages(messages)
        prompt = self.COMPRESSION_PROMPT.format(messages=formatted_messages)
        
        try:
            response = await self.llm_client.make_request(
                model_name=self.model_name,
                prompt=prompt,
                max_tokens=self.COMPRESSION_MAX_TOKENS,
                temperature=self.COMPRESSION_TEMPERATURE
            )
            return response.response
        except Exception as e:
            logger.error(f"Compression failed for session {session_id}: {e}")
            raise
    
    def _format_messages(self, messages: List[DialogMessage]) -> str:
        """Format messages for prompt.
        
        Args:
            messages: List of messages
        
        Returns:
            Formatted string
        """
        formatted = []
        for msg in messages:
            formatted.append(f"{msg.role}: {msg.content}")
        return "\n".join(formatted)

