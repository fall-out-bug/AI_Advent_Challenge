"""Configuration system for external API providers."""

import json
import logging
import os
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """Supported external API provider types."""

    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    CHADGPT = "chadgpt"
    LOCAL = "local"


@dataclass
class ProviderConfig:
    """Configuration for an external API provider."""

    provider_type: ProviderType
    api_key: str
    model: str
    timeout: float = 60.0
    enabled: bool = True
    max_tokens: int = 4000
    temperature: float = 0.7

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider_type": self.provider_type.value,
            "api_key": self.api_key,
            "model": self.model,
            "timeout": self.timeout,
            "enabled": self.enabled,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderConfig":
        """Create from dictionary."""
        return cls(
            provider_type=ProviderType(data["provider_type"]),
            api_key=data["api_key"],
            model=data["model"],
            timeout=data.get("timeout", 60.0),
            enabled=data.get("enabled", True),
            max_tokens=data.get("max_tokens", 4000),
            temperature=data.get("temperature", 0.7),
        )


class ExternalAPIConfig:
    """Configuration manager for external API providers."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration manager.

        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file or os.getenv(
            "EXTERNAL_API_CONFIG", "external_api_config.json"
        )
        self.providers: Dict[str, ProviderConfig] = {}
        self.default_provider: Optional[str] = None
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file or environment."""
        # Try to load from file first
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                self._load_from_dict(config_data)
                logger.info(f"Loaded external API config from {self.config_file}")
                return
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")

        # Load from environment variables
        self._load_from_environment()
        logger.info("Loaded external API config from environment variables")

    def _load_from_dict(self, config_data: Dict[str, Any]) -> None:
        """Load configuration from dictionary."""
        providers_data = config_data.get("providers", {})
        for name, provider_data in providers_data.items():
            try:
                self.providers[name] = ProviderConfig.from_dict(provider_data)
            except Exception as e:
                logger.error(f"Failed to load provider {name}: {e}")

        self.default_provider = config_data.get("default_provider")

    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        # ChatGPT configuration
        chatgpt_key = os.getenv("OPENAI_API_KEY")
        if chatgpt_key:
            self.providers["chatgpt"] = ProviderConfig(
                provider_type=ProviderType.CHATGPT,
                api_key=chatgpt_key,
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                timeout=float(os.getenv("OPENAI_TIMEOUT", "60.0")),
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4000")),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            )

        # ChadGPT configuration
        chadgpt_key = os.getenv("CHADGPT_API_KEY")
        if chadgpt_key:
            self.providers["chadgpt"] = ProviderConfig(
                provider_type=ProviderType.CHADGPT,
                api_key=chadgpt_key,
                model=os.getenv("CHADGPT_MODEL", "gpt-5-mini"),
                timeout=float(os.getenv("CHADGPT_TIMEOUT", "60.0")),
                max_tokens=int(os.getenv("CHADGPT_MAX_TOKENS", "4000")),
                temperature=float(os.getenv("CHADGPT_TEMPERATURE", "0.7")),
            )

        # Set default provider
        self.default_provider = os.getenv("DEFAULT_EXTERNAL_PROVIDER")
        if not self.default_provider and self.providers:
            self.default_provider = list(self.providers.keys())[0]

    def save_config(self) -> None:
        """Save configuration to file."""
        config_data = {
            "providers": {
                name: provider.to_dict() for name, provider in self.providers.items()
            },
            "default_provider": self.default_provider,
        }

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved external API config to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config file {self.config_file}: {e}")

    def add_provider(self, name: str, config: ProviderConfig) -> None:
        """Add a new provider configuration.

        Args:
            name: Provider name
            config: Provider configuration
        """
        self.providers[name] = config
        if not self.default_provider:
            self.default_provider = name
        logger.info(f"Added provider {name} ({config.provider_type.value})")

    def remove_provider(self, name: str) -> bool:
        """Remove a provider configuration.

        Args:
            name: Provider name to remove

        Returns:
            True if provider was removed
        """
        if name in self.providers:
            del self.providers[name]
            if self.default_provider == name:
                self.default_provider = (
                    list(self.providers.keys())[0] if self.providers else None
                )
            logger.info(f"Removed provider {name}")
            return True
        return False

    def get_provider(self, name: Optional[str] = None) -> Optional[ProviderConfig]:
        """Get provider configuration.

        Args:
            name: Provider name, if None uses default

        Returns:
            Provider configuration or None
        """
        provider_name = name or self.default_provider
        if provider_name and provider_name in self.providers:
            return self.providers[provider_name]
        return None

    def get_enabled_providers(self) -> Dict[str, ProviderConfig]:
        """Get all enabled providers.

        Returns:
            Dictionary of enabled providers
        """
        return {
            name: config for name, config in self.providers.items() if config.enabled
        }

    def set_default_provider(self, name: str) -> bool:
        """Set default provider.

        Args:
            name: Provider name

        Returns:
            True if provider exists and was set as default
        """
        if name in self.providers:
            self.default_provider = name
            logger.info(f"Set default provider to {name}")
            return True
        return False

    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration.

        Returns:
            Validation results
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "providers": {},
        }

        if not self.providers:
            results["warnings"].append("No providers configured")

        if not self.default_provider:
            results["warnings"].append("No default provider set")
        elif self.default_provider not in self.providers:
            results["errors"].append(
                f"Default provider '{self.default_provider}' not found"
            )
            results["valid"] = False

        for name, config in self.providers.items():
            provider_results = {
                "valid": True,
                "errors": [],
                "warnings": [],
            }

            if not config.api_key:
                provider_results["errors"].append("API key is required")
                provider_results["valid"] = False

            if config.max_tokens <= 0:
                provider_results["errors"].append("max_tokens must be positive")
                provider_results["valid"] = False

            if not 0.0 <= config.temperature <= 2.0:
                provider_results["warnings"].append(
                    "temperature should be between 0.0 and 2.0"
                )

            if config.timeout <= 0:
                provider_results["errors"].append("timeout must be positive")
                provider_results["valid"] = False

            results["providers"][name] = provider_results

            if not provider_results["valid"]:
                results["valid"] = False

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get configuration statistics.

        Returns:
            Configuration statistics
        """
        enabled_count = sum(1 for config in self.providers.values() if config.enabled)

        return {
            "total_providers": len(self.providers),
            "enabled_providers": enabled_count,
            "default_provider": self.default_provider,
            "provider_types": {
                name: config.provider_type.value
                for name, config in self.providers.items()
            },
        }


# Global configuration instance
_config_instance: Optional[ExternalAPIConfig] = None


def get_config() -> ExternalAPIConfig:
    """Get global configuration instance.

    Returns:
        Global configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ExternalAPIConfig()
    return _config_instance


def reset_config() -> None:
    """Reset global configuration instance."""
    global _config_instance
    _config_instance = None
