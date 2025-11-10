"""Data transfer objects for homework workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class HomeworkSubmission:
    """Homework submission metadata returned from checker service."""

    commit_hash: str
    archive_name: str
    assignment: str
    commit_dttm: str
    status: str


@dataclass(frozen=True)
class HomeworkListResult:
    """Result payload for listing recent homework submissions."""

    total: int
    submissions: Sequence[HomeworkSubmission]


@dataclass(frozen=True)
class HomeworkReviewResult:
    """Structured response for homework review execution."""

    success: bool
    markdown_report: str
    total_findings: int
    detected_components: Sequence[str]
    pass_2_components: Sequence[str]
    execution_time_seconds: float
