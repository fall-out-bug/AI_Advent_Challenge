"""CLI interface for the application."""

import sys
from typing import Optional

from src.infrastructure.config.settings import Settings


def print_usage() -> None:
    """Print CLI usage instructions."""
    print(
        """
AI Challenge CLI

Usage:
  python -m src.presentation.cli.main_cli <command> [options]

Commands:
  generate    Generate code from prompt
  review      Review code quality
  status      Display system status and metrics
  health      Check system health
  metrics     View and export metrics
  config      Display and validate configuration

Examples:
  python -m src.presentation.cli.main_cli generate "Create a fibonacci function"
  python -m src.presentation.cli.main_cli review --file code.py
  python -m src.presentation.cli.main_cli status
  python -m src.presentation.cli.main_cli health
  python -m src.presentation.cli.main_cli metrics
  python -m src.presentation.cli.main_cli config
    """
    )


async def handle_generate(prompt: str, agent_name: Optional[str] = None) -> None:
    """
    Handle generate command.

    Args:
        prompt: Generation prompt
        agent_name: Optional agent name
    """
    from src.application.use_cases.generate_code import GenerateCodeUseCase
    from src.infrastructure.repositories.json_agent_repository import (
        JsonAgentRepository,
    )
    from src.infrastructure.repositories.model_repository import (
        InMemoryModelRepository,
    )
    from src.infrastructure.clients.simple_model_client import SimpleModelClient

    settings = Settings.from_env()
    agent_repo = JsonAgentRepository(settings.get_agent_storage_path())
    model_repo = InMemoryModelRepository()
    model_client = SimpleModelClient()

    use_case = GenerateCodeUseCase(
        agent_repository=agent_repo,
        model_repository=model_repo,
        model_client=model_client,
    )

    task = await use_case.execute(
        prompt=prompt,
        agent_name=agent_name or "CLI",
    )

    print(f"\n✅ Task completed: {task.task_id}")
    print(f"Status: {task.status.value}")
    if task.response:
        print(f"\nGenerated code:\n{task.response}")
    if task.quality_metrics:
        print(f"\nQuality score: {task.quality_metrics.overall_score}")


async def handle_review(code: str) -> None:
    """
    Handle review command.

    Args:
        code: Code to review
    """
    from src.application.use_cases.review_code import ReviewCodeUseCase
    from src.infrastructure.repositories.json_agent_repository import (
        JsonAgentRepository,
    )
    from src.infrastructure.repositories.model_repository import (
        InMemoryModelRepository,
    )
    from src.infrastructure.clients.simple_model_client import SimpleModelClient

    settings = Settings.from_env()
    agent_repo = JsonAgentRepository(settings.get_agent_storage_path())
    model_repo = InMemoryModelRepository()
    model_client = SimpleModelClient()

    use_case = ReviewCodeUseCase(
        agent_repository=agent_repo,
        model_repository=model_repo,
        model_client=model_client,
    )

    task = await use_case.execute(code=code, agent_name="CLI")

    print(f"\n✅ Review completed: {task.task_id}")
    print(f"Status: {task.status.value}")
    if task.response:
        print(f"\nReview feedback:\n{task.response}")
    if task.quality_metrics:
        print(f"\nQuality metrics: {task.quality_metrics.scores}")


def handle_health() -> None:
    """Handle health check command."""
    from src.presentation.cli.commands.health_cmd import check_health

    exit_code = check_health()
    sys.exit(exit_code)


def handle_status() -> None:
    """Handle status command."""
    from src.presentation.cli.commands.status_cmd import display_status

    display_status()


async def main() -> None:
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    if command == "generate":
        if len(sys.argv) < 3:
            print("Error: Prompt required for generate command")
            sys.exit(1)
        import asyncio

        asyncio.run(handle_generate(" ".join(sys.argv[2:])))

    elif command == "review":
        if len(sys.argv) < 3:
            print("Error: Code or file required for review command")
            sys.exit(1)
        import asyncio

        code = " ".join(sys.argv[2:])
        asyncio.run(handle_review(code))

    elif command == "health":
        handle_health()

    elif command == "status":
        handle_status()

    elif command == "metrics":
        from src.presentation.cli.commands.metrics_cmd import display_metrics_summary

        if len(sys.argv) >= 3:
            sub_command = sys.argv[2]

            if sub_command == "export" and len(sys.argv) >= 5:
                format_type = sys.argv[3]
                output_file = sys.argv[4]

                if format_type == "json":
                    from src.presentation.cli.commands.metrics_cmd import (
                        export_metrics_json,
                    )

                    export_metrics_json(output_file)
                elif format_type == "csv":
                    from src.presentation.cli.commands.metrics_cmd import (
                        export_metrics_csv,
                    )

                    export_metrics_csv(output_file)
                else:
                    print(f"Unknown format: {format_type}. Use 'json' or 'csv'")
                    sys.exit(1)
            elif sub_command == "reset":
                from src.presentation.cli.commands.metrics_cmd import reset_metrics

                reset_metrics()
            else:
                display_metrics_summary()
        else:
            display_metrics_summary()

    elif command == "config":
        from src.presentation.cli.commands.config_cmd import (
            display_configuration,
            validate_configuration,
            list_experiments,
        )

        if len(sys.argv) >= 3:
            sub_command = sys.argv[2]

            if sub_command == "validate":
                valid = validate_configuration()
                sys.exit(0 if valid else 1)
            elif sub_command == "experiments":
                list_experiments()
            else:
                display_configuration()
        else:
            display_configuration()

    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
