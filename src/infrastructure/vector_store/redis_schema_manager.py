"""Redis vector store schema manager prototype."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Tuple


class RedisCommandable(Protocol):
    """Protocol describing the subset of redis commands used.

    Purpose:
        Allow schema manager to accept any redis-like client implementing
        ``execute_command``.

    Args:
        *args: Command arguments passed to Redis.

    Example:
        >>> class FakeRedis:
        ...     def execute_command(self, *args: Any) -> str:
        ...         return \"OK\"
        >>> FakeRedis()  # doctest: +ELLIPSIS
        <...FakeRedis object ...>
    """

    def execute_command(self, *args: Any) -> Any:
        """Execute a Redis command."""


class RedisSchemaError(RuntimeError):
    """Error raised when Redis schema operations fail.

    Purpose:
        Provide a dedicated exception for vector index schema issues.

    Args:
        message: Human-readable error message.

    Example:
        >>> raise RedisSchemaError(\"schema failure\")  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        RedisSchemaError: schema failure
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


@dataclass(frozen=True)
class RedisSchemaManager:
    """Manage Redis RediSearch index creation for embeddings.

    Purpose:
        Generate and execute commands that ensure the vector index schema
        exists before writing embeddings.
    """

    index_name: str
    key_prefix: str
    dimension: int
    distance_metric: str = "COSINE"
    initial_cap: int = 2000
    m: int = 16

    def ensure_schema(self, connection: RedisCommandable) -> None:
        """Ensure the RediSearch schema exists.

        Purpose:
            Create the index if it is absent by issuing ``FT.CREATE``.

        Args:
            connection: Redis-compatible client executing commands.

        Returns:
            None.

        Raises:
            RedisSchemaError: If the Redis command fails.

        Example:
            >>> manager = RedisSchemaManager(
            ...     index_name=\"embedding:index:v1\",
            ...     key_prefix=\"embedding:chunk:\",
            ...     dimension=1536,
            ... )
            >>> manager.ensure_schema(connection=FakeRedis())  # doctest: +SKIP
        """
        command = self._build_command()
        try:
            connection.execute_command(*command)
        except Exception as error:  # noqa: BLE001 - surface as domain-specific error.
            raise RedisSchemaError(f"Failed to ensure schema: {error}") from error

    def _build_command(self) -> Tuple[Any, ...]:
        """Build the FT.CREATE command arguments.

        Purpose:
            Compose the RediSearch schema definition used by the index.

        Args:
            None.

        Returns:
            Tuple[Any, ...]: Command tuple to pass to ``execute_command``.

        Raises:
            RedisSchemaError: Never raised.

        Example:
            >>> manager = RedisSchemaManager(
            ...     index_name=\"embedding:index:v1\",
            ...     key_prefix=\"embedding:chunk:\",
            ...     dimension=1536,
            ... )
            >>> command = manager._build_command()
            >>> command[0]
            'FT.CREATE'
        """
        return (
            "FT.CREATE",
            self.index_name,
            "ON",
            "HASH",
            "PREFIX",
            "1",
            self.key_prefix,
            "SCHEMA",
            "embedding",
            "VECTOR",
            "HNSW",
            "12",
            "TYPE",
            "FLOAT32",
            "DIM",
            str(self.dimension),
            "DISTANCE_METRIC",
            self.distance_metric,
            "INITIAL_CAP",
            str(self.initial_cap),
            "M",
            str(self.m),
        )

