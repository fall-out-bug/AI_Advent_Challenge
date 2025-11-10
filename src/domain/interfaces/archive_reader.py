"""Archive reader protocol interface."""

from __future__ import annotations

from typing import Protocol

from src.domain.value_objects.submission_archive import SubmissionArchive


class ArchiveReader(Protocol):
    """Protocol for reading submission archives.

    Purpose:
        Defines interface for archive extraction services.
        Allows different implementations (ZIP, tar.gz, etc.).
    """

    def extract_submission(
        self, archive_path: str, submission_id: str
    ) -> SubmissionArchive:
        """Extract submission from archive.

        Args:
            archive_path: Path to archive file
            submission_id: Unique submission identifier

        Returns:
            Extracted SubmissionArchive

        Raises:
            ValueError: If archive is invalid or corrupted
            FileNotFoundError: If archive path doesn't exist
        """
        ...
