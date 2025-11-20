"""Test agent CLI entry point."""

import asyncio
import sys
from pathlib import Path

import click

from src.application.test_agent.orchestrators.test_agent_orchestrator import (
    TestAgentOrchestrator,
)
from src.application.test_agent.use_cases.execute_tests_use_case import (
    ExecuteTestsUseCase,
)
from src.application.test_agent.use_cases.generate_code_use_case import (
    GenerateCodeUseCase,
)
from src.application.test_agent.use_cases.generate_tests_use_case import (
    GenerateTestsUseCase,
)
from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_result import TestStatus
from src.infrastructure.clients.llm_client import ResilientLLMClient, get_llm_client
from src.infrastructure.test_agent.adapters.pytest_executor import TestExecutor
from src.infrastructure.test_agent.reporting.test_result_reporter import (
    TestResultReporter,
)
from src.infrastructure.test_agent.services.llm_service import TestAgentLLMService


def create_orchestrator() -> TestAgentOrchestrator:
    """Create TestAgentOrchestrator with all dependencies.

    Purpose:
        Initialize all infrastructure and application components
        required for TestAgentOrchestrator to function.

    Returns:
        Fully configured TestAgentOrchestrator instance.
    """
    # Use longer timeout for test and code generation
    # LLM service has OLLAMA_REQUEST_TIMEOUT_SECONDS=600, but code generation can take longer
    # Test generation with long prompts can take 3-5 minutes
    # Code generation with complex types can take 5-10 minutes
    # Use ResilientLLMClient for automatic fallback on errors
    primary_client = get_llm_client(
        timeout=900.0
    )  # 15 minutes for complex code generation
    llm_client = ResilientLLMClient(primary_client)
    llm_service = TestAgentLLMService(llm_client=llm_client)
    test_executor = TestExecutor()
    test_reporter = TestResultReporter()

    generate_tests_use_case = GenerateTestsUseCase(
        llm_service=llm_service, llm_client=llm_client
    )
    generate_code_use_case = GenerateCodeUseCase(
        llm_service=llm_service, llm_client=llm_client
    )
    execute_tests_use_case = ExecuteTestsUseCase(test_executor=test_executor)

    return TestAgentOrchestrator(
        generate_tests_use_case=generate_tests_use_case,
        generate_code_use_case=generate_code_use_case,
        execute_tests_use_case=execute_tests_use_case,
    )


def format_result(result) -> str:
    """Format test result for CLI output.

    Args:
        result: TestResult domain entity.

    Returns:
        Formatted string for display.
    """
    status_emoji = {
        TestStatus.PASSED: "✓",
        TestStatus.FAILED: "✗",
        TestStatus.ERROR: "⚠",
    }
    emoji = status_emoji.get(result.status, "?")

    output = [
        f"{emoji} Test Status: {result.status.value.upper()}",
        f"Tests: {result.test_count} total, {result.passed_count} passed, {result.failed_count} failed",
        f"Coverage: {result.coverage:.1f}%",
    ]

    if result.errors:
        output.append("\nErrors:")
        for error in result.errors[:5]:
            output.append(f"  - {error}")

    return "\n".join(output)


@click.command()
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--save-code",
    is_flag=True,
    default=False,
    help="Save generated code to workspace/ directory",
)
@click.option(
    "--show-code",
    is_flag=True,
    default=False,
    help="Print generated code to console",
)
@click.option(
    "--save-tests",
    is_flag=True,
    default=False,
    help="Save generated tests to workspace/ directory",
)
@click.option(
    "--show-tests",
    is_flag=True,
    default=False,
    help="Print generated tests to console",
)
def main(
    file_path: Path,
    save_code: bool,
    show_code: bool,
    save_tests: bool,
    show_tests: bool,
) -> None:
    """Test Agent CLI - Generate and execute tests for Python code.

    Purpose:
        CLI entry point for test agent workflow.

    Args:
        file_path: Path to Python code file to process.

    Example:
        $ python -m src.presentation.cli.test_agent.main test.py
    """
    try:
        code_content = file_path.read_text()
        code_file = CodeFile(path=str(file_path), content=code_content)

        orchestrator = create_orchestrator()

        result = asyncio.run(orchestrator.orchestrate_test_workflow(code_file))

        workspace_dir = Path("workspace")
        workspace_dir.mkdir(exist_ok=True)

        # Handle test viewing/saving options
        if orchestrator.generated_test_cases:
            tests_content = "\n\n".join(
                tc.code for tc in orchestrator.generated_test_cases
            )

            if show_tests:
                click.echo("\n=== Generated Tests ===")
                click.echo(tests_content)
                click.echo("=" * 50)

            if save_tests:
                import uuid

                unique_id = uuid.uuid4().hex[:8]
                test_file_path = workspace_dir / f"generated_tests_{unique_id}.py"
                test_file_path.write_text(tests_content)
                click.echo(f"\n✓ Generated tests saved to: {test_file_path}")

        # Handle code viewing/saving options
        if orchestrator.generated_code:
            if show_code:
                click.echo("\n=== Generated Code ===")
                click.echo(orchestrator.generated_code.content)
                click.echo("=" * 50)

            if save_code:
                saved_path = workspace_dir / orchestrator.generated_code.path
                saved_path.write_text(orchestrator.generated_code.content)
                click.echo(f"\n✓ Generated code saved to: {saved_path}")

        # Debug: print full errors if in debug mode
        import os

        if os.getenv("TEST_AGENT_VERBOSE") and result.errors:
            click.echo("\n=== Full Error Details ===", err=True)
            for i, error in enumerate(result.errors, 1):
                click.echo(f"\nError {i}:", err=True)
                click.echo(error, err=True)

        click.echo(format_result(result))

        if result.status != TestStatus.PASSED:
            sys.exit(1)
    except FileNotFoundError:
        click.echo(f"Error: File not found: {file_path}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
