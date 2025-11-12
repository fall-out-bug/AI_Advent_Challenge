"""MongoDB implementation of DialogContextRepository.

Purpose:
    Provides MongoDB-backed persistence for dialog contexts
    with proper error handling and serialization.

Epic 21 · Stage 21_01a · Dialog Context Repository
"""

# noqa: E501
import logging
from typing import Optional

# noqa: E501
from motor.motor_asyncio import AsyncIOMotorDatabase

# noqa: E501
from src.domain.agents.state_machine import (
    DialogContext,
    DialogState,
)
from src.domain.interfaces.dialog_context_repository import (
    DialogContextRepository,
)

# noqa: E501
logger = logging.getLogger(__name__)


# noqa: E501
# noqa: E501
class RepositoryError(Exception):
    """Base exception for repository operations."""

    pass


# noqa: E501
# noqa: E501
class MongoDialogContextRepository(DialogContextRepository):
    """MongoDB implementation of DialogContextRepository.

      Purpose:
          Provides persistent storage for dialog contexts using MongoDB.
          Handles serialization/deserialization and error handling.

      Attributes:
          database: MongoDB database instance.
          collection_name: Name of collection for dialog contexts.

      Note:
          Thread-safe for async operations. Uses upsert for save operations.
    """

    def __init__(
        self,
        database: AsyncIOMotorDatabase,
        collection_name: str = "dialog_contexts",
    ):
        """Initialize repository.

              Args:
                  database: MongoDB database instance.
                  collection_name: Collection name for dialog contexts.
        """
        self.database = database
        self.collection_name = collection_name
        self.collection = database[collection_name]

    async def get_by_session(
        self, session_id: str
    ) -> Optional[DialogContext]:
        """Retrieve dialog context by session identifier.

              Args:
                  session_id: Unique session identifier.

              Returns:
                  DialogContext if found, None for new sessions.

              Raises:
                  RepositoryError: If database operation fails.
        """
        try:
            doc = await self.collection.find_one(
                {"session_id": session_id}
            )
            if doc:
                return self._deserialize_context(doc)
            return None
        except Exception as e:
            logger.error(
                f"Failed to get dialog context for session {session_id}: {e}"
            )
            raise RepositoryError(
                f"Failed to retrieve dialog context: {e}"
            ) from e

    async def save(self, context: DialogContext) -> None:
        """Persist dialog context to MongoDB.

              Args:
                  context: DialogContext to persist.

              Raises:
                  RepositoryError: If save operation fails.
        """
        try:
            doc = self._serialize_context(context)
            await self.collection.update_one(
                {"session_id": context.session_id},
                {"$set": doc},
                upsert=True,
            )
            logger.debug(
                f"Saved dialog context for session {context.session_id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to save dialog context for session {context.session_id}: {e}"
            )
            raise RepositoryError(
                f"Failed to save dialog context: {e}"
            ) from e

    async def delete(self, session_id: str) -> None:
        """Remove dialog context from storage.

              Args:
                  session_id: Session identifier to remove.

              Raises:
                  RepositoryError: If delete operation fails.
        """
        try:
            result = await self.collection.delete_one(
                {"session_id": session_id}
            )
            if result.deleted_count > 0:
                logger.debug(
                    f"Deleted dialog context for session {session_id}"
                )
            else:
                logger.warning(
                    f"No dialog context found for session {session_id}"
                )
        except Exception as e:
            logger.error(
                f"Failed to delete dialog context for session {session_id}: {e}"
            )
            raise RepositoryError(
                f"Failed to delete dialog context: {e}"
            ) from e

    def _serialize_context(self, context: DialogContext) -> dict:
        """Serialize DialogContext to MongoDB document.

              Args:
                  context: DialogContext instance.

              Returns:
                  Dictionary representation for MongoDB.
        """
        return {
            "user_id": context.user_id,
            "session_id": context.session_id,
            "state": context.state.value,  # Enum value (e.g., "idle")
            "data": context.data,
            "step_count": context.step_count,
        }

    def _deserialize_context(self, doc: dict) -> DialogContext:
        """Deserialize MongoDB document to DialogContext.

              Args:
                  doc: MongoDB document.

              Returns:
                  DialogContext instance.
        """
        return DialogContext(
            state=DialogState(doc["state"]),
            user_id=doc["user_id"],
            session_id=doc["session_id"],
            data=doc.get("data", {}),
            step_count=doc.get("step_count", 0),
        )
