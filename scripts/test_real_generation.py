#!/usr/bin/env python3
"""Test real test generation by Test Agent with actual LLM.

Purpose:
    Tests that Test Agent can actually generate valid, executable tests
    for real Python modules using real LLM service.

Usage:
    LLM_URL=http://localhost:8000 python scripts/test_real_generation.py [module_path]
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.application.test_agent.orchestrators.test_agent_orchestrator import (
    TestAgentOrchestrator,
)
from src.application.test_agent.services.code_chunker import CodeChunker
from src.application.test_agent.services.coverage_aggregator import CoverageAggregator
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
from src.infrastructure.test_agent.services.code_summarizer import CodeSummarizer
from src.infrastructure.test_agent.services.llm_service import TestAgentLLMService
from src.infrastructure.test_agent.services.token_counter import TokenCounter


def create_simple_test_module() -> str:
    """Create a simple test module for agent to generate tests for.

    Returns:
        Python code string with functions to test.
    """
    return '''"""Simple calculator module for testing."""

from typing import List, Optional


class Calculator:
    """Simple calculator class."""

    def __init__(self, initial_value: float = 0.0) -> None:
        """Initialize calculator.

        Args:
            initial_value: Starting value.
        """
        self.value = initial_value

    def add(self, number: float) -> float:
        """Add number to current value.

        Args:
            number: Number to add.

        Returns:
            Updated value.
        """
        self.value += number
        return self.value

    def subtract(self, number: float) -> float:
        """Subtract number from current value.

        Args:
            number: Number to subtract.

        Returns:
            Updated value.
        """
        self.value -= number
        return self.value

    def multiply(self, number: float) -> float:
        """Multiply current value by number.

        Args:
            number: Number to multiply by.

        Returns:
            Updated value.
        """
        self.value *= number
        return self.value

    def divide(self, number: float) -> float:
        """Divide current value by number.

        Args:
            number: Number to divide by.

        Returns:
            Updated value.

        Raises:
            ValueError: If number is zero.
        """
        if number == 0:
            raise ValueError("Cannot divide by zero")
        self.value /= number
        return self.value

    def reset(self) -> None:
        """Reset calculator to zero."""
        self.value = 0.0

    def get_value(self) -> float:
        """Get current value.

        Returns:
            Current calculator value.
        """
        return self.value


def calculate_sum(numbers: List[float]) -> float:
    """Calculate sum of numbers.

    Args:
        numbers: List of numbers to sum.

    Returns:
        Sum of all numbers.
    """
    return sum(numbers)


def calculate_average(numbers: List[float]) -> Optional[float]:
    """Calculate average of numbers.

    Args:
        numbers: List of numbers.

    Returns:
        Average of numbers, or None if list is empty.
    """
    if not numbers:
        return None
    return sum(numbers) / len(numbers)
'''


async def test_real_generation(module_path: Path | None = None) -> None:
    """Test real test generation with actual LLM.

    Purpose:
        Verifies end-to-end test generation workflow with real LLM service.
    """
    print("\n" + "=" * 80)
    print("TEST: Real Test Generation by Test Agent")
    print("=" * 80)

    # Check LLM availability
    llm_url = os.getenv("LLM_URL", "http://localhost:8000")
    print(f"LLM URL: {llm_url}")

    try:
        client = get_llm_client(timeout=10.0)
        test_result = await client.generate("test", max_tokens=5)
        print(f"✓ LLM service is available (test response: {len(test_result)} chars)")
    except Exception as e:
        print(f"❌ LLM service not available: {e}")
        print("   Please ensure LLM service is running and LLM_URL is set correctly.")
        return

    # Prepare test module
    if module_path and module_path.exists():
        print(f"\nUsing module: {module_path}")
        code = module_path.read_text(encoding="utf-8")
        test_file_path = module_path
    else:
        print("\nUsing generated test module (Calculator)")
        code = create_simple_test_module()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as tmp_file:
            tmp_file.write(code)
            test_file_path = Path(tmp_file.name)

    try:
        # Create orchestrator with Epic 27 enhancements
        print("\nInitializing Test Agent orchestrator...")
        primary_client = get_llm_client(
            timeout=900.0
        )  # 15 minutes for complex generation
        llm_client = ResilientLLMClient(primary_client)
        llm_service = TestAgentLLMService(llm_client=llm_client)
        test_executor = TestExecutor()

        # Epic 27 components
        token_counter = TokenCounter()
        code_chunker = CodeChunker(token_counter=token_counter)
        code_summarizer = CodeSummarizer(llm_client=llm_client)
        coverage_aggregator = CoverageAggregator()

        generate_tests_use_case = GenerateTestsUseCase(
            llm_service=llm_service,
            llm_client=llm_client,
            token_counter=token_counter,
            code_chunker=code_chunker,
            code_summarizer=code_summarizer,
            coverage_aggregator=coverage_aggregator,
        )
        generate_code_use_case = GenerateCodeUseCase(
            llm_service=llm_service, llm_client=llm_client
        )
        execute_tests_use_case = ExecuteTestsUseCase(test_executor=test_executor)

        orchestrator = TestAgentOrchestrator(
            generate_tests_use_case=generate_tests_use_case,
            generate_code_use_case=generate_code_use_case,
            execute_tests_use_case=execute_tests_use_case,
        )

        # Generate tests
        print(f"\n{'='*80}")
        print("GENERATING TESTS")
        print(f"{'='*80}")
        print(f"Module: {test_file_path.name}")
        print(f"Size: {len(code)} chars, {len(code.splitlines())} lines")
        print(f"Estimated tokens: {token_counter.count_tokens(code)}")
        print("\n⏳ This may take 2-5 minutes...")
        print("   (LLM generation can be slow for complex code)\n")

        code_file = CodeFile(path=str(test_file_path), content=code)
        result = await orchestrator.orchestrate_test_workflow(code_file)

        # Display results
        print(f"\n{'='*80}")
        print("GENERATION RESULTS")
        print(f"{'='*80}")
        print(f"Status: {result.status.value.upper()}")
        print(f"Tests generated: {result.test_count}")
        print(f"Tests passed: {result.passed_count}")
        print(f"Tests failed: {result.failed_count}")
        print(f"Coverage: {result.coverage:.1f}%")

        if result.errors:
            print(f"\nErrors ({len(result.errors)}):")
            for error in result.errors[:5]:
                print(f"  - {error}")

        # Display generated test cases
        if orchestrator.generated_test_cases:
            print(f"\n{'='*80}")
            print(f"GENERATED TEST CASES ({len(orchestrator.generated_test_cases)})")
            print(f"{'='*80}")
            for i, test_case in enumerate(orchestrator.generated_test_cases[:10], 1):
                print(f"\nTest {i}: {test_case.name}")
                print(f"  Code length: {len(test_case.code)} chars")
                print(f"  Preview: {test_case.code[:100]}...")

        # Validate results
        assert result.status in (
            TestStatus.PASSED,
            TestStatus.FAILED,
        ), f"Unexpected status: {result.status}"
        assert result.test_count > 0, "Should generate at least one test"
        assert (
            len(orchestrator.generated_test_cases) > 0
        ), "Should have generated test cases"

        print(f"\n{'='*80}")
        print("✅ TEST GENERATION SUCCESSFUL")
        print(f"{'='*80}")
        print(f"✓ Generated {result.test_count} test(s)")
        print(f"✓ {result.passed_count} test(s) passed")
        if result.coverage > 0:
            print(f"✓ Coverage: {result.coverage:.1f}%")
        if result.coverage >= 80.0:
            print(f"✓ Coverage target (80%) achieved!")

    except Exception as e:
        print(f"\n{'='*80}")
        print("❌ TEST GENERATION FAILED")
        print(f"{'='*80}")
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        raise
    finally:
        if not (module_path and module_path.exists()):
            # Clean up temp file
            test_file_path.unlink(missing_ok=True)


def main() -> None:
    """Run real test generation test.

    Purpose:
        Executes real test generation with actual LLM service.
    """
    print("\n" + "=" * 80)
    print("EPIC 27 REAL TEST GENERATION TEST")
    print("Testing actual test generation by Test Agent with real LLM")
    print("=" * 80)

    # Get module path from command line or use default
    module_path = None
    if len(sys.argv) > 1:
        module_path = Path(sys.argv[1])
        if not module_path.exists():
            print(f"❌ Module not found: {module_path}")
            sys.exit(1)

    asyncio.run(test_real_generation(module_path))


if __name__ == "__main__":
    main()
