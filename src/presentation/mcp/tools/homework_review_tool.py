"""Modern MCP workflow for reviewing homework archives with modular reviewer."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Mapping

from multipass_reviewer.application.config import ReviewConfig

from src.application.services.modular_review_service import ModularReviewService
from src.domain.models.code_review_models import MultiPassReport
from src.domain.services.diff_analyzer import DiffAnalyzer
from src.infrastructure.archive.archive_service import ZipArchiveService
from src.infrastructure.config.settings import Settings, get_settings
from src.infrastructure.database.mongo import get_db
from src.infrastructure.logging.review_logger import ReviewLogger
from src.infrastructure.reporting.homework_report_generator import (
    generate_detailed_markdown_report,
)
from src.infrastructure.repositories.homework_review_repository import (
    HomeworkReviewRepository,
)
from src.infrastructure.utils.path_utils import ensure_shared_in_path
from src.presentation.mcp.server import mcp

ensure_shared_in_path()

from shared_package.clients.unified_client import UnifiedModelClient

logger = logging.getLogger(__name__)


def detect_assignment_type(codebase: Mapping[str, str]) -> str:
    """Detect the most likely assignment type for the provided codebase.

    Purpose:
        Inspect archive contents and determine which homework template applies.

    Args:
        codebase: Mapping of relative file paths to their source contents.

    Returns:
        Canonical assignment label: `HW1`, `HW2`, `HW3`, or `auto` when no match.

    Raises:
        None.

    Example:
        >>> detect_assignment_type({"Dockerfile": "...", "src/app.py": "..."})
        'HW1'
    """
    if not codebase:
        return "auto"

    lower_paths = [path.lower() for path in codebase]
    lower_contents = [content.lower() for content in codebase.values()]

    if any("mlflow" in candidate for candidate in lower_paths + lower_contents):
        return "HW3"

    if any("airflow" in candidate for candidate in lower_paths + lower_contents):
        return "HW2"

    dockerfile_present = any(
        Path(path).name.lower() == "dockerfile" for path in codebase
    )
    spark_present = any(
        "spark" in candidate for candidate in lower_paths + lower_contents
    )

    if dockerfile_present and spark_present:
        return "HW1"

    return "auto"


class _HomeworkReviewWorkflow:
    """Execute modular homework review flow and persist results."""

    def __init__(
        self,
        archive_path: str,
        assignment_type: str,
        token_budget: int,
        model_name: str,
    ) -> None:
        self._archive_path = Path(archive_path)
        self._assignment_type = assignment_type
        self._token_budget = token_budget
        self._model_name = model_name
        self._settings: Settings = get_settings()
        self._archive_service = ZipArchiveService(self._settings)
        self._diff_analyzer = DiffAnalyzer()
        self._client = UnifiedModelClient(timeout=self._settings.review_llm_timeout)
        self._review_logger = ReviewLogger(enabled=True)
        self._review_config = ReviewConfig(token_budget=token_budget)
        self._review_service = ModularReviewService(
            archive_service=self._archive_service,
            diff_analyzer=self._diff_analyzer,
            llm_client=self._client,
            review_config=self._review_config,
            review_logger=self._review_logger,
            settings=self._settings,
        )
        self._logs_saved = False
        self._report_saved = False

    async def run(self) -> Dict[str, Any]:
        """Run workflow end-to-end with structured logging and persistence."""
        self._validate_archive_path()
        start_time = time.perf_counter()
        submission = self._extract_submission()
        assignment = self._resolve_assignment(submission.code_files)
        report = await self._execute_review(assignment)
        elapsed = time.perf_counter() - start_time
        if getattr(report, "execution_time_seconds", 0.0) <= 0:
            report.execution_time_seconds = elapsed
        markdown = await self._compose_markdown(report)
        await self._persist_report(report, assignment, markdown)
        await self._client.close()
        return self._serialize_response(report, assignment, markdown)

    def _validate_archive_path(self) -> None:
        """Ensure archive exists and has .zip suffix."""
        self._review_logger.log_work_step(
            "validate_archive",
            {
                "archive_path": str(self._archive_path),
                "token_budget": self._token_budget,
                "model_name": self._model_name,
            },
            status="info",
        )
        if not self._archive_path.exists():
            raise FileNotFoundError(f"Archive not found: {self._archive_path}")
        if self._archive_path.suffix.lower() != ".zip":
            raise ValueError(f"Expected .zip archive, got: {self._archive_path}")

    def _extract_submission(self) -> Any:
        """Extract code submission metadata and content."""
        submission = self._archive_service.extract_submission(
            archive_path=str(self._archive_path),
            submission_id=self._archive_path.stem,
        )
        self._review_logger.log_work_step(
            "extract_archive",
            {
                "files_count": submission.metadata.get("files_count", 0),
                "total_size_bytes": submission.metadata.get("total_size_bytes", 0),
            },
            status="success",
        )
        if not submission.code_files:
            self._review_logger.log_work_step(
                "validate_codebase",
                {"error": "No code files found"},
                status="error",
            )
            raise ValueError("No code files found in archive")
        return submission

    def _resolve_assignment(self, codebase: Mapping[str, str]) -> str:
        """Determine assignment label using heuristics or explicit override."""
        if self._assignment_type != "auto":
            self._review_logger.log_work_step(
                "detect_assignment_type",
                {"assignment_type": self._assignment_type, "mode": "manual"},
                status="info",
            )
            return self._assignment_type
        detected = detect_assignment_type(codebase)
        self._review_logger.log_work_step(
            "detect_assignment_type",
            {"assignment_type": detected},
            status="success",
        )
        return detected

    async def _execute_review(self, assignment: str) -> MultiPassReport:
        """Invoke modular reviewer service for supplied archive."""
        repo_name = self._archive_path.stem
        student_id = f"mcp_tool::{repo_name}"
        self._review_logger.log_work_step(
            "start_review",
            {
                "repo_name": repo_name,
                "student_id": student_id,
                "assignment_type": assignment,
            },
            status="info",
        )
        report = await self._review_service.review_submission(
            new_archive_path=str(self._archive_path),
            previous_archive_path=None,
            assignment_id=repo_name,
            student_id=student_id,
        )
        self._review_logger.session_id = report.session_id
        self._review_logger.log_work_step(
            "complete_review",
            {
                "session_id": report.session_id,
                "total_findings": report.total_findings,
                "execution_time": report.execution_time_seconds,
            },
            status="success",
        )
        return report

    async def _compose_markdown(self, report: MultiPassReport) -> str:
        """Generate detailed markdown, falling back to a minimal template."""
        try:
            return await generate_detailed_markdown_report(
                report,
                review_logger=self._review_logger,
                client=self._client,
            )
        except Exception as error:  # pragma: no cover - defensive path
            logger.error(
                "Error generating markdown report: %s",
                error,
                exc_info=True,
            )
            return (
                "# Code Review Report\n\n"
                f"**Archive Name**: {report.repo_name}\n"
                f"**Session ID**: {report.session_id}\n"
                f"**Review Duration**: {report.execution_time_seconds:.2f} seconds\n\n"
                "## Error\n\n"
                f"{error}\n\n"
                "## Summary\n\n"
                f"- Total Findings: {report.total_findings}\n"
                "- Detailed report generation failed; see logs for context."
            )

    async def _persist_report(
        self,
        report: MultiPassReport,
        assignment: str,
        markdown: str,
    ) -> None:
        """Persist review outputs and execution logs to MongoDB."""
        db = await get_db()
        repository = HomeworkReviewRepository(db)
        await repository.save_review_session(
            session_id=report.session_id,
            repo_name=report.repo_name,
            assignment_type=assignment,
            logs=self._review_logger.get_all_logs(),
            report={
                "markdown": markdown,
                "json": (
                    json.loads(report.to_json()) if hasattr(report, "to_json") else {}
                ),
            },
            metadata={
                "execution_time_seconds": report.execution_time_seconds,
                "detected_components": report.detected_components,
                "total_findings": report.total_findings,
                "pass_1_completed": report.pass_1 is not None,
                "pass_2_components": list(report.pass_2_results.keys()),
                "pass_3_completed": report.pass_3 is not None,
            },
        )
        self._report_saved = True
        self._logs_saved = True

    def _serialize_response(
        self,
        report: MultiPassReport,
        assignment: str,
        markdown: str,
    ) -> Dict[str, Any]:
        """Produce MCP response payload."""
        return {
            "success": True,
            "session_id": report.session_id,
            "repo_name": report.repo_name,
            "assignment_type": assignment,
            "detected_components": report.detected_components,
            "total_findings": report.total_findings,
            "execution_time_seconds": report.execution_time_seconds,
            "pass_1_completed": report.pass_1 is not None,
            "pass_2_components": list(report.pass_2_results.keys()),
            "pass_3_completed": report.pass_3 is not None,
            "markdown_report": markdown,
            "json_report": report.to_json() if hasattr(report, "to_json") else "{}",
            "logs_saved": self._logs_saved,
            "report_saved_to_mongodb": self._report_saved,
        }

    async def handle_failure(self, error: Exception) -> None:
        """Record failure details and persist logs if possible."""
        self._review_logger.log_work_step(
            "error",
            {"error": str(error), "error_type": type(error).__name__},
            status="error",
        )
        try:
            if self._review_logger.session_id:
                db = await get_db()
                repository = HomeworkReviewRepository(db)
                await repository.save_logs(
                    self._review_logger.session_id,
                    self._review_logger.get_all_logs(),
                )
                self._logs_saved = True
        except Exception:  # pragma: no cover - logging only
            logger.exception("Failed to persist error logs for homework review")
        finally:
            await self._client.close()


@mcp.tool()
async def review_homework_archive(
    archive_path: str,
    assignment_type: str = "auto",
    token_budget: int = 8000,
    model_name: str = "mistral",
) -> Dict[str, Any]:
    """Review a homework archive via modular reviewer service.

    Purpose:
        Provide a deterministic replacement for the legacy homework MCP tool using
        the shared modular reviewer pipeline.

    Args:
        archive_path: Absolute path to the `.zip` archive containing source files.
        assignment_type: Optional override for assignment label; use `auto` to detect.
        token_budget: Token allowance for reviewer prompts.
        model_name: Preferred model alias for logging (not all services use it).

    Returns:
        Structured review result with findings, metrics, markdown summary, and flags
        indicating whether logs and reports were persisted successfully.

    Raises:
        FileNotFoundError: When the archive path does not exist.
        ValueError: When the provided path is not a `.zip` archive or is empty.

    Example:
        >>> result = await review_homework_archive(\"/tmp/archive.zip\")
        >>> result[\"success\"]
        True
    """
    workflow = _HomeworkReviewWorkflow(
        archive_path=archive_path,
        assignment_type=assignment_type,
        token_budget=token_budget,
        model_name=model_name,
    )
    try:
        return await workflow.run()
    except Exception as error:
        await workflow.handle_failure(error)
        raise
