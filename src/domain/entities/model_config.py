"""Model configuration entity with identity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict


@dataclass
class ModelConfig:
    """
    Domain entity representing model configuration.

    Attributes:
        config_id: Unique identifier for configuration
        model_name: Name of the model
        provider: Model provider
        max_tokens: Maximum tokens allowed
        temperature: Sampling temperature
        top_p: Top-p sampling parameter
        presence_penalty: Presence penalty
        frequency_penalty: Frequency penalty
        system_prompt: System prompt template
        is_active: Whether configuration is active
        created_at: Configuration creation timestamp
        updated_at: Last update timestamp
        metadata: Optional additional metadata
    """

    config_id: str
    model_name: str
    provider: str
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    system_prompt: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate model configuration."""
        if self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError("Temperature must be between 0 and 2")
        if not (0.0 <= self.top_p <= 1.0):
            raise ValueError("Top-p must be between 0 and 1")

    def activate(self) -> None:
        """Activate configuration."""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate configuration."""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def update_temperature(self, temperature: float) -> None:
        """
        Update sampling temperature.

        Args:
            temperature: New temperature value
        """
        if not (0.0 <= temperature <= 2.0):
            raise ValueError("Temperature must be between 0 and 2")
        self.temperature = temperature
        self.updated_at = datetime.utcnow()

    def add_metadata(self, key: str, value: str) -> None:
        """
        Add metadata to configuration.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()
