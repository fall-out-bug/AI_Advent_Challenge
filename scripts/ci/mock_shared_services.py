"""Mock endpoints for LLM health and Prometheus metrics used in CI."""

from __future__ import annotations

import argparse
import json
import signal
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class MockHandler(BaseHTTPRequestHandler):
    """Serve health and metrics responses compatible with integration tests."""

    server_version = "MockSharedInfra/1.0"

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        """Suppress default request logging to keep CI logs clean."""

    def do_GET(self) -> None:  # noqa: N802
        """Handle GET requests for /health and /metrics."""
        if self.path.rstrip("/") == "/health":
            payload = json.dumps({"status": "ok"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if self.path.rstrip("/") == "/metrics":
            metrics = (
                "# HELP mock_request_total Total number of mock requests.\n"
                "# TYPE mock_request_total counter\n"
                'mock_request_total{service="mock_shared_infra"} 1\n'
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(metrics)))
            self.end_headers()
            self.wfile.write(metrics)
            return

        self.send_response(404)
        self.end_headers()


def run_server(port: int) -> None:
    """Run the threaded HTTP server until interrupted."""
    server = ThreadingHTTPServer(("0.0.0.0", port), MockHandler)

    def shutdown_handler(signum: int, frame) -> None:  # noqa: D401
        server.shutdown()

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    thread.join()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Mock shared infra services for CI.")
    parser.add_argument(
        "--port", type=int, default=18080, help="Port to bind the HTTP server."
    )
    args = parser.parse_args()
    run_server(args.port)


if __name__ == "__main__":
    main()
