"""Protocol for configuration providers.

This protocol defines the interface for configuration access.
Infrastructure layer implementations must conform to this protocol.
"""

from typing import Protocol, Any, Optional


class ConfigProviderProtocol(Protocol):
    """Protocol for configuration providers.

    Following Clean Architecture, this protocol is defined in domain layer
    while implementations reside in infrastructure layer.

    Methods:
        get: Get configuration value by key
        get_int: Get integer configuration value
        get_float: Get float configuration value
        get_bool: Get boolean configuration value
        get_str: Get string configuration value
    """

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.

        Args:
            key: Configuration key (supports dot notation, e.g., "llm.temperature")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        ...

    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Integer configuration value
        """
        ...

    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get float configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Float configuration value
        """
        ...

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Boolean configuration value
        """
        ...

    def get_str(self, key: str, default: str = "") -> str:
        """Get string configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            String configuration value
        """
        ...

