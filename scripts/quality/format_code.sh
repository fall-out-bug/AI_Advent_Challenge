#!/bin/bash
# Run black and isort on all Python files
# Following shell script best practices

set -euo pipefail

echo "🎨 Formatting Code"
echo "=================="
echo ""

# Format with black
echo "Running black..."
poetry run black src tests scripts

echo ""
echo "Running isort..."
poetry run isort src tests scripts

echo ""
echo "✅ Code formatting complete"
