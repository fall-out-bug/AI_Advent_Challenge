"""
Chat business logic for terminal chat.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import httpx
from typing import Dict, Tuple, Optional

# Mock LOCAL_MODELS for standalone operation
try:
    from shared_package.config.models import LOCAL_MODELS
except ImportError:
    LOCAL_MODELS = {
        "qwen": "http://localhost:8000",
        "mistral": "http://localhost:8001",
        "tinyllama": "http://localhost:8002"
    }

from utils.text_utils import clamp_temperature, contains_any, normalize_for_trigger


class ChatLogic:
    """Handles chat business logic and API calls."""
    
    def __init__(self, chat_state):
        """Initialize chat logic with state reference."""
        self.state = chat_state
        self.api_config = {
            "perplexity": {
                "url": "https://api.perplexity.ai/chat/completions",
                "model": "sonar-pro"
            },
            "chadgpt": {
                "url": "https://ask.chadgpt.ru/api/public/gpt-5-mini"
            }
        }
    
    async def call_model(
        self, 
        message: str, 
        temperature: float, 
        system_prompt: Optional[str] = None, 
        use_history: bool = False
    ) -> Dict:
        """
        Route API call to current provider (local/external).
        
        Args:
            message: User input message to process
            temperature: Generation temperature (0.0-1.5)
            system_prompt: Optional system prompt override
            use_history: Whether to include conversation history
            
        Returns:
            Dict with keys: response, input_tokens, response_tokens, total_tokens
            
        Raises:
            httpx.RequestError: On network failures
            ValueError: On invalid temperature values
        """
        if self.state.current_api in self.state.local_clients:
            return await self._call_local_model(message, temperature, system_prompt, use_history)
        elif self.state.current_api == "chadgpt":
            response_text = await self._call_chadgpt(message, temperature, system_prompt)
            return self._format_external_response(response_text)
        else:
            response_text = await self._call_perplexity(message, temperature, system_prompt)
            return self._format_external_response(response_text)
    
    async def _call_local_model(
        self, 
        message: str, 
        temperature: float, 
        system_prompt: str | None = None, 
        use_history: bool = False
    ) -> dict:
        """Call local model."""
        client = self.state.local_clients[self.state.current_api]
        messages = [{"role": "user", "content": message}]
        
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})
        
        return await client.chat(messages, temperature=temperature, use_history=use_history)
    
    async def _call_perplexity(
        self, 
        message: str, 
        temperature: float, 
        system_prompt: Optional[str] = None
    ) -> str:
        """Call Perplexity chat completion."""
        payload = self._create_perplexity_payload(message, temperature, system_prompt)
        
        try:
            config = self.api_config["perplexity"]
            response = await self.state.client.post(
                config["url"],
                headers=self._create_perplexity_headers(),
                json=payload
            )
            
            if response.status_code != 200:
                return self._format_perplexity_error(response)
            
            data = response.json()
            if "choices" not in data or not data["choices"]:
                return "❌ Неожиданный формат ответа от API Perplexity"
            
            return data["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            return f"❌ Ошибка Perplexity: {e}"
    
    async def _call_chadgpt(
        self, 
        message: str, 
        temperature: float, 
        system_prompt: Optional[str] = None
    ) -> str:
        """Call ChadGPT API."""
        prompt_text = f"{(system_prompt or self.state.get_system_prompt())}\n\nВопрос: {message}"
        payload = self._create_chadgpt_payload(prompt_text, temperature)
        
        try:
            config = self.api_config["chadgpt"]
            response = await self.state.client.post(config["url"], json=payload)
            
            if response.status_code != 200:
                return self._format_chadgpt_error(response)
            
            data = response.json()
            if not data.get('is_success') or not isinstance(data.get('response'), str):
                return "❌ Неожиданный формат ответа от ChadGPT"
            
            return data['response'].strip()
            
        except Exception as e:
            return f"❌ Ошибка ChadGPT: {e}"
    
    def _create_perplexity_payload(
        self, 
        message: str, 
        temperature: float, 
        system_prompt: Optional[str]
    ) -> Dict:
        """Create payload for Perplexity API."""
        config = self.api_config["perplexity"]
        return {
            "model": config["model"],
            "messages": [
                {"role": "system", "content": (system_prompt or self.state.get_system_prompt())},
                {"role": "user", "content": message}
            ],
            "max_tokens": 800,
            "temperature": temperature
        }
    
    def _create_perplexity_headers(self) -> Dict[str, str]:
        """Create headers for Perplexity API."""
        return {
            "Authorization": f"Bearer {self.state.api_key}",
            "Content-Type": "application/json"
        }
    
    def _create_chadgpt_payload(self, prompt_text: str, temperature: float) -> Dict[str, any]:
        """Create payload for ChadGPT API."""
        return {
            "message": prompt_text,
            "api_key": self.state.api_key,
            "temperature": temperature,
            "max_tokens": 800
        }
    
    def _format_perplexity_error(self, response: httpx.Response) -> str:
        """Format Perplexity API error."""
        body = response.text
        preview = body[:240].replace("\n", " ") if body else ""
        return f"❌ Ошибка API Perplexity: {response.status_code} {preview}"
    
    def _format_chadgpt_error(self, response: httpx.Response) -> str:
        """Format ChadGPT API error."""
        body = response.text
        preview = body[:240].replace("\n", " ") if body else ""
        return f"❌ Ошибка API ChadGPT: {response.status_code} {preview}"
    
    def _format_external_response(self, response_text: str) -> Dict[str, int]:
        """Format external API response."""
        return {
            "response": response_text,
            "input_tokens": 0,
            "response_tokens": 0,
            "total_tokens": 0
        }
    
    def parse_temp_override(self, user_message: str) -> Tuple[Optional[float], str]:
        """
        Parse one-off temperature override in 'temp=<v> <text>' format.
        
        Args:
            user_message: User input that may contain temperature override
            
        Returns:
            Tuple of (temperature_value, clean_message) where:
            - temperature_value: Parsed float or None if invalid/not found
            - clean_message: Message with temperature prefix removed
            
        Example:
            parse_temp_override("temp=0.8 Hello world") -> (0.8, "Hello world")
            parse_temp_override("Hello world") -> (None, "Hello world")
        """
        msg = user_message.strip()
        if not msg.lower().startswith("temp="):
            return None, msg
        
        try:
            head, rest = msg.split(maxsplit=1)
        except ValueError:
            head, rest = msg, ""
        
        try:
            override = float(head.split("=", 1)[1])
            override = clamp_temperature(override)
        except Exception as e:
            print(f"❌ Неверный формат temp=<value>: {e}")
            return None, rest.strip()
        
        return override, rest.strip()
    
    def apply_interactive_temperature(self, reply_text: str) -> None:
        """Apply interactive temperature based on reply content."""
        norm_text = normalize_for_trigger(reply_text)
        
        if contains_any(norm_text, ["не душни", "не души", "не дави"]):
            self.state.set_temperature(0.0)
        elif contains_any(norm_text, ["потише", "тише", "спокойнее"]):
            self.state.set_temperature(0.7)
        elif contains_any(norm_text, ["разгоняй", "разгоня", "быстрее"]):
            self.state.set_temperature(1.2)
    
    def switch_model(self, model_name: str) -> bool:
        """Switch to specified model."""
        if model_name.startswith("local-"):
            local_name = model_name[6:]  # Remove "local-" prefix
            if local_name in LOCAL_MODELS:
                self.state.current_api = local_name
                return True
        
        if model_name in ["chadgpt", "perplexity"]:
            self.state.current_api = model_name
            return True
        
        return False
