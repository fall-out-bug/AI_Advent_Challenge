"""Metrics export functionality.

Following the Zen of Python:
- Simple is better than complex
- Practicality beats purity
- Readability counts
"""

import csv
import json
from datetime import datetime
from pathlib import Path

from src.infrastructure.monitoring.metrics import MetricsCollector


class MetricsExporter:
    """Export metrics to various formats."""

    def __init__(self, metrics_collector: MetricsCollector):
        """Initialize exporter.

        Args:
            metrics_collector: Metrics collector instance
        """
        self._metrics = metrics_collector

    def export_to_json(self, filepath: str, include_history: bool = False) -> None:
        """Export metrics to JSON format.

        Args:
            filepath: Output file path
            include_history: Whether to include operation history
        """
        metrics = self._metrics.get_metrics()

        if include_history:
            metrics["recent_operations"] = self._metrics.get_recent_operations(
                limit=100
            )

        with Path(filepath).open("w") as f:
            json.dump(metrics, f, indent=2, default=str)

    def export_to_csv(self, filepath: str) -> None:
        """Export metrics to CSV format.

        Args:
            filepath: Output file path
        """
        metrics = self._metrics.get_metrics()

        with Path(filepath).open("w", newline="") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(["Metric", "Value"])

            # Write summary metrics
            writer.writerow(["Request Count", metrics["request_count"]])
            writer.writerow(["Successful Requests", metrics["successful_requests"]])
            writer.writerow(["Failed Requests", metrics["failed_requests"]])
            writer.writerow(["Success Rate", f"{metrics['success_rate']:.2%}"])
            writer.writerow(["Total Tokens Used", metrics["total_tokens_used"]])
            writer.writerow(
                ["Average Response Time (ms)", metrics["average_response_time_ms"]]
            )
            writer.writerow(["Uptime (seconds)", metrics["uptime_seconds"]])

            # Write percentiles
            percentiles = metrics.get("response_time_percentiles", {})
            if percentiles:
                writer.writerow(["P50 (ms)", percentiles.get("p50", 0)])
                writer.writerow(["P95 (ms)", percentiles.get("p95", 0)])
                writer.writerow(["P99 (ms)", percentiles.get("p99", 0)])

            # Write error counts
            writer.writerow(["", ""])
            writer.writerow(["Error Type", "Count"])
            for error_type, count in metrics.get("error_counts", {}).items():
                writer.writerow([error_type, count])

            # Write token usage by operation
            writer.writerow(["", ""])
            writer.writerow(["Operation", "Tokens Used"])
            for operation, tokens in metrics.get(
                "token_usage_by_operation", {}
            ).items():
                writer.writerow([operation, tokens])

    def export_to_markdown(self, filepath: str, include_history: bool = False) -> None:
        """Export metrics to Markdown format.

        Args:
            filepath: Output file path
            include_history: Whether to include operation history
        """
        metrics = self._metrics.get_metrics()
        timestamp = datetime.utcnow().isoformat()

        lines = [
            "# Metrics Report",
            "",
            f"**Generated:** {timestamp}",
            "",
            "## Summary",
            "",
            f"- **Total Requests:** {metrics['request_count']}",
            f"- **Successful:** {metrics['successful_requests']}",
            f"- **Failed:** {metrics['failed_requests']}",
            f"- **Success Rate:** {metrics['success_rate']:.2%}",
            f"- **Total Tokens Used:** {metrics['total_tokens_used']}",
            f"- **Average Response Time:** {metrics['average_response_time_ms']:.2f}ms",
            f"- **Uptime:** {metrics['uptime_seconds']:.2f}s",
            "",
        ]

        # Add percentiles section
        percentiles = metrics.get("response_time_percentiles", {})
        if percentiles:
            lines.extend(
                [
                    "## Response Time Percentiles",
                    "",
                    f"- **P50 (median):** {percentiles.get('p50', 0):.2f}ms",
                    f"- **P95:** {percentiles.get('p95', 0):.2f}ms",
                    f"- **P99:** {percentiles.get('p99', 0):.2f}ms",
                    "",
                ]
            )

        # Add errors section
        error_counts = metrics.get("error_counts", {})
        if error_counts:
            lines.extend(["## Errors", ""])
            for error_type, count in error_counts.items():
                lines.append(f"- **{error_type}:** {count}")
            lines.append("")

        # Add token usage section
        token_usage = metrics.get("token_usage_by_operation", {})
        if token_usage:
            lines.extend(["## Token Usage by Operation", ""])
            for operation, tokens in token_usage.items():
                lines.append(f"- **{operation}:** {tokens} tokens")
            lines.append("")

        # Add recent operations if requested
        if include_history:
            recent_ops = self._metrics.get_recent_operations(limit=20)
            if recent_ops:
                lines.extend(
                    [
                        "## Recent Operations",
                        "",
                        "| Timestamp | Operation | Response Time | Status |",
                        "|-----------|-----------|---------------|--------|",
                    ]
                )
                for op in recent_ops:
                    status = "✓" if op.get("success") else "✗"
                    lines.append(
                        f"| {op.get('timestamp', 'N/A')} | "
                        f"{op.get('operation', 'N/A')} | "
                        f"{op.get('response_time_ms', 0):.2f}ms | "
                        f"{status} |"
                    )
                lines.append("")

        # Write to file
        with Path(filepath).open("w") as f:
            f.write("\n".join(lines))
