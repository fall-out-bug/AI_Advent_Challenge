#!/usr/bin/env python3
"""Example 3: Batch Processing

This example demonstrates how to process multiple tasks in parallel
using the multi-agent system for efficient batch processing.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from communication.message_schema import OrchestratorRequest
from orchestrator import MultiAgentOrchestrator


async def process_batch_tasks(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process multiple tasks in parallel."""
    orchestrator = MultiAgentOrchestrator()
    results = []

    try:
        # Create tasks
        coroutines = []
        for task_data in tasks:
            request = OrchestratorRequest(
                task_description=task_data["description"],
                language=task_data.get("language", "python"),
                requirements=task_data.get("requirements", []),
            )
            coroutines.append(orchestrator.process_task(request))

        # Process all tasks in parallel
        print("⏳ Processing tasks in parallel...")
        task_results = await asyncio.gather(*coroutines, return_exceptions=True)

        # Process results
        for i, result in enumerate(task_results):
            if isinstance(result, Exception):
                results.append(
                    {
                        "task": tasks[i]["description"],
                        "success": False,
                        "error": str(result),
                    }
                )
            else:
                results.append(
                    {
                        "task": tasks[i]["description"],
                        "success": result.success,
                        "quality_score": (
                            result.review_result.code_quality_score
                            if result.success
                            else 0
                        ),
                        "workflow_time": result.workflow_time,
                        "generated_code": (
                            result.generation_result.generated_code
                            if result.success
                            else None
                        ),
                    }
                )

        return results

    finally:
        await orchestrator.close()


async def main():
    """Run batch processing example."""
    print("🚀 Example 3: Batch Processing")
    print("=" * 50)

    # Define multiple tasks
    tasks = [
        {
            "description": "Create a function to sort a list using quicksort",
            "requirements": ["Use recursive approach", "Include type hints"],
        },
        {
            "description": "Implement a binary search algorithm",
            "requirements": ["Handle edge cases", "Add comprehensive tests"],
        },
        {
            "description": "Create a simple hash table implementation",
            "requirements": [
                "Use chaining for collision resolution",
                "Include resize functionality",
            ],
        },
        {
            "description": "Write a function to find the longest common subsequence",
            "requirements": ["Use dynamic programming", "Optimize for space"],
        },
        {
            "description": "Implement a basic graph traversal (BFS)",
            "requirements": [
                "Use adjacency list representation",
                "Handle disconnected graphs",
            ],
        },
    ]

    print(f"📝 Processing {len(tasks)} tasks:")
    for i, task in enumerate(tasks, 1):
        print(f"   {i}. {task['description']}")

    print("\n⏳ Processing tasks...")

    try:
        # Process all tasks
        results = await process_batch_tasks(tasks)

        # Display results
        print("\n📊 Results Summary:")
        print("-" * 50)

        successful = 0
        total_time = 0
        quality_scores = []

        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['task']}")
            if result["success"]:
                successful += 1
                total_time += result["workflow_time"]
                quality_scores.append(result["quality_score"])
                print(
                    f"   ✅ Success - Quality: {result['quality_score']}/10, Time: {result['workflow_time']:.2f}s"
                )
            else:
                print(f"   ❌ Failed - Error: {result['error']}")

        # Summary statistics
        print(f"\n📈 Summary:")
        print(
            f"• Successful: {successful}/{len(tasks)} ({successful/len(tasks)*100:.1f}%)"
        )
        if quality_scores:
            print(
                f"• Average quality: {sum(quality_scores)/len(quality_scores):.1f}/10"
            )
            print(f"• Total time: {total_time:.2f}s")
            print(f"• Average time per task: {total_time/len(tasks):.2f}s")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n💡 Make sure the services are running:")
        print("   cd ../local_models && docker-compose up -d starcoder-chat")
        print("   docker-compose up -d")


if __name__ == "__main__":
    asyncio.run(main())
