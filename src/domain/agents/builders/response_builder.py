"""Response builder for agent responses.

Following Python Zen:
- Simple is better than complex
- Explicit is better than implicit
"""

from src.domain.agents.schemas import AgentResponse


class ResponseBuilder:
    """Builder for agent responses.

    Single responsibility: construct AgentResponse objects.
    """

    @staticmethod
    def build_text_response(llm_response: str) -> AgentResponse:
        """Build response from LLM text.

        Args:
            llm_response: LLM response text

        Returns:
            Agent response with text
        """
        return AgentResponse(
            success=True,
            text=llm_response,
            tools_used=[],
            tokens_used=0,
            reasoning=None,
        )

    @staticmethod
    def build_error_response(error_message: str) -> AgentResponse:
        """Build error response.

        Args:
            error_message: Error message

        Returns:
            Agent response with error
        """
        return AgentResponse(
            success=False,
            text=f"Ошибка: {error_message}",
            tools_used=[],
            tokens_used=0,
            error=error_message,
            reasoning=None,
        )

    @staticmethod
    def build_success_response(
        text: str, tool_name: str, tokens_used: int = 0
    ) -> AgentResponse:
        """Build success response from formatted text.

        Args:
            text: Formatted text response
            tool_name: Name of tool used
            tokens_used: Number of tokens used

        Returns:
            Agent response with success
        """
        return AgentResponse(
            success=True,
            text=text,
            tools_used=[tool_name],
            tokens_used=tokens_used,
            reasoning=None,
        )

    @staticmethod
    def chunk_text(text: str, max_len: int = 3800) -> str:
        """Chunk text to avoid platform limits.

        Args:
            text: Text to chunk
            max_len: Maximum length per chunk

        Returns:
            Chunked text separated by double newlines
        """
        if not isinstance(text, str) or len(text) <= max_len:
            return text
        parts: list[str] = []
        start = 0
        while start < len(text):
            parts.append(text[start : start + max_len])
            start += max_len
        return "\n\n".join(parts)
