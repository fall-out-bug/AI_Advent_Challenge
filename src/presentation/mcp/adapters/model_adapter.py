"""Adapter for model-related operations."""
import sys
from pathlib import Path
from typing import Any

_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_root / "shared"))

from src.presentation.mcp.exceptions import MCPModelError


def _get_unified_client():
    """Import UnifiedModelClient at runtime."""
    from shared_package.clients.unified_client import UnifiedModelClient
    return UnifiedModelClient


def _get_model_configs():
    """Import MODEL_CONFIGS at runtime."""
    from shared_package.config.models import MODEL_CONFIGS
    return MODEL_CONFIGS


class ModelAdapter:
    """Adapter for model listing and availability checks."""

    def __init__(self, unified_client: Any) -> None:
        """Initialize model adapter."""
        self.unified_client = unified_client

    def list_available_models(self) -> dict[str, Any]:
        """List all configured models."""
        try:
            MODEL_CONFIGS = _get_model_configs()
            local_models = []
            api_models = []

            for name, config in MODEL_CONFIGS.items():
                model_info = self._build_model_info(name, config)
                if config.get("type") == "local":
                    model_info["port"] = config.get("port")
                    local_models.append(model_info)
                else:
                    model_info["provider"] = config.get("display_name")
                    api_models.append(model_info)

            return {"local_models": local_models, "api_models": api_models}
        except Exception as e:
            raise MCPModelError(f"Failed to list models: {e}")

    def _build_model_info(self, name: str, config: dict[str, Any]) -> dict[str, Any]:
        """Build model information dictionary."""
        return {
            "name": name,
            "display_name": config.get("display_name", name),
            "description": config.get("description", ""),
        }

    async def check_model_availability(self, model_name: str) -> dict[str, bool]:
        """Check if model is available."""
        try:
            is_available = await self.unified_client.check_availability(model_name)
            return {"available": is_available}
        except Exception as e:
            raise MCPModelError(
                f"Failed to check model availability: {e}",
                model_name=model_name,
            )
