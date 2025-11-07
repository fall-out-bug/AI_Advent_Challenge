"""Value object for submission archives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SubmissionArchive:
    """Extracted submission archive with code and metadata.

    Purpose:
        Represents a parsed and extracted submission archive with
        code files, test logs, and metadata.

    Args:
        submission_id: Unique submission identifier
        archive_path: Original archive file path
        extracted_path: Path where archive was extracted
        code_files: Dictionary mapping file paths to code content
        test_logs: Test execution logs (if available)
        metadata: Additional metadata (size, file count, etc.)
    """

    submission_id: str
    archive_path: str
    extracted_path: str
    code_files: dict[str, str] = field(default_factory=dict)
    test_logs: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate archive data."""
        if not self.submission_id:
            raise ValueError("submission_id cannot be empty")
        if not self.archive_path:
            raise ValueError("archive_path cannot be empty")
        if not self.extracted_path:
            raise ValueError("extracted_path cannot be empty")

    def get_total_code_size(self) -> int:
        """Get total size of all code files in characters.

        Returns:
            Total character count
        """
        return sum(len(content) for content in self.code_files.values())

    def get_code_file_count(self) -> int:
        """Get number of code files.

        Returns:
            Number of code files
        """
        return len(self.code_files)

