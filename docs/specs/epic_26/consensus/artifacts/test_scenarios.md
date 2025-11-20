# Additional Test Scenarios

## Current Coverage

- ✅ Basic functionality tested (creation, validation)
- ✅ Happy path covered (all entities)
- ✅ Validation errors tested (empty strings, None values, negative numbers)
- ✅ Edge cases covered (metadata handling, coverage boundaries)
- ✅ Value object immutability tested

## Recommended Additional Tests

### Edge Case Tests

```python
def test_code_file_metadata_with_special_characters():
    """CodeFile should handle metadata with special characters."""
    metadata = {"key@with#special": "value with spaces", "unicode": "测试"}
    code_file = CodeFile(
        path="test.py",
        content="def test(): pass",
        metadata=metadata
    )
    assert code_file.metadata == metadata
```

```python
def test_test_result_coverage_boundaries():
    """TestResult should validate coverage at exact boundaries."""
    # Test minimum boundary
    result_min = TestResult(
        status=TestStatus.PASSED,
        test_count=1,
        passed_count=1,
        failed_count=0,
        coverage=0.0
    )
    assert result_min.coverage == 0.0

    # Test maximum boundary
    result_max = TestResult(
        status=TestStatus.PASSED,
        test_count=1,
        passed_count=1,
        failed_count=0,
        coverage=100.0
    )
    assert result_max.coverage == 100.0
```

```python
def test_test_generation_request_long_path():
    """TestGenerationRequest should handle very long file paths."""
    long_path = "/" + "a" * 200 + "/test.py"
    request = TestGenerationRequest(
        code_file_path=long_path,
        language="python"
    )
    assert len(request.code_file_path) > 200
```

### Immutability Tests

```python
def test_test_generation_request_immutability_modification():
    """TestGenerationRequest should be truly immutable."""
    request = TestGenerationRequest(
        code_file_path="test.py",
        language="python",
        metadata={"key": "value"}
    )

    # Attempting to modify should raise AttributeError
    with pytest.raises(AttributeError):
        request.code_file_path = "new_path.py"

    with pytest.raises(AttributeError):
        request.metadata["new_key"] = "new_value"
```

### Integration Readiness Tests

```python
def test_code_file_serialization_ready():
    """CodeFile should be ready for JSON serialization."""
    code_file = CodeFile(
        path="test.py",
        content="def test(): pass",
        metadata={"key": "value"}
    )

    # Should be serializable to dict
    data = {
        "path": code_file.path,
        "content": code_file.content,
        "metadata": code_file.metadata
    }
    assert isinstance(data, dict)
    assert data["path"] == "test.py"
```

```python
def test_test_result_all_statuses():
    """TestResult should support all TestStatus enum values."""
    for status in TestStatus:
        result = TestResult(
            status=status,
            test_count=1,
            passed_count=1 if status == TestStatus.PASSED else 0,
            failed_count=1 if status == TestStatus.FAILED else 0
        )
        assert result.status == status
```

### Performance Tests

```python
def test_code_file_large_content():
    """CodeFile should handle large content efficiently."""
    large_content = "def test():\n" + "    pass\n" * 10000
    code_file = CodeFile(
        path="test.py",
        content=large_content
    )
    assert len(code_file.content) > 100000
    assert "def test()" in code_file.content
```

```python
def test_test_result_many_errors():
    """TestResult should handle many error messages."""
    many_errors = [f"Error {i}" for i in range(1000)]
    result = TestResult(
        status=TestStatus.FAILED,
        test_count=1000,
        passed_count=0,
        failed_count=1000,
        errors=many_errors
    )
    assert len(result.errors) == 1000
```

## Notes

These additional test scenarios would enhance test coverage for edge cases and ensure robustness. However, the current test suite already provides excellent coverage (100%) for the domain layer implementation. These tests can be added incrementally as the codebase evolves or if specific edge cases are discovered during integration testing.

---

# Stage 2 Additional Test Scenarios

## Current Coverage

- ✅ Basic functionality tested (all adapters and services)
- ✅ Happy path covered (test execution, prompt generation, reporting)
- ✅ Error handling tested (missing files, syntax errors)
- ✅ Edge cases covered (coverage calculation, error formatting)

## Recommended Additional Tests

### TestExecutor Edge Cases

```python
def test_executor_timeout_expiration(tmp_path):
    """TestExecutor should handle timeout expiration gracefully."""
    test_file = tmp_path / "test_slow.py"
    test_file.write_text("""
import time
def test_slow():
    time.sleep(120)  # Exceeds 60s timeout
    assert True
""")
    executor = TestExecutor()
    result = executor.execute(str(test_file))

    assert result.status == TestStatus.ERROR
    assert "timeout" in result.errors[0].lower()
```

```python
def test_get_coverage_malformed_output(tmp_path):
    """TestExecutor should handle malformed coverage output."""
    test_file = tmp_path / "test_coverage.py"
    test_file.write_text("def test_coverage(): assert True")

    executor = TestExecutor()
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.stdout = "Invalid coverage output format"
        mock_run.return_value.returncode = 0

        coverage = executor.get_coverage(str(test_file))
        assert coverage == 0.0
```

```python
def test_executor_pytest_not_installed():
    """TestExecutor should handle pytest not being installed."""
    executor = TestExecutor()
    with patch('subprocess.run', side_effect=FileNotFoundError("pytest not found")):
        result = executor.execute("test.py")
        assert result.status == TestStatus.ERROR
        assert len(result.errors) > 0
```

### TestAgentLLMService Edge Cases

```python
def test_generate_tests_prompt_empty_code(mock_llm_client):
    """TestAgentLLMService should handle empty code input."""
    service = TestAgentLLMService(llm_client=mock_llm_client)
    prompt = service.generate_tests_prompt("")

    assert isinstance(prompt, str)
    assert len(prompt) > 0
```

```python
def test_generate_code_prompt_empty_requirements(mock_llm_client):
    """TestAgentLLMService should handle empty requirements."""
    service = TestAgentLLMService(llm_client=mock_llm_client)
    prompt = service.generate_code_prompt("", "def test(): pass")

    assert isinstance(prompt, str)
    assert "test" in prompt.lower()
```

### TestResultReporter Edge Cases

```python
def test_report_zero_tests():
    """TestResultReporter should handle zero test count."""
    reporter = TestResultReporter()
    result = TestResult(
        status=TestStatus.PASSED,
        test_count=0,
        passed_count=0,
        failed_count=0
    )

    report = reporter.report(result)
    assert "0" in report
    assert "Total Tests: 0" in report
```

```python
def test_report_coverage_boundary_values():
    """TestResultReporter should handle coverage boundary values."""
    reporter = TestResultReporter()

    assert "0.00%" in reporter.report_coverage(0.0)
    assert "100.00%" in reporter.report_coverage(100.0)
    assert "50.50%" in reporter.report_coverage(50.5)
```

## Notes

Stage 2 test coverage is 90% overall (pytest_executor 80%, others 100%). The uncovered lines in pytest_executor are primarily error handling paths that are difficult to test without mocking subprocess behavior extensively. These additional tests would improve coverage and robustness but do not block production deployment.

---

# Stage 3 Additional Test Scenarios

## Current Coverage

- ✅ Basic functionality tested (all use cases)
- ✅ Happy path covered (test generation, code generation, test execution)
- ✅ Error handling tested (LLM errors, syntax validation, architecture validation)
- ✅ Edge cases covered (pytest syntax validation, Clean Architecture boundary checks)

## Recommended Additional Tests

### GenerateTestsUseCase Edge Cases

```python
async def test_generate_tests_empty_code_file(mock_llm_service, mock_llm_client):
    """GenerateTestsUseCase should handle empty code file."""
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    code_file = CodeFile(path="test.py", content="")

    result = await use_case.generate_tests(code_file)

    assert isinstance(result, list)
    # Should handle gracefully or raise appropriate error
```

```python
async def test_generate_tests_empty_llm_response(mock_llm_service, mock_llm_client):
    """GenerateTestsUseCase should handle empty LLM response."""
    mock_llm_client.generate = AsyncMock(return_value="")
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    code_file = CodeFile(path="test.py", content="def func(): pass")

    result = await use_case.generate_tests(code_file)

    assert isinstance(result, list)
    # Should return empty list or handle appropriately
```

```python
async def test_generate_tests_multiple_test_functions(mock_llm_service, mock_llm_client):
    """GenerateTestsUseCase should parse multiple test functions correctly."""
    mock_llm_client.generate = AsyncMock(
        return_value="""
def test_one():
    assert True

def test_two():
    assert False

def test_three():
    assert 1 + 1 == 2
"""
    )
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    code_file = CodeFile(path="test.py", content="def func(): pass")

    result = await use_case.generate_tests(code_file)

    assert len(result) == 3
    assert all(tc.name.startswith("test_") for tc in result)
```

### GenerateCodeUseCase Edge Cases

```python
async def test_generate_code_empty_requirements(mock_llm_service, mock_llm_client, sample_test_cases):
    """GenerateCodeUseCase should handle empty requirements."""
    use_case = GenerateCodeUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )

    result = await use_case.generate_code("", sample_test_cases)

    assert isinstance(result, CodeFile)
    assert len(result.content) > 0
```

```python
async def test_generate_code_various_import_patterns(mock_llm_service, mock_llm_client, sample_test_cases):
    """GenerateCodeUseCase should catch various Clean Architecture violations."""
    violation_patterns = [
        "from src.presentation import Something",
        "import src.infrastructure",
        "from src.infrastructure.llm import Client",
        "import src.presentation.cli"
    ]

    for pattern in violation_patterns:
        mock_llm_client.generate = AsyncMock(return_value=pattern)
        use_case = GenerateCodeUseCase(
            llm_service=mock_llm_service, llm_client=mock_llm_client
        )

        with pytest.raises(ValueError, match="Clean Architecture"):
            await use_case.generate_code("requirements", sample_test_cases)
```

### ExecuteTestsUseCase Edge Cases

```python
def test_execute_tests_empty_test_cases(test_executor):
    """ExecuteTestsUseCase should handle empty test cases list."""
    use_case = ExecuteTestsUseCase(test_executor=test_executor)
    code_file = CodeFile(path="code.py", content="def func(): pass")

    result = use_case.execute_tests([], code_file)

    assert isinstance(result, TestResult)
    assert result.test_count == 0
```

```python
def test_execute_tests_tempfile_failure(test_executor):
    """ExecuteTestsUseCase should handle tempfile creation failure."""
    use_case = ExecuteTestsUseCase(test_executor=test_executor)
    test_cases = [TestCase(name="test_one", code="def test_one(): assert True")]
    code_file = CodeFile(path="code.py", content="def func(): pass")

    with patch('tempfile.TemporaryDirectory', side_effect=OSError("Disk full")):
        with pytest.raises(Exception, match="Test execution failed"):
            use_case.execute_tests(test_cases, code_file)
```

```python
def test_execute_tests_large_test_suite(test_executor):
    """ExecuteTestsUseCase should handle large test suites."""
    use_case = ExecuteTestsUseCase(test_executor=test_executor)
    test_cases = [
        TestCase(name=f"test_{i}", code=f"def test_{i}(): assert True")
        for i in range(100)
    ]
    code_file = CodeFile(path="code.py", content="def func(): pass")

    result = use_case.execute_tests(test_cases, code_file)

    assert isinstance(result, TestResult)
    assert result.test_count >= 0
```

## Notes

Stage 3 test coverage is 88% overall (generate_tests_use_case 85%, generate_code_use_case 90%, execute_tests_use_case 100%). The uncovered lines are primarily edge cases in parsing and error handling. These additional tests would improve coverage and robustness but do not block production deployment.

---

# Stage 4 Additional Test Scenarios

## Current Coverage

- ✅ Basic functionality tested (orchestrator workflow)
- ✅ Happy path covered (complete workflow execution)
- ✅ Error handling tested (exception propagation)
- ✅ Edge cases covered (workflow coordination)

## Recommended Additional Tests

### Orchestrator Edge Cases

```python
async def test_orchestrate_with_empty_test_cases(
    mock_generate_tests_use_case,
    mock_generate_code_use_case,
    mock_execute_tests_use_case,
    sample_code_file,
):
    """TestAgentOrchestrator should handle empty test cases list."""
    mock_generate_tests_use_case.generate_tests = AsyncMock(return_value=[])
    orchestrator = TestAgentOrchestrator(
        generate_tests_use_case=mock_generate_tests_use_case,
        generate_code_use_case=mock_generate_code_use_case,
        execute_tests_use_case=mock_execute_tests_use_case,
    )

    result = await orchestrator.orchestrate_test_workflow(sample_code_file)

    assert isinstance(result, TestResult)
    # Should handle gracefully
```

```python
async def test_orchestrate_with_missing_requirements(
    mock_generate_tests_use_case,
    mock_generate_code_use_case,
    mock_execute_tests_use_case,
):
    """TestAgentOrchestrator should handle missing requirements in metadata."""
    code_file = CodeFile(
        path="test.py",
        content="def func(): pass",
        metadata={}  # No requirements
    )
    orchestrator = TestAgentOrchestrator(
        generate_tests_use_case=mock_generate_tests_use_case,
        generate_code_use_case=mock_generate_code_use_case,
        execute_tests_use_case=mock_execute_tests_use_case,
    )

    result = await orchestrator.orchestrate_test_workflow(code_file)

    assert isinstance(result, TestResult)
    # Should use empty string for requirements
```

```python
async def test_orchestrate_error_in_code_generation(
    mock_generate_tests_use_case,
    mock_generate_code_use_case,
    mock_execute_tests_use_case,
    sample_code_file,
):
    """TestAgentOrchestrator should handle errors in code generation step."""
    mock_generate_code_use_case.generate_code = AsyncMock(
        side_effect=Exception("Code generation failed")
    )
    orchestrator = TestAgentOrchestrator(
        generate_tests_use_case=mock_generate_tests_use_case,
        generate_code_use_case=mock_generate_code_use_case,
        execute_tests_use_case=mock_execute_tests_use_case,
    )

    with pytest.raises(Exception, match="Code generation failed"):
        await orchestrator.orchestrate_test_workflow(sample_code_file)
```

```python
async def test_orchestrate_error_in_test_execution(
    mock_generate_tests_use_case,
    mock_generate_code_use_case,
    mock_execute_tests_use_case,
    sample_code_file,
):
    """TestAgentOrchestrator should handle errors in test execution step."""
    mock_execute_tests_use_case.execute_tests = MagicMock(
        side_effect=Exception("Test execution failed")
    )
    orchestrator = TestAgentOrchestrator(
        generate_tests_use_case=mock_generate_tests_use_case,
        generate_code_use_case=mock_generate_code_use_case,
        execute_tests_use_case=mock_execute_tests_use_case,
    )

    with pytest.raises(Exception, match="Test execution failed"):
        await orchestrator.orchestrate_test_workflow(sample_code_file)
```

## Notes

Stage 4 test coverage is 100% which exceeds the 80% requirement. The orchestrator is well-tested with excellent coverage of workflow coordination. These additional tests would cover edge cases but do not block production deployment.

---

# Stage 5 Additional Test Scenarios

## Current Coverage

- ✅ Basic functionality tested (CLI entry point, orchestrator integration)
- ✅ Happy path covered (file processing, result output)
- ✅ Error handling tested (file not found, execution errors, failed tests)
- ✅ Edge cases covered (error output formatting, exit codes)

## Recommended Additional Tests

### CLI Edge Cases

```python
def test_cli_with_coverage_none(cli_runner, sample_code_file):
    """CLI should handle TestResult with coverage=None."""
    with patch(
        "src.presentation.cli.test_agent.main.create_orchestrator"
    ) as mock_create:
        mock_orch = AsyncMock()
        test_result = TestResult(
            status=TestStatus.PASSED,
            test_count=5,
            passed_count=5,
            failed_count=0,
            coverage=None,  # No coverage
        )
        mock_orch.orchestrate_test_workflow = AsyncMock(return_value=test_result)
        mock_create.return_value = mock_orch

        result = cli_runner.invoke(
            main, [str(sample_code_file)], catch_exceptions=False
        )

        assert result.exit_code == 0
        # Should not crash on None coverage
```

```python
def test_cli_with_many_errors(cli_runner, sample_code_file):
    """CLI should handle many error messages gracefully."""
    with patch(
        "src.presentation.cli.test_agent.main.create_orchestrator"
    ) as mock_create:
        mock_orch = AsyncMock()
        test_result = TestResult(
            status=TestStatus.FAILED,
            test_count=10,
            passed_count=0,
            failed_count=10,
            coverage=0.0,
            errors=[f"Error {i}" for i in range(20)],  # Many errors
        )
        mock_orch.orchestrate_test_workflow = AsyncMock(return_value=test_result)
        mock_create.return_value = mock_orch

        result = cli_runner.invoke(
            main, [str(sample_code_file)], catch_exceptions=False
        )

        assert result.exit_code == 1
        # Should limit displayed errors (currently shows first 5)
```

```python
def test_create_orchestrator_with_mocked_dependencies():
    """Test create_orchestrator with mocked dependencies."""
    with patch("src.presentation.cli.test_agent.main.get_llm_client") as mock_llm:
        mock_llm.return_value = AsyncMock()

        orchestrator = create_orchestrator()

        assert orchestrator is not None
        assert orchestrator.generate_tests_use_case is not None
        assert orchestrator.generate_code_use_case is not None
        assert orchestrator.execute_tests_use_case is not None
```

## Notes

Stage 5 test coverage is 96% which exceeds the 80% requirement. The CLI is well-tested with comprehensive integration tests. These additional tests would cover edge cases but do not block production deployment.

---

# Epic 26 Complete - Summary

All 5 stages have been implemented and reviewed:
- **Stage 1 (Domain Layer)**: 100% coverage ✅
- **Stage 2 (Infrastructure Layer)**: 90% coverage ✅
- **Stage 3 (Application Layer - Use Cases)**: 88% coverage ✅
- **Stage 4 (Application Layer - Orchestrator)**: 100% coverage ✅
- **Stage 5 (Presentation Layer - CLI)**: 96% coverage ✅

**Overall Epic Coverage**: 90% (exceeds 80% requirement)

All acceptance criteria have been verified and met. The epic is production-ready.
