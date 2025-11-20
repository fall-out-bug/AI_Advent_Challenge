"""Integration tests for TestAgentCLI."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_result import TestResult, TestStatus
from src.presentation.cli.test_agent.main import create_orchestrator, main


@pytest.fixture
def cli_runner():
    """Create Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_code_file():
    """Create temporary code file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def add(a, b):\n    return a + b\n")
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink(missing_ok=True)


@pytest.fixture
def mock_orchestrator():
    """Create mock orchestrator."""
    orchestrator = AsyncMock()
    orchestrator.orchestrate_test_workflow = AsyncMock(
        return_value=TestResult(
            status=TestStatus.PASSED,
            test_count=5,
            passed_count=5,
            failed_count=0,
            coverage=85.5,
        )
    )
    return orchestrator


def test_cli_accepts_file_argument(cli_runner, sample_code_file):
    """Test CLI accepts file argument."""
    with patch(
        "src.presentation.cli.test_agent.main.create_orchestrator"
    ) as mock_create:
        mock_orch = AsyncMock()
        mock_orch.orchestrate_test_workflow = AsyncMock(
            return_value=TestResult(
                status=TestStatus.PASSED,
                test_count=5,
                passed_count=5,
                failed_count=0,
                coverage=85.5,
            )
        )
        mock_create.return_value = mock_orch

        result = cli_runner.invoke(
            main, [str(sample_code_file)], catch_exceptions=False
        )

        assert result.exit_code == 0
        mock_create.assert_called_once()


def test_cli_calls_orchestrator(cli_runner, sample_code_file):
    """Test CLI calls orchestrator."""
    with patch(
        "src.presentation.cli.test_agent.main.create_orchestrator"
    ) as mock_create:
        mock_orch = AsyncMock()
        mock_orch.orchestrate_test_workflow = AsyncMock(
            return_value=TestResult(
                status=TestStatus.PASSED,
                test_count=5,
                passed_count=5,
                failed_count=0,
                coverage=85.5,
            )
        )
        mock_create.return_value = mock_orch

        cli_runner.invoke(main, [str(sample_code_file)], catch_exceptions=False)

        mock_orch.orchestrate_test_workflow.assert_called_once()
        call_args = mock_orch.orchestrate_test_workflow.call_args[0][0]
        assert isinstance(call_args, CodeFile)
        assert call_args.path == str(sample_code_file)


def test_cli_outputs_results(cli_runner, sample_code_file):
    """Test CLI outputs results."""
    with patch(
        "src.presentation.cli.test_agent.main.create_orchestrator"
    ) as mock_create:
        mock_orch = AsyncMock()
        test_result = TestResult(
            status=TestStatus.PASSED,
            test_count=5,
            passed_count=5,
            failed_count=0,
            coverage=85.5,
        )
        mock_orch.orchestrate_test_workflow = AsyncMock(return_value=test_result)
        mock_create.return_value = mock_orch

        result = cli_runner.invoke(
            main, [str(sample_code_file)], catch_exceptions=False
        )

        assert result.exit_code == 0
        assert "PASSED" in result.output or "passed" in result.output.lower()
        assert "5" in result.output
        assert "85.5" in result.output or "85" in result.output


def test_cli_handles_errors(cli_runner, sample_code_file):
    """Test CLI handles errors."""
    with patch(
        "src.presentation.cli.test_agent.main.create_orchestrator"
    ) as mock_create:
        mock_orch = AsyncMock()
        mock_orch.orchestrate_test_workflow = AsyncMock(
            side_effect=Exception("Test error")
        )
        mock_create.return_value = mock_orch

        result = cli_runner.invoke(main, [str(sample_code_file)], catch_exceptions=True)

        assert result.exit_code != 0
        assert "error" in result.output.lower() or "Error" in result.output


def test_cli_handles_file_not_found(cli_runner):
    """Test CLI handles file not found error."""
    result = cli_runner.invoke(main, ["nonexistent.py"], catch_exceptions=True)

    # Click validates file existence before calling main, so exit code is 2
    assert result.exit_code != 0


def test_cli_outputs_errors_when_present(cli_runner, sample_code_file):
    """Test CLI outputs errors when test result has errors."""
    with patch(
        "src.presentation.cli.test_agent.main.create_orchestrator"
    ) as mock_create:
        mock_orch = AsyncMock()
        test_result = TestResult(
            status=TestStatus.FAILED,
            test_count=3,
            passed_count=1,
            failed_count=2,
            coverage=50.0,
            errors=["Test assertion failed", "Another error"],
        )
        mock_orch.orchestrate_test_workflow = AsyncMock(return_value=test_result)
        mock_create.return_value = mock_orch

        result = cli_runner.invoke(
            main, [str(sample_code_file)], catch_exceptions=False
        )

        assert result.exit_code == 1
        assert "Errors:" in result.output
        assert "Test assertion failed" in result.output


def test_cli_exits_with_error_on_failed_tests(cli_runner, sample_code_file):
    """Test CLI exits with error code when tests fail."""
    with patch(
        "src.presentation.cli.test_agent.main.create_orchestrator"
    ) as mock_create:
        mock_orch = AsyncMock()
        test_result = TestResult(
            status=TestStatus.FAILED,
            test_count=2,
            passed_count=0,
            failed_count=2,
            coverage=0.0,
        )
        mock_orch.orchestrate_test_workflow = AsyncMock(return_value=test_result)
        mock_create.return_value = mock_orch

        result = cli_runner.invoke(
            main, [str(sample_code_file)], catch_exceptions=False
        )

        assert result.exit_code == 1


def test_create_orchestrator():
    """Test create_orchestrator creates orchestrator with dependencies."""
    orchestrator = create_orchestrator()

    assert orchestrator is not None
    assert orchestrator.generate_tests_use_case is not None
    assert orchestrator.generate_code_use_case is not None
    assert orchestrator.execute_tests_use_case is not None


def test_cli_save_code_option(cli_runner, sample_code_file, tmp_path, monkeypatch):
    """Test CLI --save-code option saves generated code."""
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    # Change to tmp_path so workspace/ is created there
    monkeypatch.chdir(tmp_path)

    with patch(
        "src.presentation.cli.test_agent.main.create_orchestrator"
    ) as mock_create:
        mock_orch = AsyncMock()
        generated_code_file = CodeFile(
            path="generated_code_abc123.py",
            content="def calculate(a, b):\n    return a + b\n",
        )
        mock_orch.generated_code = generated_code_file
        mock_orch.generated_test_cases = []
        mock_orch.orchestrate_test_workflow = AsyncMock(
            return_value=TestResult(
                status=TestStatus.PASSED,
                test_count=5,
                passed_count=5,
                failed_count=0,
                coverage=85.5,
            )
        )
        mock_create.return_value = mock_orch

        result = cli_runner.invoke(
            main, [str(sample_code_file), "--save-code"], catch_exceptions=False
        )

        assert result.exit_code == 0
        saved_file = workspace_dir / "generated_code_abc123.py"
        assert saved_file.exists()
        assert saved_file.read_text() == "def calculate(a, b):\n    return a + b\n"


def test_cli_show_code_option(cli_runner, sample_code_file):
    """Test CLI --show-code option prints generated code."""
    with patch(
        "src.presentation.cli.test_agent.main.create_orchestrator"
    ) as mock_create:
        mock_orch = AsyncMock()
        generated_code_file = CodeFile(
            path="generated_code_abc123.py",
            content="def calculate(a, b):\n    return a + b\n",
        )
        mock_orch.generated_code = generated_code_file
        mock_orch.generated_test_cases = []
        mock_orch.orchestrate_test_workflow = AsyncMock(
            return_value=TestResult(
                status=TestStatus.PASSED,
                test_count=5,
                passed_count=5,
                failed_count=0,
                coverage=85.5,
            )
        )
        mock_create.return_value = mock_orch

        result = cli_runner.invoke(
            main, [str(sample_code_file), "--show-code"], catch_exceptions=False
        )

        assert result.exit_code == 0
        assert "def calculate(a, b):" in result.output
        assert "return a + b" in result.output


def test_cli_both_options(cli_runner, sample_code_file, tmp_path, monkeypatch):
    """Test CLI --save-code and --show-code work together."""
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    # Change to tmp_path so workspace/ is created there
    monkeypatch.chdir(tmp_path)

    with patch(
        "src.presentation.cli.test_agent.main.create_orchestrator"
    ) as mock_create:
        mock_orch = AsyncMock()
        generated_code_file = CodeFile(
            path="generated_code_abc123.py",
            content="def calculate(a, b):\n    return a + b\n",
        )
        mock_orch.generated_code = generated_code_file
        mock_orch.generated_test_cases = []
        mock_orch.orchestrate_test_workflow = AsyncMock(
            return_value=TestResult(
                status=TestStatus.PASSED,
                test_count=5,
                passed_count=5,
                failed_count=0,
                coverage=85.5,
            )
        )
        mock_create.return_value = mock_orch

        result = cli_runner.invoke(
            main,
            [str(sample_code_file), "--save-code", "--show-code"],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "def calculate(a, b):" in result.output
        saved_file = workspace_dir / "generated_code_abc123.py"
        assert saved_file.exists()


def test_cli_save_tests_option(cli_runner, sample_code_file, tmp_path, monkeypatch):
    """Test CLI --save-tests option saves generated tests."""
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    monkeypatch.chdir(tmp_path)

    with patch(
        "src.presentation.cli.test_agent.main.create_orchestrator"
    ) as mock_create:
        mock_orch = AsyncMock()
        from src.domain.test_agent.entities.test_case import TestCase

        test_cases = [
            TestCase(
                name="test_add",
                code="def test_add():\n    assert add(2, 3) == 5\n",
            ),
            TestCase(
                name="test_subtract",
                code="def test_subtract():\n    assert subtract(5, 3) == 2\n",
            ),
        ]
        mock_orch.generated_test_cases = test_cases
        mock_orch.generated_code = None
        mock_orch.orchestrate_test_workflow = AsyncMock(
            return_value=TestResult(
                status=TestStatus.PASSED,
                test_count=2,
                passed_count=2,
                failed_count=0,
                coverage=85.5,
            )
        )
        mock_create.return_value = mock_orch

        result = cli_runner.invoke(
            main, [str(sample_code_file), "--save-tests"], catch_exceptions=False
        )

        assert result.exit_code == 0
        # Find saved test file
        test_files = list(workspace_dir.glob("generated_tests_*.py"))
        assert len(test_files) == 1
        test_content = test_files[0].read_text()
        assert "def test_add():" in test_content
        assert "def test_subtract():" in test_content


def test_cli_show_tests_option(cli_runner, sample_code_file):
    """Test CLI --show-tests option prints generated tests."""
    with patch(
        "src.presentation.cli.test_agent.main.create_orchestrator"
    ) as mock_create:
        mock_orch = AsyncMock()
        from src.domain.test_agent.entities.test_case import TestCase

        test_cases = [
            TestCase(
                name="test_add",
                code="def test_add():\n    assert add(2, 3) == 5\n",
            ),
        ]
        mock_orch.generated_test_cases = test_cases
        mock_orch.generated_code = None
        mock_orch.orchestrate_test_workflow = AsyncMock(
            return_value=TestResult(
                status=TestStatus.PASSED,
                test_count=1,
                passed_count=1,
                failed_count=0,
                coverage=85.5,
            )
        )
        mock_create.return_value = mock_orch

        result = cli_runner.invoke(
            main, [str(sample_code_file), "--show-tests"], catch_exceptions=False
        )

        assert result.exit_code == 0
        assert "=== Generated Tests ===" in result.output
        assert "def test_add():" in result.output
        assert "assert add(2, 3) == 5" in result.output
