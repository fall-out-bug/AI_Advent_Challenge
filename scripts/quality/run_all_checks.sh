#!/bin/bash
# Run all quality checks locally (tests, linters, coverage)
# Following shell script best practices: set -euo pipefail

set -euo pipefail

echo "🔍 Running All Quality Checks"
echo "=============================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run command and check result
run_check() {
    local name=$1
    local command=$2
    
    echo -e "${YELLOW}Running: ${name}${NC}"
    if eval "$command"; then
        echo -e "${GREEN}✓ ${name} passed${NC}\n"
    else
        echo -e "${RED}✗ ${name} failed${NC}\n"
        exit 1
    fi
}

# Run tests
run_check "Unit Tests" "poetry run pytest src/tests/unit -v"
run_check "Integration Tests" "poetry run pytest src/tests/integration -v --tb=short"

# Run linting
run_check "Flake8 Linting" "poetry run flake8 src"
run_check "MyPy Type Checking" "poetry run mypy src"
run_check "Bandit Security Scan" "poetry run bandit -r src"

# Check coverage
run_check "Coverage Check" "poetry run pytest src/tests --cov=src --cov-report=term --cov-fail-under=75"

# Format check (should not change files)
run_check "Code Format Check" "poetry run black --check src tests"
run_check "Import Sort Check" "poetry run isort --check-only src tests"

echo ""
echo -e "${GREEN}=============================="
echo "✓ All quality checks passed!"
echo "=============================="


