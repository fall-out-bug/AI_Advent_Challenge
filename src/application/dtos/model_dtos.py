"""Model data transfer objects."""

from dataclasses import dataclass


@dataclass
class ModelConfigDTO:
    """
    Data transfer object for model configuration.

    Attributes:
        config_id: Configuration identifier
        model_name: Model name
        provider: Model provider
        max_tokens: Maximum tokens
        temperature: Sampling temperature
        is_active: Active status
    """

    config_id: str
    model_name: str
    provider: str
    max_tokens: int
    temperature: float
    is_active: bool

    def to_dict(self) -> dict:
        """
        Convert DTO to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "config_id": self.config_id,
            "model_name": self.model_name,
            "provider": self.provider,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "is_active": self.is_active,
        }
