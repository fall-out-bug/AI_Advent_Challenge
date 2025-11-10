"""Health check command for system validation.

Following the Zen of Python:
- Simple is better than complex
- Errors should never pass silently
- Explicit is better than implicit
"""

from pathlib import Path
from typing import Dict

import httpx
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.infrastructure.config.settings import Settings


def check_health() -> int:
    """Run comprehensive health checks.

    Returns:
        Exit code (0 = healthy, 1 = unhealthy)
    """
    console = Console()
    console.print("\n[bold cyan]🔍 Running Health Checks[/bold cyan]\n")

    checks = [
        ("Configuration", _check_configuration),
        ("Storage", _check_storage),
        ("Model Endpoints", _check_model_endpoints),
        ("YAML Config", _check_yaml_config),
    ]

    results = []
    for name, check_func in checks:
        result = check_func()
        results.append((name, result))
        _display_check_result(console, name, result)

    # Summary
    healthy = all(result["healthy"] for _, result in results)

    if healthy:
        console.print("\n[bold green]✓ All systems healthy[/bold green]")
        return 0
    else:
        console.print("\n[bold red]✗ Some health checks failed[/bold red]")
        return 1


def _display_check_result(console: Console, name: str, result: Dict) -> None:
    """Display a single health check result.

    Args:
        console: Rich console instance
        name: Check name
        result: Check result dictionary
    """
    status = "✓" if result["healthy"] else "✗"
    color = "green" if result["healthy"] else "red"

    console.print(f"[{color}]{status}[/{color}] {name}")

    if not result["healthy"] and result.get("error"):
        console.print(f"  Error: {result['error']}", style="dim red")

    if result.get("details"):
        for detail in result["details"]:
            console.print(f"  • {detail}", style="dim")


def _check_configuration() -> Dict:
    """Check application configuration.

    Returns:
        Health check result
    """
    try:
        settings = Settings.from_env()

        # Validate required paths
        if not settings.storage_path:
            return {"healthy": False, "error": "Storage path not configured"}

        return {"healthy": True, "details": [f"Storage: {settings.storage_path}"]}
    except Exception as e:
        return {"healthy": False, "error": str(e)}


def _check_storage() -> Dict:
    """Check storage availability.

    Returns:
        Health check result
    """
    try:
        settings = Settings.from_env()
        storage_path = settings.get_agent_storage_path()

        # Check if directory exists or can be created
        storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if storage is readable/writable
        if storage_path.exists():
            try:
                # Read existing data to verify read access
                storage_path.read_text()

                # Test write access using a temporary file in the same directory
                temp_file = (
                    storage_path.parent / f".health_check_{storage_path.name}.tmp"
                )
                temp_file.write_text("{}")
                temp_file.unlink()  # Clean up immediately
            except Exception as e:
                return {"healthy": False, "error": f"Cannot access storage: {e}"}

        details = [f"Path: {storage_path}"]
        if storage_path.exists():
            details.append("Storage exists and is accessible")
        else:
            details.append("Storage will be created on first use")

        return {"healthy": True, "details": details}
    except Exception as e:
        return {"healthy": False, "error": str(e)}


def _check_model_endpoints() -> Dict:
    """Check model endpoints availability.

    Returns:
        Health check result
    """
    endpoints = [
        ("StarCoder", "http://localhost:8000"),
        ("Mistral", "http://localhost:8001"),
        ("Qwen", "http://localhost:8002"),
    ]

    results = []
    for name, url in endpoints:
        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.get(f"{url}/health")
                is_healthy = response.status_code == 200
                results.append(f"{name}: {'✓' if is_healthy else '✗'} {url}")
        except Exception:
            results.append(f"{name}: ✗ Not available")

    healthy = any("✓" in r for r in results)

    return {
        "healthy": healthy,
        "details": results,
        "error": None if healthy else "Some models are unavailable",
    }


def _check_yaml_config() -> Dict:
    """Check YAML configuration files.

    Returns:
        Health check result
    """
    config_files = [
        Path("config/models.yml"),
        Path("config/agent_configs.yaml"),
    ]

    results = []
    for config_file in config_files:
        if config_file.exists():
            try:
                with config_file.open() as f:
                    yaml.safe_load(f)
                results.append(f"✓ {config_file.name}")
            except Exception as e:
                results.append(f"✗ {config_file.name}: Invalid YAML")
                return {
                    "healthy": False,
                    "error": f"Invalid YAML in {config_file.name}: {e}",
                }
        else:
            results.append(f"✗ {config_file.name}: Not found")

    return {"healthy": True, "details": results}


def display_health_report() -> None:
    """Display detailed health report."""
    console = Console()

    metrics = Table(title="System Health Overview")
    metrics.add_column("Component", style="cyan")
    metrics.add_column("Status", justify="center")
    metrics.add_column("Details", style="dim")

    # Check configuration
    config_check = _check_configuration()
    metrics.add_row(
        "Configuration",
        "[green]✓[/green]" if config_check["healthy"] else "[red]✗[/red]",
        config_check.get("error", "OK"),
    )

    # Check storage
    storage_check = _check_storage()
    metrics.add_row(
        "Storage",
        "[green]✓[/green]" if storage_check["healthy"] else "[red]✗[/red]",
        storage_check.get("error", "OK"),
    )

    console.print(Panel(metrics, title="Health Report", border_style="cyan"))
