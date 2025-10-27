"""Configuration-driven model selection.

Following the Zen of Python:
- Simple is better than complex
- Readability counts
- Explicit is better than implicit
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.domain.entities.model_config import ModelConfig


class ModelSelector:
    """Selects models based on configuration and task requirements.

    Provides intelligent model selection based on:
    - Task type (code_generation, code_review, analysis)
    - Token constraints
    - Latency requirements
    - Model availability

    Following the Zen of Python:
    - There should be one obvious way to do it
    - Simple is better than complex
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize model selector.

        Args:
            config_path: Path to models.yml configuration file
        """
        self.config_path = config_path or self._find_config_path()
        self.config = self._load_config()

    def _find_config_path(self) -> Path:
        """Find configuration file path robustly.

        Searches for the project root by looking for common markers
        (pyproject.toml, setup.py, .git, etc.) and then constructs
        the path to config/models.yml.

        Returns:
            Path to models.yml configuration file

        Raises:
            FileNotFoundError: If project root cannot be determined
        """
        # Start from current file location
        current = Path(__file__).resolve()
        
        # Marker files that indicate project root
        project_markers = ["pyproject.toml", "setup.py", "setup.cfg", ".git"]
        
        # Walk up the directory tree to find project root
        for parent in current.parents:
            for marker in project_markers:
                if (parent / marker).exists():
                    config_path = parent / "config" / "models.yml"
                    if config_path.exists():
                        return config_path
        
        # Fallback: assume we're in src/infrastructure/config
        # and go up to project root
        fallback_root = Path(__file__).resolve().parents[3]
        return fallback_root / "config" / "models.yml"

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file.

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid
        """
        try:
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration.

        Returns:
            Default configuration dictionary
        """
        return {
            "models": {
                "default": "starcoder",
                "by_task": {
                    "code_generation": "starcoder",
                    "code_review": "mistral",
                    "analysis": "qwen",
                },
                "available": {
                    "starcoder": {
                        "name": "StarCoder",
                        "max_input_tokens": 2048,
                        "max_output_tokens": 1024,
                        "best_for": ["code_generation"],
                    },
                    "mistral": {
                        "name": "Mistral",
                        "max_input_tokens": 4096,
                        "max_output_tokens": 2048,
                        "best_for": ["code_review"],
                    },
                },
            },
        }

    def select_model(
        self,
        task_type: Optional[str] = None,
        max_tokens: Optional[int] = None,
        preferred_model: Optional[str] = None,
    ) -> str:
        """Select appropriate model for task.

        Args:
            task_type: Type of task (code_generation, code_review, analysis)
            max_tokens: Maximum tokens required
            preferred_model: User-specified model preference

        Returns:
            Selected model name
        """
        # Use preferred model if specified and available
        if preferred_model and self._is_available(preferred_model):
            return preferred_model

        # Select by task type
        if task_type:
            model = self._select_by_task_type(task_type)
            if model:
                return model

        # Select by constraints
        if max_tokens:
            model = self._select_by_constraints(max_tokens)
            if model:
                return model

        # Fall back to default
        return self.config["models"]["default"]

    def _select_by_task_type(self, task_type: str) -> Optional[str]:
        """Select model based on task type.

        Args:
            task_type: Type of task

        Returns:
            Selected model name or None
        """
        task_mapping = self.config["models"].get("by_task", {})
        model_name = task_mapping.get(task_type)

        if model_name and self._is_available(model_name):
            return model_name

        return None

    def _select_by_constraints(self, max_tokens: int) -> Optional[str]:
        """Select model based on token constraints.

        Args:
            max_tokens: Maximum tokens required

        Returns:
            Selected model name or None
        """
        available = self.config["models"].get("available", {})

        # Find models that can handle the token requirement
        suitable_models = []
        for name, config in available.items():
            if not self._is_available(name):
                continue

            max_input = config.get("max_input_tokens", 0)
            if max_input >= max_tokens:
                suitable_models.append((name, config))

        if not suitable_models:
            return None

        # Return the model with closest capacity
        suitable_models.sort(key=lambda x: x[1]["max_input_tokens"])
        return suitable_models[0][0]

    def _is_available(self, model_name: str) -> bool:
        """Check if model is available.

        Args:
            model_name: Name of model to check

        Returns:
            True if model is available
        """
        available = self.config["models"].get("available", {})
        return model_name in available

    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get configuration for specific model.

        Args:
            model_name: Name of model

        Returns:
            ModelConfig or None if not found
        """
        available = self.config["models"].get("available", {})

        if model_name not in available:
            return None

        config_dict = available[model_name]

        return ModelConfig(
            config_id=f"{model_name}_config",
            model_name=model_name,
            provider="huggingface",
            max_tokens=config_dict.get("max_input_tokens", 2048)
            + config_dict.get("max_output_tokens", 1024),
            temperature=config_dict.get("temperature_default", 0.7),
        )

    def get_fallback_order(self) -> List[str]:
        """Get ordered list of fallback models.

        Returns:
            List of model names in fallback order
        """
        fallback = self.config["models"].get("fallback", {})
        return fallback.get("order", [self.config["models"]["default"]])

    def list_available_models(self) -> List[str]:
        """List all available models.

        Returns:
            List of available model names
        """
        available = self.config["models"].get("available", {})
        return [name for name in available.keys() if self._is_available(name)]

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a model.

        Args:
            model_name: Name of model

        Returns:
            Model information dictionary or None
        """
        available = self.config["models"].get("available", {})

        if model_name not in available:
            return None

        return available[model_name].copy()
