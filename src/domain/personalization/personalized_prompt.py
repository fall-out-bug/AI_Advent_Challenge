"""Personalized prompt value object."""

from dataclasses import dataclass


@dataclass
class PersonalizedPrompt:
    """Personalized LLM prompt with persona and memory context.

    Purpose:
        Assembles persona instructions, memory context, and new message
        into a complete prompt for LLM generation.

    Attributes:
        persona_section: Persona instructions and tone.
        memory_context: Formatted memory events and summary.
        new_message: Current user message to respond to.
        full_prompt: Complete assembled prompt.

    Example:
        >>> prompt = PersonalizedPrompt(
        ...     persona_section="You are Alfred",
        ...     memory_context="Previous: User asked about Python",
        ...     new_message="Tell me more",
        ...     full_prompt="You are Alfred\\n\\nPrevious...\\n\\nUser: Tell me more"
        ... )
        >>> prompt.estimate_tokens()
        25
    """

    persona_section: str
    memory_context: str
    new_message: str
    full_prompt: str

    def estimate_tokens(self) -> int:
        """Estimate token count for full prompt.

        Purpose:
            Simple heuristic for token estimation to enforce limits.
            Uses 4 characters ≈ 1 token approximation.

        Returns:
            Estimated token count.

        Example:
            >>> prompt = PersonalizedPrompt(..., full_prompt="Hello world")
            >>> prompt.estimate_tokens()
            2
        """
        return len(self.full_prompt) // 4

    def is_within_limit(self, token_limit: int = 2000) -> bool:
        """Check if prompt is within token limit.

        Args:
            token_limit: Maximum allowed tokens (default: 2000).

        Returns:
            True if prompt is within limit.

        Example:
            >>> prompt = PersonalizedPrompt(..., full_prompt="short")
            >>> prompt.is_within_limit(2000)
            True
        """
        return self.estimate_tokens() <= token_limit
