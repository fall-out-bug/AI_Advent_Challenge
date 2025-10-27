"""Tests for run_tests script."""

import subprocess
import sys
from io import StringIO
from unittest.mock import Mock, patch

import pytest
from run_tests import lint_code
from run_tests import main as run_tests_main
from run_tests import run_coverage, run_tests


class TestRunTestsScript:
    """Test run_tests script functionality."""

    @patch("run_tests.subprocess.run")
    def test_run_unit_tests_success(self, mock_run):
        """Test successful unit test execution."""
        mock_run.return_value = Mock(returncode=0, stdout="Tests passed")

        result = run_unit_tests()
        assert result is True
        mock_run.assert_called_once()

    @patch("run_tests.subprocess.run")
    def test_run_unit_tests_failure(self, mock_run):
        """Test failed unit test execution."""
        mock_run.return_value = Mock(returncode=1, stdout="Tests failed")

        result = run_unit_tests()
        assert result is False

    @patch("run_tests.subprocess.run")
    def test_run_integration_tests_success(self, mock_run):
        """Test successful integration test execution."""
        mock_run.return_value = Mock(returncode=0, stdout="Integration tests passed")

        result = run_integration_tests()
        assert result is True
        mock_run.assert_called_once()

    @patch("run_tests.subprocess.run")
    def test_run_integration_tests_failure(self, mock_run):
        """Test failed integration test execution."""
        mock_run.return_value = Mock(returncode=1, stdout="Integration tests failed")

        result = run_integration_tests()
        assert result is False

    @patch("run_tests.subprocess.run")
    def test_run_coverage_tests_success(self, mock_run):
        """Test successful coverage test execution."""
        mock_run.return_value = Mock(returncode=0, stdout="Coverage: 85%")

        result = run_coverage_tests()
        assert result is True
        mock_run.assert_called_once()

    @patch("run_tests.subprocess.run")
    def test_run_coverage_tests_failure(self, mock_run):
        """Test failed coverage test execution."""
        mock_run.return_value = Mock(returncode=1, stdout="Coverage: 45%")

        result = run_coverage_tests()
        assert result is False

    @patch("run_tests.run_unit_tests")
    @patch("run_tests.run_integration_tests")
    @patch("run_tests.run_coverage_tests")
    def test_main_all_success(self, mock_coverage, mock_integration, mock_unit):
        """Test main function with all tests passing."""
        mock_unit.return_value = True
        mock_integration.return_value = True
        mock_coverage.return_value = True

        with patch("sys.argv", ["run_tests.py"]):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                result = run_tests_main()
                output = mock_stdout.getvalue()

                assert result == 0
                assert "All tests passed!" in output

    @patch("run_tests.run_unit_tests")
    @patch("run_tests.run_integration_tests")
    @patch("run_tests.run_coverage_tests")
    def test_main_unit_failure(self, mock_coverage, mock_integration, mock_unit):
        """Test main function with unit test failure."""
        mock_unit.return_value = False
        mock_integration.return_value = True
        mock_coverage.return_value = True

        with patch("sys.argv", ["run_tests.py"]):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                result = run_tests_main()
                output = mock_stdout.getvalue()

                assert result == 1
                assert "Unit tests failed!" in output

    @patch("run_tests.run_unit_tests")
    @patch("run_tests.run_integration_tests")
    @patch("run_tests.run_coverage_tests")
    def test_main_integration_failure(self, mock_coverage, mock_integration, mock_unit):
        """Test main function with integration test failure."""
        mock_unit.return_value = True
        mock_integration.return_value = False
        mock_coverage.return_value = True

        with patch("sys.argv", ["run_tests.py"]):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                result = run_tests_main()
                output = mock_stdout.getvalue()

                assert result == 1
                assert "Integration tests failed!" in output

    @patch("run_tests.run_unit_tests")
    @patch("run_tests.run_integration_tests")
    @patch("run_tests.run_coverage_tests")
    def test_main_coverage_failure(self, mock_coverage, mock_integration, mock_unit):
        """Test main function with coverage test failure."""
        mock_unit.return_value = True
        mock_integration.return_value = True
        mock_coverage.return_value = False

        with patch("sys.argv", ["run_tests.py"]):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                result = run_tests_main()
                output = mock_stdout.getvalue()

                assert result == 1
                assert "Coverage tests failed!" in output

    def test_main_with_help(self):
        """Test main function with help argument."""
        with patch("sys.argv", ["run_tests.py", "--help"]):
            with pytest.raises(SystemExit):
                run_tests_main()

    def test_main_with_unit_only(self):
        """Test main function with unit tests only."""
        with patch("run_tests.run_unit_tests") as mock_unit:
            mock_unit.return_value = True

            with patch("sys.argv", ["run_tests.py", "--unit-only"]):
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    result = run_tests_main()
                    output = mock_stdout.getvalue()

                    assert result == 0
                    assert "Unit tests passed!" in output
                    mock_unit.assert_called_once()

    def test_main_with_integration_only(self):
        """Test main function with integration tests only."""
        with patch("run_tests.run_integration_tests") as mock_integration:
            mock_integration.return_value = True

            with patch("sys.argv", ["run_tests.py", "--integration-only"]):
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    result = run_tests_main()
                    output = mock_stdout.getvalue()

                    assert result == 0
                    assert "Integration tests passed!" in output
                    mock_integration.assert_called_once()

    def test_main_with_coverage_only(self):
        """Test main function with coverage tests only."""
        with patch("run_tests.run_coverage_tests") as mock_coverage:
            mock_coverage.return_value = True

            with patch("sys.argv", ["run_tests.py", "--coverage-only"]):
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    result = run_tests_main()
                    output = mock_stdout.getvalue()

                    assert result == 0
                    assert "Coverage tests passed!" in output
                    mock_coverage.assert_called_once()

    @patch("run_tests.subprocess.run")
    def test_subprocess_error_handling(self, mock_run):
        """Test subprocess error handling."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "pytest")

        result = run_unit_tests()
        assert result is False

    def test_parse_arguments(self):
        """Test argument parsing."""
        from run_tests import parse_arguments

        with patch("sys.argv", ["run_tests.py", "--unit-only", "--verbose"]):
            args = parse_arguments()
            assert args.unit_only is True
            assert args.verbose is True
            assert args.integration_only is False
            assert args.coverage_only is False
