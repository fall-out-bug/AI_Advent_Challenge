"""Integration tests for shared infrastructure connectivity (TDD red phase).

These tests intentionally fail until the project is wired to the shared
MongoDB, LLM, and Prometheus instances defined in `/home/fall_out_bug/work/infra`.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

import httpx
import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from src.infrastructure.config.settings import Settings


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

    llm_url = os.getenv("MISTRAL_API_URL") or os.getenv("LLM_URL")
    assert llm_url, "Shared LLM URL must be configured via MISTRAL_API_URL or LLM_URL"

    health_endpoint = llm_url.rstrip("/") + "/health"

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(health_endpoint)

    response.raise_for_status()
    payload = response.json()
    assert payload.get("status") in {"ok", "healthy", "UP"}


@pytest.mark.asyncio
async def test_shared_prometheus_metrics() -> None:
    """Assert that Prometheus metrics endpoint is reachable."""

    prometheus_url = os.getenv("PROMETHEUS_URL")
    assert prometheus_url, "PROMETHEUS_URL must point to the shared Prometheus instance"

    metrics_endpoint = prometheus_url.rstrip("/") + "/metrics"

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(metrics_endpoint)

    response.raise_for_status()
    assert "# TYPE" in response.text
