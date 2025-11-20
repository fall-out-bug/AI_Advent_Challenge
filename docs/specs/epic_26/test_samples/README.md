# Test Agent - Sample Input Files

This directory contains sample Python code files to test the Test Agent functionality.

## Test Agent Workflow

The Test Agent accepts a Python code file and:
1. **Analyzes** the code structure
2. **Generates** comprehensive pytest test cases
3. **Executes** the generated tests
4. **Reports** test results and coverage

## Sample Files

### Level 1: Simple Functions (Easy)

#### `01_simple_functions.py`
```python
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def subtract(a: int, b: int) -> int:
    """Subtract b from a."""
    return a - b
```

**Expected**: Agent generates basic test cases for both functions.

#### `02_calculator.py`
```python
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

**Expected**: Agent generates tests including edge case for division by zero.

### Level 2: Classes (Medium)

#### `03_shopping_cart.py`
```python
class ShoppingCart:
    """Shopping cart implementation."""

    def __init__(self):
        self.items: list[dict] = []

    def add_item(self, item: dict) -> None:
        """Add item to cart."""
        self.items.append(item)

    def remove_item(self, item_id: str) -> None:
        """Remove item by ID."""
        self.items = [item for item in self.items if item.get("id") != item_id]

    def get_total(self, tax_rate: float = 0.1) -> float:
        """Get total with tax."""
        subtotal = sum(item.get("price", 0) for item in self.items)
        return subtotal * (1 + tax_rate)

    def is_empty(self) -> bool:
        """Check if cart is empty."""
        return len(self.items) == 0
```

**Expected**: Agent generates tests for all methods, including edge cases (empty cart, etc.).

### Level 3: Complex Logic (Hard)

#### `04_data_processor.py`
```python
from typing import List, Optional

def filter_even(numbers: List[int]) -> List[int]:
    """Filter even numbers from list."""
    return [n for n in numbers if n % 2 == 0]

def calculate_average(numbers: List[float]) -> float:
    """Calculate average of numbers."""
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)

def find_max(numbers: List[int]) -> Optional[int]:
    """Find maximum value in list."""
    if not numbers:
        return None
    return max(numbers)

def process_data(data: List[dict], filter_key: str, value: any) -> List[dict]:
    """Filter data by key-value pair."""
    return [item for item in data if item.get(filter_key) == value]
```

**Expected**: Agent generates tests for edge cases (empty lists, None values, etc.).

### Level 4: Real Project Code (Integration)

#### Examples from existing codebase:

1. **Domain Entity** (`src/domain/test_agent/entities/code_file.py`)
   - Test Agent should generate tests for CodeFile entity
   - Tests should cover validation, metadata handling

2. **Use Case** (`src/application/test_agent/use_cases/generate_tests_use_case.py`)
   - Test Agent should generate tests for GenerateTestsUseCase
   - Tests should cover LLM integration, validation logic

3. **Infrastructure Adapter** (`src/infrastructure/test_agent/adapters/pytest_executor.py`)
   - Test Agent should generate tests for TestExecutor
   - Tests should cover pytest execution, error handling

## Testing Strategy

### Phase 1: Simple Examples (Validation)
Test with simple functions to validate basic functionality:
```bash
python -m src.presentation.cli.test_agent.main docs/specs/epic_26/test_samples/01_simple_functions.py
```

### Phase 2: Complex Examples (Quality)
Test with classes and complex logic to check test quality:
```bash
python -m src.presentation.cli.test_agent.main docs/specs/epic_26/test_samples/03_shopping_cart.py
```

### Phase 3: Real Code (Integration)
Test with actual project files to verify integration:
```bash
python -m src.presentation.cli.test_agent.main src/domain/test_agent/entities/code_file.py
```

## Expected Test Quality

For each input file, Test Agent should generate:

1. **Complete Coverage**:
   - Tests for all public functions/methods
   - Tests for edge cases (empty inputs, None values, errors)
   - Tests for boundary conditions

2. **Valid pytest Syntax**:
   - `def test_*` naming convention
   - pytest assertions (`assert`)
   - Proper fixtures if needed

3. **Good Test Quality**:
   - Descriptive test names
   - Clear assertions
   - Appropriate test data

4. **Coverage ≥80%**:
   - Generated tests should achieve ≥80% coverage
   - All branches should be tested

## Success Criteria

Test Agent is successful if:

- ✅ Generates valid pytest code (AST validation passes)
- ✅ Generated tests execute without syntax errors
- ✅ Test coverage ≥80% for target module
- ✅ Tests cover edge cases and error paths
- ✅ Tests follow pytest best practices
