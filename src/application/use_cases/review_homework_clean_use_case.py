"""Clean Architecture use case for reviewing homework.

Uses domain services instead of direct infrastructure dependencies.
Following Clean Architecture: Application layer orchestrates domain services.

Epic 21 · Stage 21_01d · Use Case Decomposition
"""

# noqa: E501
from typing import Optional

# noqa: E501
from src.application.dtos.homework_dtos import (
    HomeworkReviewResult,
)
from src.domain.interfaces.homework_review_service import (
    HomeworkReviewService,
)


# noqa: E501
# noqa: E501
class ReviewHomeworkCleanUseCase:
    """Clean Architecture use case for homework review orchestration.

      Purpose:
          Orchestrate homework review business logic using domain services.
          Follows Clean Architecture: Application layer depends only on
          domain interfaces.

      Attributes:
          homework_review_service: Domain service for homework review operations.
    """

    def __init__(
        self,
        homework_review_service: HomeworkReviewService,
    ):
        """Initialize use case with domain service.

              Args:
                  homework_review_service: Domain service for homework operations.
        """
        self.homework_review_service = homework_review_service

    async def execute(
        self, commit_hash: str, days: Optional[int] = None
    ) -> HomeworkReviewResult:
        """Execute homework review orchestration.

              Args:
                  commit_hash: Git commit hash to review.
                  days: Optional days parameter for context (future use).

              Returns:
                  HomeworkReviewResult with review outcomes.

              Raises:
                  ValueError: If commit_hash is invalid.
                  RuntimeError: If review operation fails.
        """
        if not commit_hash or not isinstance(commit_hash, str):
            raise ValueError(
                "commit_hash must be a non-empty string"
            )

        if len(commit_hash.strip()) == 0:
            raise ValueError(
                "commit_hash cannot be empty or whitespace"
            )

        # Create minimal context for domain service
        # Domain service expects DialogContext, create a minimal one
        from src.domain.agents.state_machine import (
            DialogContext,
            DialogState,
        )

        context = DialogContext(
            state=DialogState.IDLE,
            user_id="system",  # System operation
            # Unique session per review
            session_id=f"review_{commit_hash[:8]}",
        )

        try:
            # Delegate to domain service
            result = await self.homework_review_service.review_homework(
                context, commit_hash
            )

            # Parse result - domain service returns string format for file sending
            # For use case, we need to convert back to structured result
            if result.startswith("FILE:"):
                # Extract components from FILE:format
                try:
                    _, filename, content_b64 = result.split(
                        ":", 2
                    )
                    # For now, return basic success result
                    # In real implementation, might need to decode and parse
                    # content
                    return HomeworkReviewResult(
                        success=True,
                        markdown_report="Review completed - see file attachment",
                        total_findings=0,  # Would be parsed from actual report
                        detected_components=[],
                        pass_2_components=[],
                        execution_time_seconds=0.0,
                    )
                except ValueError:
                    raise RuntimeError(
                        f"Invalid FILE format from review service: {result}"
                    )
            else:
                # Error message from service
                raise RuntimeError(f"Review failed: {result}")

        except Exception as e:
            # Wrap domain service exceptions
            raise RuntimeError(
                f"Homework review failed: {str(e)}"
            ) from e

    async def list_recent_homeworks(
        self, days: int = 1
    ) -> list[dict]:
        """List recent homework submissions.

              Args:
                  days: Number of days to look back.

              Returns:
                  List of homework submission metadata.
        """
        try:
            result = await self.homework_review_service.list_homeworks(
                days
            )

            # Result is already in expected format from domain service
            if isinstance(result, dict) and "commits" in result:
                return result["commits"]
            else:
                return []

        except Exception as e:
            raise RuntimeError(
                f"Failed to list homeworks: {str(e)}"
            ) from e
