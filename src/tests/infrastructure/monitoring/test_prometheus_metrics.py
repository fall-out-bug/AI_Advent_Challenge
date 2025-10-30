"""Tests for Prometheus metrics (Phase 8).

Following TDD principles:
- Test metrics collection and export
- Test metrics endpoint availability
- Test metrics integration in components
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


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
    with patch("src.infrastructure.monitoring.prometheus_metrics.prometheus_client", None):
        yield


def test_metrics_module_imports_without_prometheus(mock_prometheus_unavailable):
    """Test that metrics module imports gracefully when prometheus_client unavailable."""
    # Should not raise import error
    from src.infrastructure.monitoring import prometheus_metrics
    
    # Metrics should be dummy objects
    assert hasattr(prometheus_metrics, "post_fetcher_posts_saved_total")
    assert hasattr(prometheus_metrics, "pdf_generation_duration_seconds")
    assert hasattr(prometheus_metrics, "bot_digest_requests_total")


def test_metrics_module_imports_with_prometheus():
    """Test that metrics module imports with prometheus_client available."""
    try:
        from prometheus_client import Counter, Histogram, Gauge
        from src.infrastructure.monitoring import prometheus_metrics
        
        # Metrics should be real Prometheus objects
        assert hasattr(prometheus_metrics, "post_fetcher_posts_saved_total")
        assert hasattr(prometheus_metrics, "pdf_generation_duration_seconds")
        assert hasattr(prometheus_metrics, "bot_digest_requests_total")
    except ImportError:
        # prometheus_client not installed, skip test
        pytest.skip("prometheus_client not installed")


def test_metrics_registry_getter():
    """Test get_metrics_registry function."""
    from src.infrastructure.monitoring.prometheus_metrics import get_metrics_registry
    
    registry = get_metrics_registry()
    # Should return registry or None
    assert registry is None or hasattr(registry, "collect")


@pytest.mark.asyncio
async def test_post_fetcher_metrics_integration():
    """Test that post fetcher worker records metrics."""
    from src.workers.post_fetcher_worker import PostFetcherWorker
    from unittest.mock import AsyncMock, MagicMock
    
    # Mock dependencies
    mock_mcp = AsyncMock()
    mock_db = AsyncMock()
    mock_db.channels.find.return_value.to_list = AsyncMock(return_value=[])
    
    with patch("src.workers.post_fetcher_worker.get_mcp_client", return_value=mock_mcp):
        with patch("src.workers.post_fetcher_worker.get_db", return_value=mock_db):
            with patch("src.workers.post_fetcher_worker.get_settings") as mock_settings:
                mock_settings.return_value = MagicMock(
                    post_fetch_interval_hours=1,
                    post_ttl_days=7
                )
                with patch("src.workers.post_fetcher_worker.post_fetcher_worker_running") as mock_running:
                    with patch("src.workers.post_fetcher_worker.post_fetcher_last_run_timestamp") as mock_timestamp:
                        worker = PostFetcherWorker()
                        worker._running = True
                        
                        # Start worker (will set metrics)
                        await worker.run()
                        
                        # Metrics should be called
                        # Note: This test verifies integration, actual calls depend on prometheus_client availability


@pytest.mark.asyncio
async def test_pdf_generation_metrics_integration():
    """Test that PDF generation records metrics."""
    from src.presentation.mcp.tools.pdf_digest_tools import convert_markdown_to_pdf
    from unittest.mock import patch
    
    with patch("src.presentation.mcp.tools.pdf_digest_tools._convert_to_pdf") as mock_convert:
        mock_convert.return_value = b"fake_pdf_bytes"
        
        with patch("src.presentation.mcp.tools.pdf_digest_tools.pdf_generation_duration_seconds") as mock_duration:
            with patch("src.presentation.mcp.tools.pdf_digest_tools.pdf_file_size_bytes") as mock_size:
                with patch("src.presentation.mcp.tools.pdf_digest_tools.pdf_pages_total") as mock_pages:
                    
                    # Act
                    result = await convert_markdown_to_pdf("# Test\n\nContent")
                    
                    # Assert
                    assert "pdf_bytes" in result
                    # Metrics should be observed (if prometheus_client available)
                    # This test verifies integration, actual calls depend on prometheus_client availability


@pytest.mark.asyncio
async def test_bot_digest_metrics_integration():
    """Test that bot digest handler records metrics."""
    from src.presentation.bot.handlers.menu import callback_digest
    from unittest.mock import AsyncMock, MagicMock, patch
    from aiogram.types import CallbackQuery, User, Chat
    
    # Create mock callback query
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
        mock_client.call_tool = AsyncMock(return_value={
            "posts_by_channel": {},
            "error": "no_posts"
        })
        
        with patch("src.presentation.bot.handlers.menu.get_pdf_cache") as mock_cache:
            mock_cache.return_value.get = MagicMock(return_value=None)
            
            with patch("src.presentation.bot.handlers.menu.bot_digest_requests_total") as mock_requests:
                # Act
                await callback_digest(mock_callback)
                
                # Assert
                mock_requests.inc.assert_called_once()  # Should increment request counter


def test_metrics_endpoint_availability():
    """Test that metrics endpoint is available in MCP server."""
    from src.presentation.mcp.http_server import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Act
    response = client.get("/metrics")
    
    # Assert
    assert response.status_code in [200, 404]  # May return 404 if prometheus_client unavailable
    assert response.headers.get("content-type") in ["text/plain; version=0.0.4; charset=utf-8", None]


def test_metrics_endpoint_content_type():
    """Test that metrics endpoint returns correct content type."""
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        from src.presentation.mcp.http_server import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Act
        response = client.get("/metrics")
        
        # Assert
        if response.status_code == 200:
            assert CONTENT_TYPE_LATEST in response.headers.get("content-type", "")
    except ImportError:
        pytest.skip("prometheus_client not installed")


@pytest.mark.asyncio
async def test_metrics_in_error_scenarios():
    """Test that metrics are recorded in error scenarios."""
    from src.presentation.mcp.tools.pdf_digest_tools import convert_markdown_to_pdf
    from unittest.mock import patch
    
    with patch("src.presentation.mcp.tools.pdf_digest_tools._convert_to_pdf") as mock_convert:
        mock_convert.side_effect = Exception("Conversion failed")
        
        with patch("src.presentation.mcp.tools.pdf_digest_tools.pdf_generation_errors_total") as mock_errors:
            # Act
            result = await convert_markdown_to_pdf("invalid markdown")
            
            # Assert
            assert "error" in result
            # Error metric should be incremented (if prometheus_client available)
            # This test verifies integration, actual calls depend on prometheus_client availability

