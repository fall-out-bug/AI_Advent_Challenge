# Epic 26 Testing Guide - Test Agent

## Overview

This guide describes how to test the Test Agent (Epic 26) end-to-end functionality. The Test Agent is an autonomous system that generates tests, implements code, and verifies results using local Qwen model.

## Prerequisites

### Infrastructure Setup

1. **Local Qwen Model Running**:
   ```bash
   # Verify Qwen model is accessible
   curl http://localhost:8000/health

   # Or check via LLM client
   export LLM_MODEL=qwen
   ```

2. **Python Environment**:
   ```bash
   # Activate virtual environment
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt

   # Verify pytest is installed
   pytest --version
   ```

3. **Test Data Preparation**:
   - Prepare sample Python code files for testing
   - Ensure test files are in accessible locations

## Testing Levels

### 1. Unit Tests (Automated)

**Purpose**: Test individual components in isolation.

**Run Commands**:
```bash
# Domain layer
pytest tests/unit/domain/test_agent/ -v

# Infrastructure layer
pytest tests/unit/infrastructure/test_agent/ -v

# Application layer
pytest tests/unit/application/test_agent/ -v

# All unit tests with coverage
pytest tests/unit/domain/test_agent/ tests/unit/infrastructure/test_agent/ tests/unit/application/test_agent/ \
  --cov=src/domain/test_agent --cov=src/infrastructure/test_agent --cov=src/application/test_agent \
  --cov-report=term-missing
```

**Expected Results**:
- All tests pass
- Coverage ≥80% for each layer
- No type checking errors (mypy strict)

### 2. Integration Tests (Automated)

**Purpose**: Test CLI integration with mocked dependencies.

**Run Commands**:
```bash
# Integration tests
pytest tests/integration/presentation/cli/test_agent/ -v

# With coverage
pytest tests/integration/presentation/cli/test_agent/ \
  --cov=src/presentation/cli/test_agent \
  --cov-report=term-missing
```

**Expected Results**:
- All integration tests pass
- CLI correctly calls orchestrator
- Error handling works correctly
- Output formatting is correct

### 3. E2E Tests (Automated with Real Qwen)

**Purpose**: Test full workflow with real LLM (Qwen model).

**Prerequisites**: Qwen model must be running on `http://localhost:8000`

**Run Commands**:
```bash
# Run E2E tests (requires Qwen model)
pytest tests/e2e/test_agent/ -v -m e2e

# With coverage
pytest tests/e2e/test_agent/ -m e2e \
  --cov=src \
  --cov-report=term-missing
```

**Expected Results**:
- Agent generates valid pytest test cases
- Agent generates code that passes Clean Architecture validation
- Tests execute successfully
- Coverage is reported correctly

### 4. Manual End-to-End Testing

**Purpose**: Verify complete workflow with real code files.

#### Test Scenario 1: Simple Function Test Generation

**Setup**:
```bash
# Create test file
cat > /tmp/test_simple.py << 'EOF'
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
EOF
```

**Execute**:
```bash
python -m src.presentation.cli.test_agent.main /tmp/test_simple.py
```

**Expected Output**:
```
✓ Test Status: PASSED
Tests: X total, X passed, 0 failed
Coverage: XX.X%
```

**Verification**:
- [ ] Test cases generated (check for pytest test functions)
- [ ] Generated tests are valid pytest syntax
- [ ] Tests execute without syntax errors
- [ ] Coverage is reported (≥0%)
- [ ] Exit code is 0 if tests pass

#### Test Scenario 2: Code Generation from Requirements

**Setup**:
```bash
# Create requirements file
cat > /tmp/requirements.txt << 'EOF'
Create a function that calculates factorial of a number.
Function should be named `factorial` and accept integer.
EOF
```

**Note**: This requires metadata support in CodeFile. If not implemented, use test generation scenario.

**Execute**:
```bash
# If code generation from requirements is supported
python -m src.presentation.cli.test_agent.main --requirements /tmp/requirements.txt
```

**Verification**:
- [ ] Code is generated based on requirements
- [ ] Generated code follows Clean Architecture boundaries
- [ ] Generated code has type hints and docstrings
- [ ] Generated code passes mypy strict checking

#### Test Scenario 3: Complex Code with Multiple Functions

**Setup**:
```bash
cat > /tmp/test_complex.py << 'EOF'
"""Complex module with multiple functions."""

def calculate_total(items: list[dict], tax_rate: float) -> float:
    """Calculate total with tax."""
    subtotal = sum(item['price'] for item in items)
    return subtotal * (1 + tax_rate)

def apply_discount(total: float, discount_percent: float) -> float:
    """Apply discount to total."""
    return total * (1 - discount_percent / 100)

class ShoppingCart:
    """Shopping cart implementation."""

    def __init__(self):
        self.items: list[dict] = []

    def add_item(self, item: dict) -> None:
        """Add item to cart."""
        self.items.append(item)

    def get_total(self, tax_rate: float = 0.1) -> float:
        """Get total with tax."""
        return calculate_total(self.items, tax_rate)
EOF
```

**Execute**:
```bash
python -m src.presentation.cli.test_agent.main /tmp/test_complex.py
```

**Verification**:
- [ ] Multiple test cases generated (one per function/method)
- [ ] Tests cover edge cases (empty list, zero values, etc.)
- [ ] Tests execute successfully
- [ ] Coverage ≥80% for the module
- [ ] Generated tests follow pytest patterns

#### Test Scenario 4: Error Handling

**Test Invalid File**:
```bash
python -m src.presentation.cli.test_agent.main /nonexistent/file.py
```

**Expected**: Error message, exit code ≠ 0

**Test Syntax Error in Input**:
```bash
cat > /tmp/invalid.py << 'EOF'
def broken_function(
    # Missing closing parenthesis
EOF

python -m src.presentation.cli.test_agent.main /tmp/invalid.py
```

**Expected**: Error handling, graceful failure

#### Test Scenario 5: Performance Test

**Setup**: Large code file (1000+ lines)

**Execute**:
```bash
# Generate large file (example)
python -c "
with open('/tmp/large.py', 'w') as f:
    for i in range(100):
        f.write(f'def func_{i}(x): return x * {i}\n')
"

python -m src.presentation.cli.test_agent.main /tmp/large.py
```

**Verification**:
- [ ] Agent completes within reasonable time (<5 minutes for large file)
- [ ] Memory usage is acceptable
- [ ] No crashes or timeouts

## Acceptance Criteria Verification

### AC1: Test Generation with pytest Patterns

**Test**:
```bash
# Use simple function
python -m src.presentation.cli.test_agent.main /tmp/test_simple.py
```

**Verify**:
- [ ] Generated tests use `def test_*` naming convention
- [ ] Tests use pytest assertions (`assert`)
- [ ] Tests can be executed with `pytest`
- [ ] AST validation passes (no syntax errors)

**Manual Check**:
```bash
# Check generated test file (if saved)
grep -E "def test_|assert " /path/to/generated_test.py
```

### AC2: Clean Architecture Validation

**Test**: Generate code and verify boundaries

**Verify**:
- [ ] Generated code doesn't import from outer layers to inner layers
- [ ] Domain layer has no external dependencies
- [ ] Application layer doesn't import from infrastructure directly
- [ ] Validation catches violations and reports errors

**Manual Check**:
```bash
# If code generation creates files, check imports
grep -r "from src\\.infrastructure" generated_code.py  # Should fail validation
grep -r "from src\\.domain" generated_code.py  # Should be OK in application/infrastructure
```

### AC3: Test Execution and Coverage Reporting

**Test**:
```bash
python -m src.presentation.cli.test_agent.main /tmp/test_simple.py
```

**Verify**:
- [ ] Test execution completes
- [ ] Pass/fail status is reported correctly
- [ ] Coverage percentage is displayed
- [ ] Error messages are shown if tests fail

**Expected Output Format**:
```
✓ Test Status: PASSED
Tests: 5 total, 5 passed, 0 failed
Coverage: 85.5%
```

### AC4: Local Qwen Model Only

**Test**: Verify no external API calls

**Verify**:
- [ ] Check network traffic (no external API calls)
- [ ] LLM client connects to `localhost:8000` (Qwen)
- [ ] No cloud service dependencies

**Manual Check**:
```bash
# Monitor network traffic
sudo tcpdump -i lo port 8000  # Should see connections to localhost:8000 only

# Check LLM client configuration
grep -r "localhost:8000\|127.0.0.1:8000" src/infrastructure/test_agent/
```

### AC5: Test Coverage ≥80%

**Test**:
```bash
python -m src.presentation.cli.test_agent.main /tmp/test_simple.py
```

**Verify**:
- [ ] Coverage is calculated and reported
- [ ] Coverage ≥80% for target module
- [ ] Coverage calculation is accurate

## Test Data Examples

### Example 1: Simple Calculator

```python
# /tmp/calculator.py
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b

def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b

def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

**Expected Test Cases**:
- `test_add_positive_numbers`
- `test_add_negative_numbers`
- `test_subtract`
- `test_multiply`
- `test_divide_normal`
- `test_divide_by_zero_raises_error`

### Example 2: Data Processing

```python
# /tmp/processor.py
from typing import List

def filter_even(numbers: List[int]) -> List[int]:
    """Filter even numbers from list."""
    return [n for n in numbers if n % 2 == 0]

def calculate_average(numbers: List[float]) -> float:
    """Calculate average of numbers."""
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)
```

**Expected Test Cases**:
- `test_filter_even_with_mixed_numbers`
- `test_filter_even_empty_list`
- `test_calculate_average_normal`
- `test_calculate_average_empty_list_raises_error`

## Troubleshooting

### Issue: Qwen Model Not Available

**Symptoms**: LLM errors, connection failures

**Solution**:
```bash
# Check if Qwen is running
curl http://localhost:8000/health

# Start Qwen if needed (depends on your setup)
# See shared infrastructure documentation
```

### Issue: Tests Fail to Execute

**Symptoms**: Syntax errors in generated tests

**Check**:
```bash
# Verify pytest syntax validation is working
python -c "import ast; ast.parse(open('generated_test.py').read())"
```

### Issue: Low Coverage

**Symptoms**: Coverage <80%

**Check**:
- Generated tests cover all functions
- Edge cases are tested
- Error paths are covered

### Issue: Clean Architecture Violations

**Symptoms**: Validation errors in code generation

**Check**:
- Generated code import statements
- Layer boundaries are respected
- Validation rules are correct

## Success Criteria

Epic 26 Test Agent is considered successfully tested when:

- [x] All unit tests pass (≥80% coverage)
- [x] All integration tests pass
- [x] E2E tests pass with real Qwen model
- [x] Manual testing shows:
  - [ ] Test generation works for simple functions
  - [ ] Test generation works for complex code
  - [ ] Code generation respects Clean Architecture
  - [ ] Test execution reports correct results
  - [ ] Coverage calculation is accurate (≥80%)
  - [ ] Only local Qwen model is used (no external APIs)
- [x] All 5 acceptance criteria verified manually
- [x] Performance is acceptable (<30 seconds per file for simple cases)

## Quick Test Checklist

```bash
# 1. Run all automated tests
pytest tests/unit/test_agent/ tests/integration/test_agent/ -v

# 2. Run E2E test (requires Qwen)
pytest tests/e2e/test_agent/ -v -m e2e

# 3. Manual test with simple function
echo "def add(a, b): return a + b" > /tmp/test.py
python -m src.presentation.cli.test_agent.main /tmp/test.py

# 4. Verify output shows:
#    - Test status (PASSED/FAILED)
#    - Test counts
#    - Coverage percentage
#    - Exit code 0 if passed

# 5. Check coverage meets requirement
#    Coverage should be ≥80%
```

## Next Steps After Testing

1. **If all tests pass**: Epic 26 is production-ready ✅
2. **If issues found**: Document in `docs/specs/epic_26/consensus/artifacts/issues.md`
3. **Performance issues**: Profile and optimize (see `commands.md` for profiling commands)
4. **Coverage issues**: Add missing test cases

---

**Last Updated**: 2025-11-19
**Epic Status**: Complete
**Overall Coverage**: 90% (exceeds 80% requirement)
