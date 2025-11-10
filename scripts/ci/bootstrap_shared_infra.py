"""Bootstrap shared infrastructure services for CI environments."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path


STATE_PATH = Path(__file__).resolve().parent / ".shared_infra_state.json"


def _wait_for_port(host: str, port: int, timeout: float) -> None:
    """Wait until the given host/port accepts TCP connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return
        except OSError:
            time.sleep(1.0)
    raise RuntimeError(f"Timeout waiting for {host}:{port} to become ready")


def _append_env_variable(env_path: Path, key: str, value: str) -> None:
    """Append an environment variable assignment to the GitHub Actions env file."""
    env_path.parent.mkdir(parents=True, exist_ok=True)
    with env_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{key}={value}\n")


def _docker_rm(container_name: str) -> None:
    """Remove a Docker container if it exists."""
    subprocess.run(
        ["docker", "rm", "-f", container_name],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _start_mongo(container_name: str, port: int) -> None:
    """Start a MongoDB container exposed on the given port."""
    _docker_rm(container_name)
    subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "-p",
            f"{port}:27017",
            "-e",
            "MONGO_INITDB_ROOT_USERNAME=ci_admin",
            "-e",
            "MONGO_INITDB_ROOT_PASSWORD=ci_password",
            "-e",
            "MONGO_INITDB_DATABASE=butler",
            "mongo:6.0",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    _wait_for_port("127.0.0.1", port, timeout=60.0)


def _start_mock_services(port: int) -> subprocess.Popen[bytes]:
    """Start the mock LLM/Prometheus service."""
    script_path = Path(__file__).resolve().parent / "mock_shared_services.py"
    process = subprocess.Popen(
        [sys.executable, str(script_path), "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _wait_for_port("127.0.0.1", port, timeout=15.0)
    return process


def main() -> None:
    """Entry point for CI bootstrap script."""
    parser = argparse.ArgumentParser(
        description="Bootstrap shared infra services (Mongo + mock LLM/Prometheus) for CI.",
    )
    parser.add_argument("--mongo-port", type=int, default=27017, help="Host port for MongoDB.")
    parser.add_argument("--mock-port", type=int, default=18080, help="Host port for mock LLM/Prometheus service.")
    parser.add_argument(
        "--github-env",
        type=Path,
        default=Path(os.environ.get("GITHUB_ENV", "") or Path.cwd() / ".github-env"),
        help="Path to the GitHub Actions environment file.",
    )
    parser.add_argument(
        "--state-path",
        type=Path,
        default=STATE_PATH,
        help="Path to persist container/process metadata for cleanup.",
    )
    args = parser.parse_args()

    mongo_container = "ai-challenge-ci-mongo"
    _start_mongo(mongo_container, args.mongo_port)

    mock_process = _start_mock_services(args.mock_port)

    mongo_uri = f"mongodb://ci_admin:ci_password@127.0.0.1:{args.mongo_port}/butler?authSource=admin"
    llm_url = f"http://127.0.0.1:{args.mock_port}"
    prometheus_url = f"http://127.0.0.1:{args.mock_port}"

    _append_env_variable(args.github_env, "MONGODB_URL", mongo_uri)
    _append_env_variable(args.github_env, "TEST_MONGODB_URL", mongo_uri)
    _append_env_variable(args.github_env, "LLM_URL", llm_url)
    _append_env_variable(args.github_env, "PROMETHEUS_URL", prometheus_url)

    args.state_path.parent.mkdir(parents=True, exist_ok=True)
    args.state_path.write_text(
        json.dumps(
            {
                "mongo_container": mongo_container,
                "mock_pid": mock_process.pid,
            }
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
