"""Integration tests for shared infrastructure bootstrap scripts (TL-05).

Purpose:
    Verify that bootstrap/cleanup scripts work correctly and can be used
    for CI automation and local development (make day-23-up/down).
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pytest


@pytest.fixture
def bootstrap_script() -> Path:
    """Return path to bootstrap script."""
    return (
        Path(__file__).resolve().parent.parent.parent.parent
        / "scripts/ci/bootstrap_shared_infra.py"
    )


@pytest.fixture
def cleanup_script() -> Path:
    """Return path to cleanup script."""
    return (
        Path(__file__).resolve().parent.parent.parent.parent
        / "scripts/ci/cleanup_shared_infra.py"
    )


@pytest.fixture
def test_ports() -> tuple[int, int]:
    """Return test ports for MongoDB and mock services."""
    return (49017, 29080)


def test_bootstrap_check_fails_when_services_down(
    bootstrap_script: Path,
    test_ports: tuple[int, int],
) -> None:
    """Assert that --check flag returns non-zero when services are not running."""
    mongo_port, mock_port = test_ports

    # Ensure services are down
    cleanup_result = subprocess.run(
        [sys.executable, str(bootstrap_script.parent / "cleanup_shared_infra.py")],
        capture_output=True,
        check=False,
    )

    # Check should fail when services are down
    result = subprocess.run(
        [
            sys.executable,
            str(bootstrap_script),
            "--check",
            "--mongo-port",
            str(mongo_port),
            "--mock-port",
            str(mock_port),
        ],
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0, "--check should fail when services are not running"


def test_bootstrap_starts_services(
    bootstrap_script: Path,
    cleanup_script: Path,
    test_ports: tuple[int, int],
) -> None:
    """Assert that bootstrap script starts MongoDB and mock services."""
    mongo_port, mock_port = test_ports

    # Clean up first
    subprocess.run(
        [sys.executable, str(cleanup_script)],
        capture_output=True,
        check=False,
    )
    time.sleep(1)

    try:
        # Bootstrap services
        result = subprocess.run(
            [
                sys.executable,
                str(bootstrap_script),
                "--mongo-port",
                str(mongo_port),
                "--mock-port",
                str(mock_port),
            ],
            capture_output=True,
            check=True,
            text=True,
        )

        assert result.returncode == 0, "Bootstrap should succeed"

        # Wait a bit for services to fully start
        time.sleep(2)

        # Verify check passes after bootstrap
        check_result = subprocess.run(
            [
                sys.executable,
                str(bootstrap_script),
                "--check",
                "--mongo-port",
                str(mongo_port),
                "--mock-port",
                str(mock_port),
            ],
            capture_output=True,
            check=True,
            text=True,
        )

        assert check_result.returncode == 0, "--check should pass after bootstrap"
    finally:
        # Clean up
        subprocess.run(
            [sys.executable, str(cleanup_script)],
            capture_output=True,
            check=False,
        )
        time.sleep(1)


def test_cleanup_removes_services(
    bootstrap_script: Path,
    cleanup_script: Path,
    test_ports: tuple[int, int],
) -> None:
    """Assert that cleanup script removes containers and processes."""
    mongo_port, mock_port = test_ports

    # Start services first
    subprocess.run(
        [
            sys.executable,
            str(bootstrap_script),
            "--mongo-port",
            str(mongo_port),
            "--mock-port",
            str(mock_port),
        ],
        capture_output=True,
        check=False,
    )
    time.sleep(2)

    # Clean up
    result = subprocess.run(
        [sys.executable, str(cleanup_script)],
        capture_output=True,
        check=True,
        text=True,
    )

    assert result.returncode == 0, "Cleanup should succeed"
    time.sleep(1)

    # Verify check fails after cleanup
    check_result = subprocess.run(
        [
            sys.executable,
            str(bootstrap_script),
            "--check",
            "--mongo-port",
            str(mongo_port),
            "--mock-port",
            str(mock_port),
        ],
        capture_output=True,
        check=False,
    )

    assert check_result.returncode != 0, "--check should fail after cleanup"


def test_restart_validation(
    bootstrap_script: Path,
    cleanup_script: Path,
    test_ports: tuple[int, int],
) -> None:
    """Assert that services can be restarted (down + up) cleanly."""
    mongo_port, mock_port = test_ports

    try:
        # First bootstrap
        subprocess.run(
            [
                sys.executable,
                str(bootstrap_script),
                "--mongo-port",
                str(mongo_port),
                "--mock-port",
                str(mock_port),
            ],
            capture_output=True,
            check=True,
        )
        time.sleep(2)

        # Verify first bootstrap works
        check_1 = subprocess.run(
            [
                sys.executable,
                str(bootstrap_script),
                "--check",
                "--mongo-port",
                str(mongo_port),
                "--mock-port",
                str(mock_port),
            ],
            capture_output=True,
            check=True,
        )
        assert check_1.returncode == 0

        # Cleanup
        subprocess.run(
            [sys.executable, str(cleanup_script)],
            capture_output=True,
            check=True,
        )
        time.sleep(1)

        # Second bootstrap (restart)
        subprocess.run(
            [
                sys.executable,
                str(bootstrap_script),
                "--mongo-port",
                str(mongo_port),
                "--mock-port",
                str(mock_port),
            ],
            capture_output=True,
            check=True,
        )
        time.sleep(2)

        # Verify second bootstrap works
        check_2 = subprocess.run(
            [
                sys.executable,
                str(bootstrap_script),
                "--check",
                "--mongo-port",
                str(mongo_port),
                "--mock-port",
                str(mock_port),
            ],
            capture_output=True,
            check=True,
        )
        assert check_2.returncode == 0
    finally:
        # Final cleanup
        subprocess.run(
            [sys.executable, str(cleanup_script)],
            capture_output=True,
            check=False,
        )
