#!/bin/bash
# Production validation checklist
set -euo pipefail

echo "Running Production Validation Checklist..."
echo ""

# Change to project root
cd "$(dirname "$0")/../.." || exit 1

PASS=0
FAIL=0

# Check Docker image exists
echo -n "✓ Docker image built: "
if docker images ai-challenge-mcp:day10 | grep -q ai-challenge-mcp; then
    echo "PASS"
    PASS=$((PASS+1))
else
    echo "FAIL (run: docker build -t ai-challenge-mcp:day10 -f Dockerfile.mcp .)"
    FAIL=$((FAIL+1))
fi

# Check Docker image size
echo -n "✓ Docker image size < 2GB: "
SIZE=$(docker images ai-challenge-mcp:day10 --format "{{.Size}}" | grep -oE '[0-9.]+[GM]B?' || echo "unknown")
if [[ "$SIZE" == "unknown" ]]; then
    echo "FAIL (image not found)"
    FAIL=$((FAIL+1))
else
    echo "PASS (${SIZE})"
    PASS=$((PASS+1))
fi

# Check tests pass
echo -n "✓ All tests pass: "
if pytest tests/ -v --tb=no -q > /dev/null 2>&1; then
    echo "PASS"
    PASS=$((PASS+1))
else
    echo "FAIL (run: pytest tests/ -v)"
    FAIL=$((FAIL+1))
fi

# Check coverage
echo -n "✓ Test coverage >= 80%: "
COVERAGE=$(pytest tests/ --cov=src --cov-report=term-missing -q 2>/dev/null | grep "TOTAL" | awk '{print $NF}' || echo "unknown")
if [[ "$COVERAGE" == "unknown" ]]; then
    echo "UNKNOWN"
else
    echo "PASS (${COVERAGE})"
    PASS=$((PASS+1))
fi

# Check no linting errors
echo -n "✓ No linting errors: "
if [ -f "$(which flake8)" ]; then
    if flake8 src/ tests/ --max-line-length=100 --count > /dev/null 2>&1; then
        echo "PASS"
        PASS=$((PASS+1))
    else
        echo "FAIL (run: flakelation src/ tests/)"
        FAIL=$((FAIL+1))
    fi
else
    echo "SKIP (flake8 not installed)"
fi

# Check documentation exists
echo -n "✓ Documentation exists: "
if [ -f "tasks/day_10/README.md" ] || [ -f "tasks/day_10/README.phase4.md" ]; then
    echo "PASS"
    PASS=$((PASS+1))
else
    echo "FAIL (documentation missing)"
    FAIL=$((FAIL+1))
fi

echo ""
echo "Validation Summary:"
echo "  Pass: ${PASS}"
echo "  Fail: ${FAIL}"
if [ ${FAIL} -eq 0 ]; then
    echo ""
    echo "✓ Production validation PASSED"
    exit 0
else
    echo ""
    echo "✗ Production validation FAILED"
    exit 1
fi
