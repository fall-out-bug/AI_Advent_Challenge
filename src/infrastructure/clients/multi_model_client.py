"""Multi-model client support.

Following the Zen of Python:
- Simple is better than complex
- Readability counts
- Explicit is better than implicit
"""

from typing import Dict, List, Optional


class MultiModelSupport:
    """
    Support for multi-model operations.

    Provides model selection, switching, and information retrieval.
    """

    # Available models and their configurations
    AVAILABLE_MODELS = {
        "starcoder": {
            "name": "starcoder",
            "max_tokens": 2048,
            "recommended_tokens": 1536,
            "temperature_range": (0.0, 1.0),
        },
        "mistral": {
            "name": "mistral",
            "max_tokens": 4096,
            "recommended_tokens": 3072,
            "temperature_range": (0.0, 1.0),
        },
        "qwen": {
            "name": "qwen",
            "max_tokens": 4096,
            "recommended_tokens": 3072,
            "temperature_range": (0.0, 1.0),
        },
        "tinyllama": {
            "name": "tinyllama",
            "max_tokens": 2048,
            "recommended_tokens": 1536,
            "temperature_range": (0.0, 1.0),
        },
    }

    def __init__(self, current_model: str = "starcoder"):
        """
        Initialize multi-model support.

        Args:
            current_model: Currently selected model
        """
        self.current_model = current_model
        self.model_history: List[str] = [current_model]

    def get_available_models(self) -> List[str]:
        """
        Get list of available model names.

        Returns:
            List of model names
        """
        return list(self.AVAILABLE_MODELS.keys())

    def get_model_info(self, model_name: str) -> Optional[Dict[str, any]]:
        """
        Get information about a specific model.

        Args:
            model_name: Name of the model

        Returns:
            Model information dictionary or None if not found
        """
        return self.AVAILABLE_MODELS.get(model_name)

    def select_model(self, model_name: str) -> bool:
        """
        Select a model by name.

        Args:
            model_name: Name of the model to select

        Returns:
            True if model was selected, False if not available
        """
        if model_name in self.AVAILABLE_MODELS:
            self.current_model = model_name
            if model_name not in self.model_history:
                self.model_history.append(model_name)
            return True
        return False

    def get_current_model(self) -> str:
        """
        Get currently selected model.

        Returns:
            Currently selected model name
        """
        return self.current_model

    def validate_model_availability(self, model_name: str) -> bool:
        """
        Check if a model is available.

        Args:
            model_name: Name of the model

        Returns:
            True if model is available, False otherwise
        """
        return model_name in self.AVAILABLE_MODELS

    def get_model_history(self) -> List[str]:
        """
        Get history of models used.

        Returns:
            List of model names in order of selection
        """
        return self.model_history.copy()

    def get_recommended_tokens(self, model_name: Optional[str] = None) -> int:
        """
        Get recommended token limit for a model.

        Args:
            model_name: Name of the model (defaults to current)

        Returns:
            Recommended token limit
        """
        model = model_name or self.current_model
        info = self.get_model_info(model)
        return info["recommended_tokens"] if info else 1536

    def get_max_tokens(self, model_name: Optional[str] = None) -> int:
        """
        Get maximum token limit for a model.

        Args:
            model_name: Name of the model (defaults to current)

        Returns:
            Maximum token limit
        """
        model = model_name or self.current_model
        info = self.get_model_info(model)
        return info["max_tokens"] if info else 2048
