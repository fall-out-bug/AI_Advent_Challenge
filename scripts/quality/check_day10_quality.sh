#!/bin/bash
# Check Day 10 code quality
set -euo pipefail

echo "Running Day 10 Code Quality Checks..."

# Change to project root
cd "$(dirname "$0")/../.." || exit 1

# Check Python syntax
echo ""
echo "Checking Python syntax..."
find src/presentation/mcp src/application/orchestrators/mistral_orchestrator.py -name "*.py" -exec python -m py_compile {} \;
echo "✓ Python syntax OK"

# Run flake8
if command -v flake8 &> /dev/null; then
    echo ""
    echo "Running flake8..."
    flake8 src/presentation/mcp src/application/orchestrators/mistral_orchestrator.py --max-line-length=100 --exclude=__pycache__ || true
else
    echo "Skipping flake8 (not installed)"
fi

# Run mypy type checking
if command -v mypy &> /dev/null; then
    echo ""
    echo "Running mypy type checks..."
    mypy src/presentation/mcp src/application/orchestrators/mistral_orchestrator.py --ignore-missing-imports --no-error-summary || true
else
    echo "Skipping mypy (not installed)"
fi

# Run vulture for dead code detection
if command -v vulture &> /dev/null; then
    echo ""
    echo "Checking for dead code with vulture..."
    vulture src/presentation/mcp src/application/orchestrators/mistral_orchestrator.py \
        --min-confidence 70 || true
else
    echo "Skipping vulture (not installed, install with: pip install vulture)"
fi

# Run autoflake to check for unused imports
if command -v autoflake &> /dev/null; then
    echo ""
    echo "Checking for unused imports with autoflake..."
    autoflake --check src/presentation/mcp src/application/orchestrators/mistral_orchestrator.py \
        --remove-all-unused-imports --recursive || true
else
    echo "Skipping autoflake (not installed, install with: pip install autoflake)"
fi

# Run bandit for security
if command -v bandit &> /dev/null; then
    echo ""
    echo "Running security scan with bandit..."
    bandit -r src/presentation/mcp src/application/orchestrators/ --severity-level medium --confidence-level medium || true
else
    echo "Skipping bandit (not installed)"
fi

echo ""
echo "Quality checks complete!"

