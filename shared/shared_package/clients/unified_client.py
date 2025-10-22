"""
Unified client for all model types.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import asyncio
from typing import Dict, List, Optional
import httpx

from .base_client import BaseModelClient, ModelResponse
from ..config.models import MODEL_CONFIGS, ModelType, get_model_config, is_local_model
from ..config.constants import (
    DEFAULT_TIMEOUT, 
    DEFAULT_MAX_TOKENS, 
    DEFAULT_TEMPERATURE,
    TEST_MAX_TOKENS
)
from ..config.api_keys import get_api_key, is_api_key_configured
from ..validation.models import ModelRequest, ValidationError, sanitize_input
from ..exceptions.model_errors import (
    ModelConnectionError, 
    ModelRequestError, 
    ModelTimeoutError,
    ModelConfigurationError,
    ModelNotAvailableError
)


class UnifiedModelClient(BaseModelClient):
    """
    Unified client for all model types (local and external).
    
    Following Python Zen: "Simple is better than complex"
    and "Explicit is better than implicit".
    
    This client provides a single interface for interacting
    with both local and external models, abstracting away
    the differences between them.
    """
    
    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        """
        Initialize unified client.
        
        Args:
            timeout: Request timeout in seconds
        """
        super().__init__(timeout)
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    async def make_request(
        self, 
        model_name: str, 
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> ModelResponse:
        """Make request to any model type with input validation."""
        validated_request = self._validate_request(model_name, prompt, max_tokens, temperature)
        self._check_model_exists(validated_request.model_name)
        
        if is_local_model(validated_request.model_name):
            return await self._make_local_request(
                validated_request.model_name, 
                validated_request.prompt, 
                validated_request.max_tokens, 
                validated_request.temperature
            )
        else:
            return await self._make_external_request(
                validated_request.model_name, 
                validated_request.prompt, 
                validated_request.max_tokens, 
                validated_request.temperature
            )
    
    def _validate_request(
        self, 
        model_name: str, 
        prompt: str, 
        max_tokens: Optional[int], 
        temperature: Optional[float]
    ) -> ModelRequest:
        """Validate input data and return ModelRequest."""
        try:
            return ModelRequest(
                model_name=model_name,
                prompt=sanitize_input(prompt),
                max_tokens=max_tokens or DEFAULT_MAX_TOKENS,
                temperature=temperature or DEFAULT_TEMPERATURE
            )
        except Exception as e:
            raise ValidationError(f"Input validation failed: {str(e)}")
    
    def _check_model_exists(self, model_name: str) -> None:
        """Check if model exists in configuration."""
        if model_name not in MODEL_CONFIGS:
            raise ModelConfigurationError(f"Unknown model: {model_name}")
    
    async def _make_local_request(
        self, 
        model_name: str, 
        prompt: str, 
        max_tokens: int, 
        temperature: float
    ) -> ModelResponse:
        """Make request to local model."""
        config = get_model_config(model_name)
        url = f"{config['url']}/chat"
        payload = self._create_local_payload(prompt, max_tokens, temperature)
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            return self._parse_local_response(response, model_name, start_time)
        except httpx.ConnectError as e:
            raise ModelConnectionError(f"Failed to connect to local model {model_name}: {e}")
        except httpx.TimeoutException as e:
            raise ModelTimeoutError(f"Request to local model {model_name} timed out: {e}")
        except httpx.HTTPStatusError as e:
            raise ModelRequestError(f"HTTP error for local model {model_name}: {e}")
        except Exception as e:
            raise ModelRequestError(f"Unexpected error with local model {model_name}: {e}")
    
    def _create_local_payload(
        self, 
        prompt: str, 
        max_tokens: int, 
        temperature: float
    ) -> Dict[str, any]:
        """Create payload for local model request."""
        return {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
    
    def _parse_local_response(
        self, 
        response: httpx.Response, 
        model_name: str, 
        start_time: float
    ) -> ModelResponse:
        """Parse local model response into ModelResponse."""
        end_time = asyncio.get_event_loop().time()
        response_time = end_time - start_time
        data = response.json()
        
        return ModelResponse(
            response=data["response"],
            response_tokens=data["response_tokens"],
            input_tokens=data["input_tokens"],
            total_tokens=data["total_tokens"],
            model_name=model_name,
            response_time=response_time
        )
    
    async def _make_external_request(
        self, 
        model_name: str, 
        prompt: str, 
        max_tokens: int, 
        temperature: float
    ) -> ModelResponse:
        """Make request to external API."""
        self._check_api_key_configured(model_name)
        api_key = get_api_key(model_name)
        start_time = asyncio.get_event_loop().time()
        
        try:
            return await self._route_external_request(
                model_name, prompt, max_tokens, temperature, api_key, start_time
            )
        except httpx.ConnectError as e:
            raise ModelConnectionError(f"Failed to connect to external API {model_name}: {e}")
        except httpx.TimeoutException as e:
            raise ModelTimeoutError(f"Request to external API {model_name} timed out: {e}")
        except httpx.HTTPStatusError as e:
            raise ModelRequestError(f"HTTP error for external API {model_name}: {e}")
        except Exception as e:
            raise ModelRequestError(f"Unexpected error with external API {model_name}: {e}")
    
    def _check_api_key_configured(self, model_name: str) -> None:
        """Check if API key is configured for external model."""
        if not is_api_key_configured(model_name):
            raise ModelConfigurationError(f"API key not configured for {model_name}")
    
    async def _route_external_request(
        self, 
        model_name: str, 
        prompt: str, 
        max_tokens: int, 
        temperature: float, 
        api_key: str, 
        start_time: float
    ) -> ModelResponse:
        """Route external request to appropriate handler."""
        if model_name == "perplexity":
            return await self._make_perplexity_request(
                prompt, max_tokens, temperature, api_key, start_time
            )
        elif model_name == "chadgpt":
            return await self._make_chadgpt_request(
                prompt, max_tokens, temperature, api_key, start_time
            )
        else:
            raise ModelConfigurationError(f"Unsupported external model: {model_name}")
    
    async def _make_perplexity_request(
        self, 
        prompt: str, 
        max_tokens: int, 
        temperature: float, 
        api_key: str,
        start_time: float
    ) -> ModelResponse:
        """Make request to Perplexity API."""
        url = "https://api.perplexity.ai/chat/completions"
        payload = self._create_perplexity_payload(prompt, max_tokens, temperature)
        headers = self._create_perplexity_headers(api_key)
        
        response = await self.client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        return self._parse_perplexity_response(response, prompt, start_time)
    
    def _create_perplexity_payload(
        self, 
        prompt: str, 
        max_tokens: int, 
        temperature: float
    ) -> Dict[str, any]:
        """Create payload for Perplexity API request."""
        return {
            "model": "sonar-pro",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
    
    def _create_perplexity_headers(self, api_key: str) -> Dict[str, str]:
        """Create headers for Perplexity API request."""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def _parse_perplexity_response(
        self, 
        response: httpx.Response, 
        prompt: str, 
        start_time: float
    ) -> ModelResponse:
        """Parse Perplexity API response into ModelResponse."""
        end_time = asyncio.get_event_loop().time()
        response_time = end_time - start_time
        data = response.json()
        
        if "choices" not in data or not data["choices"]:
            raise ModelRequestError("Unexpected response format from Perplexity API")
        
        response_text = data["choices"][0]["message"]["content"]
        input_tokens, response_tokens = self._estimate_tokens(prompt, response_text)
        
        return ModelResponse(
            response=response_text,
            response_tokens=response_tokens,
            input_tokens=input_tokens,
            total_tokens=input_tokens + response_tokens,
            model_name="perplexity",
            response_time=response_time
        )
    
    def _estimate_tokens(self, prompt: str, response: str) -> tuple[int, int]:
        """Estimate token counts for external APIs."""
        input_tokens = int(len(prompt.split()) * 1.3)
        response_tokens = int(len(response.split()) * 1.3)
        return input_tokens, response_tokens
    
    async def _make_chadgpt_request(
        self, 
        prompt: str, 
        max_tokens: int, 
        temperature: float, 
        api_key: str,
        start_time: float
    ) -> ModelResponse:
        """Make request to ChadGPT API."""
        url = "https://ask.chadgpt.ru/api/public/gpt-5-mini"
        payload = self._create_chadgpt_payload(prompt, max_tokens, temperature, api_key)
        
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        
        return self._parse_chadgpt_response(response, prompt, start_time)
    
    def _create_chadgpt_payload(
        self, 
        prompt: str, 
        max_tokens: int, 
        temperature: float, 
        api_key: str
    ) -> Dict[str, any]:
        """Create payload for ChadGPT API request."""
        return {
            "message": prompt,
            "api_key": api_key,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
    
    def _parse_chadgpt_response(
        self, 
        response: httpx.Response, 
        prompt: str, 
        start_time: float
    ) -> ModelResponse:
        """Parse ChadGPT API response into ModelResponse."""
        end_time = asyncio.get_event_loop().time()
        response_time = end_time - start_time
        data = response.json()
        
        if not data.get('is_success') or not isinstance(data.get('response'), str):
            raise ModelRequestError("Unexpected response format from ChadGPT API")
        
        response_text = data['response']
        input_tokens, response_tokens = self._estimate_tokens(prompt, response_text)
        
        return ModelResponse(
            response=response_text,
            response_tokens=response_tokens,
            input_tokens=input_tokens,
            total_tokens=input_tokens + response_tokens,
            model_name="chadgpt",
            response_time=response_time
        )
    
    async def check_availability(self, model_name: str) -> bool:
        """
        Check if model is available.
        
        Args:
            model_name: Name of the model
            
        Returns:
            bool: True if model is available
        """
        if model_name not in MODEL_CONFIGS:
            return False
        
        if is_local_model(model_name):
            return await self._check_local_availability(model_name)
        else:
            return await self._check_external_availability(model_name)
    
    async def _check_local_availability(self, model_name: str) -> bool:
        """Check local model availability."""
        config = get_model_config(model_name)
        url = f"{config['url']}/chat"
        
        try:
            response = await self.client.post(
                url, 
                json={
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": TEST_MAX_TOKENS
                }
            )
            return response.status_code == 200
        except (httpx.HTTPError, httpx.ConnectError, httpx.TimeoutException):
            return False
    
    async def _check_external_availability(self, model_name: str) -> bool:
        """
        Check external API availability.
        
        Args:
            model_name: Name of the external model
            
        Returns:
            bool: True if external API is available
        """
        # Check if API key is configured
        if not is_api_key_configured(model_name):
            return False
        
        # For external APIs, we assume they're available if API key is configured
        # In a production environment, you might want to make a test request
        return True
    
    async def check_all_availability(self) -> Dict[str, bool]:
        """
        Check availability of all models.
        
        Returns:
            Dict[str, bool]: Availability status of each model
        """
        availability = {}
        
        for model_name in MODEL_CONFIGS.keys():
            availability[model_name] = await self.check_availability(model_name)
        
        return availability
    
    async def get_available_models(self) -> List[str]:
        """
        Get list of available models.
        
        Returns:
            List[str]: List of available model names
        """
        availability = await self.check_all_availability()
        return [model for model, is_available in availability.items() if is_available]
