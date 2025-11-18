"""Mongo-backed user profile repository."""

from datetime import datetime
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

from src.domain.interfaces.personalization import UserProfileRepository
from src.domain.personalization.user_profile import UserProfile
from src.infrastructure.logging import get_logger
from src.infrastructure.personalization.metrics import (
    user_profile_reads_total,
    user_profile_writes_total,
)

logger = get_logger("profile_repository")


class MongoUserProfileRepository:
    """Mongo-backed repository for user profiles.

    Purpose:
        Implements UserProfileRepository protocol using MongoDB.
        Handles persistence, retrieval, and default profile creation.

    Attributes:
        collection: MongoDB collection for user_profiles.

    Example:
        >>> from motor.motor_asyncio import AsyncIOMotorClient
        >>> client = AsyncIOMotorClient("mongodb://localhost:27017")
        >>> repo = MongoUserProfileRepository(client, "butler")
        >>> profile = await repo.get("123456789")
    """

    def __init__(
        self, mongo_client: AsyncIOMotorClient, database: str = "butler"  # type: ignore[type-arg]
    ) -> None:
        """Initialize repository with Mongo client.

        Args:
            mongo_client: Motor async Mongo client.
            database: Database name (default: "butler").
        """
        self.collection = mongo_client[database]["user_profiles"]
        logger.info(
            "MongoUserProfileRepository initialized",
            extra={"database": database, "collection": "user_profiles"},
        )

    async def get(self, user_id: str) -> Optional[UserProfile]:
        """Get profile by user ID (auto-create if missing).

        Purpose:
            Retrieve user profile from MongoDB. If profile doesn't exist,
            automatically create and save default profile.

        Args:
            user_id: User identifier.

        Returns:
            UserProfile (newly created if didn't exist).

        Raises:
            PyMongoError: If MongoDB operation fails.

        Example:
            >>> profile = await repo.get("123")
            >>> profile.persona
            'Alfred-style дворецкий'
        """
        user_profile_reads_total.inc()

        try:
            doc = await self.collection.find_one({"user_id": user_id})

            if not doc:
                # Auto-create default profile
                logger.info(
                    "Profile not found, creating default",
                    extra={"user_id": user_id},
                )
                profile = UserProfile.create_default_profile(user_id)
                await self.save(profile)
                return profile

            # Convert document to UserProfile
            profile = self._doc_to_profile(doc)
            logger.debug(
                "Profile loaded",
                extra={
                    "user_id": user_id,
                    "persona": profile.persona,
                    "language": profile.language,
                },
            )
            return profile

        except PyMongoError as e:
            logger.error(
                "Failed to get profile",
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True,
            )
            raise

    async def save(self, profile: UserProfile) -> None:
        """Save (upsert) user profile.

        Purpose:
            Persist profile to MongoDB using upsert (insert or update).

        Args:
            profile: Profile to save.

        Raises:
            PyMongoError: If MongoDB operation fails.

        Example:
            >>> profile = UserProfile.create_default_profile("123")
            >>> await repo.save(profile)
        """
        user_profile_writes_total.inc()

        try:
            doc = self._profile_to_doc(profile)
            await self.collection.update_one(
                {"user_id": profile.user_id}, {"$set": doc}, upsert=True
            )

            logger.info(
                "Profile saved",
                extra={
                    "user_id": profile.user_id,
                    "persona": profile.persona,
                    "has_summary": profile.memory_summary is not None,
                },
            )

        except PyMongoError as e:
            logger.error(
                "Failed to save profile",
                extra={"user_id": profile.user_id, "error": str(e)},
                exc_info=True,
            )
            raise

    async def reset(self, user_id: str) -> None:
        """Delete profile and recreate with defaults.

        Purpose:
            Remove existing profile and create fresh default profile.
            Used for "reset memory" functionality.

        Args:
            user_id: User identifier.

        Raises:
            PyMongoError: If MongoDB operation fails.

        Example:
            >>> await repo.reset("123")
        """
        try:
            # Delete existing profile
            await self.collection.delete_one({"user_id": user_id})

            # Create default profile
            profile = UserProfile.create_default_profile(user_id)
            await self.save(profile)

            logger.info("Profile reset to defaults", extra={"user_id": user_id})

        except PyMongoError as e:
            logger.error(
                "Failed to reset profile",
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True,
            )
            raise

    def _doc_to_profile(self, doc: dict[str, Any]) -> UserProfile:
        """Convert Mongo document to UserProfile.

        Args:
            doc: MongoDB document.

        Returns:
            UserProfile value object.
        """
        return UserProfile(
            user_id=doc["user_id"],
            language=doc["language"],
            persona=doc["persona"],
            tone=doc["tone"],
            preferred_topics=doc.get("preferred_topics", []),
            memory_summary=doc.get("memory_summary"),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
        )

    def _profile_to_doc(self, profile: UserProfile) -> dict[str, Any]:
        """Convert UserProfile to Mongo document.

        Args:
            profile: UserProfile value object.

        Returns:
            MongoDB document dictionary.
        """
        return {
            "user_id": profile.user_id,
            "language": profile.language,
            "persona": profile.persona,
            "tone": profile.tone,
            "preferred_topics": profile.preferred_topics,
            "memory_summary": profile.memory_summary,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
        }
