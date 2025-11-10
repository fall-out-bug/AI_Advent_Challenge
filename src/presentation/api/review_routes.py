"""FastAPI routes for review API."""

import logging
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from src.application.use_cases.enqueue_review_task_use_case import (
    EnqueueReviewTaskUseCase,
)
from src.application.use_cases.get_review_status_use_case import GetReviewStatusUseCase
from src.infrastructure.config.settings import Settings
from src.presentation.api.schemas.review_schemas import ReviewStatusResponse

logger = logging.getLogger(__name__)


def create_review_router(
    enqueue_use_case: EnqueueReviewTaskUseCase,
    get_status_use_case: GetReviewStatusUseCase,
    settings: Settings,
) -> APIRouter:
    """Create review API router.

    Args:
        enqueue_use_case: Enqueue use case
        get_status_use_case: Get status use case
        settings: Application settings

    Returns:
        Configured APIRouter
    """
    router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])

    # Directory for storing uploaded archives
    review_archives_dir = Path("review_archives")
    review_archives_dir.mkdir(exist_ok=True)
    max_archive_size_mb = settings.archive_max_total_size_mb

    @router.post("", status_code=status.HTTP_201_CREATED)
    async def create_review(
        student_id: str = Form(...),
        assignment_id: str = Form(...),
        new_commit: str = Form(...),
        old_commit: str | None = Form(None),
        new_zip: UploadFile = File(...),
        old_zip: UploadFile | None = File(None),
        logs_zip: UploadFile | None = File(None),
    ) -> ReviewStatusResponse:
        """Create new review task with multipart file upload.

        Purpose:
            Accepts code archives and logs via multipart/form-data,
            saves them to disk, and enqueues review task.

        Args:
            student_id: Student identifier
            assignment_id: Assignment identifier
            new_commit: Commit hash for new submission
            old_commit: Optional commit hash for previous submission
            new_zip: New submission ZIP archive (required)
            old_zip: Previous submission ZIP archive (optional)
            logs_zip: Logs ZIP archive (optional)

        Returns:
            Created task info

        Raises:
            HTTPException: On validation or file size errors
        """
        new_submission_path = None
        previous_submission_path = None
        logs_zip_path = None

        try:
            if not new_commit.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="new_commit cannot be empty",
                )
            new_commit_value = new_commit.strip()

            # Validate and save new_zip
            if new_zip.size > max_archive_size_mb * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"new_zip exceeds size limit: {max_archive_size_mb}MB",
                )
            new_submission_path = (
                review_archives_dir
                / f"{student_id}_{assignment_id}_new_{new_zip.filename}"
            )
            with open(new_submission_path, "wb") as f:
                content = await new_zip.read()
                f.write(content)
            logger.info(f"Saved new submission: {new_submission_path}")

            # Save old_zip if provided
            if old_zip:
                if old_zip.size > max_archive_size_mb * 1024 * 1024:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"old_zip exceeds size limit: {max_archive_size_mb}MB",
                    )
                previous_submission_path = (
                    review_archives_dir
                    / f"{student_id}_{assignment_id}_old_{old_zip.filename}"
                )
                with open(previous_submission_path, "wb") as f:
                    content = await old_zip.read()
                    f.write(content)
                logger.info(f"Saved old submission: {previous_submission_path}")

            # Save logs_zip if provided
            if logs_zip:
                if logs_zip.size > max_archive_size_mb * 1024 * 1024:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"logs_zip exceeds size limit: {max_archive_size_mb}MB",
                    )
                logs_zip_path = (
                    review_archives_dir
                    / f"{student_id}_{assignment_id}_logs_{logs_zip.filename}"
                )
                with open(logs_zip_path, "wb") as f:
                    content = await logs_zip.read()
                    f.write(content)
                logger.info(f"Saved logs archive: {logs_zip_path}")

            # Enqueue task
            task = await enqueue_use_case.execute(
                student_id=student_id,
                assignment_id=assignment_id,
                new_submission_path=str(new_submission_path),
                previous_submission_path=str(previous_submission_path)
                if previous_submission_path
                else None,
                new_commit=new_commit_value,
                old_commit=old_commit,
                logs_zip_path=str(logs_zip_path) if logs_zip_path else None,
            )

            # Extract metadata for response
            metadata = task.metadata
            return ReviewStatusResponse(
                task_id=task.task_id,
                status=task.status.value,
                student_id=metadata.get("student_id"),
                assignment_id=metadata.get("assignment_id"),
                created_at=task.created_at.isoformat() if task.created_at else None,
            )
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except Exception as e:
            logger.error(f"Failed to create review: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process review request",
            ) from e

    @router.get("/{task_id}")
    async def get_review_status(task_id: str) -> ReviewStatusResponse:
        """Get review task status.

        Args:
            task_id: Task ID

        Returns:
            Task status and result
        """
        result = await get_status_use_case.execute(task_id)
        if result.get("status") == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task not found: {task_id}",
            )
        return ReviewStatusResponse(**result)

    return router
