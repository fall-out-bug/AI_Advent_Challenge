"""TestGenerationRequest value object."""

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class TestGenerationRequest:
    """
    Value object representing a request for test generation.

    Purpose:
        Immutable value object that encapsulates parameters for test generation.

    Attributes:
        code_file_path: Path to the code file for which tests should be generated.
        language: Programming language (e.g., "python", "javascript").
        metadata: Optional metadata dictionary.

    Example:
        >>> request = TestGenerationRequest(
        ...     code_file_path="src/example.py",
        ...     language="python"
        ... )
        >>> request.code_file_path
        'src/example.py'
    """

    code_file_path: str
    language: str
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate TestGenerationRequest attributes."""
        if not self.code_file_path:
            raise ValueError("code_file_path cannot be empty")
        if not self.language:
            raise ValueError("language cannot be empty")
