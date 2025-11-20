# Epic 27 Real Test Generation Test Guide

**Purpose:** Guide for testing real test generation by Test Agent with actual LLM service.

## Prerequisites

1. **LLM Service Running:**
   ```bash
   docker ps | grep llm-api
   # Should show llm-api-gigachat container running
   ```

2. **LLM Service Ready:**
   - Model must be fully loaded (can take 2-5 minutes)
   - Health check should pass: `curl http://localhost:8000/health`

3. **Environment Variable:**
   ```bash
   export LLM_URL=http://localhost:8000
   ```

## Running Tests

### Option 1: Wait for LLM and Test (Recommended)

```bash
LLM_URL=http://localhost:8000 python scripts/test_real_generation_wait.py
```

This script will:
- Wait for LLM service to be ready (up to 5 minutes)
- Run test generation on a simple Calculator module
- Display results and generated tests

### Option 2: Test Specific Module

```bash
# Test on medium module
LLM_URL=http://localhost:8000 python scripts/test_real_generation_wait.py \
  src/application/test_agent/services/code_chunker.py

# Test on large module
LLM_URL=http://localhost:8000 python scripts/test_real_generation_wait.py \
  src/presentation/bot/handlers/butler_handler.py
```

### Option 3: Direct Test (if LLM is already ready)

```bash
LLM_URL=http://localhost:8000 python scripts/test_real_generation.py
```

## Expected Results

### Successful Generation

```
================================================================================
GENERATION RESULTS
================================================================================
Status: PASSED
Tests generated: 8
Tests passed: 8
Tests failed: 0
Coverage: 85.5%

================================================================================
GENERATED TEST CASES (8)
================================================================================
Test 1: test_calculator_add
  Code length: 234 chars
  Preview: def test_calculator_add():
    """Test calculator addition."""
    calc = Calculator(5.0)
    result = calc.add(3.0)
    assert result == 8.0...

✅ TEST GENERATION SUCCESSFUL
✓ Generated 8 test(s)
✓ 8 test(s) passed
✓ Coverage: 85.5%
✓ Coverage target (80%) achieved!
```

### What to Check

1. **Test Count:** Should generate at least 3-5 tests for simple modules
2. **Test Quality:**
   - Tests should follow pytest conventions (`test_*` naming)
   - Tests should have assertions
   - Tests should be syntactically valid Python
3. **Coverage:** Should aim for >=80% coverage
4. **Execution:** Generated tests should be executable by pytest

## Troubleshooting

### LLM Service Not Available

**Error:** `LLM service not available: Connection refused`

**Solution:**
```bash
# Check if container is running
docker ps | grep llm-api

# Check container logs
docker logs llm-api-gigachat --tail 50

# Restart container if needed
docker restart llm-api-gigachat
```

### Model Still Loading

**Error:** `ReadError` or timeout

**Solution:**
- Wait 2-5 minutes for model to load
- Check logs: `docker logs llm-api-gigachat --tail 20`
- Look for "Application startup complete" or "Model loaded" messages

### Low Quality Tests

**Issue:** Generated tests are invalid or don't follow conventions

**Possible Causes:**
- LLM model not fully loaded
- LLM service using fallback client
- Model quality issues

**Solution:**
- Ensure GigaChat model is fully loaded
- Check LLM service logs for errors
- Try with simpler module first

## Test Modules

### Simple Module (Recommended for First Test)

The default test uses a `Calculator` class with:
- 5 methods (add, subtract, multiply, divide, reset)
- 2 utility functions (calculate_sum, calculate_average)
- Error handling (division by zero)

**Expected:** 6-10 tests, 80%+ coverage

### Medium Module

`src/application/test_agent/services/code_chunker.py`
- 482 lines, ~4K tokens
- Multiple classes and functions
- Complex AST parsing logic

**Expected:** 15-25 tests, may use chunking

### Large Module

`src/presentation/bot/handlers/butler_handler.py`
- 1,736 lines, ~16K tokens
- Will definitely use chunking
- May take 10-15 minutes to generate

**Expected:** 30-50+ tests, uses Epic 27 chunking features

## Performance Expectations

| Module Size | Generation Time | Tests Generated |
|-------------|----------------|----------------|
| Small (<500 lines) | 2-5 minutes | 5-15 tests |
| Medium (500-1000 lines) | 5-10 minutes | 15-30 tests |
| Large (>1000 lines) | 10-20 minutes | 30-50+ tests |

## Integration with CI/CD

For CI/CD environments:
1. Use `SKIP_INTEGRATION_TESTS=1` to skip if LLM unavailable
2. Integration tests are marked with `@pytest.mark.skipif(SKIP_INTEGRATION, ...)`
3. Real generation tests should run in dedicated LLM-enabled environments

## Next Steps

After successful test generation:
1. Review generated tests for quality
2. Check coverage reports
3. Verify tests execute successfully
4. Compare with manual test writing
5. Document any issues or improvements needed

---

**Scripts:**
- `scripts/test_real_generation.py` - Direct test (requires LLM ready)
- `scripts/test_real_generation_wait.py` - Waits for LLM, then tests

**Related Tests:**
- `tests/integration/application/test_agent/test_full_workflow.py` - Integration tests
- `scripts/test_quality_integrity.py` - Quality tests (no LLM needed)
- `scripts/test_large_module.py` - Large module tests (no LLM needed)
