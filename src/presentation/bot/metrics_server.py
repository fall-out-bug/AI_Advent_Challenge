"""HTTP server for exposing Prometheus metrics.

Purpose:
    Lightweight HTTP server running alongside Butler Bot to expose
    Prometheus metrics on port 9091 for scraping.

Following Python Zen: Simple, explicit, readable.
Following Clean Architecture: Presentation layer HTTP server.
"""

import asyncio
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Optional

from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from src.infrastructure.logging import get_logger

from src.infrastructure.monitoring.prometheus_metrics import get_metrics_registry


logger = get_logger("metrics_server")


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Prometheus metrics endpoint."""

    def do_GET(self) -> None:
        """Handle GET requests to /metrics endpoint."""
        if self.path == "/metrics":
            try:
                registry = get_metrics_registry()
                if registry is None:
                    self.send_response(503)
                    self.end_headers()
                    self.wfile.write(b"# Metrics registry unavailable\n")
                    return

                output = generate_latest(registry)

                self.send_response(200)
                self.send_header("Content-Type", CONTENT_TYPE_LATEST)
                self.end_headers()
                self.wfile.write(output)
            except Exception as e:
                logger.error(f"Error generating metrics: {e}", exc_info=True)
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"Internal Server Error")
        elif self.path == "/health":
            """Health check endpoint."""
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def log_message(self, format: str, *args: object) -> None:
        """Suppress default logging (we use our own logger)."""


class MetricsServer:
    """Prometheus metrics HTTP server.

    Purpose:
        Runs a simple HTTP server in a separate thread to expose metrics.
        Integrates with graceful shutdown.

    Args:
        port: Port to listen on (default: 9091 from METRICS_PORT env)
        host: Host to bind to (default: 0.0.0.0)

    Example:
        >>> server = MetricsServer(port=9091)
        >>> await server.start()
        >>> # ... bot runs ...
        >>> await server.stop()
    """

    def __init__(self, port: Optional[int] = None, host: str = "0.0.0.0") -> None:
        """Initialize metrics server.

        Args:
            port: Port to listen on. Defaults to METRICS_PORT env var or 9091.
            host: Host to bind to (default: 0.0.0.0 for all interfaces)
        """
        self.port = port or int(os.getenv("METRICS_PORT", "9091"))
        self.host = host
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[Thread] = None
        self._running = False

    def _run_server(self) -> None:
        """Run HTTP server in thread."""
        try:
            self.server = HTTPServer((self.host, self.port), MetricsHandler)
            logger.info(f"Metrics server started on {self.host}:{self.port}")
            self._running = True
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"Metrics server error: {e}", exc_info=True)
            self._running = False

    async def start(self) -> None:
        """Start metrics server in background thread.

        Raises:
            RuntimeError: If server fails to start
        """
        if self._running:
            logger.warning("Metrics server already running")
            return

        self.thread = Thread(target=self._run_server, daemon=True)
        self.thread.start()

        # Wait a bit to ensure server started
        await asyncio.sleep(0.1)

        if not self._running:
            raise RuntimeError("Failed to start metrics server")

        logger.info(
            f"Metrics server listening on http://{self.host}:{self.port}/metrics"
        )

    async def stop(self) -> None:
        """Stop metrics server gracefully."""
        if not self._running or self.server is None:
            return

        logger.info("Stopping metrics server...")
        self.server.shutdown()
        self.server.server_close()
        self._running = False

        if self.thread:
            self.thread.join(timeout=2.0)

        logger.info("Metrics server stopped")

    def is_running(self) -> bool:
        """Check if server is running.

        Returns:
            True if server is running, False otherwise
        """
        return self._running
