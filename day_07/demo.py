#!/usr/bin/env python3
"""Demo script for StarCoder Multi-Agent System."""

import asyncio
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from communication.message_schema import OrchestratorRequest
from orchestrator import MultiAgentOrchestrator, process_simple_task

# Use environment variables for URLs with fallbacks
DEMO_GENERATOR_URL = os.getenv("GENERATOR_URL", "http://generator.localhost")
DEMO_REVIEWER_URL = os.getenv("REVIEWER_URL", "http://reviewer.localhost")


async def wait_for_services():
    """Wait for services to be ready."""
    import aiohttp
    import asyncio
    
    print("⏳ Waiting for services to be ready...")
    
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        try:
            async with aiohttp.ClientSession() as session:
                # Check generator service
                async with session.get(f"{DEMO_GENERATOR_URL}/health") as resp:
                    if resp.status != 200:
                        raise Exception(f"Generator service not ready: {resp.status}")
                
                # Check reviewer service
                async with session.get(f"{DEMO_REVIEWER_URL}/health") as resp:
                    if resp.status != 200:
                        raise Exception(f"Reviewer service not ready: {resp.status}")
                        
            print("✅ Services are ready!")
            return True
            
        except Exception as e:
            attempt += 1
            print(f"⏳ Attempt {attempt}/{max_attempts}: {str(e)}")
            if attempt < max_attempts:
                await asyncio.sleep(2)
            else:
                print("❌ Services failed to start within timeout")
                return False


async def demo_simple_task():
    """Demo with a simple task."""
    print("🚀 Demo: Simple Task Processing")
    print("=" * 50)

    # Wait for services to be ready
    if not await wait_for_services():
        print("❌ Cannot proceed without ready services")
        return

    task = "Create a function to calculate the factorial of a number"

    try:
        result = await process_simple_task(
            task_description=task,
            language="python",
            requirements=["Handle edge cases", "Include type hints"],
            generator_url=DEMO_GENERATOR_URL,
            reviewer_url=DEMO_REVIEWER_URL,
        )

        if result.success:
            print(f"✅ Task completed successfully!")
            print(f"⏱️  Workflow time: {result.workflow_time:.2f}s")
            print(
                f"📊 Code quality score: {result.review_result.code_quality_score}/10"
            )
            print(f"🔍 Issues found: {len(result.review_result.issues)}")
            print(f"💡 Recommendations: {len(result.review_result.recommendations)}")

            print("\n📝 Generated Code:")
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
        print(f"❌ Demo failed: {str(e)}")


async def demo_multiple_tasks():
    """Demo with multiple tasks."""
    print("\n🚀 Demo: Multiple Tasks Processing")
    print("=" * 50)

    # Wait for services to be ready
    if not await wait_for_services():
        print("❌ Cannot proceed without ready services")
        return

    orchestrator = MultiAgentOrchestrator(
        generator_url=DEMO_GENERATOR_URL, reviewer_url=DEMO_REVIEWER_URL
    )

    tasks = [
        "Create a function to reverse a string",
        "Create a function to check if a number is prime",
        "Create a function to find the maximum element in a list",
    ]

    results = []

    for i, task in enumerate(tasks, 1):
        print(f"\n📋 Processing task {i}: {task}")

        request = OrchestratorRequest(
            task_description=task,
            language="python",
            requirements=["Include error handling", "Add docstrings"],
        )

        try:
            result = await orchestrator.process_task(request)
            results.append(result)

            if result.success:
                print(
                    f"✅ Task {i} completed - Quality: {result.review_result.code_quality_score}/10"
                )
            else:
                print(f"❌ Task {i} failed: {result.error_message}")

        except Exception as e:
            print(f"❌ Task {i} error: {str(e)}")

    # Summary
    successful = sum(1 for r in results if r.success)
    total = len(results)
    avg_quality = (
        sum(r.review_result.code_quality_score for r in results if r.success)
        / successful
        if successful > 0
        else 0
    )

    print(f"\n📊 Summary:")
    print(f"• Tasks completed: {successful}/{total}")
    print(f"• Average quality score: {avg_quality:.1f}/10")
    print(f"• Results saved in: {orchestrator.results_dir}")


async def demo_agent_status():
    """Demo agent status checking."""
    print("\n🚀 Demo: Agent Status Check")
    print("=" * 50)

    # Wait for services to be ready
    if not await wait_for_services():
        print("❌ Cannot proceed without ready services")
        return

    orchestrator = MultiAgentOrchestrator(
        generator_url=DEMO_GENERATOR_URL, reviewer_url=DEMO_REVIEWER_URL
    )

    try:
        # Check agent status
        status = await orchestrator.get_agent_status()

        print("🤖 Agent Status:")
        for agent_name, agent_status in status.items():
            if agent_name != "error":
                print(
                    f"• {agent_name}: {agent_status.get('status', 'unknown')} "
                    f"(uptime: {agent_status.get('uptime', 0):.1f}s)"
                )
            else:
                print(f"• Error: {agent_status}")

        # Get agent statistics
        stats = await orchestrator.get_agent_stats()

        print("\n📈 Agent Statistics:")
        for agent_name, agent_stats in stats.items():
            if agent_name != "error" and agent_stats:
                if isinstance(agent_stats, dict) and "error" not in agent_stats:
                    print(f"• {agent_name}:")
                    print(f"  - Total requests: {agent_stats.get('total_requests', 0)}")
                    print(
                        f"  - Success rate: {agent_stats.get('successful_requests', 0)}/{agent_stats.get('total_requests', 0)}"
                    )
                    print(
                        f"  - Avg response time: {agent_stats.get('average_response_time', 0):.2f}s"
                    )
                elif isinstance(agent_stats, dict) and "error" in agent_stats:
                    print(f"• {agent_name}: Error - {agent_stats['error']}")

        # Get results summary
        summary = orchestrator.get_results_summary()

        print("\n📊 Results Summary:")
        if "message" in summary:
            print(f"• {summary['message']}")
        else:
            print(f"• Total workflows: {summary.get('total_workflows', 0)}")
            print(f"• Success rate: {summary.get('success_rate', 0):.1%}")
            print(
                f"• Average workflow time: {summary.get('average_workflow_time', 0):.2f}s"
            )
            print(
                f"• Average quality score: {summary.get('average_quality_score', 0):.1f}/10"
            )

    except Exception as e:
        print(f"❌ Status check failed: {str(e)}")


async def main():
    """Main demo function."""
    print("🌟 StarCoder Multi-Agent System Demo")
    print("=" * 60)

    try:
        # Demo 1: Simple task
        await demo_simple_task()

        # Demo 2: Multiple tasks
        await demo_multiple_tasks()

        # Demo 3: Agent status
        await demo_agent_status()

        print("\n🎉 Demo completed successfully!")
        print("\n💡 Tips:")
        print("• Check the 'results/' directory for saved workflow results")
        print("• Use the orchestrator directly for custom workflows")
        print("• Monitor agent health with the status endpoints")

    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("• Make sure StarCoder is running on port 8003")
        print("• Make sure agent services are running on ports 9001 and 9002")
        print("• Check the logs for detailed error information")


if __name__ == "__main__":
    asyncio.run(main())
