"""Unified adapter for both local and external API providers."""

import logging
from typing import Any, Dict, Optional, Union
from datetime import datetime

from agents.core.model_client_adapter import ModelClientAdapter
from agents.core.external_api_provider import (
    ExternalAPIProvider, 
    ChatGPTProvider, 
    ChadGPTProvider
)
from agents.core.external_api_config import get_config, ProviderType
from agents.core.smart_model_selector import get_smart_selector, ModelRecommendation

# Configure logging
logger = logging.getLogger(__name__)


class UnifiedModelAdapter:
    """
    Unified adapter that can work with both local models and external APIs.
    
    This adapter follows the Strategy pattern, allowing seamless switching
    between different model providers without changing the agent code.
    """

    def __init__(
        self, 
        model_name: str = "starcoder",
        external_provider: Optional[str] = None,
        timeout: float = 600.0
    ):
        """Initialize the unified model adapter.

        Args:
            model_name: Name of the model to use
            external_provider: External provider name (if using external API)
            timeout: Request timeout in seconds
        """
        self.model_name = model_name
        self.external_provider = external_provider
        self.timeout = timeout
        
        # Initialize adapters
        self.local_adapter: Optional[ModelClientAdapter] = None
        self.external_adapter: Optional[ExternalAPIProvider] = None
        
        # Determine which adapter to use
        self._initialize_adapter()

    def _initialize_adapter(self) -> None:
        """Initialize the appropriate adapter based on configuration."""
        if self.external_provider:
            # Use external API provider
            config_manager = get_config()
            provider_config = config_manager.get_provider(self.external_provider)
            
            if not provider_config:
                raise ValueError(f"External provider '{self.external_provider}' not found")
            
            if not provider_config.enabled:
                raise ValueError(f"External provider '{self.external_provider}' is disabled")
            
            # Create external provider based on type
            if provider_config.provider_type == ProviderType.CHATGPT:
                self.external_adapter = ChatGPTProvider(
                    api_key=provider_config.api_key,
                    model=provider_config.model,
                    timeout=provider_config.timeout
                )
            elif provider_config.provider_type == ProviderType.CHADGPT:
                self.external_adapter = ChadGPTProvider(
                    api_key=provider_config.api_key,
                    model=provider_config.model,
                    timeout=provider_config.timeout
                )
            else:
                raise ValueError(f"Unsupported provider type: {provider_config.provider_type}")
            
            logger.info(f"Initialized external adapter: {self.external_provider}")
            
        else:
            # Use local model adapter
            self.local_adapter = ModelClientAdapter(
                model_name=self.model_name,
                timeout=self.timeout
            )
            logger.info(f"Initialized local adapter: {self.model_name}")

    async def make_request(
        self, 
        prompt: str, 
        max_tokens: int, 
        temperature: float
    ) -> Dict[str, Any]:
        """Make request to model through appropriate adapter.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature

        Returns:
            Dict containing response data

        Raises:
            Exception: If model request fails
        """
        if self.external_adapter:
            # Use external API
            async with self.external_adapter as provider:
                return await provider.make_request(prompt, max_tokens, temperature)
        else:
            # Use local model
            if not self.local_adapter:
                raise RuntimeError("Local adapter not initialized")
            return await self.local_adapter.make_request(prompt, max_tokens, temperature)

    async def check_availability(self) -> bool:
        """Check if model is available.

        Returns:
            True if model is available
        """
        if self.external_adapter:
            # Check external API availability
            async with self.external_adapter as provider:
                return await provider.check_availability()
        else:
            # Check local model availability
            if not self.local_adapter:
                return False
            return await self.local_adapter.check_availability()

    async def close(self) -> None:
        """Close adapter resources."""
        if self.local_adapter:
            await self.local_adapter.close()
        # External adapters are closed automatically via context manager

    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current provider.

        Returns:
            Provider information
        """
        if self.external_adapter:
            config_manager = get_config()
            provider_config = config_manager.get_provider(self.external_provider)
            
            info = {
                "type": "external",
                "provider": self.external_provider,
                "provider_type": provider_config.provider_type.value if provider_config else "unknown",
                "model": provider_config.model if provider_config else "unknown",
                "timeout": provider_config.timeout if provider_config else self.timeout,
            }
            
            # Add smart model info for ChadGPT
            if (provider_config and 
                provider_config.provider_type.value == "chadgpt" and 
                hasattr(self.external_adapter, 'get_supported_models')):
                info["supported_models"] = self.external_adapter.get_supported_models()
                info["current_model_info"] = self.external_adapter._get_model_info()
            
            return info
        else:
            return {
                "type": "local",
                "model": self.model_name,
                "timeout": self.timeout,
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics.

        Returns:
            Adapter statistics
        """
        if self.external_adapter:
            return {
                "provider": self.external_provider,
                "stats": self.external_adapter.stats,
            }
        else:
            return {
                "provider": "local",
                "model": self.model_name,
                "stats": "Local model stats not available",
            }


class ModelProviderFactory:
    """Factory for creating model adapters with different configurations."""

    @staticmethod
    def create_local_adapter(
        model_name: str = "starcoder",
        timeout: float = 600.0
    ) -> UnifiedModelAdapter:
        """Create adapter for local model.

        Args:
            model_name: Name of local model
            timeout: Request timeout

        Returns:
            Unified model adapter configured for local model
        """
        return UnifiedModelAdapter(
            model_name=model_name,
            external_provider=None,
            timeout=timeout
        )

    @staticmethod
    def create_external_adapter(
        provider_name: str,
        timeout: float = 600.0
    ) -> UnifiedModelAdapter:
        """Create adapter for external API provider.

        Args:
            provider_name: Name of external provider
            timeout: Request timeout

        Returns:
            Unified model adapter configured for external API

        Raises:
            ValueError: If provider not found or disabled
        """
        config_manager = get_config()
        provider_config = config_manager.get_provider(provider_name)
        
        if not provider_config:
            raise ValueError(f"Provider '{provider_name}' not found")
        
        if not provider_config.enabled:
            raise ValueError(f"Provider '{provider_name}' is disabled")
        
        return UnifiedModelAdapter(
            model_name=provider_config.model,
            external_provider=provider_name,
            timeout=timeout
        )

    @staticmethod
    def create_auto_adapter(
        preferred_provider: Optional[str] = None,
        fallback_to_local: bool = True,
        timeout: float = 600.0
    ) -> UnifiedModelAdapter:
        """Create adapter with automatic provider selection.

        Args:
            preferred_provider: Preferred external provider name
            fallback_to_local: Whether to fallback to local model
            timeout: Request timeout

        Returns:
            Unified model adapter with automatic provider selection

        Raises:
            RuntimeError: If no suitable provider found
        """
        config_manager = get_config()
        
        # Try preferred provider first
        if preferred_provider:
            provider_config = config_manager.get_provider(preferred_provider)
            if provider_config and provider_config.enabled:
                try:
                    adapter = ModelProviderFactory.create_external_adapter(
                        preferred_provider, timeout
                    )
                    logger.info(f"Using preferred provider: {preferred_provider}")
                    return adapter
                except Exception as e:
                    logger.warning(f"Preferred provider {preferred_provider} failed: {e}")
        
        # Try default external provider
        default_provider = config_manager.default_provider
        if default_provider:
            provider_config = config_manager.get_provider(default_provider)
            if provider_config and provider_config.enabled:
                try:
                    adapter = ModelProviderFactory.create_external_adapter(
                        default_provider, timeout
                    )
                    logger.info(f"Using default provider: {default_provider}")
                    return adapter
                except Exception as e:
                    logger.warning(f"Default provider {default_provider} failed: {e}")
        
        # Try any enabled external provider
        enabled_providers = config_manager.get_enabled_providers()
        for provider_name in enabled_providers:
            try:
                adapter = ModelProviderFactory.create_external_adapter(
                    provider_name, timeout
                )
                logger.info(f"Using available provider: {provider_name}")
                return adapter
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed: {e}")
        
        # Fallback to local model
        if fallback_to_local:
            logger.info("Falling back to local model")
            return ModelProviderFactory.create_local_adapter(timeout=timeout)
        
        raise RuntimeError("No suitable model provider found")


# Convenience functions for easy usage
async def create_model_adapter(
    model_name: Optional[str] = None,
    external_provider: Optional[str] = None,
    timeout: float = 600.0
) -> UnifiedModelAdapter:
    """Create a model adapter with specified configuration.

    Args:
        model_name: Name of local model (if using local)
        external_provider: Name of external provider (if using external)
        timeout: Request timeout

    Returns:
        Configured model adapter

    Raises:
        ValueError: If configuration is invalid
    """
    if external_provider and model_name:
        raise ValueError("Cannot specify both external_provider and model_name")
    
    if external_provider:
        return ModelProviderFactory.create_external_adapter(external_provider, timeout)
    else:
        return ModelProviderFactory.create_local_adapter(
            model_name or "starcoder", timeout
        )


    async def get_available_providers() -> Dict[str, Any]:
        """Get information about all available providers.

        Returns:
            Dictionary with provider information
        """
        config_manager = get_config()
        providers_info = {}
        
        # Check local models (this would need to be implemented based on your local setup)
        providers_info["local"] = {
            "available": True,  # Assuming local models are always available
            "models": ["starcoder", "mistral", "qwen", "tinyllama"],
        }
        
        # Check external providers
        for provider_name, provider_config in config_manager.providers.items():
            if provider_config.enabled:
                try:
                    adapter = ModelProviderFactory.create_external_adapter(provider_name)
                    is_available = await adapter.check_availability()
                    providers_info[provider_name] = {
                        "available": is_available,
                        "provider_type": provider_config.provider_type.value,
                        "model": provider_config.model,
                        "timeout": provider_config.timeout,
                    }
                    
                    # Add smart model info for ChadGPT
                    if (provider_config.provider_type.value == "chadgpt" and 
                        hasattr(adapter.external_adapter, 'get_supported_models')):
                        providers_info[provider_name]["supported_models"] = (
                            adapter.external_adapter.get_supported_models()
                        )
                        
                except Exception as e:
                    providers_info[provider_name] = {
                        "available": False,
                        "error": str(e),
                    }
        
        return providers_info
