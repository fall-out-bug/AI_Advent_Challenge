"""Domain value objects for log analysis.

Following Clean Architecture: pure business logic, no external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class LogEntry:
    """Structured log entry.

    Purpose:
        Represents a single parsed log line with metadata.

    Args:
        timestamp: Log timestamp string
        level: Log level (ERROR, WARNING, INFO, DEBUG)
        component: Component name (airflow, spark, redis, etc.)
        message: Log message text
        traceback: Optional traceback text
        file_path: Optional source file path
        line_number: Optional line number
        raw_line: Original raw log line

    Raises:
        ValueError: If component is empty or level is invalid

    Example:
        entry = LogEntry(
            timestamp="2025-11-03 00:29:35",
            level="ERROR",
            component="checker",
            message="Connection failed"
        )
    """

    timestamp: str
    level: str  # ERROR, WARNING, INFO, DEBUG
    component: str  # airflow, spark, redis, checker, docker
    message: str
    traceback: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    raw_line: str = ""

    def __post_init__(self) -> None:
        """Validate entry."""
        if not self.component:
            raise ValueError("component required")
        if self.level not in ("ERROR", "WARNING", "INFO", "DEBUG"):
            raise ValueError(f"Invalid level: {self.level}")


@dataclass
class LogGroup:
    """Group of similar log entries.

    Purpose:
        Represents a deduplicated group of log entries with same pattern.

    Args:
        component: Component name
        severity: Severity level (critical, error, warning, info)
        count: Total count of similar entries
        entries: Sample entries (first N)
        first_occurrence: First occurrence timestamp
        last_occurrence: Last occurrence timestamp
        error_pattern: Normalized error signature

    Example:
        group = LogGroup(
            component="checker",
            severity="error",
            count=5,
            entries=[entry1, entry2],
            first_occurrence="2025-11-03 00:29:35",
            last_occurrence="2025-11-03 00:30:00",
            error_pattern="Connection failed"
        )
    """

    component: str
    severity: str  # critical, error, warning, info
    count: int
    entries: List[LogEntry]
    first_occurrence: str
    last_occurrence: str
    error_pattern: str

    def sample_content(self, max_lines: int = 20) -> str:
        """Get representative sample of log content.

        Purpose:
            Extract sample log lines for LLM analysis, truncating if needed.

        Args:
            max_lines: Maximum number of entries to include

        Returns:
            Formatted sample string with timestamps and messages

        Example:
            sample = group.sample_content(max_lines=10)
        """
        lines = []
        for entry in self.entries[:max_lines]:
            lines.append(f"[{entry.timestamp}] {entry.level}: {entry.message}")
            if entry.traceback:
                lines.append(entry.traceback[:500])
        return "\n".join(lines)


@dataclass
class LogAnalysisResult:
    """Result of LLM analysis of log group.

    Purpose:
        Structured analysis result with classification, recommendations.

    Args:
        log_group: Original log group analyzed
        classification: Severity classification (critical, major, minor, warning)
        description: Brief problem description
        root_cause: Root cause analysis
        recommendations: List of actionable recommendations
        confidence: Analysis confidence (0.0-1.0)

    Raises:
        ValueError: If confidence outside 0.0-1.0 or invalid classification

    Example:
        result = LogAnalysisResult(
            log_group=group,
            classification="critical",
            description="Redis connection failed",
            root_cause="Container not started",
            recommendations=["Start Redis"],
            confidence=0.95
        )
    """

    log_group: LogGroup
    classification: str  # critical, major, minor, warning
    description: str
    root_cause: str
    recommendations: List[str]
    confidence: float  # 0.0-1.0

    def __post_init__(self) -> None:
        """Validate result."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be 0.0-1.0")
        if self.classification not in ("critical", "major", "minor", "warning"):
            raise ValueError(f"Invalid classification: {self.classification}")

    def to_markdown(self) -> str:
        """Export as markdown section.

        Purpose:
            Format analysis result as markdown for report inclusion.

        Returns:
            Markdown formatted string

        Example:
            md = result.to_markdown()
        """
        md = f"### [{self.classification.upper()}] {self.log_group.component}\n\n"
        md += f"**Count:** {self.log_group.count}  \n"
        md += f"**First:** {self.log_group.first_occurrence}  \n"
        md += f"**Last:** {self.log_group.last_occurrence}\n\n"
        md += f"**Description:**\n{self.description}\n\n"
        md += f"**Root Cause:**\n{self.root_cause}\n\n"
        md += f"**Recommendations:**\n"
        for i, rec in enumerate(self.recommendations, 1):
            md += f"{i}. {rec}\n"
        md += f"\n*Confidence: {self.confidence:.0%}*\n"
        return md

