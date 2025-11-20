# Testing Guide for Epic 27 Enhanced Test Agent

## Overview

This guide provides comprehensive instructions for testing the enhanced Test Agent (Epic 27) to verify it works correctly with large modules, chunking, summarization, and coverage aggregation.

## Quick Start Testing

### 1. Run E2E User Simulation Scripts (Recommended)

The easiest way to test the agent is using the pre-built E2E scripts that simulate real user workflows:

```bash
# Scenario 1: Medium-sized module
python scripts/e2e/epic_27/test_scenario_1_medium_module.py

# Scenario 2: Compare with Cursor-agent tests
python scripts/e2e/epic_27/test_scenario_2_cursor_comparison.py

# Scenario 3: Large package (multiple modules)
python scripts/e2e/epic_27/test_scenario_3_large_package.py

# Run all scenarios
for script in scripts/e2e/epic_27/test_scenario_*.py; do
    echo "Running $script..."
    python "$script" || echo "FAILED: $script"
done
```

**What to verify:**
- ✅ Scripts complete without errors
- ✅ Tests are generated and saved
- ✅ Generated tests execute with pytest
- ✅ Coverage >= 80% (for Scenario 1)
- ✅ No context limit errors (for Scenario 3)

### 2. Run Integration Tests

```bash
# Run full workflow integration tests
pytest tests/integration/application/test_agent/test_full_workflow.py -v

# Expected: 5 tests passing
```

**What to verify:**
- ✅ All 5 integration tests pass
- ✅ Tests generate successfully
- ✅ Generated tests execute
- ✅ Coverage reaches 80%

### 3. Manual Testing with CLI

#### Test Small Module (Epic 26 compatibility)

```bash
# Create a small test module
cat > /tmp/test_small.py << 'EOF'
"""Small module for testing."""

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b
EOF

# Run Test Agent
python -m src.presentation.cli.test_agent.main /tmp/test_small.py --save-tests

# Run generated tests
pytest workspace/generated_tests_*.py -v --cov=/tmp/test_small.py --cov-report=term
```

**What to verify:**
- ✅ Tests generated successfully
- ✅ Tests execute and pass
- ✅ Coverage >= 80%
- ✅ No chunking needed (small module)

#### Test Medium Module (Chunking)

```bash
# Create a medium-sized module (multiple classes/functions)
cat > /tmp/test_medium.py << 'EOF'
"""Medium module for testing chunking."""

class Calculator:
    def __init__(self, value: float = 0.0):
        self.value = value

    def add(self, n: float) -> float:
        self.value += n
        return self.value

    def subtract(self, n: float) -> float:
        self.value -= n
        return self.value

    def multiply(self, n: float) -> float:
        self.value *= n
        return self.value

    def divide(self, n: float) -> float:
        if n == 0:
            raise ValueError("Division by zero")
        self.value /= n
        return self.value

class Statistics:
    @staticmethod
    def mean(numbers: list[float]) -> float:
        return sum(numbers) / len(numbers) if numbers else 0.0

    @staticmethod
    def median(numbers: list[float]) -> float:
        sorted_nums = sorted(numbers)
        n = len(sorted_nums)
        if n % 2 == 0:
            return (sorted_nums[n//2 - 1] + sorted_nums[n//2]) / 2
        return sorted_nums[n//2]
EOF

# Run Test Agent
python -m src.presentation.cli.test_agent.main /tmp/test_medium.py --save-tests

# Check logs for chunking activity
# Look for: "Chunking module" or "Using chunking strategy"

# Run generated tests
pytest workspace/generated_tests_*.py -v --cov=/tmp/test_medium.py --cov-report=term
```

**What to verify:**
- ✅ Tests generated successfully
- ✅ Chunking was used (check logs)
- ✅ Tests execute and pass
- ✅ Coverage >= 80%

#### Test Large Package (Multiple Modules)

```bash
# Create a package with multiple modules
mkdir -p /tmp/test_package
cat > /tmp/test_package/__init__.py << 'EOF'
"""Test package."""
EOF

cat > /tmp/test_package/module1.py << 'EOF'
"""Module 1."""

def function1():
    return "module1"
EOF

cat > /tmp/test_package/module2.py << 'EOF'
"""Module 2."""

def function2():
    return "module2"
EOF

# Run Test Agent on package
python -m src.presentation.cli.test_agent.main /tmp/test_package --save-tests

# Run generated tests
pytest workspace/generated_tests_*.py -v --cov=/tmp/test_package --cov-report=term
```

**What to verify:**
- ✅ Tests generated for all modules
- ✅ No context limit errors
- ✅ Tests execute successfully
- ✅ Coverage >= 80%

## Verification Checklist

### Functional Verification

- [ ] **Small modules work** (Epic 26 compatibility)
  - Generate tests for a small module (< 100 lines)
  - Verify tests execute and pass
  - Verify coverage >= 80%

- [ ] **Medium modules use chunking**
  - Generate tests for a medium module (200-500 lines)
  - Check logs for chunking activity
  - Verify tests execute and pass
  - Verify coverage >= 80%

- [ ] **Large packages work**
  - Generate tests for a package with multiple modules
  - Verify no context limit errors
  - Verify tests generated for all modules
  - Verify coverage >= 80%

- [ ] **Chunking strategies work**
  - Function-based: Groups by functions
  - Class-based: Groups by classes
  - Sliding-window: Overlapping chunks

- [ ] **Coverage aggregation works**
  - Generate tests for chunked module
  - Verify overall coverage >= 80%
  - Verify gap identification works

### Quality Verification

- [ ] **Generated tests follow standards**
  - Type hints present
  - Docstrings present
  - PEP 8 compliant
  - pytest syntax correct

- [ ] **No regressions**
  - Run Epic 26 regression tests: `pytest tests/ -k "test_agent" -v`
  - All should pass (116 passed, 4 skipped expected)

- [ ] **Security**
  - No sensitive data in logs
  - No token leakage
  - Safe subprocess usage

## Production Verification

### Health Check

```bash
# Check if service is running (if deployed)
docker ps | grep test-agent

# Check health endpoint (if available)
curl http://localhost:8000/health
```

### Monitor Logs

```bash
# Watch for chunking activity
docker logs -f test-agent | grep -i "chunk"

# Watch for errors
docker logs -f test-agent | grep -i "error"

# Watch for coverage reports
docker logs -f test-agent | grep -i "coverage"
```

### Test in Production

```bash
# Use production CLI (if available)
python -m src.presentation.cli.test_agent.main <module_path> --save-tests

# Verify generated tests
pytest workspace/generated_tests_*.py -v --cov=<module_path> --cov-report=term
```

## Troubleshooting

### Issue: Tests not generating

**Check:**
- LLM service is running: `docker ps | grep llm-api-gigachat`
- LLM URL configured: Check environment variables
- Token counter working: Check logs for token counting errors

### Issue: Coverage below 80%

**Possible causes:**
- Module too complex
- Chunking strategy not optimal
- LLM generation quality

**Solutions:**
- Try different chunking strategy
- Check coverage gaps: Look for `identify_gaps` output
- Verify generated tests cover main public APIs

### Issue: Context limit errors

**Check:**
- Token counting accuracy
- Chunking strategy selection
- Summarization working

**Solutions:**
- Verify token counter uses GigaChat tokenizer
- Check chunk size (should be < 3600 tokens with 10% buffer)
- Verify summarization preserves critical context

## Performance Testing

### Measure Generation Time

```bash
time python -m src.presentation.cli.test_agent.main <module_path> --save-tests
```

**Expected:**
- Small module: < 30 seconds
- Medium module: < 2 minutes
- Large package: < 5 minutes

### Measure Test Execution Time

```bash
time pytest workspace/generated_tests_*.py -v
```

**Expected:**
- Tests execute in reasonable time (< 1 minute for typical module)

## Success Criteria

The enhanced Test Agent is working correctly if:

1. ✅ **E2E scripts pass** - All 3 scenarios complete successfully
2. ✅ **Integration tests pass** - All 5 workflow tests pass
3. ✅ **Small modules work** - Epic 26 compatibility maintained
4. ✅ **Medium modules chunk** - Chunking activates and works
5. ✅ **Large packages work** - No context limit errors
6. ✅ **Coverage >= 80%** - Generated tests achieve target coverage
7. ✅ **Tests execute** - Generated tests run without manual fixes
8. ✅ **No regressions** - Epic 26 tests still pass

## Next Steps After Testing

If all tests pass:
- ✅ Agent is ready for production use
- ✅ Monitor production metrics
- ✅ Collect user feedback

If issues found:
- Review error logs
- Check specific component (chunker, summarizer, aggregator)
- Run component-specific tests
- Report issues with detailed logs
