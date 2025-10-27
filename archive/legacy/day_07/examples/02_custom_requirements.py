#!/usr/bin/env python3
"""Example 2: Custom Requirements

This example shows how to use custom requirements to guide code generation.
It demonstrates generating code with specific constraints and preferences.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import process_simple_task


async def main():
    """Run custom requirements example."""
    print("🚀 Example 2: Custom Requirements")
    print("=" * 50)

    # Define a task with specific requirements
    task_description = "Create a REST API client for a weather service"

    requirements = [
        "Use httpx library for HTTP requests",
        "Implement exponential backoff for retries",
        "Add proper error handling for HTTP errors",
        "Include type hints for all functions",
        "Add logging for debugging",
        "Handle rate limiting gracefully",
        "Return structured data (Pydantic models)",
    ]

    print(f"📝 Task: {task_description}")
    print("\n📋 Requirements:")
    for i, req in enumerate(requirements, 1):
        print(f"   {i}. {req}")

    print("\n⏳ Generating code...")

    try:
        # Process the task with custom requirements
        result = await process_simple_task(
            task_description=task_description,
            language="python",
            requirements=requirements,
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

            print("\n📊 Metadata:")
            print("-" * 30)
            metadata = result.generation_result.metadata
            print(f"• Complexity: {metadata.complexity}")
            print(f"• Lines of code: {metadata.lines_of_code}")
            print(f"• Estimated time: {metadata.estimated_time}")
            print(f"• Dependencies: {', '.join(metadata.dependencies)}")

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
