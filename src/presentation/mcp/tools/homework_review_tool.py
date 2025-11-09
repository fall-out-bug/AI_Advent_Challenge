"""MCP tool for reviewing student homework archives using multi-pass code review.

Following Clean Architecture principles and the Zen of Python.
"""

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from multipass_reviewer.application.config import ReviewConfig

from src.application.services.modular_review_service import ModularReviewService
from src.domain.services.diff_analyzer import DiffAnalyzer
from src.infrastructure.archive.archive_service import ZipArchiveService
from src.infrastructure.config.settings import get_settings
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


def detect_assignment_type(codebase: Mapping[str, str]) -> str:
    """Auto-detect assignment type from codebase structure and contents.

    Args:
        codebase: Mapping of relative file paths to file contents.

    Returns:
        Assignment type label: "HW1", "HW2", "HW3", or "auto".
    """
    if not codebase:
        return "auto"

    lower_paths = [path.lower() for path in codebase.keys()]
    lower_contents = [content.lower() for content in codebase.values()]

    if any("mlflow" in path for path in lower_paths) or any(
        "mlflow" in content for content in lower_contents
    ):
        return "HW3"

    if any("airflow" in path for path in lower_paths) or any(
        "airflow" in content for content in lower_contents
    ):
        return "HW2"

    dockerfile_exists = any(
        Path(path).name.lower() == "dockerfile" for path in codebase
    )
    spark_exists = any("spark" in path for path in lower_paths) or any(
        "sparksession" in content for content in lower_contents
    )

    if dockerfile_exists and spark_exists:
        return "HW1"

    return "auto"


@mcp.tool()
async def review_homework_archive(
    archive_path: str,
    assignment_type: str = "auto",
    token_budget: int = 8000,
    model_name: str = "mistral",
) -> Dict[str, Any]:
    """Review student homework archive using multi-pass code review.

    Args:
        archive_path: Path to .zip archive with student homework
        assignment_type: Type of assignment ("HW1", "HW2", "HW3", or "auto" for auto-detection)
        token_budget: Token budget for review (default: 8000)
        model_name: Model name to use (default: "mistral")

    Returns:
        Dict with review results including findings, components, execution time

    Raises:
        FileNotFoundError: If archive_path doesn't exist
        ValueError: If archive is invalid or assignment type is unknown
    """
    archive_path_obj = Path(archive_path)

    if not archive_path_obj.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    if not archive_path_obj.suffix == ".zip":
        raise ValueError(f"Expected .zip archive, got: {archive_path}")

    review_logger: Optional[ReviewLogger] = None
    client: Optional[UnifiedModelClient] = None
    detected_assignment = assignment_type

    try:
        settings = get_settings()
        archive_service = ZipArchiveService(settings)
        diff_analyzer = DiffAnalyzer()

        review_logger = ReviewLogger(enabled=True)
        review_logger.log_work_step(
            "validate_archive",
            {
                "archive_path": archive_path,
                "token_budget": token_budget,
                "model_name": model_name,
            },
            status="info",
        )

        submission = archive_service.extract_submission(
            archive_path=str(archive_path_obj),
            submission_id=archive_path_obj.stem,
        )

        review_logger.log_work_step(
            "extract_archive",
            {
                "files_count": submission.metadata.get("files_count", 0),
                "total_size_bytes": submission.metadata.get("total_size_bytes", 0),
            },
            status="success",
        )

        if not submission.code_files:
            review_logger.log_work_step(
                "validate_codebase",
                {"error": "No code files found"},
                status="error",
            )
            raise ValueError("No code files found in archive")

        if assignment_type == "auto":
            detected_assignment = detect_assignment_type(submission.code_files)
            review_logger.log_work_step(
                "detect_assignment_type",
                {"assignment_type": detected_assignment},
                status="success",
            )
        else:
            detected_assignment = assignment_type
            review_logger.log_work_step(
                "detect_assignment_type",
                {"assignment_type": detected_assignment, "mode": "manual"},
                status="info",
            )

        review_config = ReviewConfig(token_budget=token_budget)
        client = UnifiedModelClient(timeout=settings.review_llm_timeout)

        review_service = ModularReviewService(
            archive_service=archive_service,
            diff_analyzer=diff_analyzer,
            llm_client=client,
            review_config=review_config,
            review_logger=review_logger,
            settings=settings,
        )

        repo_name = archive_path_obj.stem
        student_id = f"mcp_tool::{repo_name}"

        review_logger.log_work_step(
            "start_review",
            {
                "repo_name": repo_name,
                "student_id": student_id,
                "assignment_type": detected_assignment,
            },
            status="info",
        )

        report = await review_service.review_submission(
            new_archive_path=str(archive_path_obj),
            previous_archive_path=None,
            assignment_id=repo_name,
            student_id=student_id,
        )

        review_logger.session_id = report.session_id
        review_logger.log_work_step(
            "complete_review",
            {
                "session_id": report.session_id,
                "total_findings": report.total_findings,
                "execution_time": report.execution_time_seconds,
            },
            status="success",
        )

        try:
            detailed_markdown = await generate_detailed_markdown_report(
                report,
                review_logger=review_logger,
                client=client,
            )
        except Exception as error:
            import logging

            logger = logging.getLogger(__name__)
            logger.error("Error generating markdown report: %s", error, exc_info=True)
            detailed_markdown = f"""# Code Review Report

**Archive Name**: {report.repo_name}
**Session ID**: {report.session_id}
**Review Duration**: {report.execution_time_seconds:.2f} seconds

## Error

An error occurred while generating the detailed report: {error}

## Basic Information

- **Total Findings**: {report.total_findings}
- **Detected Components**: {', '.join(report.detected_components) if report.detected_components else 'None'}
"""

        db = await get_db()
        repository = HomeworkReviewRepository(db)
        await repository.save_review_session(
            session_id=report.session_id,
            repo_name=report.repo_name,
            assignment_type=detected_assignment,
            logs=review_logger.get_all_logs(),
            report={
                "markdown": detailed_markdown,
                "json": json.loads(report.to_json())
                if hasattr(report, "to_json")
                else {},
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

        return {
            "success": True,
            "session_id": report.session_id,
            "repo_name": report.repo_name,
            "assignment_type": detected_assignment,
            "detected_components": report.detected_components,
            "total_findings": report.total_findings,
            "execution_time_seconds": report.execution_time_seconds,
            "pass_1_completed": report.pass_1 is not None,
            "pass_2_components": list(report.pass_2_results.keys()),
            "pass_3_completed": report.pass_3 is not None,
            "markdown_report": detailed_markdown,
            "json_report": report.to_json(),
            "logs_saved": True,
            "report_saved_to_mongodb": True,
        }

    except Exception as error:
        if review_logger:
            review_logger.log_work_step(
                "error",
                {"error": str(error), "error_type": type(error).__name__},
                status="error",
            )
            try:
                db = await get_db()
                repository = HomeworkReviewRepository(db)
                if review_logger.session_id:
                    await repository.save_logs(
                        review_logger.session_id, review_logger.get_all_logs()
                    )
            except Exception:
                pass
        raise

    finally:
        if client:
            await client.close()
