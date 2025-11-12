#!/bin/bash
# Fast pre-commit style checks (no tests)
# Following shell script best practices

set -euo pipefail

echo "⚡ Quick Quality Check"
echo "===================="
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

# Quick checks (no tests)
run_check "Flake8 Linting" "poetry run flake8 src --count --statistics"
run_check "Black Format Check" "poetry run black --check src"
run_check "Isort Import Check" "poetry run isort --check-only src"

echo ""
echo -e "${GREEN}===================="
echo "✓ Quick check passed!"
echo "===================="
