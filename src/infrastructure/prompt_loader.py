"""Prompt loader for multi-pass code review system.

Following Clean Architecture principles and the Zen of Python.
"""

import logging
from importlib import resources
from typing import List

import yaml

logger = logging.getLogger(__name__)


class PromptLoader:
    """Load prompts embedded in the `prompts.reviewer` package.

    Purpose:
        Provides centralized prompt loading from versioned files packaged as
        importable resources. Manages a registry for discovery and versioning
        without depending on file-system access at runtime.

    Example:
        loader = PromptLoader()
        prompt_template = loader.load_prompt("pass_1_architecture")
        formatted_prompt = prompt_template.format(
            code_snippet=code,
            component_summary=summary
        )
    """

    PROMPTS_PACKAGE = "prompts.reviewer"
    REGISTRY_FILENAME = "prompt_registry.yaml"

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
        prompt_filename = prompt_info["filename"]

        try:
            prompt_content = (
                resources.files(cls.PROMPTS_PACKAGE)
                .joinpath(prompt_filename)
                .read_text(encoding="utf-8")
            )
        except (FileNotFoundError, ModuleNotFoundError) as exc:
            raise FileNotFoundError(
                f"Prompt file '{prompt_filename}' not found in package "
                f"{cls.PROMPTS_PACKAGE}."
            ) from exc

        logger.debug(
            "Loading prompt '%s' from package resource %s",
            prompt_name,
            prompt_filename,
        )
        return prompt_content

    @classmethod
    def _load_registry(cls) -> dict:
        """Load prompt registry from YAML file.

        Returns:
            Registry dictionary with prompts metadata

        Raises:
            FileNotFoundError: If registry file does not exist
            yaml.YAMLError: If registry file is invalid YAML
        """
        try:
            registry_text = (
                resources.files(cls.PROMPTS_PACKAGE)
                .joinpath(cls.REGISTRY_FILENAME)
                .read_text(encoding="utf-8")
            )
        except (FileNotFoundError, ModuleNotFoundError) as exc:
            raise FileNotFoundError(
                f"Prompt registry '{cls.REGISTRY_FILENAME}' not found in package "
                f"{cls.PROMPTS_PACKAGE}."
            ) from exc

        try:
            registry = yaml.safe_load(registry_text)
            if registry is None:
                registry = {"prompts": {}}
            return registry
        except yaml.YAMLError as exc:
            logger.error("Failed to parse prompt registry YAML: %s", exc)
            raise

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
