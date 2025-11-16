# Coding Standards & Best Practices

## Python Code Standards (EP23 Payment Service)

### File Structure
```
src/
├── domain/           # Pure business logic
│   └── entities/
│       └── payment.py
├── application/      # Use cases
│   └── use_cases/
│       └── process_payment.py
└── infrastructure/   # External integrations
    └── adapters/
        └── stripe_adapter.py
```

### Code Style
```python
# ✅ GOOD: Clean, typed, documented
from typing import Optional
from dataclasses import dataclass

@dataclass
class Payment:
    """Payment entity following Clean Architecture.
    
    Attributes:
        amount_cents: Amount in cents (no floats for money!)
        currency: ISO 4217 code (USD, EUR, GBP)
        transaction_id: Unique transaction identifier
    """
    amount_cents: int
    currency: str
    transaction_id: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate payment data."""
        if self.amount_cents <= 0:
            raise ValueError("Amount must be positive")
        if self.currency not in ["USD", "EUR", "GBP"]:
            raise ValueError(f"Invalid currency: {self.currency}")

# ❌ BAD: No types, no validation, magic numbers
class Payment:
    def __init__(self, amount, currency):
        self.amount = amount  # Float? Int? Unclear
        self.currency = currency  # No validation
```

### Quality Checklist
- [x] Type hints: 100% coverage (`mypy --strict` passes)
- [x] Docstrings: All public functions/classes
- [x] Line length: ≤88 characters (Black default)
- [x] Function length: ≤15 lines where possible
- [x] No magic numbers (use constants)
- [x] No print() statements (use logging)
- [x] Test coverage: ≥80%

### Pre-Commit Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        args: [--line-length=88]
        
  - repo: https://github.com/PyCQA/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]
        
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        args: [--strict, --ignore-missing-imports]
        additional_dependencies: [types-requests]
```

**Usage:** `pre-commit install` → Auto-run on every commit
