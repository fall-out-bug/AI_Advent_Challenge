"""Experiment template loader and validator.

Following the Zen of Python:
- Simple is better than complex
- Readability counts
- Explicit is better than implicit
"""

import yaml
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)


class ExperimentTemplate:
    """Experiment template with validation and instantiation.

    Provides loading and validation of experiment templates
    from YAML configuration files.

    Following the Zen of Python:
    - There should be one obvious way to do it
    - Simple is better than complex
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize template from configuration.

        Args:
            config: Template configuration dictionary
        """
        self.config = config
        self._validate()

    def _validate(self) -> None:
        """Validate template configuration.

        Raises:
            ValueError: If template is invalid
        """
        if "experiment" not in self.config:
            raise ValueError("Template must contain 'experiment' key")

        experiment = self.config["experiment"]

        # Validate required fields
        required = ["name", "description"]
        for field in required:
            if field not in experiment:
                raise ValueError(f"Experiment must contain '{field}' field")

    @classmethod
    def load_from_file(cls, template_path: Path) -> "ExperimentTemplate":
        """Load template from YAML file.

        Args:
            template_path: Path to template file

        Returns:
            ExperimentTemplate instance

        Raises:
            FileNotFoundError: If template file doesn't exist
            ValueError: If template is invalid
        """
        try:
            with open(template_path, "r") as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded template from {template_path}")
            return cls(config)
        except FileNotFoundError:
            logger.error(f"Template file not found: {template_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in template: {e}")
            raise ValueError(f"Invalid YAML: {e}")

    @classmethod
    def load_from_name(
        cls, name: str, template_dir: Optional[Path] = None
    ) -> "ExperimentTemplate":
        """Load template by name.

        Args:
            name: Template name (e.g., 'model_comparison')
            template_dir: Optional template directory path

        Returns:
            ExperimentTemplate instance
        """
        if template_dir is None:
            # Go up from src/domain/templates/ to root, then to config/experiment_templates/
            template_dir = (
                Path(__file__).parent.parent.parent.parent
                / "config"
                / "experiment_templates"
            )

        template_path = template_dir / f"{name}.yml"
        return cls.load_from_file(template_path)

    def get_experiment_name(self) -> str:
        """Get experiment name.

        Returns:
            Experiment name
        """
        return self.config["experiment"]["name"]

    def get_description(self) -> str:
        """Get experiment description.

        Returns:
            Experiment description
        """
        return self.config["experiment"]["description"]

    def get_models(self) -> List[Dict[str, Any]]:
        """Get list of models to test.

        Returns:
            List of model configurations
        """
        return self.config["experiment"].get("models", [])

    def get_task_description(self) -> Optional[str]:
        """Get task description.

        Returns:
            Task description or None
        """
        return self.config["experiment"].get("task", {}).get("description")

    def get_metrics(self) -> List[str]:
        """Get list of metrics to collect.

        Returns:
            List of metric names
        """
        return self.config["experiment"].get("metrics", [])

    def get_aggregation_strategy(self) -> str:
        """Get aggregation strategy.

        Returns:
            Aggregation strategy name
        """
        return (
            self.config["experiment"].get("aggregation", {}).get("strategy", "average")
        )


def list_available_templates(template_dir: Optional[Path] = None) -> List[str]:
    """List available experiment templates.

    Args:
        template_dir: Optional template directory path

    Returns:
        List of template names
    """
    if template_dir is None:
        # Go up from src/domain/templates/ to root, then to config/experiment_templates/
        template_dir = (
            Path(__file__).parent.parent.parent.parent
            / "config"
            / "experiment_templates"
        )

    if not template_dir.exists():
        return []

    return [f.stem for f in template_dir.glob("*.yml")]
