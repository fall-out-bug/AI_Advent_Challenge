"""Archive reader protocol for multipass reviewer package."""

from __future__ import annotations

from typing import Mapping, Protocol


class ArchiveReader(Protocol):
    async def read_latest(
        self, archive_path: str, *_args: object, **_kwargs: object
    ) -> Mapping[str, str]:
        """Return extracted code files for the latest submission."""
        ...
