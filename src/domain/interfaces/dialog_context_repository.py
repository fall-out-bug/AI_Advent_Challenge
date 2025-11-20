"""Domain interface for dialog context persistence.

This interface defines the contract for storing and retrieving dialog contexts
in the domain layer. Implementations should be provided by infrastructure
layer.  # noqa: E501

Epic 21 · Stage 21_01a · Dialog Context Repository
"""

# noqa: E501
from abc import ABC, abstractmethod
from typing import Optional

# noqa: E501
from src.domain.agents.state_machine import DialogContext


# noqa: E501
# noqa: E501
class DialogContextRepository(ABC):
    """Repository interface for dialog context persistence.

    Purpose:
        Abstract the storage of dialog contexts to enable testing,
        infrastructure flexibility, and clean architecture compliance.

    This interface ensures domain logic remains independent of
    specific storage implementations (MongoDB, Redis, etc.).

    Example:
        >>> repo = SomeDialogContextRepository()
        >>> context = await repo.get_by_session("session_123")
        >>> await repo.save(context)
    """

    @abstractmethod
    async def get_by_session(self, session_id: str) -> Optional[DialogContext]:
        """Retrieve dialog context by session identifier.

        Args:
            session_id: Unique session identifier.

        Returns:
            DialogContext instance if found, None otherwise.

        Raises:
            RepositoryError: If retrieval operation fails.
        """

    @abstractmethod
    async def save(self, context: DialogContext) -> None:
        """Persist dialog context.

        Args:
            context: DialogContext instance to save.

        Raises:
            RepositoryError: If save operation fails.
        """

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Remove dialog context by session identifier.

        Args:
            session_id: Session identifier to delete.

        Raises:
            RepositoryError: If delete operation fails.
        """
