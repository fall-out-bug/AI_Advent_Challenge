"""MongoDB client factory for dependency injection.

Purpose:
    Provide DI-based factory for creating MongoDB clients (sync and async)
    to replace direct MongoClient(...) instantiations.

This module implements Cluster A refactoring requirements (TL24-01).
"""

from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from src.infrastructure.config.settings import Settings, get_settings


class MongoClientFactory:
    """Factory for creating MongoDB clients with DI-based configuration.

    Purpose:
        Centralize MongoDB client creation using Settings, enabling
        easy switching between production and test environments.

    Attributes:
        settings: Settings instance (injected or retrieved via get_settings())
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """Initialize factory with settings.

        Args:
            settings: Settings instance. If None, uses get_settings().
        """
        self.settings = settings or get_settings()

    def create_sync_client(self, use_test_url: bool = False) -> MongoClient:
        """Create a synchronous MongoDB client.

        Args:
            use_test_url: If True, use test_mongodb_url. Otherwise, use mongodb_url.

        Returns:
            MongoClient: Configured synchronous MongoDB client.
        """
        url = (
            self.settings.test_mongodb_url
            if use_test_url
            else self.settings.mongodb_url
        )
        return MongoClient(
            url,
            serverSelectionTimeoutMS=self.settings.mongo_timeout_ms,
            socketTimeoutMS=self.settings.mongo_timeout_ms,
            connectTimeoutMS=self.settings.mongo_timeout_ms,
        )

    def create_async_client(
        self, use_test_url: bool = False
    ) -> AsyncIOMotorClient:
        """Create an asynchronous MongoDB client.

        Args:
            use_test_url: If True, use test_mongodb_url. Otherwise, use mongodb_url.

        Returns:
            AsyncIOMotorClient: Configured asynchronous MongoDB client.
        """
        url = (
            self.settings.test_mongodb_url
            if use_test_url
            else self.settings.mongodb_url
        )
        return AsyncIOMotorClient(
            url,
            serverSelectionTimeoutMS=self.settings.mongo_timeout_ms,
            socketTimeoutMS=self.settings.mongo_timeout_ms,
            connectTimeoutMS=self.settings.mongo_timeout_ms,
        )


def get_mongo_client_factory(settings: Optional[Settings] = None) -> MongoClientFactory:
    """Get MongoClientFactory instance (convenience function).

    Args:
        settings: Optional Settings instance. If None, uses get_settings().

    Returns:
        MongoClientFactory: Factory instance.
    """
    return MongoClientFactory(settings)
