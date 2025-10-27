"""
API payload factory for unified payload creation.

Following Python Zen: "Simple is better than complex"
and "Don't repeat yourself".
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class PayloadConfig:
    """Configuration for API payload creation."""
    model: str
    max_tokens: int = 800
    temperature: float = 0.7
    system_prompt: Optional[str] = None


class PayloadFactory:
    """Factory for creating API payload objects."""
    
    @staticmethod
    def create_perplexity_payload(
        message: str, 
        config: PayloadConfig
    ) -> Dict[str, Any]:
        """Create Perplexity API payload."""
        messages = []
        
        if config.system_prompt:
            messages.append({"role": "system", "content": config.system_prompt})
        
        messages.append({"role": "user", "content": message})
        
        return {
            "model": config.model,
            "messages": messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature
        }
    
    @staticmethod
    def create_chadgpt_payload(
        message: str, 
        config: PayloadConfig,
        api_key: str
    ) -> Dict[str, Any]:
        """Create ChadGPT API payload."""
        prompt_text = message
        if config.system_prompt:
            prompt_text = f"{config.system_prompt}\n\nВопрос: {message}"
        
        return {
            "message": prompt_text,
            "api_key": api_key,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens
        }
    
    @staticmethod
    def create_local_payload(
        messages: List[Dict[str, str]], 
        config: PayloadConfig
    ) -> Dict[str, Any]:
        """Create local model API payload."""
        return {
            "messages": messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature
        }
    
    @staticmethod
    def create_availability_check_payload() -> Dict[str, Any]:
        """Create payload for availability check."""
        return {
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 1
        }
    
    @staticmethod
    def create_chat_messages(
        user_message: str, 
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Create chat messages list."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": user_message})
        
        return messages
