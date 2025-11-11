"""Unit tests for Redis vector store schema prototype."""

from __future__ import annotations

from typing import Any, List, Tuple

import pytest

from src.infrastructure.vector_store.redis_schema_manager import (
    RedisSchemaError,
    RedisSchemaManager,
)


class FakeRedis:
    """Fake Redis connection capturing executed commands."""

    def __init__(self) -> None:
        """Initialise command store.

        Purpose:
            Keep executed commands for assertion in tests.

        Args:
            None.

        Returns:
            None.

        Raises:
            ValueError: Never raised.

        Example:
            >>> FakeRedis()
            FakeRedis()
        """
        self.commands: List[Tuple[Any, ...]] = []

    def execute_command(self, *args: Any) -> str:
        """Record command arguments and return OK."""
        self.commands.append(args)
        return "OK"


def test_ensure_schema_emits_expected_command() -> None:
    """Ensure schema manager constructs RediSearch indexing command."""
    connection = FakeRedis()
    manager = RedisSchemaManager(
        index_name="embedding:index:v1",
        key_prefix="embedding:chunk:",
        dimension=1536,
    )

    manager.ensure_schema(connection=connection)

    assert len(connection.commands) == 1
    command = connection.commands[0]
    assert command[0] == "FT.CREATE"
    assert "embedding:index:v1" in command
    assert "embedding:chunk:" in command
    assert "DIM" in command
    assert str(1536) in command


def test_ensure_schema_wraps_errors() -> None:
    """Ensure Redis errors surface as RedisSchemaError."""

    class FailingRedis:
        def execute_command(self, *args: Any) -> None:
            raise RuntimeError("boom")

    manager = RedisSchemaManager(
        index_name="embedding:index:v1",
        key_prefix="embedding:chunk:",
        dimension=1536,
    )

    with pytest.raises(RedisSchemaError):
        manager.ensure_schema(connection=FailingRedis())

