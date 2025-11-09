"""MongoDB client utilities using Motor (async)."""

from __future__ import annotations

import asyncio
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.infrastructure.config.settings import get_settings

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None
_lock = asyncio.Lock()


async def get_client() -> AsyncIOMotorClient:
    """Get a singleton Motor client instance.

    Returns:
        AsyncIOMotorClient: The initialized Motor client
    """

    global _client
    if _client is not None:
        return _client

    async with _lock:
        if _client is None:
            settings = get_settings()
            _client = AsyncIOMotorClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=settings.mongo_timeout_ms,
                socketTimeoutMS=settings.mongo_timeout_ms,
                connectTimeoutMS=settings.mongo_timeout_ms,
            )
    return _client


async def get_db() -> AsyncIOMotorDatabase:
    """Return database handle from the singleton client.

    Returns:
        AsyncIOMotorDatabase: Selected database instance
    """
    # Always get fresh settings to ensure environment variables are read
    # This is important for tests where DB_NAME might change
    settings = get_settings()
    db_name = settings.db_name

    global _db
    # Reset DB if name changed (important for tests)
    if _db is not None and _db.name != db_name:
        _db = None

    if _db is not None:
        return _db

    client = await get_client()
    _db = client[db_name]
    return _db


async def close_client() -> None:
    """Close the global client if it exists."""

    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None
