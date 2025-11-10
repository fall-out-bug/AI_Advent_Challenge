"""Use case for listing recent homework submissions."""

from __future__ import annotations

from typing import Iterable

from src.application.dtos.homework_dtos import (
    HomeworkListResult,
    HomeworkSubmission,
)
from src.domain.interfaces.homework_checker import HomeworkCheckerProtocol


class ListHomeworkSubmissionsUseCase:
    """Fetch and convert recent homework submissions metadata."""

    def __init__(self, homework_checker: HomeworkCheckerProtocol) -> None:
        """Initialize use case with homework checker dependency."""
        self._homework_checker = homework_checker

    async def execute(self, days: int = 1) -> HomeworkListResult:
        """Return recent homework submissions for the given window."""
        payload = await self._homework_checker.get_recent_commits(days=days)
        raw_commits: Iterable[dict] = payload.get("commits", [])
        submissions = [
            HomeworkSubmission(
                commit_hash=str(item.get("commit_hash", "")),
                archive_name=str(item.get("archive_name", "")),
                assignment=str(item.get("assignment", "")),
                commit_dttm=str(item.get("commit_dttm", "")),
                status=str(item.get("status", "")),
            )
            for item in raw_commits
        ]
        total = int(payload.get("total", len(submissions)))
        return HomeworkListResult(total=total, submissions=submissions)
