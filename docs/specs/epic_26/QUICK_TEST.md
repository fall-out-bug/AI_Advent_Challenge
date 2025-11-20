# Epic 26 - Quick Test Guide

## 🚀 Quick Start Testing

### Prerequisites Check

```bash
# 1. Check Qwen is running
curl http://localhost:8000/health || echo "⚠️  Qwen not running - start it first!"

# 2. Check pytest is installed
pytest --version || echo "⚠️  Install pytest: pip install pytest pytest-cov"

# 3. Activate environment
source venv/bin/activate
```

### Automated Tests (Fast)

```bash
# Run all unit + integration tests (mocked, fast)
pytest tests/unit/test_agent/ tests/integration/test_agent/ -v

# Expected: All tests pass, coverage ≥80%
```

### E2E Test with Real Qwen (Requires Qwen Running)

```bash
# Run E2E tests (real LLM calls, slower)
pytest tests/e2e/test_agent/ -v -m e2e

# Expected: Agent generates tests, executes them, reports coverage
```

### Manual CLI Test (5 minutes)

```bash
# 1. Create test file
cat > /tmp/test_sample.py << 'EOF'
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b
EOF

# 2. Run test agent
python -m src.presentation.cli.test_agent.main /tmp/test_sample.py

# 3. Verify output:
#    ✓ Test Status: PASSED
#    Tests: X total, X passed, 0 failed
#    Coverage: XX.X%
#    Exit code: 0
```

### Acceptance Criteria Quick Check

```bash
# AC1: Test generation with pytest patterns
python -m src.presentation.cli.test_agent.main /tmp/test_sample.py
# ✅ Check: Generated tests use `def test_*` and `assert`

# AC2: Clean Architecture validation
# ✅ Check: No layer violations in generated code (if code generation used)

# AC3: Test execution and coverage
# ✅ Check: Output shows test counts and coverage percentage

# AC4: Local Qwen only
netstat -an | grep 8000  # Should see localhost:8000 connections only

# AC5: Coverage ≥80%
# ✅ Check: Coverage percentage in output is ≥80%
```

## 📊 Expected Results

### Successful Run Output

```
✓ Test Status: PASSED
Tests: 5 total, 5 passed, 0 failed
Coverage: 85.5%
```

### Exit Codes

- `0` = Tests passed
- `1` = Tests failed or error occurred

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| `Connection refused` | Start Qwen: `curl http://localhost:8000/health` |
| `pytest not found` | Install: `pip install pytest pytest-cov` |
| `Low coverage` | Check generated tests cover all functions |
| `Syntax errors` | AST validation should catch these |

## 📝 Full Testing Guide

See `TESTING_GUIDE.md` for comprehensive testing scenarios and examples.
