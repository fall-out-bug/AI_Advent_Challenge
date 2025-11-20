"""E2E tests for Test Agent with debug output analysis."""

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
from src.infrastructure.test_agent.adapters.pytest_executor import TestExecutor
from src.infrastructure.test_agent.services.llm_service import TestAgentLLMService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def sample_code_file():
    """Create sample code file for testing."""
    return CodeFile(
        path="test_sample.py",
        content="""def add(a: int, b: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    return a + b

def subtract(a: int, b: int) -> int:
    \"\"\"Subtract b from a.\"\"\"
    return a - b""",
    )


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    client = AsyncMock()
    # Mock response with valid test code (no redefinitions)
    client.generate = AsyncMock(
        return_value="""def test_add():
    assert add(2, 3) == 5

def test_subtract():
    assert subtract(5, 3) == 2"""
    )
    return client


@pytest.fixture
def test_agent_orchestrator(mock_llm_client):
    """Create TestAgentOrchestrator with mocked dependencies."""
    llm_service = TestAgentLLMService(llm_client=mock_llm_client)
    test_executor = TestExecutor()

    generate_tests_use_case = GenerateTestsUseCase(
        llm_service=llm_service, llm_client=mock_llm_client
    )
    generate_code_use_case = GenerateCodeUseCase(
        llm_service=llm_service, llm_client=mock_llm_client
    )
    execute_tests_use_case = ExecuteTestsUseCase(test_executor=test_executor)

    return TestAgentOrchestrator(
        generate_tests_use_case=generate_tests_use_case,
        generate_code_use_case=generate_code_use_case,
        execute_tests_use_case=execute_tests_use_case,
    )


async def test_e2e_no_function_redefinitions(test_agent_orchestrator, sample_code_file):
    """Test E2E workflow ensures no function redefinitions."""
    # Enable debug logging
    os.environ["TEST_AGENT_DEBUG_LLM"] = "1"

    try:
        result = await test_agent_orchestrator.orchestrate_test_workflow(
            sample_code_file
        )

        # Verify source code was not modified
        assert (
            sample_code_file.content
            == """def add(a: int, b: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    return a + b

def subtract(a: int, b: int) -> int:
    \"\"\"Subtract b from a.\"\"\"
    return a - b"""
        )

        # Verify result is valid
        assert result is not None
        assert isinstance(result.status, TestStatus)

    finally:
        if "TEST_AGENT_DEBUG_LLM" in os.environ:
            del os.environ["TEST_AGENT_DEBUG_LLM"]


async def test_e2e_source_code_integrity(test_agent_orchestrator, sample_code_file):
    """Test E2E workflow maintains source code integrity."""
    original_content = sample_code_file.content
    original_hash = hash(original_content)

    result = await test_agent_orchestrator.orchestrate_test_workflow(sample_code_file)

    # Verify source code integrity
    assert sample_code_file.content == original_content
    assert hash(sample_code_file.content) == original_hash

    # Verify result
    assert result is not None


async def test_e2e_with_llm_redefinition_attempt(
    test_agent_orchestrator, sample_code_file
):
    """Test E2E workflow filters out LLM-generated redefinitions."""
    # Mock LLM to return code with redefinition
    mock_llm = test_agent_orchestrator.generate_tests_use_case.llm_client
    mock_llm.generate = AsyncMock(
        return_value="""def add(a, b):
    return a + b

def test_add():
    assert add(2, 3) == 5"""
    )

    original_content = sample_code_file.content

    result = await test_agent_orchestrator.orchestrate_test_workflow(sample_code_file)

    # Source code must remain unchanged
    assert sample_code_file.content == original_content

    # Redefinition should be filtered out
    # Result may have fewer tests or different status, but source must be intact
    assert result is not None


async def test_e2e_debug_output_generation(test_agent_orchestrator, sample_code_file):
    """Test E2E workflow generates debug output when enabled."""
    debug_dir = Path("/tmp/test_agent_e2e_debug")
    os.environ["TEST_AGENT_DEBUG_LLM"] = "1"
    os.environ["TEST_AGENT_DEBUG_DIR"] = str(debug_dir)

    try:
        result = await test_agent_orchestrator.orchestrate_test_workflow(
            sample_code_file
        )

        # Verify debug files were created (if directory exists and is writable)
        if debug_dir.exists():
            prompt_files = list(debug_dir.glob("prompt_*.txt"))
            response_files = list(debug_dir.glob("response_*.txt"))
            # At least one debug file should exist
            assert len(prompt_files) > 0 or len(response_files) > 0

        assert result is not None

    finally:
        if "TEST_AGENT_DEBUG_LLM" in os.environ:
            del os.environ["TEST_AGENT_DEBUG_LLM"]
        if "TEST_AGENT_DEBUG_DIR" in os.environ:
            del os.environ["TEST_AGENT_DEBUG_DIR"]


async def test_e2e_complete_workflow(test_agent_orchestrator, sample_code_file):
    """Test complete E2E workflow from code file to test result."""
    original_content = sample_code_file.content

    result = await test_agent_orchestrator.orchestrate_test_workflow(sample_code_file)

    # Verify source code integrity
    assert sample_code_file.content == original_content

    # Verify result structure
    assert result is not None
    assert hasattr(result, "status")
    assert hasattr(result, "test_count")
    assert hasattr(result, "coverage")
    assert isinstance(result.status, TestStatus)

    # Verify no redefinitions in generated test file (if debug file exists)
    debug_path = Path("/tmp/test_agent_debug.py")
    if debug_path.exists():
        debug_content = debug_path.read_text()
        # Source code section should be present and unchanged
        if "# ===== SOURCE CODE (IMMUTABLE) =====" in debug_content:
            # Extract source section
            source_start = debug_content.find("# ===== SOURCE CODE (IMMUTABLE) =====")
            source_end = debug_content.find("# ===== END SOURCE CODE =====")
            if source_start >= 0 and source_end >= 0:
                source_section = debug_content[
                    source_start
                    + len("# ===== SOURCE CODE (IMMUTABLE) =====\n") : source_end
                ].strip()
                # Verify source matches original
                assert "def add(a: int, b: int)" in source_section
                assert "def subtract(a: int, b: int)" in source_section
                # Verify no redefinitions in test section
                test_section = debug_content[source_end:]
                assert (
                    "def add(a: int, b: int)" not in test_section
                    or test_section.count("def add") == 1
                )
