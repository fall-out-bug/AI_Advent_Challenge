"""Protocol for code chunking services."""

from typing import List, Protocol

from src.domain.test_agent.entities.code_chunk import CodeChunk


class ICodeChunker(Protocol):
    """Protocol for code chunking services.

    Purpose:
        Defines the interface for code chunking services used by test agent.
        Application layer implementations must conform to this protocol.

    Methods:
        chunk_module: Split a module into chunks
        chunk_package: Split a package into chunks
    """

    def chunk_module(
        self, code: str, max_tokens: int, strategy: str = "function_based"
    ) -> List[CodeChunk]:
        """Split a module into chunks that fit within token limit.

        Args:
            code: Source code of the module.
            max_tokens: Maximum tokens per chunk.
            strategy: Chunking strategy (function_based, class_based, sliding_window).

        Returns:
            List of CodeChunk entities.
        """
        ...

    def chunk_package(
        self, package_path: str, max_tokens: int, strategy: str = "function_based"
    ) -> List[CodeChunk]:
        """Split a package into chunks that fit within token limit.

        Args:
            package_path: Path to the package directory.
            max_tokens: Maximum tokens per chunk.
            strategy: Chunking strategy (function_based, class_based, sliding_window).

        Returns:
            List of CodeChunk entities.
        """
        ...
