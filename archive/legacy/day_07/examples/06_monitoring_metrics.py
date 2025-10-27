#!/usr/bin/env python3
"""Example 6: Monitoring and Metrics

This example demonstrates how to monitor the multi-agent system
and collect performance metrics for analysis.
"""

import asyncio
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

from orchestrator import process_simple_task


class SystemMonitor:
    """Monitor system health and performance."""

    def __init__(self):
        self.generator_url = "http://localhost:9001"
        self.reviewer_url = "http://localhost:9002"
        self.metrics = []

    async def check_service_health(self) -> Dict[str, Any]:
        """Check health of all services."""
        health_status = {}

        try:
            async with httpx.AsyncClient() as client:
                # Check generator agent
                try:
                    response = await client.get(
                        f"{self.generator_url}/health", timeout=5.0
                    )
                    health_status["generator"] = {
                        "status": response.json()["status"],
                        "uptime": response.json()["uptime"],
                    }
                except Exception as e:
                    health_status["generator"] = {
                        "status": "unhealthy",
                        "error": str(e),
                    }

                # Check reviewer agent
                try:
                    response = await client.get(
                        f"{self.reviewer_url}/health", timeout=5.0
                    )
                    health_status["reviewer"] = {
                        "status": response.json()["status"],
                        "uptime": response.json()["uptime"],
                    }
                except Exception as e:
                    health_status["reviewer"] = {"status": "unhealthy", "error": str(e)}

        except Exception as e:
            health_status["error"] = str(e)

        return health_status

    async def get_service_stats(self) -> Dict[str, Any]:
        """Get performance statistics from all services."""
        stats = {}

        try:
            async with httpx.AsyncClient() as client:
                # Get generator stats
                try:
                    response = await client.get(
                        f"{self.generator_url}/stats", timeout=5.0
                    )
                    stats["generator"] = response.json()
                except Exception as e:
                    stats["generator"] = {"error": str(e)}

                # Get reviewer stats
                try:
                    response = await client.get(
                        f"{self.reviewer_url}/stats", timeout=5.0
                    )
                    stats["reviewer"] = response.json()
                except Exception as e:
                    stats["reviewer"] = {"error": str(e)}

        except Exception as e:
            stats["error"] = str(e)

        return stats

    async def run_performance_test(self, tasks: List[str]) -> List[Dict[str, Any]]:
        """Run performance test with multiple tasks."""
        results = []

        for i, task in enumerate(tasks):
            print(f"   Running task {i+1}/{len(tasks)}: {task[:50]}...")

            start_time = time.time()

            try:
                result = await process_simple_task(
                    task_description=task, language="python"
                )

                end_time = time.time()

                results.append(
                    {
                        "task": task,
                        "success": result.success,
                        "workflow_time": result.workflow_time,
                        "total_time": end_time - start_time,
                        "quality_score": (
                            result.review_result.code_quality_score
                            if result.success
                            else 0
                        ),
                        "tokens_used": (
                            result.generation_result.tokens_used
                            if result.success
                            else 0
                        ),
                        "error": result.error_message if not result.success else None,
                    }
                )

            except Exception as e:
                end_time = time.time()
                results.append(
                    {
                        "task": task,
                        "success": False,
                        "workflow_time": 0,
                        "total_time": end_time - start_time,
                        "quality_score": 0,
                        "tokens_used": 0,
                        "error": str(e),
                    }
                )

        return results

    def analyze_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze collected metrics."""
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        if not successful:
            return {
                "total_tasks": len(results),
                "successful": 0,
                "failed": len(failed),
                "success_rate": 0.0,
                "average_quality": 0.0,
                "average_workflow_time": 0.0,
                "average_total_time": 0.0,
                "total_tokens": 0,
            }

        return {
            "total_tasks": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(results),
            "average_quality": sum(r["quality_score"] for r in successful)
            / len(successful),
            "average_workflow_time": sum(r["workflow_time"] for r in successful)
            / len(successful),
            "average_total_time": sum(r["total_time"] for r in successful)
            / len(successful),
            "total_tokens": sum(r["tokens_used"] for r in successful),
            "min_quality": min(r["quality_score"] for r in successful),
            "max_quality": max(r["quality_score"] for r in successful),
            "min_time": min(r["workflow_time"] for r in successful),
            "max_time": max(r["workflow_time"] for r in successful),
        }


async def main():
    """Run monitoring and metrics example."""
    print("🚀 Example 6: Monitoring and Metrics")
    print("=" * 50)

    monitor = SystemMonitor()

    # Check service health
    print("🏥 Checking service health...")
    health = await monitor.check_service_health()

    print("Health Status:")
    for service, status in health.items():
        if service == "error":
            print(f"   ❌ Error: {status}")
        else:
            print(
                f"   {service}: {status['status']} (uptime: {status.get('uptime', 0):.1f}s)"
            )

    # Get service statistics
    print("\n📊 Getting service statistics...")
    stats = await monitor.get_service_stats()

    print("Service Statistics:")
    for service, data in stats.items():
        if service == "error":
            print(f"   ❌ Error: {data}")
        elif "error" in data:
            print(f"   ❌ {service}: {data['error']}")
        else:
            print(f"   {service}:")
            print(f"     • Total requests: {data.get('total_requests', 0)}")
            print(f"     • Successful: {data.get('successful_requests', 0)}")
            print(f"     • Failed: {data.get('failed_requests', 0)}")
            print(
                f"     • Avg response time: {data.get('average_response_time', 0):.2f}s"
            )
            print(f"     • Total tokens: {data.get('total_tokens_used', 0)}")

    # Run performance test
    print("\n⚡ Running performance test...")

    test_tasks = [
        "Create a function to calculate fibonacci numbers",
        "Implement a binary search algorithm",
        "Write a function to sort a list",
        "Create a simple hash table",
        "Implement a graph traversal algorithm",
    ]

    print(f"Testing with {len(test_tasks)} tasks...")
    results = await monitor.run_performance_test(test_tasks)

    # Analyze results
    print("\n📈 Performance Analysis:")
    analysis = monitor.analyze_metrics(results)

    print(f"• Total tasks: {analysis['total_tasks']}")
    print(f"• Successful: {analysis['successful']}")
    print(f"• Failed: {analysis['failed']}")
    print(f"• Success rate: {analysis['success_rate']:.1%}")

    if analysis["successful"] > 0:
        print(f"• Average quality: {analysis['average_quality']:.1f}/10")
        print(
            f"• Quality range: {analysis['min_quality']:.1f} - {analysis['max_quality']:.1f}"
        )
        print(f"• Average workflow time: {analysis['average_workflow_time']:.2f}s")
        print(
            f"• Time range: {analysis['min_time']:.2f}s - {analysis['max_time']:.2f}s"
        )
        print(f"• Total tokens used: {analysis['total_tokens']}")

    # Save metrics
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metrics_file = f"monitoring_metrics_{timestamp}.json"

    with open(metrics_file, "w") as f:
        json.dump(
            {
                "timestamp": timestamp,
                "health_status": health,
                "service_stats": stats,
                "performance_test": {
                    "tasks": test_tasks,
                    "results": results,
                    "analysis": analysis,
                },
            },
            f,
            indent=2,
            default=str,
        )

    print(f"\n💾 Metrics saved to: {metrics_file}")

    # Monitoring recommendations
    print("\n🔧 Monitoring Best Practices:")
    print("-" * 50)
    print("1. Set up health check endpoints")
    print("2. Monitor response times and error rates")
    print("3. Track resource usage (CPU, memory, GPU)")
    print("4. Implement alerting for critical metrics")
    print("5. Log all requests and responses")
    print("6. Use metrics for capacity planning")
    print("7. Monitor token usage and costs")
    print("8. Set up dashboards for visualization")

    print("\n📊 Key Metrics to Monitor:")
    print("-" * 50)
    print("• Request rate and success rate")
    print("• Response time percentiles (p50, p95, p99)")
    print("• Error rate by type")
    print("• Resource utilization")
    print("• Token consumption")
    print("• Queue depth and processing time")
    print("• Service availability")


if __name__ == "__main__":
    asyncio.run(main())
