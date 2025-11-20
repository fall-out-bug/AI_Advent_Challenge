# Epic 27 Test Agent - Validation and Testing Guide

## Overview

This guide provides comprehensive strategies to test and validate the enhanced Test Agent (Epic 27) to ensure it's useful and meets production requirements.

## Quick Start Testing

### 1. Run Existing E2E Scripts

The E2E scripts simulate real user workflows:

```bash
# Scenario 1: Medium-sized module
python scripts/e2e/epic_27/test_scenario_1_medium_module.py

# Scenario 2: Comparison with Cursor-agent
python scripts/e2e/epic_27/test_scenario_2_cursor_comparison.py

# Scenario 3: Large package
python scripts/e2e/epic_27/test_scenario_3_large_package.py
```

### 2. Use Epic 26 Test Samples

Test with known-good samples:

```bash
# Run verification script on Epic 26 samples
python scripts/verify_test_agent.py

# Or test individual samples
python -m src.presentation.cli.test_agent.main \
  docs/specs/epic_26/test_samples/03_shopping_cart.py \
  --save-tests

# Run generated tests
pytest workspace/generated_tests_*.py --cov=docs/specs/epic_26/test_samples/03_shopping_cart.py
```

## Comprehensive Testing Strategy

### Phase 1: Functional Validation

#### Test Small Modules (Backward Compatibility)

```bash
# Test that small modules still work as before (Epic 26 behavior)
python -m src.presentation.cli.test_agent.main \
  src/domain/test_agent/entities/code_file.py \
  --save-tests --show-tests

# Verify:
# - Tests generated successfully
# - No chunking occurs (should use Epic 26 logic)
# - Coverage >= 80%
```

#### Test Medium Modules (New Chunking Feature)

```bash
# Find a medium-sized module (200-500 lines)
python -m src.presentation.cli.test_agent.main \
  src/application/test_agent/orchestrators/test_agent_orchestrator.py \
  --save-tests

# Verify:
# - Chunking is used (check logs for "chunking" messages)
# - Multiple test files generated (if chunked)
# - Coverage aggregated across chunks
# - Coverage >= 80%
```

#### Test Large Modules (Stress Test)

```bash
# Test with a large module (>1000 lines)
# Example: Find a large module in your codebase
find src/ -name "*.py" -exec wc -l {} \; | sort -rn | head -5

# Test the largest module
python -m src.presentation.cli.test_agent.main \
  <path_to_large_module> \
  --save-tests

# Verify:
# - Chunking strategy selected automatically
# - No context limit errors
# - Tests generated for all chunks
# - Coverage aggregated correctly
```

### Phase 2: Quality Validation

#### Coverage Quality Check

```bash
# Generate tests and check coverage quality
python -m src.presentation.cli.test_agent.main \
  <module_path> \
  --save-tests

# Run with detailed coverage
pytest workspace/generated_tests_*.py \
  --cov=<module_path> \
  --cov-report=html \
  --cov-report=term-missing

# Open coverage report
firefox htmlcov/index.html

# Verify:
# - Coverage >= 80%
# - Critical paths covered (main functions, edge cases)
# - No obvious gaps in important logic
```

#### Test Quality Assessment

```bash
# Check generated test quality
pytest workspace/generated_tests_*.py -v

# Verify:
# - Tests are readable and well-structured
# - Tests follow pytest conventions
# - Tests have meaningful names
# - Tests cover edge cases (None, empty, invalid inputs)
# - Tests have proper assertions
```

### Phase 3: Comparison Testing

#### Compare with Cursor-agent

```bash
# If you have Cursor-generated tests for a module:
# 1. Run local Test Agent
python -m src.presentation.cli.test_agent.main \
  <module_with_cursor_tests> \
  --save-tests

# 2. Run both test suites
pytest <cursor_test_file> --cov=<module> --cov-report=term
pytest workspace/generated_tests_*.py --cov=<module> --cov-report=term

# 3. Compare:
# - Coverage percentages (should be comparable)
# - Test count (local should be reasonable)
# - Test quality (both should be good)
```

#### Compare with Manual Tests

```bash
# If you have manually written tests:
# 1. Generate tests with Test Agent
python -m src.presentation.cli.test_agent.main <module> --save-tests

# 2. Compare coverage
pytest <manual_tests> --cov=<module>
pytest workspace/generated_tests_*.py --cov=<module>

# 3. Check if Test Agent found cases you missed
```

### Phase 4: Performance Testing

#### Measure Generation Time

```bash
# Time test generation
time python -m src.presentation.cli.test_agent.main \
  <module_path> \
  --save-tests

# Expected:
# - Small modules: < 30 seconds
# - Medium modules: < 2 minutes
# - Large modules: < 5 minutes (with chunking)
```

#### Measure Token Usage

```bash
# Check logs for token counts
python -m src.presentation.cli.test_agent.main <module> 2>&1 | grep -i token

# Verify:
# - Token counts are reasonable
# - No token limit errors
# - Chunking reduces token usage per request
```

### Phase 5: Edge Case Testing

#### Test Various Code Structures

```bash
# Test function-based code
python -m src.presentation.cli.test_agent.main \
  <module_with_many_functions> \
  --save-tests

# Test class-based code
python -m src.presentation.cli.test_agent.main \
  <module_with_classes> \
  --save-tests

# Test mixed code
python -m src.presentation.cli.test_agent.main \
  <module_with_functions_and_classes> \
  --save-tests

# Verify:
# - Appropriate chunking strategy selected
# - Tests generated for all structures
# - Coverage maintained
```

#### Test Error Handling

```bash
# Test with invalid file
python -m src.presentation.cli.test_agent.main \
  /nonexistent/file.py

# Test with empty file
echo "" > empty.py
python -m src.presentation.cli.test_agent.main empty.py

# Test with syntax errors
echo "def broken(" > broken.py
python -m src.presentation.cli.test_agent.main broken.py

# Verify:
# - Graceful error handling
# - Clear error messages
# - No crashes
```

## Real-World Testing Scenarios

### Scenario 1: New Feature Development

```bash
# 1. Write new feature code
# 2. Generate tests immediately
python -m src.presentation.cli.test_agent.main \
  src/your_new_feature.py \
  --save-tests

# 3. Review generated tests
cat workspace/generated_tests_*.py

# 4. Run tests
pytest workspace/generated_tests_*.py -v

# 5. Check coverage
pytest workspace/generated_tests_*.py \
  --cov=src/your_new_feature.py \
  --cov-report=term

# 6. Use as starting point, enhance as needed
```

### Scenario 2: Legacy Code Testing

```bash
# 1. Find untested legacy module
find src/ -name "*.py" | xargs grep -L "test_"

# 2. Generate tests
python -m src.presentation.cli.test_agent.main \
  <legacy_module> \
  --save-tests

# 3. Run tests to discover issues
pytest workspace/generated_tests_*.py -v

# 4. Fix code issues found by tests
# 5. Regenerate tests if needed
```

### Scenario 3: Refactoring Support

```bash
# 1. Generate tests before refactoring
python -m src.presentation.cli.test_agent.main \
  <module_to_refactor> \
  --save-tests

# 2. Run tests to establish baseline
pytest workspace/generated_tests_*.py

# 3. Refactor code
# 4. Run tests again to ensure nothing broke
pytest workspace/generated_tests_*.py

# 5. Update tests if interface changed
```

## Metrics to Track

### Coverage Metrics

- **Overall Coverage**: Should be >= 80%
- **Line Coverage**: All important lines covered
- **Branch Coverage**: Edge cases covered
- **Function Coverage**: All public functions tested

### Quality Metrics

- **Test Count**: Reasonable number of tests
- **Test Pass Rate**: 100% (all tests should pass)
- **Test Readability**: Tests should be understandable
- **Test Maintainability**: Tests should be easy to update

### Performance Metrics

- **Generation Time**: Should be reasonable (< 5 min for large modules)
- **Token Usage**: Should be within limits
- **Memory Usage**: Should not cause OOM errors

## Validation Checklist

### Before Using in Production

- [ ] E2E scripts pass (all 3 scenarios)
- [ ] Small modules work (backward compatibility)
- [ ] Medium modules use chunking correctly
- [ ] Large modules don't hit context limits
- [ ] Coverage >= 80% for test modules
- [ ] Generated tests are readable
- [ ] Generated tests follow pytest conventions
- [ ] Error handling works gracefully
- [ ] Performance is acceptable
- [ ] Comparison with Cursor-agent shows comparable results

### Ongoing Monitoring

- [ ] Track coverage trends over time
- [ ] Monitor generation times
- [ ] Collect user feedback
- [ ] Track test quality metrics
- [ ] Monitor error rates

## Troubleshooting

### Low Coverage

**Problem**: Coverage < 80%

**Solutions**:
- Check if module is too complex
- Verify chunking is working
- Check if summarization is losing context
- Try different chunking strategies

### Context Limit Errors

**Problem**: "Context window exceeded" errors

**Solutions**:
- Verify chunking is enabled
- Check token counter accuracy
- Reduce chunk size if needed
- Use more aggressive summarization

### Poor Test Quality

**Problem**: Generated tests are not useful

**Solutions**:
- Check LLM prompt quality
- Verify code structure is clear
- Ensure module has good docstrings
- Try regenerating with different temperature

### Slow Generation

**Problem**: Test generation takes too long

**Solutions**:
- Check LLM service performance
- Verify network connectivity
- Check if chunking is working (should be faster)
- Monitor token usage

## Best Practices

1. **Start Small**: Test with small modules first
2. **Incremental Testing**: Gradually test larger modules
3. **Review Generated Tests**: Always review before committing
4. **Enhance as Needed**: Use generated tests as starting point
5. **Track Metrics**: Monitor coverage and quality over time
6. **Compare Results**: Compare with other test generation tools
7. **Collect Feedback**: Gather user feedback on test quality

## Example Test Session

```bash
# 1. Test a small module (quick validation)
python -m src.presentation.cli.test_agent.main \
  src/domain/test_agent/entities/code_file.py \
  --save-tests

pytest workspace/generated_tests_*.py \
  --cov=src/domain/test_agent/entities/code_file.py \
  --cov-report=term

# 2. Test a medium module (chunking validation)
python -m src.presentation.cli.test_agent.main \
  src/application/test_agent/orchestrators/test_agent_orchestrator.py \
  --save-tests

pytest workspace/generated_tests_*.py \
  --cov=src/application/test_agent/orchestrators/test_agent_orchestrator.py \
  --cov-report=term

# 3. Run E2E scenarios
python scripts/e2e/epic_27/test_scenario_1_medium_module.py
python scripts/e2e/epic_27/test_scenario_2_cursor_comparison.py
python scripts/e2e/epic_27/test_scenario_3_large_package.py

# 4. Verify overall system
python scripts/verify_test_agent.py
```

## Success Criteria

The Test Agent is considered useful if:

1. ✅ **Coverage**: Achieves >= 80% coverage on test modules
2. ✅ **Quality**: Generated tests are readable and maintainable
3. ✅ **Speed**: Generates tests in reasonable time (< 5 min for large)
4. ✅ **Reliability**: Works consistently across different modules
5. ✅ **Compatibility**: Maintains backward compatibility with Epic 26
6. ✅ **Scalability**: Handles large modules without errors
7. ✅ **Usability**: Easy to use and integrate into workflow

## Next Steps

After validation:

1. **Integrate into Workflow**: Add to CI/CD pipeline
2. **Train Team**: Share best practices with team
3. **Monitor Usage**: Track adoption and feedback
4. **Iterate**: Improve based on real-world usage
5. **Document**: Update documentation with learnings
