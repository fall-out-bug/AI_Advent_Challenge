#!/usr/bin/env python3
"""Example 4: Advanced Orchestration

This example demonstrates advanced orchestration patterns including
error handling, retry logic, and result analysis.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from communication.message_schema import OrchestratorRequest
from exceptions import CodeGenerationError, CodeReviewError
from orchestrator import MultiAgentOrchestrator


class AdvancedOrchestrator:
    """Advanced orchestrator with retry logic and analysis."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.orchestrator = MultiAgentOrchestrator()
        self.results_history = []

    async def process_with_retry(self, request: OrchestratorRequest) -> Dict[str, Any]:
        """Process a request with retry logic."""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                print(f"   Attempt {attempt + 1}/{self.max_retries}...")
                result = await self.orchestrator.process_task(request)

                if result.success:
                    return {"success": True, "result": result, "attempts": attempt + 1}
                else:
                    last_error = result.error_message

            except CodeGenerationError as e:
                last_error = f"Generation error: {str(e)}"
            except CodeReviewError as e:
                last_error = f"Review error: {str(e)}"
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"

            if attempt < self.max_retries - 1:
                print(f"   Retrying in 2 seconds...")
                await asyncio.sleep(2)

        return {"success": False, "error": last_error, "attempts": self.max_retries}

    async def analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze processing results."""
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        if not successful:
            return {
                "total_tasks": len(results),
                "successful": 0,
                "failed": len(failed),
                "success_rate": 0.0,
                "average_quality": 0.0,
                "average_time": 0.0,
                "common_issues": [],
                "recommendations": [],
            }

        # Calculate metrics
        quality_scores = [
            r["result"].review_result.code_quality_score for r in successful
        ]
        workflow_times = [r["result"].workflow_time for r in successful]

        # Collect common issues
        all_issues = []
        for r in successful:
            all_issues.extend(r["result"].review_result.issues)

        # Count issue frequency
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1

        common_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[
            :5
        ]

        # Collect recommendations
        all_recommendations = []
        for r in successful:
            all_recommendations.extend(r["result"].review_result.recommendations)

        return {
            "total_tasks": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(results),
            "average_quality": sum(quality_scores) / len(quality_scores),
            "average_time": sum(workflow_times) / len(workflow_times),
            "common_issues": common_issues,
            "recommendations": list(set(all_recommendations))[:5],
        }

    async def close(self):
        """Close the orchestrator."""
        await self.orchestrator.close()


async def main():
    """Run advanced orchestration example."""
    print("🚀 Example 4: Advanced Orchestration")
    print("=" * 50)

    # Define complex tasks
    tasks = [
        {
            "description": "Create a machine learning pipeline for text classification",
            "requirements": [
                "Use scikit-learn",
                "Include data preprocessing",
                "Add model evaluation metrics",
                "Implement cross-validation",
                "Handle imbalanced datasets",
            ],
        },
        {
            "description": "Implement a distributed task queue system",
            "requirements": [
                "Use Redis for message broker",
                "Support task prioritization",
                "Add retry mechanisms",
                "Include monitoring endpoints",
                "Handle worker failures gracefully",
            ],
        },
        {
            "description": "Create a real-time data processing system",
            "requirements": [
                "Use Apache Kafka for streaming",
                "Implement windowing operations",
                "Add data validation",
                "Include alerting for anomalies",
                "Support multiple data sources",
            ],
        },
    ]

    print(f"📝 Processing {len(tasks)} complex tasks:")
    for i, task in enumerate(tasks, 1):
        print(f"   {i}. {task['description']}")

    # Initialize advanced orchestrator
    orchestrator = AdvancedOrchestrator(max_retries=3)

    try:
        print("\n⏳ Processing tasks with retry logic...")
        results = []

        for i, task_data in enumerate(tasks, 1):
            print(f"\n{i}. Processing: {task_data['description']}")

            request = OrchestratorRequest(
                task_description=task_data["description"],
                language="python",
                requirements=task_data["requirements"],
            )

            result = await orchestrator.process_with_retry(request)
            results.append(result)

            if result["success"]:
                print(f"   ✅ Success after {result['attempts']} attempts")
                print(
                    f"   📊 Quality: {result['result'].review_result.code_quality_score}/10"
                )
                print(f"   ⏱️  Time: {result['result'].workflow_time:.2f}s")
            else:
                print(f"   ❌ Failed after {result['attempts']} attempts")
                print(f"   Error: {result['error']}")

        # Analyze results
        print("\n📊 Analysis:")
        print("-" * 50)

        analysis = await orchestrator.analyze_results(results)

        print(f"• Total tasks: {analysis['total_tasks']}")
        print(f"• Successful: {analysis['successful']}")
        print(f"• Failed: {analysis['failed']}")
        print(f"• Success rate: {analysis['success_rate']:.1%}")

        if analysis["successful"] > 0:
            print(f"• Average quality: {analysis['average_quality']:.1f}/10")
            print(f"• Average time: {analysis['average_time']:.2f}s")

            print(f"\n🔍 Common Issues:")
            for issue, count in analysis["common_issues"]:
                print(f"   • {issue} ({count} times)")

            print(f"\n💡 Top Recommendations:")
            for rec in analysis["recommendations"]:
                print(f"   • {rec}")

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"advanced_orchestration_results_{timestamp}.json"

        with open(results_file, "w") as f:
            json.dump(
                {
                    "timestamp": timestamp,
                    "analysis": analysis,
                    "results": [
                        {
                            "task": tasks[i]["description"],
                            "success": r["success"],
                            "attempts": r["attempts"],
                            "quality_score": (
                                r["result"].review_result.code_quality_score
                                if r["success"]
                                else 0
                            ),
                            "workflow_time": (
                                r["result"].workflow_time if r["success"] else 0
                            ),
                            "error": r.get("error"),
                        }
                        for i, r in enumerate(results)
                    ],
                },
                f,
                indent=2,
                default=str,
            )

        print(f"\n💾 Results saved to: {results_file}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n💡 Make sure the services are running:")
        print("   cd ../local_models && docker-compose up -d starcoder-chat")
        print("   docker-compose up -d")

    finally:
        await orchestrator.close()


if __name__ == "__main__":
    asyncio.run(main())
