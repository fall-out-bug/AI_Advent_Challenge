"""Integration tests for shared infrastructure connectivity (TDD red phase).

These tests intentionally fail until the project is wired to the shared
MongoDB, LLM, and Prometheus instances defined in `/home/fall_out_bug/work/infra`.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

import httpx
import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from src.infrastructure.config.settings import Settings


def _load_shared_infra_env() -> None:
    """Load shared infra environment defaults if available."""

    env_path = Path.home() / "work/infra/.env.infra"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@pytest.mark.asyncio
async def test_shared_mongo_connection() -> None:
    """Assert that the shared MongoDB instance is reachable and responsive."""

    settings = Settings()
    mongo_url = os.getenv("MONGODB_URL", settings.mongodb_url)
    db_name = settings.db_name

    parsed = urlparse(mongo_url)
    if parsed.path and parsed.path.strip("/"):
        db_name = parsed.path.strip("/")

    client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=3000)
    try:
        response = await client[db_name].command("ping")
    finally:
        client.close()

    assert response["ok"] == 1.0


@pytest.mark.asyncio
async def test_shared_llm_health_endpoint() -> None:
    """Assert that the shared LLM service exposes a healthy endpoint."""

    _load_shared_infra_env()
    llm_url = os.getenv("MISTRAL_API_URL") or os.getenv("LLM_URL") or Settings().llm_url
    if not llm_url:
        pytest.fail(
            "LLM_URL/MISTRAL_API_URL is not configured. Run shared infra (make day-12-up) "
            "or export variables from ~/work/infra/.env.infra before running tests."
        )

    health_endpoint = llm_url.rstrip("/") + "/health"

    timeout = httpx.Timeout(2.0, connect=1.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(health_endpoint)
    except httpx.HTTPError as exc:
        pytest.fail(
            f"Shared LLM endpoint unreachable ({health_endpoint}): {exc}. "
            "Ensure shared infra is running."
        )

    response.raise_for_status()
    payload = response.json()
    assert payload.get("status") in {"ok", "healthy", "UP"}


@pytest.mark.asyncio
async def test_shared_prometheus_metrics() -> None:
    """Assert that Prometheus metrics endpoint is reachable."""

    _load_shared_infra_env()
    prometheus_url = os.getenv("PROMETHEUS_URL")
    if not prometheus_url:
        pytest.fail(
            "PROMETHEUS_URL not configured. Start shared infra or export variables from "
            "~/work/infra/.env.infra before running tests."
        )

    metrics_endpoint = prometheus_url.rstrip("/") + "/metrics"

    timeout = httpx.Timeout(2.0, connect=1.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(metrics_endpoint)
    except httpx.HTTPError as exc:
        pytest.fail(
            f"Prometheus endpoint unreachable ({metrics_endpoint}): {exc}. "
            "Ensure shared infra is running."
        )

    response.raise_for_status()
    assert "# TYPE" in response.text
