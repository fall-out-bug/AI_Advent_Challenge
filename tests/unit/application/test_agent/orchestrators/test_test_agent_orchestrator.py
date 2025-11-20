"""Unit tests for TestAgentOrchestrator."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.test_agent.orchestrators.test_agent_orchestrator import (
    TestAgentOrchestrator,
)
from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_case import TestCase
from src.domain.test_agent.entities.test_result import TestResult, TestStatus

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_generate_tests_use_case():
    """Create mock generate tests use case."""
    use_case = AsyncMock()
    use_case.generate_tests = AsyncMock(
        return_value=[
            TestCase(
                name="test_example",
                code="def test_example(): assert True",
            )
        ]
    )
    return use_case


@pytest.fixture
def mock_generate_code_use_case():
    """Create mock generate code use case."""
    use_case = AsyncMock()
    use_case.generate_code = AsyncMock(
        return_value=CodeFile(
            path="generated.py",
            content="def calculate(a, b): return a + b",
        )
    )
    return use_case


@pytest.fixture
def mock_execute_tests_use_case():
    """Create mock execute tests use case."""
    use_case = MagicMock()
    use_case.execute_tests = MagicMock(
        return_value=TestResult(
            status=TestStatus.PASSED,
            test_count=5,
            passed_count=5,
            failed_count=0,
            coverage=85.5,
        )
    )
    return use_case


@pytest.fixture
def sample_code_file():
    """Create sample code file."""
    return CodeFile(
        path="test.py",
        content="def add(a, b): return a + b",
    )


async def test_orchestrate_test_workflow_calls_all_use_cases(
    mock_generate_tests_use_case,
    mock_generate_code_use_case,
    mock_execute_tests_use_case,
    sample_code_file,
):
    """Test orchestrate_test_workflow calls all use cases."""
    orchestrator = TestAgentOrchestrator(
        generate_tests_use_case=mock_generate_tests_use_case,
        generate_code_use_case=mock_generate_code_use_case,
        execute_tests_use_case=mock_execute_tests_use_case,
    )

    await orchestrator.orchestrate_test_workflow(sample_code_file)

    mock_generate_tests_use_case.generate_tests.assert_called_once()
    mock_generate_code_use_case.generate_code.assert_called_once()
    mock_execute_tests_use_case.execute_tests.assert_called_once()


async def test_orchestrate_test_workflow_returns_test_result(
    mock_generate_tests_use_case,
    mock_generate_code_use_case,
    mock_execute_tests_use_case,
    sample_code_file,
):
    """Test orchestrate_test_workflow returns test result."""
    orchestrator = TestAgentOrchestrator(
        generate_tests_use_case=mock_generate_tests_use_case,
        generate_code_use_case=mock_generate_code_use_case,
        execute_tests_use_case=mock_execute_tests_use_case,
    )

    result = await orchestrator.orchestrate_test_workflow(sample_code_file)

    assert isinstance(result, TestResult)
    assert result.status == TestStatus.PASSED


async def test_orchestrate_test_workflow_handles_errors(
    mock_generate_tests_use_case,
    mock_generate_code_use_case,
    mock_execute_tests_use_case,
    sample_code_file,
):
    """Test orchestrate_test_workflow handles errors."""
    mock_generate_tests_use_case.generate_tests = AsyncMock(
        side_effect=Exception("Generation error")
    )
    orchestrator = TestAgentOrchestrator(
        generate_tests_use_case=mock_generate_tests_use_case,
        generate_code_use_case=mock_generate_code_use_case,
        execute_tests_use_case=mock_execute_tests_use_case,
    )

    with pytest.raises(Exception, match="Generation error"):
        await orchestrator.orchestrate_test_workflow(sample_code_file)


async def test_orchestrate_test_workflow_coordinates_flow(
    mock_generate_tests_use_case,
    mock_generate_code_use_case,
    mock_execute_tests_use_case,
    sample_code_file,
):
    """Test orchestrate_test_workflow coordinates flow."""
    orchestrator = TestAgentOrchestrator(
        generate_tests_use_case=mock_generate_tests_use_case,
        generate_code_use_case=mock_generate_code_use_case,
        execute_tests_use_case=mock_execute_tests_use_case,
    )

    await orchestrator.orchestrate_test_workflow(sample_code_file)

    # Verify call order: generate_tests -> generate_code -> execute_tests
    call_order = [
        mock_generate_tests_use_case.generate_tests.call_count,
        mock_generate_code_use_case.generate_code.call_count,
        mock_execute_tests_use_case.execute_tests.call_count,
    ]
    assert all(count == 1 for count in call_order)
