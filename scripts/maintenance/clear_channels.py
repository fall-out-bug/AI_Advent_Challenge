"""Script to clear all channel subscriptions from MongoDB.

Purpose:
    Remove all channel subscriptions from the channels collection.
    Useful for resetting the database and starting fresh.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.database.mongo import close_client, get_db
from src.infrastructure.logging import get_logger

logger = get_logger("clear_channels")


async def clear_all_channels() -> None:
    """Clear all channel subscriptions from database.

    Purpose:
        Delete all documents from the channels collection.
        Logs the number of deleted records.
    """
    try:
        db = await get_db()

        # Count before deletion
        count_before = await db.channels.count_documents({})
        logger.info(f"Found {count_before} channel subscriptions in database")

        if count_before == 0:
            print("No channels to delete. Database is already empty.")
            return

        # Delete all channels
        result = await db.channels.delete_many({})
        deleted_count = result.deleted_count

        logger.info(f"Deleted {deleted_count} channel subscriptions from database")
        print(f"✅ Successfully deleted {deleted_count} channel subscription(s)")

        # Verify deletion
        count_after = await db.channels.count_documents({})
        if count_after > 0:
            logger.warning(
                f"Warning: {count_after} channels still remain after deletion"
            )
            print(f"⚠️  Warning: {count_after} channel(s) still remain")
        else:
            print("✅ Database cleared successfully")

    except Exception as e:
        logger.error(f"Error clearing channels: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        raise
    finally:
        await close_client()


if __name__ == "__main__":
    asyncio.run(clear_all_channels())
