"""Status command for displaying system state.

Following the Zen of Python:
- Simple is better than complex
- Beautiful is better than ugly
- Readability counts
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.infrastructure.config.settings import Settings
from src.infrastructure.monitoring.metrics import get_metrics
from src.infrastructure.repositories.json_agent_repository import JsonAgentRepository


def display_status() -> None:
    """Display system status with current metrics and recent operations."""
    console = Console()

    # Get current metrics
    metrics = get_metrics().get_metrics()

    # Create main table
    table = Table(title="System Status", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    # Add basic metrics
    table.add_row("Total Requests", str(metrics["request_count"]))
    table.add_row("Successful", str(metrics["successful_requests"]))
    table.add_row("Failed", str(metrics["failed_requests"]))
    table.add_row("Success Rate", f"{metrics['success_rate']:.1%}")
    table.add_row("Total Tokens", f"{metrics['total_tokens_used']:,}")

    if metrics["request_count"] > 0:
        avg_time = metrics["average_response_time_ms"]
        table.add_row("Avg Response Time", f"{avg_time:.2f} ms")

    uptime_hours = metrics["uptime_seconds"] / 3600
    table.add_row("Uptime", f"{uptime_hours:.1f} hours")

    console.print(Panel(table, title="Current Metrics", border_style="cyan"))

    # Display recent operations
    _display_recent_operations(console)

    # Display token usage breakdown
    _display_token_usage(console, metrics)


def _display_recent_operations(console: Console, limit: int = 10) -> None:
    """Display recent operations.

    Args:
        console: Rich console instance
        limit: Maximum number of operations to show
    """
    recent = get_metrics().get_recent_operations(limit=limit)

    if not recent:
        console.print("\n📋 No recent operations found", style="dim")
        return

    table = Table(title=f"Recent Operations (Last {len(recent)})")
    table.add_column("Time", style="dim")
    table.add_column("Operation", style="cyan")
    table.add_column("Status", justify="right")
    table.add_column("Time (ms)", justify="right")

    for op in recent[-10:]:
        status = "✓" if op["success"] else "✗"
        status_style = "green" if op["success"] else "red"

        timestamp = (
            op["timestamp"].split("T")[1].split(".")[0]
            if "timestamp" in op
            else "unknown"
        )

        table.add_row(
            timestamp,
            op.get("operation", "unknown"),
            Text(status, style=status_style),
            f"{op['response_time_ms']:.2f}",
        )

    console.print("\n")
    console.print(table)


def _display_token_usage(console: Console, metrics: dict) -> None:
    """Display token usage breakdown by operation.

    Args:
        console: Rich console instance
        metrics: Current metrics dictionary
    """
    token_usage = metrics.get("token_usage_by_operation", {})

    if not token_usage:
        return

    table = Table(title="Token Usage by Operation")
    table.add_column("Operation", style="cyan")
    table.add_column("Tokens Used", justify="right", style="yellow")

    # Sort by usage
    sorted_ops = sorted(token_usage.items(), key=lambda x: x[1], reverse=True)

    for operation, tokens in sorted_ops:
        table.add_row(operation, f"{tokens:,}")

    console.print("\n")
    console.print(table)


def _display_agent_status(console: Console) -> None:
    """Display agent repository status.

    Args:
        console: Rich console instance
    """
    settings = Settings.from_env()
    JsonAgentRepository(settings.get_agent_storage_path())

    # Check if storage exists and has data
    storage_path = settings.get_agent_storage_path()
    exists = storage_path.exists()

    if exists:
        try:
            import json

            data = json.loads(storage_path.read_text())
            task_count = len(data)
        except Exception:
            task_count = 0
    else:
        task_count = 0

    info = f"Storage Path: {storage_path}\n"
    info += f"Storage Exists: {'Yes' if exists else 'No'}\n"
    info += f"Tasks Stored: {task_count}"

    console.print(Panel(info, title="Agent Storage", border_style="blue"))
