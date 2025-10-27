"""Config command for displaying and validating configuration.

Following the Zen of Python:
- Simple is better than complex
- Explicit is better than implicit
- Readability counts
"""

import yaml
from pathlib import Path
from typing import Dict

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from src.infrastructure.config.settings import Settings


def display_configuration() -> None:
    """Display current configuration."""
    console = Console()

    settings = Settings.from_env()

    # Display application settings
    config_table = Table(title="Application Configuration", show_header=True)
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")

    config_table.add_row("Storage Path", str(settings.storage_path))
    config_table.add_row("Default Model", settings.model_default_name)
    config_table.add_row("Default Max Tokens", str(settings.model_default_max_tokens))
    config_table.add_row("Default Temperature", str(settings.model_default_temperature))

    console.print(Panel(config_table, title="Settings", border_style="cyan"))

    # Display model configurations
    _display_model_configs(console)

    # Display agent configurations
    _display_agent_configs(console)


def validate_configuration() -> bool:
    """Validate configuration files.

    Returns:
        True if configuration is valid
    """
    console = Console()
    console.print("\n[bold cyan]Validating Configuration...[/bold cyan]\n")

    config_files = [
        Path("config/models.yml"),
        Path("config/agent_configs.yaml"),
    ]

    all_valid = True

    for config_file in config_files:
        if not config_file.exists():
            console.print(f"[red]✗[/red] {config_file.name} not found")
            all_valid = False
            continue

        try:
            with config_file.open() as f:
                yaml.safe_load(f)
            console.print(f"[green]✓[/green] {config_file.name} is valid")
        except yaml.YAMLError as e:
            console.print(f"[red]✗[/red] {config_file.name} has YAML errors: {e}")
            all_valid = False
        except Exception as e:
            console.print(f"[red]✗[/red] {config_file.name} error: {e}")
            all_valid = False

    if all_valid:
        console.print("\n[green]✓ All configuration files are valid[/green]")
    else:
        console.print("\n[red]✗ Some configuration files are invalid[/red]")

    return all_valid


def list_experiments() -> None:
    """List available experiment templates."""
    console = Console()

    exp_dir = Path("config/experiment_templates")

    if not exp_dir.exists():
        console.print("[dim]No experiment templates found[/dim]")
        return

    templates = list(exp_dir.glob("*.yaml")) + list(exp_dir.glob("*.yml"))

    if not templates:
        console.print("[dim]No experiment templates available[/dim]")
        return

    table = Table(title="Available Experiments")
    table.add_column("Template", style="cyan")
    table.add_column("Path", style="dim")

    for template in sorted(templates):
        table.add_row(template.stem, str(template))

    console.print(table)


def _display_model_configs(console: Console) -> None:
    """Display model configurations.

    Args:
        console: Rich console instance
    """
    models_file = Path("config/models.yml")

    if not models_file.exists():
        return

    try:
        with models_file.open() as f:
            config = yaml.safe_load(f)

        models = config.get("models", {})
        available = models.get("available", {})

        table = Table(title="Available Models")
        table.add_column("Model ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Description", style="dim")

        for model_id, model_info in available.items():
            table.add_row(
                model_id,
                model_info.get("name", "Unknown"),
                model_info.get("description", ""),
            )

        console.print("\n")
        console.print(table)
    except Exception as e:
        console.print(f"[dim]Could not load model configs: {e}[/dim]")


def _display_agent_configs(console: Console) -> None:
    """Display agent configurations.

    Args:
        console: Rich console instance
    """
    agents_file = Path("config/agent_configs.yaml")

    if not agents_file.exists():
        return

    try:
        with agents_file.open() as f:
            config = yaml.safe_load(f)

        agents = config.get("agents", {})

        table = Table(title="Available Agents")
        table.add_column("Agent ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Status", justify="center")

        for agent_id, agent_info in agents.items():
            enabled = agent_info.get("enabled", False)
            status = "[green]✓[/green]" if enabled else "[red]✗[/red]"

            table.add_row(agent_id, agent_info.get("name", "Unknown"), status)

        console.print("\n")
        console.print(table)
    except Exception as e:
        console.print(f"[dim]Could not load agent configs: {e}[/dim]")
