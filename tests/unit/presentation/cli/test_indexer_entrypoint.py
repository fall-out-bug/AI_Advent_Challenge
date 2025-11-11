"""Tests for container entrypoint script used by embedding index pipeline."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_indexer_entrypoint_emits_cli_command_in_check_mode(monkeypatch):
    """Ensure the entrypoint prints the resolved CLI command when CHECK_ONLY=1.

    Purpose:
        Verify that the container entrypoint can be validated without running
        Poetry or hitting external services by using the CHECK_ONLY flag.
    """

    repo_root = Path(__file__).resolve().parents[4]
    script_path = repo_root / "scripts" / "indexer_entrypoint.sh"
    assert script_path.exists(), "entrypoint script must exist for the test"

    env = os.environ.copy()
    env.update(
        {
            "CHECK_ONLY": "1",
            "INDEX_RUN_ARGS": "--replace-fallback --show-fallback",
        }
    )

    result = subprocess.run(
        ["bash", str(script_path)],
        cwd=repo_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    expected_command = (
        "poetry run python -m src.presentation.cli.backoffice.main "
        "index run --replace-fallback --show-fallback"
    )
    assert expected_command in result.stdout
