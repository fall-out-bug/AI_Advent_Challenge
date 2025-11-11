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
        """Initialise command store."""
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
        dimension=384,
    )

    manager.ensure_schema(connection=connection)

    assert len(connection.commands) == 1
    command = connection.commands[0]
    assert command[0] == "FT.CREATE"
    assert "embedding:index:v1" in command
    assert "embedding:chunk:" in command
    assert "DIM" in command
    assert str(384) in command


def test_ensure_schema_wraps_errors() -> None:
    """Ensure Redis errors surface as RedisSchemaError."""

    class FailingRedis:
        def execute_command(self, *args: Any) -> None:
            raise RuntimeError("boom")

    manager = RedisSchemaManager(
        index_name="embedding:index:v1",
        key_prefix="embedding:chunk:",
        dimension=384,
    )

    with pytest.raises(RedisSchemaError):
        manager.ensure_schema(connection=FailingRedis())


def test_ensure_schema_falls_back_on_legacy_arguments() -> None:
    """Ensure manager retries with legacy FT.CREATE when Redis rejects new args."""

    class LegacyRedis(FakeRedis):
        def __init__(self) -> None:
            super().__init__()
            self.fail_first = True

        def execute_command(self, *args: Any) -> str:
            self.commands.append(args)
            if self.fail_first:
                self.fail_first = False
                raise RuntimeError("Expected 12 parameters but got 10")
            return "OK"

    connection = LegacyRedis()
    manager = RedisSchemaManager(
        index_name="embedding:index:v1",
        key_prefix="embedding:chunk:",
        dimension=384,
    )

    manager.ensure_schema(connection=connection)

    assert len(connection.commands) == 2
    initial_args = connection.commands[0]
    fallback_args = connection.commands[1]
    assert "INITIAL_CAP" in initial_args
    assert "INITIAL_CAP" not in fallback_args
