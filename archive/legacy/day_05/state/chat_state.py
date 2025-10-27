"""
Chat state management for terminal chat.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import httpx
from typing import Dict, Any

# Mock LOCAL_MODELS for standalone operation
try:
    from shared_package.config.models import LOCAL_MODELS
except ImportError:
    LOCAL_MODELS = {
        "qwen": "http://localhost:8000",
        "mistral": "http://localhost:8001",
        "tinyllama": "http://localhost:8002"
    }

from config import get_api_key, is_api_key_configured
from clients.local_client import LocalModelClient


class ChatState:
    """Manages chat application state and configuration."""
    
    def __init__(self):
        """Initialize chat state with default values."""
        self.api_key = None
        self.client = None
        self.default_temperature = 0.5
        self.explain_mode = False
        self.current_api = None  # "chadgpt", "perplexity", or local model name
        self._system_prompt = "Ты пожилой человек, который ехидно подшучивает. Отвечай на русском, лаконично, без ссылок."
        self.advice_mode = None
        self.local_clients = {name: LocalModelClient(name) for name in LOCAL_MODELS.keys()}
        self.use_history = False  # Default: no history
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
    
    def setup(self) -> bool:
        """Ensure at least one API is configured."""
        if self._check_local_models():
            self.current_api = "mistral"  # Default to mistral
            return True
            
        if self._setup_external_api():
            return True
            
        self._print_setup_error()
        return False
    
    def _check_local_models(self) -> bool:
        """Check if any local models are available."""
        # This would need actual availability check
        # For now, assume they're available if configured
        return len(self.local_clients) > 0
    
    def _setup_external_api(self) -> bool:
        """Setup external API (ChadGPT or Perplexity)."""
        if is_api_key_configured("chadgpt"):
            self.current_api = "chadgpt"
            self.api_key = get_api_key("chadgpt")
            return True
            
        if is_api_key_configured("perplexity"):
            self.current_api = "perplexity"
            self.api_key = get_api_key("perplexity")
            return True
            
        return False
    
    def _print_setup_error(self) -> None:
        """Print setup error message."""
        print("❌ Ни один API ключ не настроен и локальные модели недоступны!")
        print("   Установите CHAD_API_KEY или PERPLEXITY_API_KEY, или запустите локальные модели")
    
    def set_temperature(self, temperature: float) -> None:
        """Set default temperature."""
        self.default_temperature = temperature
    
    def toggle_explain_mode(self) -> None:
        """Toggle explain mode."""
        self.explain_mode = not self.explain_mode
    
    def set_explain_mode(self, enabled: bool) -> None:
        """Set explain mode."""
        self.explain_mode = enabled
    
    def switch_model(self, model_name: str) -> bool:
        """Switch to specified model."""
        if model_name in LOCAL_MODELS:
            self.current_api = model_name
            return True
        return False
    
    def get_current_model(self) -> str:
        """Get current model name."""
        return self.current_api or "unknown"
    
    def get_system_prompt(self) -> str:
        """Get system prompt."""
        return self._system_prompt
    
    def set_system_prompt(self, prompt: str) -> None:
        """Set system prompt."""
        self._system_prompt = prompt
    
    def toggle_history(self) -> None:
        """Toggle conversation history usage."""
        self.use_history = not self.use_history
    
    def set_history_usage(self, use: bool) -> None:
        """Set conversation history usage."""
        self.use_history = use
