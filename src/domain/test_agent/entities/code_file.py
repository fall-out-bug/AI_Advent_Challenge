"""CodeFile domain entity."""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class CodeFile:
    """
    Domain entity representing a source code file.

    Purpose:
        Represents a source code file with its path, content, and optional metadata.

    Attributes:
        path: File path (relative or absolute).
        content: File content as string.
        metadata: Optional metadata dictionary.

    Example:
        >>> code_file = CodeFile(
        ...     path="src/example.py",
        ...     content="def hello(): pass",
        ...     metadata={"language": "python"}
        ... )
        >>> code_file.path
        'src/example.py'
    """

    path: str
    content: str
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate CodeFile attributes."""
        if not self.path:
            raise ValueError("path cannot be empty")
        if self.content is None:
            raise ValueError("content cannot be None")
