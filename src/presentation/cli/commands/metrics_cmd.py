"""Metrics command for viewing and exporting metrics.

Following the Zen of Python:
- Simple is better than complex
- Flat is better than nested
- Readability counts
"""

import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

from src.infrastructure.monitoring.metrics import get_metrics


def display_metrics_summary() -> None:
    """Display metrics summary."""
    console = Console()
    metrics = get_metrics().get_metrics()

    # Summary table
    summary = Table(title="Metrics Summary", show_header=True, header_style="bold cyan")
    summary.add_column("Metric", style="cyan")
    summary.add_column("Value", style="green")

    summary.add_row("Total Requests", f"{metrics['request_count']:,}")
    summary.add_row("Successful", f"{metrics['successful_requests']:,}")
    summary.add_row("Failed", f"{metrics['failed_requests']:,}")
    summary.add_row("Success Rate", f"{metrics['success_rate']:.1%}")
    summary.add_row("Total Tokens", f"{metrics['total_tokens_used']:,}")

    if metrics["request_count"] > 0:
        avg_time = metrics["average_response_time_ms"]
        total_time = metrics["total_response_time_ms"]
        summary.add_row("Avg Response Time", f"{avg_time:.2f} ms")
        summary.add_row("Total Time", f"{total_time:.2f} ms")

    uptime_hours = metrics["uptime_seconds"] / 3600
    summary.add_row("Uptime", f"{uptime_hours:.1f} hours")

    console.print(summary)

    # Display errors if any
    if metrics["failed_requests"] > 0:
        console.print("\n")
        _display_errors(console, metrics)

    # Display token breakdown
    if metrics.get("token_usage_by_operation"):
        console.print("\n")
        _display_token_breakdown(console, metrics)


def export_metrics_json(output_path: str) -> None:
    """Export metrics to JSON file.

    Args:
        output_path: Path to output file
    """
    metrics = get_metrics().get_metrics()

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w") as f:
        json.dump(metrics, f, indent=2, default=str)

    console = Console()
    console.print(f"[green]✓ Metrics exported to {output_path}[/green]")


def export_metrics_csv(output_path: str) -> None:
    """Export metrics to CSV file.

    Args:
        output_path: Path to output file
    """
    metrics = get_metrics().get_metrics()
    output = Path(output_path)

    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w") as f:
        f.write("Metric,Value\n")
        f.write(f"Total Requests,{metrics['request_count']}\n")
        f.write(f"Successful Requests,{metrics['successful_requests']}\n")
        f.write(f"Failed Requests,{metrics['failed_requests']}\n")
        f.write(f"Success Rate,{metrics['success_rate']:.4f}\n")
        f.write(f"Total Tokens,{metrics['total_tokens_used']}\n")
        f.write(f"Average Response Time,{metrics['average_response_time_ms']}\n")
        f.write(f"Uptime Seconds,{metrics['uptime_seconds']}\n")
        f.write(f"Start Time,{metrics['start_time']}\n")

    console = Console()
    console.print(f"[green]✓ Metrics exported to {output_path}[/green]")


def reset_metrics() -> None:
    """Reset metrics counters."""
    get_metrics().reset()

    console = Console()
    console.print("[green]✓ Metrics reset successfully[/green]")


def _display_errors(console: Console, metrics: dict) -> None:
    """Display error statistics.

    Args:
        console: Rich console instance
        metrics: Metrics dictionary
    """
    error_counts = metrics.get("error_counts", {})

    if not error_counts:
        return

    table = Table(title="Error Summary")
    table.add_column("Error", style="red")
    table.add_column("Count", justify="right", style="yellow")

    for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
        table.add_row(error, str(count))

    console.print(table)


def _display_token_breakdown(console: Console, metrics: dict) -> None:
    """Display token usage breakdown.

    Args:
        console: Rich console instance
        metrics: Metrics dictionary
    """
    token_usage = metrics.get("token_usage_by_operation", {})

    if not token_usage:
        return

    table = Table(title="Token Usage by Operation")
    table.add_column("Operation", style="cyan")
    table.add_column("Tokens", justify="right", style="yellow")
    table.add_column("Percentage", justify="right", style="dim")

    total_tokens = metrics["total_tokens_used"]

    for operation, tokens in sorted(
        token_usage.items(), key=lambda x: x[1], reverse=True
    ):
        percentage = (tokens / total_tokens * 100) if total_tokens > 0 else 0
        table.add_row(operation, f"{tokens:,}", f"{percentage:.1f}%")

    console.print(table)
