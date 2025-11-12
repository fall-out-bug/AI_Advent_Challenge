"""
Unified client for all model types.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import asyncio
from typing import Dict, List, Optional
import httpx

try:
    from shared_package.clients.base_client import BaseModelClient, ModelResponse
    from shared_package.config.models import MODEL_CONFIGS, ModelType, get_model_config, is_local_model
    from shared_package.config.constants import (
        DEFAULT_TIMEOUT,
        DEFAULT_MAX_TOKENS,
        DEFAULT_TEMPERATURE,
        TEST_MAX_TOKENS
    )
    from shared_package.config.api_keys import get_api_key, is_api_key_configured
    from shared_package.validation.models import ModelRequest, ValidationError, sanitize_input
    from shared_package.exceptions.model_errors import (
        ModelConnectionError,
        ModelRequestError,
        ModelTimeoutError,
        ModelConfigurationError,
    )
except ImportError:
    # Fallback for different import paths
    import sys
    from pathlib import Path
    _root = Path(__file__).parent.parent
    _shared_package = _root / "shared_package"
    if _shared_package.exists():
        sys.path.insert(0, str(_root))
        from shared_package.clients.base_client import BaseModelClient, ModelResponse
        from shared_package.config.models import MODEL_CONFIGS, ModelType, get_model_config, is_local_model
        from shared_package.config.constants import (
            DEFAULT_TIMEOUT,
            DEFAULT_MAX_TOKENS,
            DEFAULT_TEMPERATURE,
            TEST_MAX_TOKENS
        )
        from shared_package.config.api_keys import get_api_key, is_api_key_configured
        from shared_package.validation.models import ModelRequest, ValidationError, sanitize_input
        from shared_package.exceptions.model_errors import (
            ModelConnectionError,
            ModelRequestError,
            ModelTimeoutError,
            ModelConfigurationError,
            ModelNotAvailableError
        )
    else:
        # For base_client, we still need shared_package
        raise ImportError("shared_package not found")


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
        """
        Make request to any model type with input validation.

        Args:
            model_name: Model name
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature

        Returns:
            ModelResponse: Model response

        Raises:
            ValidationError: If input validation fails
            ModelConfigurationError: If model not configured
            ModelConnectionError: If connection fails
            ModelRequestError: If request fails
            ModelTimeoutError: If request times out
        """
        # Validate input data
        try:
            validated_request = ModelRequest(
                model_name=model_name,
                prompt=sanitize_input(prompt),
                max_tokens=max_tokens,
                temperature=temperature
            )
        except Exception as e:
            raise ValidationError(f"Input validation failed: {str(e)}")

        # Use validated values
        model_name = validated_request.model_name
        prompt = validated_request.prompt
        max_tokens = validated_request.max_tokens
        temperature = validated_request.temperature

        if model_name not in MODEL_CONFIGS:
            raise ModelConfigurationError(f"Unknown model: {model_name}")

        if is_local_model(model_name):
            return await self._make_local_request(model_name, prompt, max_tokens, temperature)
        else:
            return await self._make_external_request(model_name, prompt, max_tokens, temperature)

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

        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        start_time = asyncio.get_event_loop().time()

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()

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

        except httpx.ConnectError as e:
            raise ModelConnectionError(f"Failed to connect to local model {model_name}: {e}")
        except httpx.TimeoutException as e:
            raise ModelTimeoutError(f"Request to local model {model_name} timed out: {e}")
        except httpx.HTTPStatusError as e:
            raise ModelRequestError(f"HTTP error for local model {model_name}: {e}")
        except Exception as e:
            raise ModelRequestError(f"Unexpected error with local model {model_name}: {e}")

    async def _make_external_request(
        self,
        model_name: str,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> ModelResponse:
        """
        Make request to external API.

        Args:
            model_name: Name of the external model
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature

        Returns:
            ModelResponse: Model response

        Raises:
            ModelConfigurationError: If API key not configured
            ModelConnectionError: If connection fails
            ModelRequestError: If request fails
            ModelTimeoutError: If request times out
        """
        config = get_model_config(model_name)

        # Check if API key is configured
        if not is_api_key_configured(model_name):
            raise ModelConfigurationError(f"API key not configured for {model_name}")

        api_key = get_api_key(model_name)

        start_time = asyncio.get_event_loop().time()

        try:
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

        except httpx.ConnectError as e:
            raise ModelConnectionError(f"Failed to connect to external API {model_name}: {e}")
        except httpx.TimeoutException as e:
            raise ModelTimeoutError(f"Request to external API {model_name} timed out: {e}")
        except httpx.HTTPStatusError as e:
            raise ModelRequestError(f"HTTP error for external API {model_name}: {e}")
        except Exception as e:
            raise ModelRequestError(f"Unexpected error with external API {model_name}: {e}")

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

        payload = {
            "model": "sonar-pro",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        response = await self.client.post(url, json=payload, headers=headers)
        response.raise_for_status()

        end_time = asyncio.get_event_loop().time()
        response_time = end_time - start_time

        data = response.json()

        if "choices" not in data or not data["choices"]:
            raise ModelRequestError("Unexpected response format from Perplexity API")

        # Estimate tokens (Perplexity doesn't provide exact counts)
        response_text = data["choices"][0]["message"]["content"]
        estimated_input_tokens = len(prompt.split()) * 1.3  # Rough estimation
        estimated_response_tokens = len(response_text.split()) * 1.3

        return ModelResponse(
            response=response_text,
            response_tokens=int(estimated_response_tokens),
            input_tokens=int(estimated_input_tokens),
            total_tokens=int(estimated_input_tokens + estimated_response_tokens),
            model_name="perplexity",
            response_time=response_time
        )

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

        payload = {
            "message": prompt,
            "api_key": api_key,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        response = await self.client.post(url, json=payload)
        response.raise_for_status()

        end_time = asyncio.get_event_loop().time()
        response_time = end_time - start_time

        data = response.json()

        if not data.get('is_success') or not isinstance(data.get('response'), str):
            raise ModelRequestError("Unexpected response format from ChadGPT API")

        response_text = data['response']

        # Estimate tokens (ChadGPT doesn't provide exact counts)
        estimated_input_tokens = len(prompt.split()) * 1.3
        estimated_response_tokens = len(response_text.split()) * 1.3

        return ModelResponse(
            response=response_text,
            response_tokens=int(estimated_response_tokens),
            input_tokens=int(estimated_input_tokens),
            total_tokens=int(estimated_input_tokens + estimated_response_tokens),
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
