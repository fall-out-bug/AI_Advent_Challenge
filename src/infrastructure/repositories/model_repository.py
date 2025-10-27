"""Model repository implementation stub."""

from typing import List, Optional

from src.domain.entities.model_config import ModelConfig
from src.domain.repositories.model_repository import ModelRepository


class InMemoryModelRepository(ModelRepository):
    """In-memory model repository implementation."""

    def __init__(self) -> None:
        """Initialize repository."""
        self._storage: dict[str, ModelConfig] = {}

    async def save(self, config: ModelConfig) -> None:
        """Save or update model configuration."""
        self._storage[config.config_id] = config

    async def get_by_id(self, config_id: str) -> Optional[ModelConfig]:
        """Get model configuration by ID."""
        return self._storage.get(config_id)

    async def get_all(self) -> List[ModelConfig]:
        """Get all model configurations."""
        return list(self._storage.values())

    async def get_active(self) -> List[ModelConfig]:
        """Get active model configurations."""
        return [config for config in self._storage.values() if config.is_active]

    async def delete(self, config_id: str) -> bool:
        """Delete model configuration."""
        if config_id in self._storage:
            del self._storage[config_id]
            return True
        return False
