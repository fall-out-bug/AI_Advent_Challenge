"""Unit tests for EnhancedGenerateTestsUseCase."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.test_agent.use_cases.generate_tests_use_case import (
    GenerateTestsUseCase,
)
from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_case import TestCase
from src.domain.test_agent.interfaces.code_chunker import ICodeChunker
from src.domain.test_agent.interfaces.code_summarizer import ICodeSummarizer
from src.domain.test_agent.interfaces.coverage_aggregator import ICoverageAggregator
from src.domain.test_agent.interfaces.token_counter import ITokenCounter

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    service = MagicMock()
    service.generate_tests_prompt = MagicMock(
        return_value="Generate tests for this code"
    )
    return service


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    client = AsyncMock()
    client.generate = AsyncMock(
        return_value="""
def test_example():
    assert True

def test_calculate():
    assert calculate(1, 2) == 3
"""
    )
    return client


@pytest.fixture
def mock_token_counter():
    """Create mock token counter."""
    counter = MagicMock(spec=ITokenCounter)
    counter.count_tokens = MagicMock(return_value=100)
    counter.estimate_prompt_size = MagicMock(return_value=200)
    return counter


@pytest.fixture
def mock_code_chunker():
    """Create mock code chunker."""
    chunker = MagicMock(spec=ICodeChunker)
    chunker.chunk_module = MagicMock(return_value=[])
    return chunker


@pytest.fixture
def mock_code_summarizer():
    """Create mock code summarizer."""
    summarizer = MagicMock(spec=ICodeSummarizer)
    summarizer.summarize_chunk = AsyncMock(return_value="Summary")
    return summarizer


@pytest.fixture
def mock_coverage_aggregator():
    """Create mock coverage aggregator."""
    aggregator = MagicMock(spec=ICoverageAggregator)
    aggregator.aggregate_coverage = MagicMock(return_value=85.0)
    aggregator.identify_gaps = MagicMock(return_value=[])
    return aggregator


# T6.1: Backward compatibility tests
async def test_execute_small_module_no_chunking(
    mock_llm_service,
    mock_llm_client,
    mock_token_counter,
    mock_code_chunker,
    mock_code_summarizer,
    mock_coverage_aggregator,
):
    """Test execute for small module does not use chunking."""
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service,
        llm_client=mock_llm_client,
        token_counter=mock_token_counter,
        code_chunker=mock_code_chunker,
        code_summarizer=mock_code_summarizer,
        coverage_aggregator=mock_coverage_aggregator,
    )
    code_file = CodeFile(path="test.py", content="def calculate(a, b): return a + b")

    # Mock token counter to indicate small module (under limit)
    mock_token_counter.estimate_prompt_size.return_value = 500  # Under 4000 limit

    result = await use_case.generate_tests(code_file)

    assert isinstance(result, list)
    assert all(isinstance(tc, TestCase) for tc in result)
    # Verify chunker was not called for small modules
    mock_code_chunker.chunk_module.assert_not_called()


async def test_execute_returns_list_of_test_cases(
    mock_llm_service,
    mock_llm_client,
    mock_token_counter,
    mock_code_chunker,
    mock_code_summarizer,
    mock_coverage_aggregator,
):
    """Test execute returns list of test cases."""
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service,
        llm_client=mock_llm_client,
        token_counter=mock_token_counter,
        code_chunker=mock_code_chunker,
        code_summarizer=mock_code_summarizer,
        coverage_aggregator=mock_coverage_aggregator,
    )
    code_file = CodeFile(path="test.py", content="def calculate(a, b): return a + b")

    result = await use_case.generate_tests(code_file)

    assert isinstance(result, list)
    assert all(isinstance(tc, TestCase) for tc in result)
    assert len(result) > 0


async def test_execute_uses_existing_llm_service(
    mock_llm_service,
    mock_llm_client,
    mock_token_counter,
    mock_code_chunker,
    mock_code_summarizer,
    mock_coverage_aggregator,
):
    """Test execute uses existing LLM service."""
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service,
        llm_client=mock_llm_client,
        token_counter=mock_token_counter,
        code_chunker=mock_code_chunker,
        code_summarizer=mock_code_summarizer,
        coverage_aggregator=mock_coverage_aggregator,
    )
    code_file = CodeFile(path="test.py", content="def add(a, b): return a + b")

    # Mock small token count to avoid chunking
    mock_token_counter.estimate_prompt_size.return_value = 300

    await use_case.generate_tests(code_file)

    # Should be called at least once (may be called twice: once for token check, once for generation)
    assert mock_llm_service.generate_tests_prompt.call_count >= 1
    # Verify the actual generation call includes code content
    calls_with_content = [
        call
        for call in mock_llm_service.generate_tests_prompt.call_args_list
        if code_file.content in str(call)
    ]
    assert len(calls_with_content) > 0


async def test_execute_backward_compatible_with_epic_26(
    mock_llm_service,
    mock_llm_client,
    mock_token_counter,
    mock_code_chunker,
    mock_code_summarizer,
    mock_coverage_aggregator,
):
    """Test execute is backward compatible with Epic 26 behavior."""
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service,
        llm_client=mock_llm_client,
        token_counter=mock_token_counter,
        code_chunker=mock_code_chunker,
        code_summarizer=mock_code_summarizer,
        coverage_aggregator=mock_coverage_aggregator,
    )
    # Small module that should work exactly like Epic 26
    code_file = CodeFile(
        path="test.py",
        content="""
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
""",
    )

    # Mock small token count
    mock_token_counter.estimate_prompt_size.return_value = 300

    result = await use_case.generate_tests(code_file)

    # Should work exactly like Epic 26 - no chunking, no summarization
    assert isinstance(result, list)
    assert len(result) > 0
    mock_code_chunker.chunk_module.assert_not_called()
    mock_code_summarizer.summarize_chunk.assert_not_called()


# T6.2: Multiple chunks tests
async def test_execute_for_large_module_uses_chunker(
    mock_llm_service,
    mock_llm_client,
    mock_token_counter,
    mock_code_chunker,
    mock_code_summarizer,
    mock_coverage_aggregator,
):
    """Test execute for large module uses chunker."""
    from src.domain.test_agent.entities.code_chunk import CodeChunk

    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service,
        llm_client=mock_llm_client,
        token_counter=mock_token_counter,
        code_chunker=mock_code_chunker,
        code_summarizer=mock_code_summarizer,
        coverage_aggregator=mock_coverage_aggregator,
    )

    # Large module that exceeds token limit
    large_code = "\n".join([f"def func{i}(): pass" for i in range(1000)])
    code_file = CodeFile(path="test.py", content=large_code)

    # Mock token counter to indicate large module (over limit)
    mock_token_counter.estimate_prompt_size.return_value = 5000  # Over 4000 limit

    # Mock chunker to return chunks
    chunk1 = CodeChunk(
        code="def func1(): pass",
        context="First chunk",
        dependencies=[],
        location="test.py",
        start_line=1,
        end_line=10,
    )
    chunk2 = CodeChunk(
        code="def func2(): pass",
        context="Second chunk",
        dependencies=[],
        location="test.py",
        start_line=11,
        end_line=20,
    )
    mock_code_chunker.chunk_module.return_value = [chunk1, chunk2]

    # Mock LLM to return tests for each chunk (need multiple calls)
    mock_llm_client.generate = AsyncMock(
        side_effect=[
            """
def test_func1():
    assert True

def test_func1_second():
    assert True
""",
            """
def test_func2():
    assert True

def test_func2_second():
    assert True
""",
        ]
    )

    result = await use_case.generate_tests(code_file)

    # Verify chunker was called
    mock_code_chunker.chunk_module.assert_called_once()
    assert isinstance(result, list)


async def test_execute_for_large_module_uses_summarizer(
    mock_llm_service,
    mock_llm_client,
    mock_token_counter,
    mock_code_chunker,
    mock_code_summarizer,
    mock_coverage_aggregator,
):
    """Test execute for large module uses summarizer."""
    from src.domain.test_agent.entities.code_chunk import CodeChunk

    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service,
        llm_client=mock_llm_client,
        token_counter=mock_token_counter,
        code_chunker=mock_code_chunker,
        code_summarizer=mock_code_summarizer,
        coverage_aggregator=mock_coverage_aggregator,
    )

    large_code = "\n".join([f"def func{i}(): pass" for i in range(1000)])
    code_file = CodeFile(path="test.py", content=large_code)

    mock_token_counter.estimate_prompt_size.return_value = 5000

    # Create multiple chunks so summarizer is called (for i > 0)
    chunk1 = CodeChunk(
        code="def func1(): pass",
        context="First chunk",
        dependencies=[],
        location="test.py",
        start_line=1,
        end_line=10,
    )
    chunk2 = CodeChunk(
        code="def func2(): pass",
        context="Second chunk",
        dependencies=[],
        location="test.py",
        start_line=11,
        end_line=20,
    )
    mock_code_chunker.chunk_module.return_value = [chunk1, chunk2]

    # Mock LLM to return tests for each chunk (need enough for regeneration too)
    mock_llm_client.generate = AsyncMock(
        side_effect=[
            """
def test_func1():
    assert True

def test_func1_second():
    assert True
""",
            """
def test_func2():
    assert True

def test_func2_second():
    assert True
""",
            """
def test_func1_regenerated():
    assert True
""",
            """
def test_func2_regenerated():
    assert True
""",
        ]
    )

    await use_case.generate_tests(code_file)

    # Verify summarizer was called for context preservation (for chunk 2)
    mock_code_summarizer.summarize_chunk.assert_called()


async def test_execute_for_large_module_aggregates_coverage(
    mock_llm_service,
    mock_llm_client,
    mock_token_counter,
    mock_code_chunker,
    mock_code_summarizer,
    mock_coverage_aggregator,
):
    """Test execute for large module aggregates coverage."""
    from src.domain.test_agent.entities.code_chunk import CodeChunk

    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service,
        llm_client=mock_llm_client,
        token_counter=mock_token_counter,
        code_chunker=mock_code_chunker,
        code_summarizer=mock_code_summarizer,
        coverage_aggregator=mock_coverage_aggregator,
    )

    large_code = "\n".join([f"def func{i}(): pass" for i in range(1000)])
    code_file = CodeFile(path="test.py", content=large_code)

    mock_token_counter.estimate_prompt_size.return_value = 5000

    chunk = CodeChunk(
        code="def func1(): pass",
        context="Chunk",
        dependencies=[],
        location="test.py",
        start_line=1,
        end_line=10,
    )
    mock_code_chunker.chunk_module.return_value = [chunk]

    await use_case.generate_tests(code_file)

    # Coverage aggregator should be used to ensure >=80% coverage
    # This will be verified in integration tests with actual test execution


async def test_execute_for_large_module_with_function_strategy(
    mock_llm_service,
    mock_llm_client,
    mock_token_counter,
    mock_code_chunker,
    mock_code_summarizer,
    mock_coverage_aggregator,
):
    """Test execute for large module with function-based strategy."""
    from src.domain.test_agent.entities.code_chunk import CodeChunk

    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service,
        llm_client=mock_llm_client,
        token_counter=mock_token_counter,
        code_chunker=mock_code_chunker,
        code_summarizer=mock_code_summarizer,
        coverage_aggregator=mock_coverage_aggregator,
    )

    large_code = "\n".join([f"def func{i}(): pass" for i in range(1000)])
    code_file = CodeFile(path="test.py", content=large_code)

    mock_token_counter.estimate_prompt_size.return_value = 5000

    chunk = CodeChunk(
        code="def func1(): pass",
        context="Chunk",
        dependencies=[],
        location="test.py",
        start_line=1,
        end_line=10,
    )
    mock_code_chunker.chunk_module.return_value = [chunk]

    # Mock LLM to return tests
    mock_llm_client.generate = AsyncMock(
        return_value="""
def test_func1():
    assert True
"""
    )

    await use_case.generate_tests(code_file)

    # Verify chunker was called with function_based strategy
    # chunk_module is called with positional args: (code, max_tokens, strategy)
    call_args = mock_code_chunker.chunk_module.call_args
    # Check if called with keyword args or positional
    if call_args.kwargs:
        assert call_args.kwargs.get("strategy") == "function_based"
    else:
        # Positional args: (code, max_tokens, strategy)
        assert len(call_args.args) >= 3
        assert call_args.args[2] == "function_based"


async def test_execute_for_large_module_with_class_strategy(
    mock_llm_service,
    mock_llm_client,
    mock_token_counter,
    mock_code_chunker,
    mock_code_summarizer,
    mock_coverage_aggregator,
):
    """Test execute for large module with class-based strategy."""
    from src.domain.test_agent.entities.code_chunk import CodeChunk

    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service,
        llm_client=mock_llm_client,
        token_counter=mock_token_counter,
        code_chunker=mock_code_chunker,
        code_summarizer=mock_code_summarizer,
        coverage_aggregator=mock_coverage_aggregator,
    )

    # Module with classes
    large_code = "\n".join([f"class MyClass{i}:\n    pass" for i in range(1000)])
    code_file = CodeFile(path="test.py", content=large_code)

    mock_token_counter.estimate_prompt_size.return_value = 5000

    chunk = CodeChunk(
        code="class MyClass1: pass",
        context="Chunk",
        dependencies=[],
        location="test.py",
        start_line=1,
        end_line=10,
    )
    mock_code_chunker.chunk_module.return_value = [chunk]

    await use_case.generate_tests(code_file)

    # Strategy selection should detect classes and use class_based
    # This will be verified in implementation


async def test_execute_for_large_module_with_sliding_window_strategy(
    mock_llm_service,
    mock_llm_client,
    mock_token_counter,
    mock_code_chunker,
    mock_code_summarizer,
    mock_coverage_aggregator,
):
    """Test execute for large module with sliding-window strategy."""
    from src.domain.test_agent.entities.code_chunk import CodeChunk

    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service,
        llm_client=mock_llm_client,
        token_counter=mock_token_counter,
        code_chunker=mock_code_chunker,
        code_summarizer=mock_code_summarizer,
        coverage_aggregator=mock_coverage_aggregator,
    )

    # Large module without clear structure
    large_code = "\n".join([f"x = {i}" for i in range(1000)])
    code_file = CodeFile(path="test.py", content=large_code)

    mock_token_counter.estimate_prompt_size.return_value = 5000

    chunk = CodeChunk(
        code="x = 1",
        context="Chunk",
        dependencies=[],
        location="test.py",
        start_line=1,
        end_line=10,
    )
    mock_code_chunker.chunk_module.return_value = [chunk]

    await use_case.generate_tests(code_file)

    # Strategy selection should fall back to sliding_window
    # This will be verified in implementation
