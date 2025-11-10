"""Value object for code differences."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CodeDiff:
    """Code difference analysis result.

    Purpose:
        Represents semantic and textual differences between two code
        versions. Includes AST-level analysis for Python code.

    Args:
        lines_added: Number of lines added
        lines_removed: Number of lines removed
        lines_changed: Number of lines changed (max of added/removed)
        change_ratio: Percentage of code changed (0-100)
        functions_added: List of function names added
        functions_removed: List of function names removed
        classes_changed: List of class names changed
        imports_added: List of imports added
        imports_removed: List of imports removed
        complexity_delta: Change in cyclomatic complexity
        has_refactor: Whether refactoring detected
        has_new_imports: Whether new imports detected
    """

    lines_added: int
    lines_removed: int
    lines_changed: int
    change_ratio: float
    functions_added: list[str] = field(default_factory=list)
    functions_removed: list[str] = field(default_factory=list)
    classes_changed: list[str] = field(default_factory=list)
    imports_added: list[str] = field(default_factory=list)
    imports_removed: list[str] = field(default_factory=list)
    complexity_delta: int = 0
    has_refactor: bool = False
    has_new_imports: bool = False

    def __post_init__(self) -> None:
        """Validate diff data."""
        if self.lines_added < 0:
            raise ValueError("lines_added must be non-negative")
        if self.lines_removed < 0:
            raise ValueError("lines_removed must be non-negative")
        if self.lines_changed < 0:
            raise ValueError("lines_changed must be non-negative")
        if not 0.0 <= self.change_ratio <= 100.0:
            raise ValueError("change_ratio must be between 0 and 100")
