"""Tests for demo script."""

import pytest
from unittest.mock import patch, Mock, AsyncMock
import sys
from io import StringIO

from demo import main as demo_main, demo_simple_task
from orchestrator import process_simple_task
from communication.message_schema import (
    OrchestratorResponse,
    CodeGenerationResponse,
    CodeReviewResponse,
    TaskMetadata,
    CodeQualityMetrics,
)
from datetime import datetime


class TestDemoScript:
    """Test demo script functionality."""

    @patch("demo.process_simple_task")
    def test_run_demo_examples_success(self, mock_process):
        """Test successful demo examples."""
        # Mock successful response
        mock_response = OrchestratorResponse(
            task_description="Create a fibonacci function",
            generation_result=CodeGenerationResponse(
                task_description="Create a fibonacci function",
                generated_code="def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
                tests="def test_fibonacci(): assert fibonacci(5) == 5",
                metadata=TaskMetadata(
                    complexity="medium",
                    lines_of_code=2,
                    dependencies=[]
                ),
                generation_time=datetime.now(),
                tokens_used=100
            ),
            review_result=CodeReviewResponse(
                code_quality_score=8.5,
                metrics=CodeQualityMetrics(
                    pep8_compliance=True,
                    pep8_score=9.0,
                    has_docstrings=False,
                    has_type_hints=False,
                    complexity_score=3.0,
                    test_coverage="medium"
                ),
                suggestions=["Add type hints"],
                recommendations=["Consider memoization"],
                review_time=datetime.now(),
                tokens_used=150
            ),
            workflow_time=5.0,
            success=True
        )
        mock_process.return_value = mock_response

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_demo_examples()
            output = mock_stdout.getvalue()
            
            assert "Demo Examples" in output
            assert "fibonacci" in output
            assert "Quality Score: 8.5" in output

    @patch("demo.process_simple_task")
    def test_run_demo_examples_failure(self, mock_process):
        """Test demo examples with failures."""
        # Mock failed response
        mock_response = OrchestratorResponse(
            task_description="Create a fibonacci function",
            generation_result=None,
            review_result=None,
            workflow_time=2.0,
            success=False,
            error_message="Agent unavailable"
        )
        mock_process.return_value = mock_response

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_demo_examples()
            output = mock_stdout.getvalue()
            
            assert "Demo Examples" in output
            assert "Error: Agent unavailable" in output

    @patch("demo.process_simple_task")
    def test_run_demo_examples_exception(self, mock_process):
        """Test demo examples with exception."""
        mock_process.side_effect = Exception("Connection error")

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_demo_examples()
            output = mock_stdout.getvalue()
            
            assert "Demo Examples" in output
            assert "Error: Connection error" in output

    def test_demo_main_function(self):
        """Test demo main function."""
        with patch("demo.run_demo_examples") as mock_run:
            with patch("sys.argv", ["demo.py"]):
                demo_main()
                mock_run.assert_called_once()

    def test_demo_main_with_args(self):
        """Test demo main function with arguments."""
        with patch("demo.run_demo_examples") as mock_run:
            with patch("sys.argv", ["demo.py", "--help"]):
                with pytest.raises(SystemExit):
                    demo_main()

    @patch("demo.process_simple_task")
    def test_demo_example_fibonacci(self, mock_process):
        """Test fibonacci demo example."""
        mock_response = OrchestratorResponse(
            task_description="Create a fibonacci function",
            generation_result=CodeGenerationResponse(
                task_description="Create a fibonacci function",
                generated_code="def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
                tests="def test_fibonacci(): assert fibonacci(5) == 5",
                metadata=TaskMetadata(
                    complexity="medium",
                    lines_of_code=2,
                    dependencies=[]
                ),
                generation_time=datetime.now(),
                tokens_used=100
            ),
            review_result=CodeReviewResponse(
                code_quality_score=8.5,
                metrics=CodeQualityMetrics(
                    pep8_compliance=True,
                    pep8_score=9.0,
                    has_docstrings=False,
                    has_type_hints=False,
                    complexity_score=3.0,
                    test_coverage="medium"
                ),
                suggestions=["Add type hints"],
                recommendations=["Consider memoization"],
                review_time=datetime.now(),
                tokens_used=150
            ),
            workflow_time=5.0,
            success=True
        )
        mock_process.return_value = mock_response

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_demo_examples()
            output = mock_stdout.getvalue()
            
            assert "Example 1: Fibonacci Function" in output
            assert "def fibonacci(n)" in output

    @patch("demo.process_simple_task")
    def test_demo_example_data_processor(self, mock_process):
        """Test data processor demo example."""
        mock_response = OrchestratorResponse(
            task_description="Create a data processor",
            generation_result=CodeGenerationResponse(
                task_description="Create a data processor",
                generated_code="class DataProcessor: pass",
                tests="def test_data_processor(): pass",
                metadata=TaskMetadata(
                    complexity="high",
                    lines_of_code=10,
                    dependencies=["pandas", "numpy"]
                ),
                generation_time=datetime.now(),
                tokens_used=200
            ),
            review_result=CodeReviewResponse(
                code_quality_score=7.5,
                metrics=CodeQualityMetrics(
                    pep8_compliance=True,
                    pep8_score=8.0,
                    has_docstrings=True,
                    has_type_hints=True,
                    complexity_score=5.0,
                    test_coverage="high"
                ),
                suggestions=["Add error handling"],
                recommendations=["Consider using async"],
                review_time=datetime.now(),
                tokens_used=180
            ),
            workflow_time=8.0,
            success=True
        )
        mock_process.return_value = mock_response

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_demo_examples()
            output = mock_stdout.getvalue()
            
            assert "Example 2: Data Processor" in output
            assert "class DataProcessor" in output
            assert "Quality Score: 7.5" in output
