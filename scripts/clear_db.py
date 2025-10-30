#!/usr/bin/env python3
"""Script to clear MongoDB data for channels and tasks.

Clears:
- channels collection (all channel subscriptions)
- tasks collection (all tasks)
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import os

load_dotenv()

from src.infrastructure.database.mongo import get_db, close_client
from src.infrastructure.monitoring.logger import get_logger

logger = get_logger(name="clear_db")


async def clear_database():
    """Clear channels and tasks collections."""
    db = await get_db()
    
    try:
        # Clear channels collection
        channels_result = await db.channels.delete_many({})
        logger.info(f"Deleted {channels_result.deleted_count} channel subscriptions")
        print(f"✅ Deleted {channels_result.deleted_count} channel subscriptions")
        
        # Clear tasks collection (if exists)
        try:
            tasks_result = await db.tasks.delete_many({})
            logger.info(f"Deleted {tasks_result.deleted_count} tasks")
            print(f"✅ Deleted {tasks_result.deleted_count} tasks")
        except Exception as e:
            logger.debug(f"Tasks collection may not exist: {e}")
            print(f"ℹ️  Tasks collection not found (may not exist)")
        
        # Show remaining collections
        collections = await db.list_collection_names()
        print(f"\n📊 Remaining collections in database:")
        for col in collections:
            count = await db[col].count_documents({})
            print(f"  - {col}: {count} documents")
        
        print("\n✅ Database cleared successfully!")
        
    except Exception as e:
        logger.error(f"Error clearing database: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    finally:
        await close_client()


if __name__ == "__main__":
    print("🗑️  Clearing MongoDB data...")
    print(f"MongoDB URL: {os.getenv('MONGODB_URL', 'mongodb://localhost:27017')}")
    print(f"Database: {os.getenv('DB_NAME', 'butler')}")
    print()
    
    asyncio.run(clear_database())

