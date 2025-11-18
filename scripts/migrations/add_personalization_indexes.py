"""Add MongoDB indexes for personalization collections."""

import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

from src.infrastructure.config.settings import get_settings
from src.infrastructure.logging import get_logger

logger = get_logger("personalization_indexes")


async def create_indexes() -> None:
    """Create MongoDB indexes for personalization.

    Purpose:
        Create indexes for user_profiles and user_memory collections.
        Ensures efficient queries and TTL cleanup.

    Example:
        >>> await create_indexes()
    """
    settings = get_settings()
    client = AsyncIOMotorClient(
        settings.mongodb_url,
        serverSelectionTimeoutMS=settings.mongo_timeout_ms,
        socketTimeoutMS=settings.mongo_timeout_ms,
        connectTimeoutMS=settings.mongo_timeout_ms,
    )
    db = client[settings.db_name]

    try:
        # User profiles indexes
        logger.info("Creating user_profiles indexes...")
        await db.user_profiles.create_index(
            [("user_id", 1)], unique=True, name="user_id_unique"
        )
        logger.info("✓ user_profiles.user_id_unique index created")

        # User memory indexes
        logger.info("Creating user_memory indexes...")

        # Compound index for efficient queries
        await db.user_memory.create_index(
            [("user_id", 1), ("created_at", -1)], name="user_id_created_at"
        )
        logger.info("✓ user_memory.user_id_created_at index created")

        # TTL index for auto-cleanup (90 days)
        await db.user_memory.create_index(
            [("created_at", 1)],
            expireAfterSeconds=7776000,  # 90 days
            name="created_at_ttl",
        )
        logger.info("✓ user_memory.created_at_ttl index created (90 days)")

        logger.info("All personalization indexes created successfully")

    except Exception as e:
        logger.error(
            "Failed to create indexes",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(create_indexes())
