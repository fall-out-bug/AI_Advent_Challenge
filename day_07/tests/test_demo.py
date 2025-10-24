"""Tests for demo script."""

from datetime import datetime
from io import StringIO
from unittest.mock import patch

from examples.demos.demo import demo_simple_task
from examples.demos.demo import main as demo_main

from communication.message_schema import (
    CodeGenerationResponse,
    CodeQualityMetrics,
    CodeReviewResponse,
    OrchestratorResponse,
    TaskMetadata,
)


class TestDemoScript:
    """Test demo script functionality."""

    @patch("examples.demos.demo.process_simple_task")
    async def test_demo_simple_task_success(self, mock_process):
        """Test successful simple task demo."""
        # Mock successful response
        mock_response = OrchestratorResponse(
            task_description="Create a fibonacci function",
            generation_result=CodeGenerationResponse(
                task_description="Create a fibonacci function",
                generated_code=(
                    "def fibonacci(n): return n if n <= 1 else "
                    "fibonacci(n-1) + fibonacci(n-2)"
                ),
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
                issues=["Add type hints"],
                recommendations=["Consider memoization"],
                review_time=datetime.now(),
                tokens_used=150,
            ),
            workflow_time=5.0,
            success=True,
        )
        mock_process.return_value = mock_response

        with patch("examples.demos.demo.wait_for_services", return_value=True):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                await demo_simple_task()
                output = mock_stdout.getvalue()

                assert "Demo: Simple Task Processing" in output
                assert "Task completed successfully!" in output
                assert "Code quality score: 8.5/10" in output

    @patch("examples.demos.demo.process_simple_task")
    async def test_demo_simple_task_failure(self, mock_process):
        """Test simple task demo with failure."""
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

        with patch("examples.demos.demo.wait_for_services", return_value=True):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                await demo_simple_task()
                output = mock_stdout.getvalue()

                assert "Demo: Simple Task Processing" in output
                assert "Task failed: Agent unavailable" in output

    @patch("examples.demos.demo.process_simple_task")
    async def test_demo_simple_task_exception(self, mock_process):
        """Test simple task demo with exception."""
        mock_process.side_effect = Exception("Connection error")

        with patch("examples.demos.demo.wait_for_services", return_value=True):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                await demo_simple_task()
                output = mock_stdout.getvalue()

                assert "Demo: Simple Task Processing" in output
                assert "Demo failed: Connection error" in output

    def test_demo_main_function(self):
        """Test demo main function."""
        with patch("examples.demos.demo.demo_simple_task") as mock_simple:
            with patch("examples.demos.demo.demo_multiple_tasks") as mock_multiple:
                with patch("examples.demos.demo.demo_agent_status") as mock_status:
                    with patch("sys.argv", ["demo.py"]):
                        import asyncio
                        asyncio.run(demo_main())
                        mock_simple.assert_called_once()
                        mock_multiple.assert_called_once()
                        mock_status.assert_called_once()

    def test_demo_main_with_args(self):
        """Test demo main function with arguments."""
        with patch("examples.demos.demo.demo_simple_task") as mock_simple:
            with patch("examples.demos.demo.demo_multiple_tasks") as mock_multiple:
                with patch("examples.demos.demo.demo_agent_status") as mock_status:
                    with patch("sys.argv", ["demo.py", "--help"]):
                        # The main function doesn't handle --help, so it will run normally
                        import asyncio
                        asyncio.run(demo_main())
                        mock_simple.assert_called_once()
                        mock_multiple.assert_called_once()
                        mock_status.assert_called_once()
