"""External API provider interface for integrating third-party AI services."""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

# Configure logging
logger = logging.getLogger(__name__)


class ExternalAPIProvider(ABC):
    """Abstract base class for external API providers."""

    def __init__(self, api_key: str, timeout: float = 60.0):
        """Initialize the external API provider.

        Args:
            api_key: API key for the external service
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens_used": 0,
            "response_times": [],
        }

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @abstractmethod
    async def make_request(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> Dict[str, Any]:
        """Make request to external API.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature

        Returns:
            Dict containing response data

        Raises:
            Exception: If API request fails
        """
        pass

    @abstractmethod
    async def check_availability(self) -> bool:
        """Check if API is available.

        Returns:
            True if API is available
        """
        pass

    def _update_stats(
        self, success: bool, tokens_used: int, response_time: float
    ) -> None:
        """Update provider statistics.

        Args:
            success: Whether request was successful
            tokens_used: Number of tokens used
            response_time: Response time in seconds
        """
        self.stats["total_requests"] += 1
        if success:
            self.stats["successful_requests"] += 1
            self.stats["total_tokens_used"] += tokens_used
        else:
            self.stats["failed_requests"] += 1

        self.stats["response_times"].append(response_time)

    def get_average_response_time(self) -> float:
        """Get average response time.

        Returns:
            Average response time in seconds
        """
        if not self.stats["response_times"]:
            return 0.0
        return sum(self.stats["response_times"]) / len(self.stats["response_times"])

    def get_success_rate(self) -> float:
        """Get success rate.

        Returns:
            Success rate as percentage
        """
        if self.stats["total_requests"] == 0:
            return 0.0
        return (self.stats["successful_requests"] / self.stats["total_requests"]) * 100


class ChatGPTProvider(ExternalAPIProvider):
    """OpenAI ChatGPT API provider."""

    def __init__(
        self, api_key: str, model: str = "gpt-3.5-turbo", timeout: float = 60.0
    ):
        """Initialize ChatGPT provider.

        Args:
            api_key: OpenAI API key
            model: Model to use (gpt-3.5-turbo, gpt-4, etc.)
            timeout: Request timeout in seconds
        """
        super().__init__(api_key, timeout)
        self.model = model
        self.base_url = "https://api.openai.com/v1"

    async def make_request(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> Dict[str, Any]:
        """Make request to ChatGPT API.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature

        Returns:
            Dict containing response data

        Raises:
            Exception: If API request fails
        """
        if not self._client:
            raise RuntimeError("Provider not initialized. Use async context manager.")

        start_time = datetime.now()

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            logger.debug(f"Making request to ChatGPT API with {max_tokens} tokens")

            response = await self._client.post(
                f"{self.base_url}/chat/completions", headers=headers, json=payload
            )

            response.raise_for_status()
            response_data = response.json()

            # Extract response content
            content = response_data["choices"][0]["message"]["content"]
            usage = response_data.get("usage", {})

            response_time = (datetime.now() - start_time).total_seconds()

            result = {
                "response": content,
                "input_tokens": usage.get("prompt_tokens", 0),
                "response_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }

            self._update_stats(True, result["total_tokens"], response_time)

            logger.debug(
                f"ChatGPT request completed in {response_time:.2f}s, "
                f"used {result['total_tokens']} tokens"
            )

            return result

        except httpx.HTTPStatusError as e:
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(False, 0, response_time)

            error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
            logger.error(f"ChatGPT API error: {error_msg}")
            raise Exception(error_msg) from e

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(False, 0, response_time)

            logger.error(f"ChatGPT request failed: {str(e)}")
            raise Exception(f"ChatGPT request failed: {str(e)}") from e

    async def check_availability(self) -> bool:
        """Check if ChatGPT API is available.

        Returns:
            True if API is available
        """
        if not self._client:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            # Simple test request
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1,
            }

            response = await self._client.post(
                f"{self.base_url}/chat/completions", headers=headers, json=payload
            )

            return response.status_code == 200

        except Exception as e:
            logger.debug(f"ChatGPT availability check failed: {str(e)}")
            return False


class ChadGPTProvider(ExternalAPIProvider):
    """ChadGPT API provider supporting multiple models."""

    def __init__(self, api_key: str, model: str = "gpt-5-mini", timeout: float = 60.0):
        """Initialize ChadGPT provider.

        Args:
            api_key: ChadGPT API key
            model: Model to use (gpt-5, gpt-5-mini, gpt-5-nano, claude-4.1-opus, claude-4.5-sonnet)
            timeout: Request timeout in seconds
        """
        super().__init__(api_key, timeout)
        self.model = model
        self.base_url = "https://ask.chadgpt.ru/api/public"

        # Validate model
        self._validate_model()

    def _validate_model(self) -> None:
        """Validate that the model is supported by ChadGPT."""
        supported_models = {
            "gpt-5",
            "gpt-5-mini",
            "gpt-5-nano",
            "claude-4.1-opus",
            "claude-4.5-sonnet",
        }

        if self.model not in supported_models:
            raise ValueError(
                f"Unsupported model: {self.model}. "
                f"Supported models: {', '.join(supported_models)}"
            )

    def _get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model.

        Returns:
            Dict with model information
        """
        model_info = {
            "gpt-5": {
                "display_name": "GPT-5",
                "description": "Most powerful GPT model",
                "max_tokens": 8000,
                "recommended_temperature": 0.7,
            },
            "gpt-5-mini": {
                "display_name": "GPT-5 Mini",
                "description": "Fast and efficient GPT model",
                "max_tokens": 4000,
                "recommended_temperature": 0.7,
            },
            "gpt-5-nano": {
                "display_name": "GPT-5 Nano",
                "description": "Lightweight GPT model",
                "max_tokens": 2000,
                "recommended_temperature": 0.8,
            },
            "claude-4.1-opus": {
                "display_name": "Claude 4.1 Opus",
                "description": "Most capable Claude model",
                "max_tokens": 6000,
                "recommended_temperature": 0.6,
            },
            "claude-4.5-sonnet": {
                "display_name": "Claude 4.5 Sonnet",
                "description": "Balanced Claude model",
                "max_tokens": 5000,
                "recommended_temperature": 0.7,
            },
        }

        return model_info.get(
            self.model,
            {
                "display_name": self.model,
                "description": "Unknown model",
                "max_tokens": 4000,
                "recommended_temperature": 0.7,
            },
        )

    async def make_request(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> Dict[str, Any]:
        """Make request to ChadGPT API.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature

        Returns:
            Dict containing response data

        Raises:
            Exception: If API request fails
        """
        if not self._client:
            raise RuntimeError("Provider not initialized. Use async context manager.")

        start_time = datetime.now()

        try:
            # Get model info for validation
            model_info = self._get_model_info()

            # Validate max_tokens against model limits
            if max_tokens > model_info["max_tokens"]:
                logger.warning(
                    f"Max tokens {max_tokens} exceeds model limit {model_info['max_tokens']}. "
                    f"Using model limit instead."
                )
                max_tokens = model_info["max_tokens"]

            # Adjust temperature if needed
            recommended_temp = model_info["recommended_temperature"]
            if abs(temperature - recommended_temp) > 0.3:
                logger.info(
                    f"Temperature {temperature} differs significantly from recommended "
                    f"{recommended_temp} for {self.model}"
                )

            payload = {
                "message": prompt,
                "api_key": self.api_key,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "model": self.model,  # Specify model in request
            }

            logger.debug(
                f"Making request to ChadGPT API with {self.model} ({max_tokens} tokens)"
            )

            response = await self._client.post(
                f"{self.base_url}/{self.model}", json=payload
            )

            response.raise_for_status()
            response_data = response.json()

            # Check if request was successful
            if not response_data.get("is_success") or not isinstance(
                response_data.get("response"), str
            ):
                raise Exception("ChadGPT API returned unsuccessful response")

            # Extract response content
            content = response_data["response"]

            # Estimate token usage (ChadGPT doesn't provide exact counts)
            input_tokens = int(len(prompt.split()) * 1.3)
            response_tokens = int(len(content.split()) * 1.3)
            total_tokens = input_tokens + response_tokens

            response_time = (datetime.now() - start_time).total_seconds()

            result = {
                "response": content,
                "input_tokens": input_tokens,
                "response_tokens": response_tokens,
                "total_tokens": total_tokens,
                "model_used": self.model,
                "model_info": model_info,
            }

            self._update_stats(True, result["total_tokens"], response_time)

            logger.debug(
                f"ChadGPT request completed in {response_time:.2f}s, "
                f"used {result['total_tokens']} tokens with {self.model}"
            )

            return result

        except httpx.HTTPStatusError as e:
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(False, 0, response_time)

            error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
            logger.error(f"ChadGPT API error: {error_msg}")
            raise Exception(error_msg) from e

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(False, 0, response_time)

            logger.error(f"ChadGPT request failed: {str(e)}")
            raise Exception(f"ChadGPT request failed: {str(e)}") from e

    async def check_availability(self) -> bool:
        """Check if ChadGPT API is available.

        Returns:
            True if API is available
        """
        if not self._client:
            return False

        try:
            # Simple test request
            payload = {
                "message": "test",
                "api_key": self.api_key,
                "temperature": 0.1,
                "max_tokens": 1,
                "model": self.model,
            }

            response = await self._client.post(
                f"{self.base_url}/{self.model}", json=payload
            )

            return response.status_code == 200

        except Exception as e:
            logger.debug(f"ChadGPT availability check failed: {str(e)}")
            return False

    def get_supported_models(self) -> Dict[str, Dict[str, Any]]:
        """Get all supported models and their information.

        Returns:
            Dict with all supported models and their info
        """
        return {
            "gpt-5": self._get_model_info_for_model("gpt-5"),
            "gpt-5-mini": self._get_model_info_for_model("gpt-5-mini"),
            "gpt-5-nano": self._get_model_info_for_model("gpt-5-nano"),
            "claude-4.1-opus": self._get_model_info_for_model("claude-4.1-opus"),
            "claude-4.5-sonnet": self._get_model_info_for_model("claude-4.5-sonnet"),
        }

    def _get_model_info_for_model(self, model: str) -> Dict[str, Any]:
        """Get model info for a specific model."""
        original_model = self.model
        self.model = model
        info = self._get_model_info()
        self.model = original_model
        return info
