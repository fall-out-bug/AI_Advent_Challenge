"""Prompt loader for multi-pass code review system.

Following Clean Architecture principles and the Zen of Python.
"""

import logging
from pathlib import Path
from typing import List

import yaml

logger = logging.getLogger(__name__)


class PromptLoader:
    """Load prompts from prompts/v1/ directory.

    Purpose:
        Provides centralized prompt loading from versioned prompt files.
        Manages prompt registry for discovery and versioning.

    Example:
        loader = PromptLoader()
        prompt_template = loader.load_prompt("pass_1_architecture")
        formatted_prompt = prompt_template.format(
            code_snippet=code,
            component_summary=summary
        )
    """

    PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts" / "v1"
    REGISTRY_FILE = PROMPTS_DIR / "prompt_registry.yaml"

    @classmethod
    def load_prompt(cls, prompt_name: str) -> str:
        """Load prompt by name from registry.

        Purpose:
            Loads prompt template file based on registry mapping.
            Validates file existence and returns content.

        Args:
            prompt_name: Name of prompt from registry (e.g., "pass_1_architecture")

        Returns:
            Prompt template content as string

        Raises:
            ValueError: If prompt name not found in registry
            FileNotFoundError: If prompt file does not exist

        Example:
            template = PromptLoader.load_prompt("pass_1_architecture")
        """
        registry = cls._load_registry()

        if prompt_name not in registry.get("prompts", {}):
            available = list(registry.get("prompts", {}).keys())
            raise ValueError(
                f"Prompt '{prompt_name}' not found in registry. "
                f"Available prompts: {available}"
            )

        prompt_info = registry["prompts"][prompt_name]
        prompt_file = cls.PROMPTS_DIR / prompt_info["filename"]

        if not prompt_file.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_file}. "
                f"Expected path: {cls.PROMPTS_DIR}"
            )

        logger.debug(f"Loading prompt '{prompt_name}' from {prompt_file}")
        with open(prompt_file, "r", encoding="utf-8") as f:
            content = f.read()

        return content

    @classmethod
    def _load_registry(cls) -> dict:
        """Load prompt registry from YAML file.

        Returns:
            Registry dictionary with prompts metadata

        Raises:
            FileNotFoundError: If registry file does not exist
            yaml.YAMLError: If registry file is invalid YAML
        """
        if not cls.REGISTRY_FILE.exists():
            logger.warning(
                f"Registry file not found: {cls.REGISTRY_FILE}. "
                "Creating default registry structure..."
            )
            cls._create_default_registry()

        with open(cls.REGISTRY_FILE, "r", encoding="utf-8") as f:
            try:
                registry = yaml.safe_load(f)
                if registry is None:
                    registry = {"prompts": {}}
                return registry
            except yaml.YAMLError as e:
                logger.error(f"Failed to parse registry YAML: {e}")
                raise

    @classmethod
    def _create_default_registry(cls) -> None:
        """Create default registry structure if missing."""
        default_registry = {
            "version": "1.0",
            "created_at": "2025-01-XX",
            "author": "multi_pass_review_system",
            "description": "Multi-pass code review prompts for Docker, Airflow, Spark, MLflow",
            "prompts": {},
        }

        cls.PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(cls.REGISTRY_FILE, "w", encoding="utf-8") as f:
            yaml.dump(default_registry, f, default_flow_style=False)

        logger.info(f"Created default registry at {cls.REGISTRY_FILE}")

    @classmethod
    def list_prompts(cls) -> List[str]:
        """List all available prompts from registry.

        Returns:
            List of prompt names

        Example:
            prompts = PromptLoader.list_prompts()
            # Returns: ['pass_1_architecture', 'pass_2_docker', ...]
        """
        registry = cls._load_registry()
        return list(registry.get("prompts", {}).keys())

    @classmethod
    def prompt_exists(cls, prompt_name: str) -> bool:
        """Check if prompt exists in registry.

        Args:
            prompt_name: Name of prompt to check

        Returns:
            True if prompt exists, False otherwise
        """
        try:
            registry = cls._load_registry()
            return prompt_name in registry.get("prompts", {})
        except Exception:
            return False

