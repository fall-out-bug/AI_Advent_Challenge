#!/bin/bash
# Script to setup ChadGPT environment with API key from api_key.txt

echo "🔧 Setting up ChadGPT environment..."
echo "==================================="

# Check if api_key.txt exists
if [ ! -f "../api_key.txt" ]; then
    echo "❌ api_key.txt file not found"
    echo "   Please create ../api_key.txt with format: chadgpt:your-key"
    exit 1
fi

echo "📄 Found api_key.txt file"

# Extract ChadGPT key
CHADGPT_KEY=$(grep "chadgpt:" ../api_key.txt | cut -d: -f2)

if [ -z "$CHADGPT_KEY" ]; then
    echo "❌ ChadGPT key not found in api_key.txt"
    echo "   Please add line: chadgpt:your-key"
    exit 1
fi

echo "✅ Found ChadGPT key in api_key.txt"

# Set environment variable
export CHADGPT_API_KEY="$CHADGPT_KEY"
echo "✅ CHADGPT_API_KEY is set"

# Install dependencies
echo "📦 Installing dependencies..."
poetry install

# Test configuration
echo "🧪 Testing configuration..."
poetry run python manage_providers.py test

echo "✅ ChadGPT environment is ready!"
echo ""
echo "🚀 Next steps:"
echo "   make demo-chadgpt-quick     - Run quick demo"
echo "   make demo-chadgpt           - Run full demo"
echo "   make chadgpt-models         - Show available models"
echo ""
echo "💡 To use in current shell, run:"
echo "   export CHADGPT_API_KEY=\"$CHADGPT_KEY\""
