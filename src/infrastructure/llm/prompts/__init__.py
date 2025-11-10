"""Prompt building and template utilities for LLM."""

from __future__ import annotations

import sys
from pathlib import Path

# Import from legacy prompts.py file (backward compatibility)
# Check if prompts.py exists at the parent level
_llm_dir = Path(__file__).parent.parent
_prompts_file = _llm_dir / "prompts.py"
if _prompts_file.exists():
    # Import from the file directly using importlib
    import importlib.util

    spec = importlib.util.spec_from_file_location("llm_prompts", _prompts_file)
    if spec and spec.loader:
        prompts_module = importlib.util.module_from_spec(spec)
        sys.modules["llm_prompts"] = prompts_module
        spec.loader.exec_module(prompts_module)
        get_intent_parse_prompt = prompts_module.get_intent_parse_prompt
    else:
        # Fallback stub
        def get_intent_parse_prompt(
            text: str, language: str = "en", context: dict | None = None
        ) -> str:
            """Stub for intent parse prompt."""
            return f"Parse intent from: {text}"

else:
    # Fallback stub
    def get_intent_parse_prompt(
        text: str, language: str = "en", context: dict | None = None
    ) -> str:
        """Stub for intent parse prompt."""
        return f"Parse intent from: {text}"


from .prompt_builder import PromptBuilder
from .summarization_prompts import (
    get_direct_summarization_prompt,
    get_map_prompt,
    get_reduce_prompt,
)

__all__ = [
    "PromptBuilder",
    "get_map_prompt",
    "get_reduce_prompt",
    "get_direct_summarization_prompt",
    "get_intent_parse_prompt",
]
