"""MCP tool for reviewing student homework archives using multi-pass code review.

Following Clean Architecture principles and the Zen of Python.
"""

import json
import sys
import zipfile
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

# Add root to path for imports
_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(_root))
shared_path = _root / "shared"
sys.path.insert(0, str(shared_path))

from shared_package.clients.unified_client import UnifiedModelClient

from src.domain.agents.multi_pass_reviewer import MultiPassReviewerAgent
from src.infrastructure.database.mongo import get_db
from src.infrastructure.logging.review_logger import ReviewLogger
from src.infrastructure.repositories.homework_review_repository import (
    HomeworkReviewRepository,
)
from src.infrastructure.reporting.homework_report_generator import (
    generate_detailed_markdown_report,
)
from src.presentation.mcp.server import mcp


def load_all_files_as_string(directory: Path, extensions: Optional[list] = None) -> str:
    """Load all files from directory as single string.

    Args:
        directory: Path to directory with files
        extensions: List of file extensions to include (None = all)

    Returns:
        Concatenated file contents
    """
    if extensions is None:
        extensions = [".py", ".yml", ".yaml", ".sh", ".txt", ".md", "Dockerfile"]

    content_parts = []
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            if any(
                file_path.suffix in ext or ext in str(file_path.name)
                for ext in extensions
            ):
                try:
                    rel_path = file_path.relative_to(directory)
                    content_parts.append(f"\n# File: {rel_path}\n")
                    content_parts.append(
                        file_path.read_text(encoding="utf-8", errors="ignore")
                    )
                    content_parts.append("\n\n")
                except Exception as e:
                    content_parts.append(f"# Error reading {file_path}: {e}\n\n")

    return "".join(content_parts)


def extract_archive(archive_path: str) -> Path:
    """Extract ZIP archive to temporary directory.

    Args:
        archive_path: Path to ZIP archive

    Returns:
        Path to temporary directory with extracted files
    """
    temp_dir = tempfile.mkdtemp(prefix="homework_review_")

    with zipfile.ZipFile(archive_path, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    return Path(temp_dir)


def detect_assignment_type(directory: Path) -> str:
    """Auto-detect assignment type from directory structure.

    Args:
        directory: Path to extracted project directory

    Returns:
        Assignment type: "HW1", "HW2", "HW3", or "auto"
    """
    # Check for HW3: MLflow directory
    if (directory / "mlflow").exists() or any(
        "mlflow" in str(p) for p in directory.rglob("*")
    ):
        return "HW3"

    # Check for HW2: Airflow DAGs
    if (directory / "airflow").exists() or any(
        "airflow" in str(p).lower() for p in directory.rglob("*")
    ):
        return "HW2"

    # Check for HW1: Docker + Spark
    dockerfile_exists = any(p.name == "Dockerfile" for p in directory.rglob("*"))
    spark_exists = any(
        "spark" in str(p).lower() or "SparkSession" in p.read_text(errors="ignore")
        for p in directory.rglob("*.py")
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

    # Extract archive
    temp_dir = None
    review_logger = None
    client = None
    try:
        # Create ReviewLogger for detailed logging
        review_logger = ReviewLogger(enabled=True)
        review_logger.log_work_step(
            "extract_archive",
            {"archive_path": archive_path},
            status="info",
        )

        temp_dir = extract_archive(archive_path)

        review_logger.log_work_step(
            "extract_archive",
            {"extracted_to": str(temp_dir)},
            status="success",
        )

        # Find root project directory
        root_dir = temp_dir
        subdirs = [d for d in temp_dir.iterdir() if d.is_dir()]
        if len(subdirs) == 1:
            root_dir = subdirs[0]

        review_logger.log_work_step(
            "find_project_root",
            {"root_dir": str(root_dir)},
            status="success",
        )

        # Auto-detect assignment type if needed
        if assignment_type == "auto":
            assignment_type = detect_assignment_type(root_dir)
            review_logger.log_work_step(
                "detect_assignment_type",
                {"assignment_type": assignment_type},
                status="success",
            )
        else:
            review_logger.log_work_step(
                "detect_assignment_type",
                {"assignment_type": assignment_type, "mode": "manual"},
                status="info",
            )

        # Load all files
        review_logger.log_work_step("load_files", {}, status="info")
        code = load_all_files_as_string(root_dir)

        if not code.strip():
            review_logger.log_work_step(
                "load_files",
                {"error": "No code files found"},
                status="error",
            )
            raise ValueError("No code files found in archive")

        review_logger.log_work_step(
            "load_files",
            {"files_loaded": True, "code_length": len(code)},
            status="success",
        )

        # Initialize client and agent with logger
        client = UnifiedModelClient(timeout=300.0)
        agent = MultiPassReviewerAgent(
            client, token_budget=token_budget, review_logger=review_logger
        )

        # Determine repo name
        repo_name = archive_path_obj.stem
        review_logger.session_id = None  # Will be set after process_multi_pass

        # Run multi-pass review
        review_logger.log_work_step("start_review", {"repo_name": repo_name}, status="info")
        report = await agent.process_multi_pass(code, repo_name=repo_name)

        # Set session_id in logger for consistency
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

        # Generate detailed markdown report
        try:
            detailed_markdown = await generate_detailed_markdown_report(
                report, review_logger=review_logger, client=client
            )
            # Log markdown report length for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                f"Generated markdown report: length={len(detailed_markdown) if detailed_markdown else 0}, "
                f"total_findings={report.total_findings}, "
                f"components={len(report.detected_components)}"
            )
            if not detailed_markdown or not detailed_markdown.strip():
                logger.warning(
                    f"Markdown report is empty! total_findings={report.total_findings}, "
                    f"pass_1={report.pass_1 is not None}, pass_2={len(report.pass_2_results)}, "
                    f"pass_3={report.pass_3 is not None}"
                )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating markdown report: {e}", exc_info=True)
            # Fallback: generate minimal report
            detailed_markdown = f"""# Code Review Report

**Archive Name**: {report.repo_name}
**Session ID**: {report.session_id}
**Review Duration**: {report.execution_time_seconds:.2f} seconds

## Error

An error occurred while generating the detailed report: {str(e)}

## Basic Information

- **Total Findings**: {report.total_findings}
- **Detected Components**: {', '.join(report.detected_components) if report.detected_components else 'None'}
"""

        # Initialize MongoDB repository and save
        db = await get_db()
        repository = HomeworkReviewRepository(db)

        # Save all logs and reports to MongoDB
        await repository.save_review_session(
            session_id=report.session_id,
            repo_name=report.repo_name,
            assignment_type=assignment_type,
            logs=review_logger.get_all_logs(),
            report={
                "markdown": detailed_markdown,
                "json": json.loads(report.to_json()) if hasattr(report, "to_json") else {},
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

        # Convert report to dict
        return {
            "success": True,
            "session_id": report.session_id,
            "repo_name": report.repo_name,
            "assignment_type": assignment_type,
            "detected_components": report.detected_components,
            "total_findings": report.total_findings,
            "execution_time_seconds": report.execution_time_seconds,
            "pass_1_completed": report.pass_1 is not None,
            "pass_2_components": list(report.pass_2_results.keys()),
            "pass_3_completed": report.pass_3 is not None,
            "markdown_report": detailed_markdown,  # Use detailed report
            "json_report": report.to_json(),
            "logs_saved": True,
            "report_saved_to_mongodb": True,
        }

    except Exception as e:
        # Log error if logger is available
        if review_logger:
            review_logger.log_work_step(
                "error",
                {"error": str(e), "error_type": type(e).__name__},
                status="error",
            )
            # Try to save logs even on error
            try:
                db = await get_db()
                repository = HomeworkReviewRepository(db)
                if review_logger.session_id:
                    await repository.save_logs(
                        review_logger.session_id, review_logger.get_all_logs()
                    )
            except Exception:
                pass  # Ignore save errors during exception handling
        raise

    finally:
        # Cleanup
        if temp_dir:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)
        if client:
            await client.close()
