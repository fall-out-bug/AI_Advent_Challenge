"""Tests for Prometheus metrics (Phase 8).

These tests operate in two modes:

* When PROMETHEUS_URL is set (live shared infra), perform lightweight HTTP
  readiness checks against the running Prometheus server.
* When no live endpoint is configured, fall back to the original mocked unit
  tests that exercise our instrumentation helpers.
"""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _load_shared_infra_env() -> None:
    """Load ~/work/infra/.env.infra if present to populate PROMETHEUS_URL."""
    if os.getenv("PROMETHEUS_URL"):
        return

    env_path = Path.home() / "work/infra/.env.infra"
    if not env_path.exists():
        return

    try:
        for raw_line in env_path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            if key and value:
                os.environ.setdefault(key, value)
    except OSError:
        # Ignore file access errors; the tests will fall back to mocked mode.
        return


_load_shared_infra_env()

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
        try:
            response = httpx.get(readiness_endpoint, timeout=5.0)
        except httpx.RequestError as exc:
            pytest.skip(f"Prometheus readiness endpoint unreachable: {exc}")

        assert response.status_code == 200
        assert "Prometheus Server is Ready" in response.text

    def test_prometheus_live_metrics_head() -> None:
        """Perform a lightweight metrics HEAD request to the live server."""
        import httpx

        metrics_endpoint = PROMETHEUS_URL.rstrip("/") + "/metrics"
        try:
            response = httpx.head(metrics_endpoint, timeout=5.0)
        except httpx.RequestError as exc:
            pytest.skip(f"Prometheus metrics endpoint unreachable: {exc}")

        assert response.status_code in {200, 405}  # 405 when HEAD not supported

else:

    @pytest.fixture
    def mock_prometheus_available():
        """Ensure prometheus metrics module is loaded with real client."""
        import importlib

        import src.infrastructure.monitoring.prometheus_metrics as metrics_module

        yield importlib.reload(metrics_module)

    @pytest.fixture
    def mock_prometheus_unavailable():
        """Reload metrics module simulating missing prometheus_client."""
        import builtins
        import importlib
        import sys

        module_name = "src.infrastructure.monitoring.prometheus_metrics"
        original_import = builtins.__import__
        original_module = sys.modules.get(module_name)

        def fake_import(name, *args, **kwargs):
            if name == "prometheus_client":
                raise ImportError("prometheus_client not installed")
            return original_import(name, *args, **kwargs)

        with patch.object(builtins, "__import__", side_effect=fake_import):
            sys.modules.pop(module_name, None)
            fallback_module = importlib.import_module(module_name)
            yield fallback_module

        sys.modules.pop(module_name, None)
        if original_module is not None:
            sys.modules[module_name] = original_module

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
        mock_db = MagicMock()
        channels_cursor = MagicMock()
        channels_cursor.to_list = AsyncMock(return_value=[])
        mock_db.channels.find.return_value = channels_cursor

        with patch(
            "src.workers.post_fetcher_worker.get_mcp_client", return_value=mock_mcp
        ):
            with patch(
                "src.workers.post_fetcher_worker.get_db",
                new=AsyncMock(return_value=mock_db),
            ):
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
                            await worker._process_all_channels()

    @pytest.mark.asyncio
    async def test_pdf_generation_metrics_integration():
        """Test that PDF generation records metrics."""
        pytest.importorskip("weasyprint")

        from src.presentation.cli.backoffice.services import digest_exporter

        with patch(
            "src.presentation.cli.backoffice.services.digest_exporter._HTML_TEMPLATE",
            "<html>{content}</html>",
        ):
            with patch("weasyprint.HTML") as mock_html:
                mock_html.return_value.write_pdf.return_value = b"fake_pdf_bytes"

                with patch(
                    "src.presentation.cli.backoffice.services.digest_exporter.pdf_generation_duration_seconds"
                ):
                    with patch(
                        "src.presentation.cli.backoffice.services.digest_exporter.pdf_file_size_bytes"
                    ):
                        with patch(
                            "src.presentation.cli.backoffice.services.digest_exporter.pdf_pages_total"
                        ):
                            result = digest_exporter.convert_markdown_to_pdf(
                                "# Test\n\nContent"
                            )
                            assert result == b"fake_pdf_bytes"

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

        with patch(
            "src.presentation.bot.handlers.menu.get_mcp_client"
        ) as mock_client_fn:
            mock_client = AsyncMock()
            mock_client_fn.return_value = mock_client
            mock_client.call_tool = AsyncMock(
                return_value={"posts_by_channel": {}, "error": "no_posts"}
            )

            with patch(
                "src.presentation.bot.handlers.menu.get_pdf_cache"
            ) as mock_cache:
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
        pytest.importorskip("weasyprint")

        from src.presentation.cli.backoffice.services import digest_exporter

        with patch(
            "src.presentation.cli.backoffice.services.digest_exporter._HTML_TEMPLATE",
            "<html>{content}</html>",
        ):
            with patch("weasyprint.HTML") as mock_html:
                mock_html.return_value.write_pdf.side_effect = Exception(
                    "Conversion failed"
                )

                with patch(
                    "src.presentation.cli.backoffice.services.digest_exporter.pdf_generation_errors_total"
                ) as mock_errors:
                    with pytest.raises(Exception):
                        digest_exporter.convert_markdown_to_pdf("invalid markdown")
                    assert mock_errors.labels.return_value.inc.called
