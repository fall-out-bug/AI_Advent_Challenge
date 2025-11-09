"""Domain interface for log parsing.

Following Clean Architecture: protocol definition in domain layer.
"""

from __future__ import annotations

from typing import List, Protocol

from src.domain.value_objects.log_analysis import LogEntry


class LogParser(Protocol):
    """Protocol for parsing logs from various sources.

    Purpose:
        Defines interface for parsing log content into structured LogEntry objects.
        Implementations handle different log formats (checker, docker, container).

    Example:
        parser = LogParserImpl()
        entries = parser.parse(content="2025-11-03 | ERROR | module | msg", source="checker")
    """

    def parse(self, content: str, source: str) -> List[LogEntry]:
        """Parse log content into structured entries.

        Purpose:
            Convert raw log text into list of LogEntry objects based on source type.

        Args:
            content: Raw log content as string
            source: Source identifier (e.g., 'checker', 'docker-stderr', 'container')

        Returns:
            List of parsed LogEntry objects

        Raises:
            ValueError: If source format is invalid or content cannot be parsed

        Example:
            entries = parser.parse(
                content="2025-11-03 00:29:35 | WARNING | checker | Message",
                source="checker"
            )
        """
        ...
