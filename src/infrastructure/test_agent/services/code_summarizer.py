"""Code summarization service for test agent."""

from src.domain.test_agent.interfaces.code_summarizer import ICodeSummarizer
from src.infrastructure.llm.clients.llm_client import LLMClient
from src.infrastructure.logging import get_logger


class CodeSummarizer:
    """
    Code summarization service implementing ICodeSummarizer.

    Purpose:
        Generates concise summaries of code chunks and package structures
        using LLM to preserve critical context while reducing size.

    Example:
        >>> from src.infrastructure.llm.clients.llm_client import LLMClient
        >>> summarizer = CodeSummarizer(llm_client=llm_client)
        >>> summary = await summarizer.summarize_chunk("def add(a, b): return a + b")
    """

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize service with LLM client.

        Args:
            llm_client: LLMClient Protocol implementation.
        """
        self.llm_client = llm_client
        self.logger = get_logger("test_agent.code_summarizer")

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
        prompt = self._create_chunk_summary_prompt(code)
        summary = await self.llm_client.generate(
            prompt=prompt,
            temperature=0.2,
            max_tokens=512,
        )
        self.logger.debug(
            "Code chunk summarized",
            extra={
                "original_length": len(code),
                "summary_length": len(summary),
                "compression_ratio": len(summary) / len(code) if code else 0,
            },
        )
        return summary

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
        prompt = self._create_package_summary_prompt(files)
        summary = await self.llm_client.generate(
            prompt=prompt,
            temperature=0.2,
            max_tokens=512,
        )
        self.logger.debug(
            "Package structure summarized",
            extra={
                "file_count": len(files),
                "summary_length": len(summary),
            },
        )
        return summary

    def _create_chunk_summary_prompt(self, code: str) -> str:
        """Create prompt for chunk summarization.

        Args:
            code: Source code to summarize.

        Returns:
            Formatted prompt string.
        """
        return f"""Summarize the following Python code chunk concisely.

CRITICAL REQUIREMENTS:
- Preserve ALL function signatures (names, parameters, return types)
- Preserve ALL class definitions (names, methods, inheritance)
- Preserve ALL import statements and dependencies
- Remove implementation details (function bodies, variable assignments)
- Keep summary under 30% of original size
- Focus on structure, not implementation

Code to summarize:
```python
{code}
```

Generate a concise summary that preserves:
1. Function/class signatures
2. Import statements
3. Dependencies
4. Type hints

Remove:
- Implementation details
- Variable assignments
- Loop bodies
- Conditional logic details

Summary:"""

    def _create_package_summary_prompt(self, files: list[str]) -> str:
        """Create prompt for package structure summarization.

        Args:
            files: List of file paths.

        Returns:
            Formatted prompt string.
        """
        files_list = "\n".join(f"- {f}" for f in files)
        return f"""Summarize the structure of this Python package.

List the main modules, classes, and functions organized by file.

Files in package:
{files_list}

Generate a structured overview that lists:
1. Main modules/files
2. Classes in each module
3. Key functions in each module
4. Package-level dependencies

Format as a clear, hierarchical overview:"""
