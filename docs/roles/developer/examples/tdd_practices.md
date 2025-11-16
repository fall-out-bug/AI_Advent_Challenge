# TDD Practices: Red-Green-Refactor

## Example: Payment Validation (EP23)

### Step 1: RED (Write Failing Test)
```python
# tests/unit/domain/test_payment.py
import pytest
from src.domain.entities.payment import Payment

def test_payment_amount_must_be_positive():
    """Payment with negative amount should raise ValueError."""
    with pytest.raises(ValueError, match="Amount must be positive"):
        Payment(amount_cents=-100, currency="USD")

def test_payment_currency_must_be_valid():
    """Payment with invalid currency should raise ValueError."""
    with pytest.raises(ValueError, match="Invalid currency"):
        Payment(amount_cents=1000, currency="XXX")
```
**Run:** `pytest tests/unit/domain/test_payment.py`  
**Result:** ❌ FAIL (Payment class doesn't exist yet)

### Step 2: GREEN (Minimal Implementation)
```python
# src/domain/entities/payment.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Payment:
    amount_cents: int
    currency: str
    transaction_id: Optional[str] = None
    
    def __post_init__(self) -> None:
        if self.amount_cents <= 0:
            raise ValueError("Amount must be positive")
        if self.currency not in ["USD", "EUR", "GBP"]:
            raise ValueError(f"Invalid currency: {self.currency}")
```
**Run:** `pytest tests/unit/domain/test_payment.py`  
**Result:** ✅ PASS (tests pass, implementation works)

### Step 3: REFACTOR (Improve Design)
```python
# src/domain/entities/payment.py
from dataclasses import dataclass
from typing import Optional

SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP"]

@dataclass
class Payment:
    """Payment entity with validation."""
    amount_cents: int
    currency: str
    transaction_id: Optional[str] = None
    
    def __post_init__(self) -> None:
        self._validate()
    
    def _validate(self) -> None:
        """Validate payment attributes."""
        if self.amount_cents <= 0:
            raise ValueError("Amount must be positive")
        if self.currency not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Invalid currency: {self.currency}")
```
**Run:** `pytest tests/unit/domain/test_payment.py`  
**Result:** ✅ PASS (cleaner code, tests still pass)

## TDD Benefits
- ✅ Tests drive design (simpler interfaces)
- ✅ High confidence (tests written before code)
- ✅ Fast feedback (catch bugs immediately)
- ✅ Living documentation (tests show usage)

**Coverage:** `pytest --cov=src/domain tests/unit/domain/`  
**Expected:** 100% domain layer coverage
