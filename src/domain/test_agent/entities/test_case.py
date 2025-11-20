"""TestCase domain entity."""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class TestCase:
    """
    Domain entity representing a test case.

    Purpose:
        Represents a single test case with its name, code, and optional metadata.

    Attributes:
        name: Test case name (e.g., "test_calculate_sum").
        code: Test case code as string.
        metadata: Optional metadata dictionary.

    Example:
        >>> test_case = TestCase(
        ...     name="test_example",
        ...     code="def test_example(): assert True",
        ...     metadata={"type": "unit"}
        ... )
        >>> test_case.name
        'test_example'
    """

    name: str
    code: str
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate TestCase attributes."""
        if not self.name:
            raise ValueError("name cannot be empty")
        if self.code is None:
            raise ValueError("code cannot be None")
