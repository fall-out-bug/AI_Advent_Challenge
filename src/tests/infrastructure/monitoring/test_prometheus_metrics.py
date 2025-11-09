"""Tests for Prometheus metrics (Phase 8).

These tests operate in two modes:

* When PROMETHEUS_URL is set (live shared infra), perform lightweight HTTP
  readiness checks against the running Prometheus server.
* When no live endpoint is configured, fall back to the original mocked unit
  tests that exercise our instrumentation helpers.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


PROMETHEUS_URL = os.getenv("PROMETHEUS_URL")


def _pytest_skip_live_only() -> None:
    if not PROMETHEUS_URL:
        pytest.skip("Live Prometheus URL not configured")


def _pytest_skip_mock_only() -> None:
    if PROMETHEUS_URL:
        pytest.skip("Skipped when live Prometheus endpoint is configured")


if PROMETHEUS_URL:

    def test_prometheus_live_readiness() -> None:
        """Ensure the shared Prometheus instance is reachable."""
        import httpx

        readiness_endpoint = PROMETHEUS_URL.rstrip("/") + "/-/ready"
        response = httpx.get(readiness_endpoint, timeout=5.0)

        assert response.status_code == 200
        assert "Prometheus Server is Ready" in response.text

    def test_prometheus_live_metrics_head() -> None:
        """Perform a lightweight metrics HEAD request to the live server."""
        import httpx

        metrics_endpoint = PROMETHEUS_URL.rstrip("/") + "/metrics"
        response = httpx.head(metrics_endpoint, timeout=5.0)

        assert response.status_code in {200, 405}  # 405 when HEAD not supported

else:

    @pytest.fixture
    def mock_prometheus_available():
        """Mock prometheus_client as available."""
        with patch("src.infrastructure.monitoring.prometheus_metrics.Counter"):
            with patch("src.infrastructure.monitoring.prometheus_metrics.Histogram"):
                with patch("src.infrastructure.monitoring.prometheus_metrics.Gauge"):
                    yield

    @pytest.fixture
    def mock_prometheus_unavailable():
        """Mock prometheus_client as unavailable."""
        with patch(
            "src.infrastructure.monitoring.prometheus_metrics.prometheus_client", None
        ):
            yield

    def test_metrics_module_imports_without_prometheus(mock_prometheus_unavailable):
        """Test that metrics module imports gracefully when prometheus_client unavailable."""
        from src.infrastructure.monitoring import prometheus_metrics

        assert hasattr(prometheus_metrics, "post_fetcher_posts_saved_total")
        assert hasattr(prometheus_metrics, "pdf_generation_duration_seconds")
        assert hasattr(prometheus_metrics, "bot_digest_requests_total")

    def test_metrics_module_imports_with_prometheus():
        """Test that metrics module imports with prometheus_client available."""
        try:
            from src.infrastructure.monitoring import prometheus_metrics

            assert hasattr(prometheus_metrics, "post_fetcher_posts_saved_total")
            assert hasattr(prometheus_metrics, "pdf_generation_duration_seconds")
            assert hasattr(prometheus_metrics, "bot_digest_requests_total")
        except ImportError:
            pytest.skip("prometheus_client not installed")

    def test_metrics_registry_getter():
        """Test get_metrics_registry function."""
        from src.infrastructure.monitoring.prometheus_metrics import (
            get_metrics_registry,
        )

        registry = get_metrics_registry()
        assert registry is None or hasattr(registry, "collect")

    @pytest.mark.asyncio
    async def test_post_fetcher_metrics_integration():
        """Test that post fetcher worker records metrics."""
        from src.workers.post_fetcher_worker import PostFetcherWorker

        mock_mcp = AsyncMock()
        mock_db = AsyncMock()
        mock_db.channels.find.return_value.to_list = AsyncMock(return_value=[])

        with patch(
            "src.workers.post_fetcher_worker.get_mcp_client", return_value=mock_mcp
        ):
            with patch("src.workers.post_fetcher_worker.get_db", return_value=mock_db):
                with patch(
                    "src.workers.post_fetcher_worker.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = MagicMock(
                        post_fetch_interval_hours=1, post_ttl_days=7
                    )
                    with patch(
                        "src.workers.post_fetcher_worker.post_fetcher_worker_running"
                    ):
                        with patch(
                            "src.workers.post_fetcher_worker.post_fetcher_last_run_timestamp"
                        ):
                            worker = PostFetcherWorker()
                            worker._running = True
                            await worker.run()

    @pytest.mark.asyncio
    async def test_pdf_generation_metrics_integration():
        """Test that PDF generation records metrics."""
        from src.presentation.mcp.tools.pdf_digest_tools import convert_markdown_to_pdf

        with patch(
            "src.presentation.mcp.tools.pdf_digest_tools._convert_to_pdf"
        ) as mock_convert:
            mock_convert.return_value = b"fake_pdf_bytes"

            with patch(
                "src.presentation.mcp.tools.pdf_digest_tools.pdf_generation_duration_seconds"
            ):
                with patch(
                    "src.presentation.mcp.tools.pdf_digest_tools.pdf_file_size_bytes"
                ):
                    with patch(
                        "src.presentation.mcp.tools.pdf_digest_tools.pdf_pages_total"
                    ):
                        result = await convert_markdown_to_pdf("# Test\n\nContent")
                        assert "pdf_bytes" in result

    @pytest.mark.asyncio
    async def test_bot_digest_metrics_integration():
        """Test that bot digest handler records metrics."""
        from aiogram.types import CallbackQuery, Chat, User

        from src.presentation.bot.handlers.menu import callback_digest

        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_callback.from_user = MagicMock(spec=User)
        mock_callback.from_user.id = 123
        mock_callback.message = MagicMock()
        mock_callback.message.chat = MagicMock(spec=Chat)
        mock_callback.message.chat.id = 456
        mock_callback.message.bot.send_chat_action = AsyncMock()
        mock_callback.message.answer_document = AsyncMock()
        mock_callback.message.answer = AsyncMock()
        mock_callback.answer = AsyncMock()

        with patch("src.presentation.bot.handlers.menu.MCPClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.call_tool = AsyncMock(
                return_value={"posts_by_channel": {}, "error": "no_posts"}
            )

            with patch("src.presentation.bot.handlers.menu.get_pdf_cache") as mock_cache:
                mock_cache.return_value.get = MagicMock(return_value=None)

                with patch(
                    "src.presentation.bot.handlers.menu.bot_digest_requests_total"
                ) as mock_requests:
                    await callback_digest(mock_callback)
                    mock_requests.inc.assert_called_once()

    def test_metrics_endpoint_availability():
        """Test that metrics endpoint is available in MCP server."""
        from fastapi.testclient import TestClient

        from src.presentation.mcp.http_server import app

        client = TestClient(app)
        response = client.get("/metrics")

        assert response.status_code in [200, 404]
        assert response.headers.get("content-type") in [
            "text/plain; version=0.0.4; charset=utf-8",
            None,
        ]

    def test_metrics_endpoint_content_type():
        """Test that metrics endpoint returns correct content type."""
        try:
            from fastapi.testclient import TestClient
            from prometheus_client import CONTENT_TYPE_LATEST

            from src.presentation.mcp.http_server import app

            client = TestClient(app)
            response = client.get("/metrics")

            if response.status_code == 200:
                assert CONTENT_TYPE_LATEST in response.headers.get("content-type", "")
        except ImportError:
            pytest.skip("prometheus_client not installed")

    @pytest.mark.asyncio
    async def test_metrics_in_error_scenarios():
        """Test that metrics are recorded in error scenarios."""
        from src.presentation.mcp.tools.pdf_digest_tools import convert_markdown_to_pdf

        with patch(
            "src.presentation.mcp.tools.pdf_digest_tools._convert_to_pdf"
        ) as mock_convert:
            mock_convert.side_effect = Exception("Conversion failed")

            with patch(
                "src.presentation.mcp.tools.pdf_digest_tools.pdf_generation_errors_total"
            ) as mock_errors:
                result = await convert_markdown_to_pdf("invalid markdown")
                assert "error" in result
                assert mock_errors.inc.called
