"""Protocol for code summarization services."""

from typing import Protocol


class ICodeSummarizer(Protocol):
    """Protocol for code summarization services.

    Purpose:
        Defines the interface for code summarization services used by test agent.
        Infrastructure layer implementations must conform to this protocol.

    Methods:
        summarize_chunk: Generate concise summary of a code chunk
        summarize_package_structure: Generate overview of package structure
    """

    async def summarize_chunk(self, code: str) -> str:
        """Generate concise summary of a code chunk.

        Purpose:
            Summarizes code chunk while preserving critical information
            (function signatures, dependencies, class definitions).

        Args:
            code: Source code to summarize.

        Returns:
            Concise summary string (< 30% of original size).

        Raises:
            Exception: On summarization errors.
        """
        ...

    async def summarize_package_structure(self, files: list[str]) -> str:
        """Generate overview of package structure.

        Purpose:
            Creates high-level overview of package/module structure
            listing modules, classes, and main functions.

        Args:
            files: List of file paths in the package.

        Returns:
            Package structure overview string.

        Raises:
            Exception: On summarization errors.
        """
        ...
