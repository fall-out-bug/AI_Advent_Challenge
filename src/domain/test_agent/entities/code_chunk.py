"""CodeChunk domain entity."""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class CodeChunk:
    """
    Domain entity representing a chunk of code with metadata.

    Purpose:
        Represents a semantically meaningful chunk of code extracted from a larger
        module, including context, dependencies, and location information.

    Attributes:
        code: The code content of the chunk.
        context: Context metadata describing the chunk's purpose or surrounding code.
        dependencies: List of dependencies (imports, modules) used by this chunk.
        location: File path where this chunk originates.
        start_line: Starting line number of the chunk in the original file.
        end_line: Ending line number of the chunk in the original file.

    Example:
        >>> chunk = CodeChunk(
        ...     code="def hello(): pass",
        ...     context="Module-level function",
        ...     dependencies=["os"],
        ...     location="src/example.py",
        ...     start_line=1,
        ...     end_line=5
        ... )
        >>> chunk.location
        'src/example.py'
    """

    code: str
    context: str
    dependencies: List[str]
    location: str
    start_line: int
    end_line: int

    def __post_init__(self) -> None:
        """Validate CodeChunk attributes."""
        if not self.code:
            raise ValueError("code cannot be empty")
        if not self.location:
            raise ValueError("location cannot be empty")
        if self.start_line < 1:
            raise ValueError("start_line must be positive")
        if self.end_line < self.start_line:
            raise ValueError("end_line must be >= start_line")

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize CodeChunk to dictionary.

        Returns:
            Dictionary representation of the CodeChunk.

        Example:
            >>> chunk = CodeChunk(
            ...     code="def test(): pass",
            ...     context="",
            ...     dependencies=[],
            ...     location="test.py",
            ...     start_line=1,
            ...     end_line=3
            ... )
            >>> chunk.to_dict()["code"]
            'def test(): pass'
        """
        return {
            "code": self.code,
            "context": self.context,
            "dependencies": self.dependencies,
            "location": self.location,
            "start_line": self.start_line,
            "end_line": self.end_line,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeChunk":
        """
        Deserialize CodeChunk from dictionary.

        Args:
            data: Dictionary containing CodeChunk attributes.

        Returns:
            CodeChunk instance created from dictionary.

        Example:
            >>> data = {
            ...     "code": "def test(): pass",
            ...     "context": "",
            ...     "dependencies": [],
            ...     "location": "test.py",
            ...     "start_line": 1,
            ...     "end_line": 3
            ... }
            >>> chunk = CodeChunk.from_dict(data)
            >>> chunk.code
            'def test(): pass'
        """
        return cls(
            code=data["code"],
            context=data.get("context", ""),
            dependencies=data.get("dependencies", []),
            location=data["location"],
            start_line=data["start_line"],
            end_line=data["end_line"],
        )
