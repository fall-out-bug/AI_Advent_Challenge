"""Tests for main CLI interface."""

import sys
from datetime import datetime
from io import StringIO
from unittest.mock import AsyncMock, Mock, patch

import pytest

from communication.message_schema import (
    CodeGenerationResponse,
    CodeQualityMetrics,
    CodeReviewResponse,
    OrchestratorRequest,
    OrchestratorResponse,
    TaskMetadata,
)
from main import main
from orchestrator import process_simple_task


class TestMainCLI:
    """Test main CLI functionality."""

    def test_main_help(self):
        """Test help command."""
        with patch("sys.argv", ["main.py", "--help"]):
            with pytest.raises(SystemExit):
                main()

    def test_main_version(self):
        """Test version command."""
        with patch("sys.argv", ["main.py", "--version"]):
            with pytest.raises(SystemExit):
                main()

    @patch("main.process_simple_task")
    def test_main_simple_request(self, mock_process):
        """Test simple CLI request."""
        mock_process.return_value = "Test completed"

        with patch("sys.argv", ["main.py", "Create a fibonacci function"]):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                import asyncio

                asyncio.run(main())
                output = mock_stdout.getvalue()
                assert "Test completed" in output

    @patch("main.process_cli_request")
    def test_main_with_options(self, mock_process):
        """Test CLI request with options."""
        mock_process.return_value = "Test completed"

        with patch(
            "sys.argv",
            [
                "main.py",
                "Create a fibonacci function",
                "--language",
                "python",
                "--model",
                "starcoder",
                "--output",
                "output.json",
            ],
        ):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                main()
                output = mock_stdout.getvalue()
                assert "Test completed" in output

    @patch("main.process_cli_request")
    def test_main_error(self, mock_process):
        """Test CLI error handling."""
        mock_process.side_effect = Exception("Test error")

        with patch("sys.argv", ["main.py", "Create a fibonacci function"]):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with pytest.raises(SystemExit):
                    main()
                error_output = mock_stderr.getvalue()
                assert "Test error" in error_output


class TestProcessCLIRequest:
    """Test CLI request processing."""

    @patch("main.process_simple_task")
    def test_process_cli_request_success(self, mock_process):
        """Test successful CLI request processing."""
        # Mock response
        mock_response = OrchestratorResponse(
            task_description="Create a fibonacci function",
            generation_result=CodeGenerationResponse(
                task_description="Create a fibonacci function",
                generated_code="def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
                tests="def test_fibonacci(): assert fibonacci(5) == 5",
                metadata=TaskMetadata(
                    complexity="medium", lines_of_code=2, dependencies=[]
                ),
                generation_time=datetime.now(),
                tokens_used=100,
            ),
            review_result=CodeReviewResponse(
                code_quality_score=8.5,
                metrics=CodeQualityMetrics(
                    pep8_compliance=True,
                    pep8_score=9.0,
                    has_docstrings=False,
                    has_type_hints=False,
                    complexity_score=3.0,
                    test_coverage="medium",
                ),
                suggestions=["Add type hints"],
                recommendations=["Consider memoization"],
                review_time=datetime.now(),
                tokens_used=150,
            ),
            workflow_time=5.0,
            success=True,
        )
        mock_process.return_value = mock_response

        result = process_cli_request("Create a fibonacci function")

        assert "fibonacci" in result
        assert "Quality Score: 8.5" in result
        assert "Workflow completed successfully" in result

    @patch("main.process_simple_task")
    def test_process_cli_request_failure(self, mock_process):
        """Test failed CLI request processing."""
        # Mock failed response
        mock_response = OrchestratorResponse(
            task_description="Create a fibonacci function",
            generation_result=None,
            review_result=None,
            workflow_time=2.0,
            success=False,
            error_message="Agent unavailable",
        )
        mock_process.return_value = mock_response

        result = process_cli_request("Create a fibonacci function")

        assert "Error: Agent unavailable" in result
        assert "Workflow failed" in result

    @patch("main.process_simple_task")
    def test_process_cli_request_exception(self, mock_process):
        """Test CLI request with exception."""
        mock_process.side_effect = Exception("Connection error")

        result = process_cli_request("Create a fibonacci function")

        assert "Error: Connection error" in result

    def test_process_cli_request_empty_task(self):
        """Test CLI request with empty task."""
        result = process_cli_request("")

        assert "Error: Task description cannot be empty" in result

    def test_process_cli_request_long_task(self):
        """Test CLI request with very long task."""
        long_task = "x" * 10000
        result = process_cli_request(long_task)

        assert "Error: Task description too long" in result


class TestCLIArgumentParsing:
    """Test CLI argument parsing."""

    def test_parse_arguments_simple(self):
        """Test simple argument parsing."""
        from main import parse_arguments

        with patch("sys.argv", ["main.py", "Create a fibonacci function"]):
            args = parse_arguments()
            assert args.task == "Create a fibonacci function"
            assert args.language == "python"
            assert args.model == "starcoder"

    def test_parse_arguments_with_options(self):
        """Test argument parsing with options."""
        from main import parse_arguments

        with patch(
            "sys.argv",
            [
                "main.py",
                "Create a fibonacci function",
                "--language",
                "javascript",
                "--model",
                "mistral",
                "--output",
                "result.json",
            ],
        ):
            args = parse_arguments()
            assert args.task == "Create a fibonacci function"
            assert args.language == "javascript"
            assert args.model == "mistral"
            assert args.output == "result.json"

    def test_parse_arguments_invalid(self):
        """Test invalid argument parsing."""
        from main import parse_arguments

        with patch("sys.argv", ["main.py"]):  # No task provided
            with pytest.raises(SystemExit):
                parse_arguments()
