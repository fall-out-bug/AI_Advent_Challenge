"""Integration tests for verify_test_agent script."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.verify_test_agent import (
    SampleResult,
    VerificationReport,
    generate_report,
    parse_test_result,
    process_sample,
)

PROJECT_ROOT = Path(__file__).parent.parent


def test_parse_test_result_passed():
    """Test parsing passed test result."""
    stdout = """✓ Test Status: PASSED
Tests: 5 total, 5 passed, 0 failed
Coverage: 85.5%"""
    result = parse_test_result(stdout, "", 0)

    assert result.status == "passed"
    assert result.test_count == 5
    assert result.passed_count == 5
    assert result.failed_count == 0
    assert result.coverage == 85.5
    assert result.verification_passed is True


def test_parse_test_result_failed():
    """Test parsing failed test result."""
    stdout = """✗ Test Status: FAILED
Tests: 3 total, 1 passed, 2 failed
Coverage: 50.0%

Errors:
  - Test assertion failed
  - Another error"""
    result = parse_test_result(stdout, "", 1)

    assert result.status == "failed"
    assert result.test_count == 3
    assert result.passed_count == 1
    assert result.failed_count == 2
    assert result.coverage == 50.0
    assert len(result.errors) == 2
    assert result.verification_passed is False


def test_parse_test_result_low_coverage():
    """Test parsing result with low coverage."""
    stdout = """✓ Test Status: PASSED
Tests: 2 total, 2 passed, 0 failed
Coverage: 75.0%"""
    result = parse_test_result(stdout, "", 0)

    assert result.status == "passed"
    assert result.coverage == 75.0
    assert result.verification_passed is False  # Coverage < 80%


def test_parse_test_result_with_errors():
    """Test parsing result with errors."""
    stdout = """⚠ Test Status: ERROR
Tests: 0 total, 0 passed, 0 failed
Coverage: 0.0%

Errors:
  - LLM generation failed"""
    stderr = "Additional error message"
    result = parse_test_result(stdout, stderr, 1)

    assert result.status == "error"
    assert len(result.errors) >= 1
    assert "LLM generation failed" in result.errors[0]
    assert result.verification_passed is False


def test_generate_report():
    """Test report generation."""
    results = [
        SampleResult(
            file_name="test1.py",
            file_path="test1.py",
            status="passed",
            test_count=5,
            passed_count=5,
            failed_count=0,
            coverage=85.0,
            errors=[],
            verification_passed=True,
        ),
        SampleResult(
            file_name="test2.py",
            file_path="test2.py",
            status="passed",
            test_count=3,
            passed_count=3,
            failed_count=0,
            coverage=90.0,
            errors=[],
            verification_passed=True,
        ),
    ]

    report = generate_report(results)

    assert report.total_samples == 2
    assert report.passed_samples == 2
    assert report.failed_samples == 0
    assert report.overall_status == "PASS"
    assert len(report.results) == 2


def test_generate_report_with_failures():
    """Test report generation with failures."""
    results = [
        SampleResult(
            file_name="test1.py",
            file_path="test1.py",
            status="passed",
            test_count=5,
            passed_count=5,
            failed_count=0,
            coverage=85.0,
            errors=[],
            verification_passed=True,
        ),
        SampleResult(
            file_name="test2.py",
            file_path="test2.py",
            status="failed",
            test_count=3,
            passed_count=1,
            failed_count=2,
            coverage=50.0,
            errors=["Error 1"],
            verification_passed=False,
        ),
    ]

    report = generate_report(results)

    assert report.total_samples == 2
    assert report.passed_samples == 1
    assert report.failed_samples == 1
    assert report.overall_status == "FAIL"


@patch("scripts.verify_test_agent.run_test_agent")
def test_process_sample_success(mock_run):
    """Test processing sample with success."""
    mock_run.return_value = (
        """✓ Test Status: PASSED
Tests: 5 total, 5 passed, 0 failed
Coverage: 85.5%""",
        "",
        0,
    )

    file_path = Path("test.py")
    result = process_sample(file_path)

    assert result.file_name == "test.py"
    assert result.status == "passed"
    assert result.coverage == 85.5
    assert result.verification_passed is True


@patch("scripts.verify_test_agent.run_test_agent")
def test_process_sample_timeout(mock_run):
    """Test processing sample with timeout."""
    mock_run.side_effect = subprocess.TimeoutExpired("cmd", 300)

    file_path = Path("test.py")
    result = process_sample(file_path)

    assert result.status == "error"
    assert result.coverage == 0.0
    assert result.verification_passed is False
    assert "timeout" in result.errors[0].lower()


@patch("scripts.verify_test_agent.run_test_agent")
def test_process_sample_exception(mock_run):
    """Test processing sample with exception."""
    mock_run.side_effect = Exception("Test error")

    file_path = Path("test.py")
    result = process_sample(file_path)

    assert result.status == "error"
    assert result.verification_passed is False
    assert "Test error" in result.errors[0]


def test_parse_coverage_various_formats():
    """Test parsing coverage in various formats."""
    test_cases = [
        ("Coverage: 85.5%", 85.5),
        ("Coverage: 100.0%", 100.0),
        ("Coverage: 0.0%", 0.0),
        ("Coverage: 80%", 80.0),
    ]

    for stdout, expected_coverage in test_cases:
        result = parse_test_result(stdout, "", 0)
        assert result.coverage == expected_coverage, f"Failed for: {stdout}"


def test_parse_test_counts_various_formats():
    """Test parsing test counts in various formats."""
    stdout = """Tests: 10 total, 8 passed, 2 failed"""
    result = parse_test_result(stdout, "", 0)

    assert result.test_count == 10
    assert result.passed_count == 8
    assert result.failed_count == 2


@patch("scripts.verify_test_agent.SAMPLES_DIR")
def test_main_success(mock_samples_dir, tmp_path):
    """Test main function with successful execution."""
    # Create sample files
    sample1 = tmp_path / "01_test.py"
    sample1.write_text("def test(): pass")
    sample2 = tmp_path / "02_test.py"
    sample2.write_text("def test2(): pass")

    mock_samples_dir.exists.return_value = True
    mock_samples_dir.glob.return_value = [sample1, sample2]

    with patch("scripts.verify_test_agent.process_sample") as mock_process:
        mock_process.side_effect = [
            SampleResult(
                file_name="01_test.py",
                file_path=str(sample1),
                status="passed",
                test_count=5,
                passed_count=5,
                failed_count=0,
                coverage=85.0,
                errors=[],
                verification_passed=True,
            ),
            SampleResult(
                file_name="02_test.py",
                file_path=str(sample2),
                status="passed",
                test_count=3,
                passed_count=3,
                failed_count=0,
                coverage=90.0,
                errors=[],
                verification_passed=True,
            ),
        ]

        from scripts.verify_test_agent import main

        with patch("scripts.verify_test_agent.PROJECT_ROOT", tmp_path):
            with patch("scripts.verify_test_agent.save_json_report"):
                exit_code = main()

        assert exit_code == 0


@patch("scripts.verify_test_agent.SAMPLES_DIR")
def test_main_failure(mock_samples_dir, tmp_path):
    """Test main function with failed execution."""
    sample1 = tmp_path / "01_test.py"
    sample1.write_text("def test(): pass")

    mock_samples_dir.exists.return_value = True
    mock_samples_dir.glob.return_value = [sample1]

    with patch("scripts.verify_test_agent.process_sample") as mock_process:
        mock_process.return_value = SampleResult(
            file_name="01_test.py",
            file_path=str(sample1),
            status="failed",
            test_count=3,
            passed_count=1,
            failed_count=2,
            coverage=50.0,
            errors=["Error"],
            verification_passed=False,
        )

        from scripts.verify_test_agent import main

        with patch("scripts.verify_test_agent.PROJECT_ROOT", tmp_path):
            with patch("scripts.verify_test_agent.save_json_report"):
                exit_code = main()

        assert exit_code == 1


@patch("scripts.verify_test_agent.SAMPLES_DIR")
def test_main_no_samples_dir(mock_samples_dir):
    """Test main function when samples directory doesn't exist."""
    mock_samples_dir.exists.return_value = False

    from scripts.verify_test_agent import main

    exit_code = main()
    assert exit_code == 1


@patch("scripts.verify_test_agent.SAMPLES_DIR")
def test_main_no_sample_files(mock_samples_dir):
    """Test main function when no sample files found."""
    mock_samples_dir.exists.return_value = True
    mock_samples_dir.glob.return_value = []

    from scripts.verify_test_agent import main

    exit_code = main()
    assert exit_code == 1


def test_save_json_report(tmp_path):
    """Test saving JSON report."""
    from scripts.verify_test_agent import (
        SampleResult,
        VerificationReport,
        save_json_report,
    )

    results = [
        SampleResult(
            file_name="test.py",
            file_path="test.py",
            status="passed",
            test_count=5,
            passed_count=5,
            failed_count=0,
            coverage=85.0,
            errors=[],
            verification_passed=True,
        )
    ]

    report = VerificationReport(
        total_samples=1,
        passed_samples=1,
        failed_samples=0,
        results=results,
        overall_status="PASS",
    )

    output_path = tmp_path / "report.json"
    save_json_report(report, output_path)

    assert output_path.exists()
    with open(output_path) as f:
        data = json.load(f)
        assert data["total_samples"] == 1
        assert data["overall_status"] == "PASS"
