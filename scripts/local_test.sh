#!/bin/bash
# Simple local testing script for Phase 2 consolidation

set -euo pipefail

echo "🧪 Running Phase 2 Local Tests..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Run tests
echo "📋 Running unit tests..."
if poetry run pytest src/tests/unit/ -v --tb=short; then
    echo -e "${GREEN}✅ Unit tests passed${NC}"
else
    echo -e "${RED}❌ Unit tests failed${NC}"
    exit 1
fi

echo ""
echo "📋 Running integration tests..."
if poetry run pytest src/tests/integration/ -v --tb=short; then
    echo -e "${GREEN}✅ Integration tests passed${NC}"
else
    echo -e "${RED}❌ Integration tests failed${NC}"
    exit 1
fi

echo ""
echo "📊 Getting test coverage..."
poetry run pytest --cov=src --cov-report=term-missing | tail -10

echo ""
echo -e "${GREEN}✅ All local tests passed!${NC}"

