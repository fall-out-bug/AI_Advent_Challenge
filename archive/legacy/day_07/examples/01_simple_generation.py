#!/usr/bin/env python3
"""Example 1: Simple Code Generation

This example demonstrates basic code generation using the StarCoder Multi-Agent System.
It shows how to generate a simple Python function with tests.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import process_simple_task


async def main():
    """Run simple code generation example."""
    print("🚀 Example 1: Simple Code Generation")
    print("=" * 50)

    # Define a simple task
    task_description = "Create a function to calculate the factorial of a number"

    print(f"📝 Task: {task_description}")
    print("⏳ Generating code...")

    try:
        # Process the task
        result = await process_simple_task(
            task_description=task_description,
            language="python",
            requirements=["Include type hints", "Handle edge cases"],
        )

        if result.success:
            print("✅ Code generated successfully!")
            print(f"⏱️  Workflow time: {result.workflow_time:.2f}s")
            print(f"📊 Code quality score: {result.review_result.code_quality_score}/10")

            print("\n📄 Generated Code:")
            print("-" * 30)
            print(result.generation_result.generated_code)

            print("\n🧪 Generated Tests:")
            print("-" * 30)
            print(result.generation_result.tests)

            print("\n🔍 Review Issues:")
            print("-" * 30)
            for issue in result.review_result.issues:
                print(f"• {issue}")

            print("\n💡 Recommendations:")
            print("-" * 30)
            for rec in result.review_result.recommendations:
                print(f"• {rec}")

        else:
            print(f"❌ Task failed: {result.error_message}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n💡 Make sure the services are running:")
        print("   cd ../local_models && docker-compose up -d starcoder-chat")
        print("   docker-compose up -d")


if __name__ == "__main__":
    asyncio.run(main())
