"""Domain interface for homework review service.

This interface defines the contract for homework review operations
in the domain layer. Implementations should be provided by infrastructure
layer.  # noqa: E501

Epic 21 · Stage 21_01b · Homework Review Service
"""

# noqa: E501
from abc import ABC, abstractmethod
from typing import Any, Dict

# noqa: E501
from src.domain.agents.state_machine import DialogContext


# noqa: E501
# noqa: E501
class HomeworkReviewService(ABC):
    """Service interface for homework review operations.

      Purpose:
          Abstract homework review business logic to enable testing,
          infrastructure flexibility, and clean architecture compliance.

      This interface ensures domain logic remains independent of
      specific implementations (HW Checker API, review tools, etc.).

      Example:
          >>> service = SomeHomeworkReviewService()
          >>> result = await service.list_homeworks(1)
          >>> review = await service.review_homework("abc123")
    """

    @abstractmethod
    async def list_homeworks(self, days: int) -> Dict[str, Any]:
        """List recent homework submissions.

              Args:
                  days: Number of days to look back.

              Returns:
                  Dictionary with 'total' and 'commits' keys.

              Raises:
                  HomeworkReviewError: If listing operation fails.
        """

    @abstractmethod
    async def review_homework(
        self, context: DialogContext, commit_hash: str
    ) -> str:
        """Review homework by commit hash.

              Args:
                  context: Dialog context with state and data.
                  commit_hash: Git commit hash to review.

              Returns:
                  Special format string for file sending or error message.

              Raises:
                  HomeworkReviewError: If review operation fails.
        """


# noqa: E501
# noqa: E501
class HomeworkReviewError(Exception):
    """Base exception for homework review operations."""

    pass
