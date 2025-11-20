# Epic 26 - Testing Plan for Test Agent

## Overview

This document describes **what code we test** and **how to test the Test Agent** itself.

## Two Types of Testing

### 1. Testing Test Agent (The Implementation)

We test **the Test Agent implementation** to verify it works correctly:

- **Unit Tests**: Test individual components (entities, use cases, adapters)
- **Integration Tests**: Test CLI integration with mocked dependencies
- **E2E Tests**: Test full workflow with real Qwen model

**Location**: `tests/unit/test_agent/`, `tests/integration/test_agent/`, `tests/e2e/test_agent/`

### 2. Testing with Test Agent (Using the Agent)

We use **Test Agent to generate tests for sample code files**:

- **Input**: Python code files (functions, classes, etc.)
- **Output**: Generated pytest test cases
- **Validation**: Check if generated tests are valid and achieve ≥80% coverage

**Location**: `docs/specs/epic_26/test_samples/`

## Sample Input Files for Test Agent

### What Code Does Test Agent Process?

Test Agent accepts **any Python file** and generates tests for it. We provide sample files:

#### Simple Functions (Level 1 - Easy)

**File**: `docs/specs/epic_26/test_samples/01_simple_functions.py`
```python
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def subtract(a: int, b: int) -> int:
    """Subtract b from a."""
    return a - b
```

**Test Agent should generate**:
- `test_add_positive_numbers`
- `test_add_negative_numbers`
- `test_subtract_positive_numbers`
- `test_subtract_negative_numbers`

#### Calculator Functions (Level 2 - Medium)

**File**: `docs/specs/epic_26/test_samples/02_calculator.py`
```python
def add(a: float, b: float) -> float: ...
def subtract(a: float, b: float) -> float: ...
def multiply(a: float, b: float) -> float: ...
def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

**Test Agent should generate**:
- Tests for all four functions
- Edge case test: `test_divide_by_zero_raises_error`

#### Shopping Cart Class (Level 3 - Hard)

**File**: `docs/specs/epic_26/test_samples/03_shopping_cart.py`
```python
class ShoppingCart:
    def __init__(self): ...
    def add_item(self, item: dict): ...
    def remove_item(self, item_id: str): ...
    def get_total(self, tax_rate: float = 0.1) -> float: ...
    def is_empty(self) -> bool: ...
```

**Test Agent should generate**:
- Tests for all methods
- Edge cases: empty cart, removing non-existent item, etc.

#### Data Processing Functions (Level 4 - Complex)

**File**: `docs/specs/epic_26/test_samples/04_data_processor.py`
```python
def filter_even(numbers: List[int]) -> List[int]: ...
def calculate_average(numbers: List[float]) -> float: ...
def find_max(numbers: List[int]) -> Optional[int]: ...
def process_data(data: List[dict], filter_key: str, value: any): ...
```

**Test Agent should generate**:
- Tests for all functions
- Edge cases: empty lists, None values, invalid inputs

### Real Project Files (Integration Testing)

We can also test Test Agent on **actual project code**:

#### Option 1: Domain Entities
```bash
# Test on actual domain entity
python -m src.presentation.cli.test_agent.main \
  src/domain/test_agent/entities/code_file.py
```

**Expected**: Agent generates tests for CodeFile entity methods.

#### Option 2: Use Cases
```bash
# Test on actual use case
python -m src.presentation.cli.test_agent.main \
  src/application/test_agent/use_cases/generate_tests_use_case.py
```

**Expected**: Agent generates tests for GenerateTestsUseCase methods.

#### Option 3: Simple Utilities
```bash
# Test on simple utility functions
python -m src.presentation.cli.test_agent.main \
  src/domain/services/text_cleaner.py  # If exists
```

**Expected**: Agent generates tests for utility functions.

## Testing Workflow

### Step 1: Test Simple Examples (Validate Basic Functionality)

```bash
# Test with simple functions
python -m src.presentation.cli.test_agent.main \
  docs/specs/epic_26/test_samples/01_simple_functions.py

# Expected Output:
# ✓ Test Status: PASSED
# Tests: X total, X passed, 0 failed
# Coverage: XX.X%
```

**Verify**:
- [ ] Tests are generated (check for generated test file)
- [ ] Generated tests use `def test_*` naming
- [ ] Tests execute without syntax errors
- [ ] Coverage ≥80%

### Step 2: Test Complex Examples (Check Quality)

```bash
# Test with classes
python -m src.presentation.cli.test_agent.main \
  docs/specs/epic_26/test_samples/03_shopping_cart.py

# Expected Output:
# ✓ Test Status: PASSED
# Tests: X total, X passed, 0 failed
# Coverage: XX.X%
```

**Verify**:
- [ ] Tests cover all methods
- [ ] Tests include edge cases (empty cart, etc.)
- [ ] Tests use proper pytest patterns
- [ ] Coverage ≥80%

### Step 3: Test Real Project Files (Integration)

```bash
# Test on actual project code
python -m src.presentation.cli.test_agent.main \
  src/domain/test_agent/entities/code_file.py

# Expected Output:
# ✓ Test Status: PASSED
# Tests: X total, X passed, 0 failed
# Coverage: XX.X%
```

**Verify**:
- [ ] Agent can handle real project structure
- [ ] Generated tests respect Clean Architecture (no violations)
- [ ] Coverage meets requirements
- [ ] Tests are meaningful and useful

## Test Agent Capabilities

The Test Agent can generate tests for:

1. **Functions**: Simple and complex functions with parameters
2. **Classes**: Classes with methods, properties, and state
3. **Edge Cases**: Error handling, boundary conditions
4. **Type Hints**: Code with type annotations
5. **Docstrings**: Code with documentation

## What Test Agent CANNOT Do

- **External Dependencies**: Cannot test code with external API calls (needs mocking)
- **Database Operations**: Cannot test code that directly accesses databases
- **File System**: Cannot test code that modifies files outside test directory
- **Network Calls**: Cannot test code that makes HTTP requests
- **Async Code**: May have limitations with async/await patterns (depends on implementation)

## Success Metrics

Test Agent is successful if, for each input file:

- ✅ Generates valid pytest code (AST validation passes)
- ✅ Generated tests execute successfully (≥95% execution rate)
- ✅ Test coverage ≥80% for target module
- ✅ Tests follow pytest best practices
- ✅ Tests cover edge cases and error paths
- ✅ Generated tests are maintainable and readable

## Quick Test Checklist

```bash
# 1. Test simple functions
python -m src.presentation.cli.test_agent.main \
  docs/specs/epic_26/test_samples/01_simple_functions.py

# 2. Test calculator (with edge cases)
python -m src.presentation.cli.test_agent.main \
  docs/specs/epic_26/test_samples/02_calculator.py

# 3. Test class (complex logic)
python -m src.presentation.cli.test_agent.main \
  docs/specs/epic_26/test_samples/03_shopping_cart.py

# 4. Test data processing (complex types)
python -m src.presentation.cli.test_agent.main \
  docs/specs/epic_26/test_samples/04_data_processor.py

# 5. Test real project file (integration)
python -m src.presentation.cli.test_agent.main \
  src/domain/test_agent/entities/code_file.py
```

## Expected Output Format

For each test run, Test Agent should output:

```
✓ Test Status: PASSED
Tests: 5 total, 5 passed, 0 failed
Coverage: 85.5%
```

Or if tests fail:

```
✗ Test Status: FAILED
Tests: 5 total, 3 passed, 2 failed
Coverage: 60.0%

Errors:
  - test_divide_by_zero: AssertionError
  - test_calculate_average_empty: ValueError
```

---

**Summary**: Test Agent generates tests for **any Python code file** you provide. We test it on sample files (simple → complex) and real project files to verify it works correctly.
