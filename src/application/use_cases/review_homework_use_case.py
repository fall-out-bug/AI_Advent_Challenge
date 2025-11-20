"""Use case for reviewing homework archives via MCP tool."""

from __future__ import annotations

import asyncio
import os
import uuid
from pathlib import Path
from typing import Optional

from src.application.dtos.homework_dtos import HomeworkReviewResult
from src.domain.interfaces.homework_checker import HomeworkCheckerProtocol
from src.domain.interfaces.tool_client import ToolClientProtocol


class ReviewHomeworkUseCase:
    """Coordinate archive download and review execution."""

    def __init__(
        self,
        homework_checker: HomeworkCheckerProtocol,
        tool_client: ToolClientProtocol,
        *,
        assignment_type: str = "auto",
        token_budget: int = 8000,
        model_name: str = "mistral",
        temp_directory: Optional[Path] = None,
        cleanup_timeout: float = 0.1,
    ) -> None:
        """Initialize dependencies and configuration."""
        self._homework_checker = homework_checker
        self._tool_client = tool_client
        self._assignment_type = assignment_type
        self._token_budget = token_budget
        self._model_name = model_name
        self._temp_directory = temp_directory or Path(
            os.getenv("BUTLER_ARCHIVE_DIR", "/tmp")
        )
        self._cleanup_timeout = cleanup_timeout

    async def execute(self, commit_hash: str) -> HomeworkReviewResult:
        """Download archive for commit and execute review tool."""
        archive_bytes = await self._homework_checker.download_archive(commit_hash)
        archive_path = await self._write_archive(archive_bytes)

        try:
            result = await self._tool_client.call_tool(
                "review_homework_archive",
                {
                    "archive_path": str(archive_path),
                    "assignment_type": self._assignment_type,
                    "token_budget": self._token_budget,
                    "model_name": self._model_name,
                },
            )
        finally:
            await self._cleanup_file(archive_path)

        if not result.get("success"):
            error = result.get("error", "unknown error")
            raise RuntimeError(f"Review tool returned failure: {error}")

        return HomeworkReviewResult(
            success=True,
            markdown_report=str(result.get("markdown_report", "")),
            total_findings=int(result.get("total_findings", 0)),
            detected_components=list(result.get("detected_components", [])),
            pass_2_components=list(result.get("pass_2_components", [])),
            execution_time_seconds=float(result.get("execution_time_seconds", 0.0)),
        )

    async def _write_archive(self, payload: bytes) -> Path:
        """Persist archive bytes to temporary path."""
        self._temp_directory.mkdir(parents=True, exist_ok=True)
        filename = f"homework_{uuid.uuid4().hex}.zip"
        destination = self._temp_directory / filename
        await asyncio.to_thread(destination.write_bytes, payload)
        return destination

    async def _cleanup_file(self, path: Path) -> None:
        """Remove archive file with best-effort semantics."""
        try:
            await asyncio.wait_for(
                asyncio.to_thread(path.unlink, missing_ok=True),
                timeout=self._cleanup_timeout,
            )
        except (FileNotFoundError, asyncio.TimeoutError):
            pass
