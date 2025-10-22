"""
Local model client with conversation history support.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import sys
import os

# Add shared SDK to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'shared'))

from shared_package.clients.unified_client import UnifiedModelClient
from shared_package.config.constants import DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE


class LocalModelClient(UnifiedModelClient):
    """Extended client for local model APIs with conversation history support."""
    
    def __init__(self, model_name: str):
        """Initialize client for specific model."""
        super().__init__(timeout=None)  # No timeout for local models
        self.model_name = model_name
        self.conversation_history = []
    
    async def chat(
        self, 
        messages: list, 
        max_tokens: int = DEFAULT_MAX_TOKENS, 
        temperature: float = DEFAULT_TEMPERATURE, 
        use_history: bool = False
    ) -> dict:
        """Send chat request to local model with optional conversation history."""
        full_messages = self._build_messages_with_history(messages, use_history)
        user_content = self._extract_user_content(full_messages)
        
        try:
            response = await self.make_request(
                self.model_name, user_content, max_tokens, temperature
            )
            
            if use_history:
                self._update_conversation_history(full_messages, response.response)
            
            return self._format_response(response)
            
        except Exception as e:
            return self._format_error_response(str(e))
    
    def _build_messages_with_history(self, messages: list, use_history: bool) -> list:
        """Build messages with optional history."""
        if use_history:
            return self.conversation_history + messages
        return messages
    
    def _extract_user_content(self, messages: list) -> str:
        """Extract user content from messages."""
        return "\n".join([
            msg["content"] for msg in messages if msg["role"] == "user"
        ])
    
    def _update_conversation_history(self, messages: list, response: str) -> None:
        """Update conversation history with new messages and response."""
        self.conversation_history.extend(messages)
        self.conversation_history.append({
            "role": "assistant", 
            "content": response
        })
    
    def _format_response(self, response) -> dict:
        """Format successful response."""
        return {
            "response": response.response,
            "input_tokens": response.input_tokens,
            "response_tokens": response.response_tokens,
            "total_tokens": response.total_tokens
        }
    
    def _format_error_response(self, error: str) -> dict:
        """Format error response."""
        return {
            "response": f"❌ Ошибка: {error}",
            "input_tokens": 0,
            "response_tokens": 0,
            "total_tokens": 0
        }
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_history_length(self) -> int:
        """Get current conversation history length."""
        return len(self.conversation_history)
