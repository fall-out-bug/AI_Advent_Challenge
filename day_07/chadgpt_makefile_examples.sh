#!/usr/bin/env bash
# ChadGPT Makefile Usage Examples
# Following Python Zen principles: Simple, Explicit, Readable

# =============================================================================
# ChadGPT Makefile Usage Examples
# =============================================================================

echo "🌟 ChadGPT Makefile Usage Examples"
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -f "Makefile" ]; then
    echo "❌ Makefile not found. Please run this script from the day_07 directory."
    exit 1
fi

echo "📋 Available ChadGPT Commands:"
echo "=============================="
echo ""

echo "1️⃣ Basic Demo Commands:"
echo "   make demo-chadgpt-quick        - Quick demo (no API key required)"
echo "   make demo-chadgpt              - Full demo (requires API key)"
echo "   make demo-chadgpt-interactive  - Interactive demo"
echo "   make demo-chadgpt-comparison   - Compare with original system"
echo ""

echo "2️⃣ Model Management:"
echo "   make chadgpt-models            - Show available models"
echo "   make chadgpt-status           - Check configuration"
echo "   make chadgpt-recommend        - Get model recommendation"
echo ""

echo "3️⃣ Smart Recommendations:"
echo "   TASK='Create a web API' make chadgpt-recommend"
echo "   TASK='Create a web API' make chadgpt-recommend-speed"
echo "   TASK='Create a web API' make chadgpt-recommend-quality"
echo ""

echo "4️⃣ Setup and Maintenance:"
echo "   make setup-chadgpt             - Setup ChadGPT environment"
echo "   make dev-setup-chadgpt        - Development setup"
echo "   make clean-chadgpt            - Clean results"
echo "   make backup-chadgpt           - Backup results"
echo ""

echo "5️⃣ Advanced Usage:"
echo "   TASK='your task' make demo-chadgpt-task  - Demo with specific task"
echo "   make demo-chadgpt-all         - Run all demos"
echo ""

echo "🔧 Setup Instructions:"
echo "======================"
echo "1. Set API key: export CHADGPT_API_KEY='your-key'"
echo "2. Install dependencies: make install"
echo "3. Test setup: make chadgpt-status"
echo "4. Run demo: make demo-chadgpt-quick"
echo ""

echo "📝 Example Workflows:"
echo "===================="
echo ""

echo "Workflow 1: Quick Start"
echo "------------------------"
echo "make demo-chadgpt-quick"
echo ""

echo "Workflow 2: Full Setup"
echo "----------------------"
echo "export CHADGPT_API_KEY='your-key'"
echo "make setup-chadgpt"
echo "make demo-chadgpt"
echo ""

echo "Workflow 3: Smart Recommendations"
echo "----------------------------------"
echo "TASK='Create a REST API with authentication' make chadgpt-recommend"
echo "TASK='Create a REST API with authentication' make chadgpt-recommend-quality"
echo ""

echo "Workflow 4: Development"
echo "----------------------"
echo "make dev-setup-chadgpt"
echo "make chadgpt-models"
echo "TASK='Debug this code' make chadgpt-recommend"
echo ""

echo "Workflow 5: Complete Demo Suite"
echo "-------------------------------"
echo "export CHADGPT_API_KEY='your-key'"
echo "make demo-chadgpt-all"
echo ""

echo "🎯 Best Practices:"
echo "=================="
echo "• Always check API key: make chadgpt-status"
echo "• Use specific tasks for recommendations"
echo "• Clean results regularly: make clean-chadgpt"
echo "• Backup important results: make backup-chadgpt"
echo "• Start with quick demo: make demo-chadgpt-quick"
echo ""

echo "🚀 Ready to use ChadGPT Smart System!"
echo "Run 'make help' to see all available commands."
