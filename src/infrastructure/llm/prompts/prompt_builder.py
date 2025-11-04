"""Prompt builder with template support and language handling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class PromptContext:
    """Context for prompt building.

    Args:
        language: Target language (ru/en).
        include_examples: Whether to include few-shot examples.
        metadata: Additional metadata for prompt customization.
    """

    language: Literal["ru", "en"] = "ru"
    include_examples: bool = True
    metadata: dict[str, Any] | None = None


class PromptBuilder:
    """Builder for constructing LLM prompts with templates.

    Purpose:
        Provides structured way to build prompts with templates,
        language support, and few-shot examples.

    Args:
        context: Prompt context configuration.
    """

    def __init__(self, context: PromptContext | None = None) -> None:
        self.context = context or PromptContext()

    def build(
        self,
        template: str,
        variables: dict[str, Any] | None = None,
        examples: list[str] | None = None,
    ) -> str:
        """Build prompt from template with variable substitution.

        Purpose:
            Constructs prompt by substituting variables in template
            and optionally adding few-shot examples.

        Args:
            template: Template string with {variable} placeholders.
            variables: Dictionary of variables to substitute.
            examples: Optional list of example strings to append.

        Returns:
            Complete prompt string.

        Example:
            >>> builder = PromptBuilder(PromptContext(language="ru"))
            >>> template = "Summarize: {text}"
            >>> prompt = builder.build(template, {"text": "Hello world"})
        """
        variables = variables or {}
        prompt = template.format(**variables)

        if examples and self.context.include_examples:
            examples_text = self._format_examples(examples)
            prompt = f"{prompt}\n\n{examples_text}"

        return prompt.strip()

    def _format_examples(self, examples: list[str]) -> str:
        """Format few-shot examples for prompt.

        Args:
            examples: List of example strings.

        Returns:
            Formatted examples section.
        """
        if self.context.language == "ru":
            header = "Примеры:\n"
        else:
            header = "Examples:\n"

        formatted = [header]
        for i, example in enumerate(examples, 1):
            formatted.append(f"{i}. {example}")

        return "\n".join(formatted)

    def add_instructions(self, prompt: str, instructions: list[str]) -> str:
        """Add instructions section to prompt.

        Args:
            prompt: Base prompt.
            instructions: List of instruction strings.

        Returns:
            Prompt with instructions added.
        """
        if self.context.language == "ru":
            header = "ИНСТРУКЦИИ:\n"
        else:
            header = "INSTRUCTIONS:\n"

        instructions_text = "\n".join(f"- {inst}" for inst in instructions)
        return f"{prompt}\n\n{header}{instructions_text}"

    def add_context(self, prompt: str, context_data: dict[str, Any]) -> str:
        """Add contextual metadata to prompt.

        Args:
            prompt: Base prompt.
            context_data: Contextual information.

        Returns:
            Prompt with context added.
        """
        if not context_data:
            return prompt

        if self.context.language == "ru":
            header = "КОНТЕКСТ:\n"
        else:
            header = "CONTEXT:\n"

        context_text = "\n".join(f"- {k}: {v}" for k, v in context_data.items())
        return f"{prompt}\n\n{header}{context_text}"
