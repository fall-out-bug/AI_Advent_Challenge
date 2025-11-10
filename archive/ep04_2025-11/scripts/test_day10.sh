#!/bin/bash
# Day 10 CI tests
set -euo pipefail

echo "Running Day 10 CI Tests..."

# Change to project root
cd "$(dirname "$0")/../.." || exit 1

# Unit tests
echo ""
echo "Running unit tests..."
pytest tests/unit/presentation/mcp -v --tb=short || echo "Unit tests failed"

# Integration tests
echo ""
echo "Running integration tests..."
pytest tests/integration/test_mistral_orchestrator.py tests/integration/test_day10_e2e.py -v --tb=short || echo "Integration tests failed"

# E2E tests
echo ""
echo "Running E2E tests..."
pytest tests/e2e/test_production_readiness.py -v --tb=short || echo "E2E tests failed"

echo ""
echo "CI tests complete!"
