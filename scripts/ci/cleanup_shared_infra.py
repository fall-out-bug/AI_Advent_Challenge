"""Tear down CI shared infrastructure services."""

from __future__ import annotations

import json
import os
import signal
import subprocess
from pathlib import Path


STATE_PATH = Path(__file__).resolve().parent / ".shared_infra_state.json"


def _terminate_process(pid: int) -> None:
    """Terminate a process if it is running."""
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return


def _docker_rm(container_name: str) -> None:
    """Remove a Docker container if it exists."""
    subprocess.run(
        ["docker", "rm", "-f", container_name],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> None:
    """Entry point for cleanup script."""
    if not STATE_PATH.exists():
        return

    try:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        STATE_PATH.unlink(missing_ok=True)
        return

    mock_pid = state.get("mock_pid")
    if isinstance(mock_pid, int):
        _terminate_process(mock_pid)

    container = state.get("mongo_container")
    if isinstance(container, str):
        _docker_rm(container)

    STATE_PATH.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
