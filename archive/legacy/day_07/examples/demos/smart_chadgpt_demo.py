#!/usr/bin/env python3
"""Comprehensive demo of smart ChadGPT integration."""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from agents.core.code_generator import CodeGeneratorAgent
from agents.core.code_reviewer import CodeReviewerAgent
from agents.core.smart_model_selector import get_smart_selector
from communication.message_schema import CodeGenerationRequest, CodeReviewRequest
from orchestrator import MultiAgentOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SmartChadGPTDemo:
    """Comprehensive demo of smart ChadGPT integration."""

    def __init__(self):
        """Initialize the demo."""
        self.has_chadgpt = bool(os.getenv("CHADGPT_API_KEY"))
        self.selector = get_smart_selector()

    async def run_full_demo(self):
        """Run the complete demo."""
        print("🚀 Smart ChadGPT Integration Demo")
        print("=" * 50)

        # Check API key
        await self._check_api_key()

        # Demo 1: Smart model selection
        await self._demo_smart_selection()

        # Demo 2: Code generation with smart models
        await self._demo_smart_generation()

        # Demo 3: Code review with optimal models
        await self._demo_smart_review()

        # Demo 4: Multi-agent orchestration
        await self._demo_orchestration()

        # Demo 5: Performance comparison
        await self._demo_performance_comparison()

        print("\n🎉 Demo completed successfully!")
        print("\n📚 Key Takeaways:")
        print("   • Smart model selection optimizes performance")
        print("   • Different models excel at different tasks")
        print("   • ChadGPT provides access to multiple powerful models")
        print("   • System automatically chooses the best model for each task")

    async def _check_api_key(self):
        """Check API key availability."""
        print(f"\n🔑 API Key Status:")
        print(f"   ChadGPT: {'✅ Available' if self.has_chadgpt else '❌ Not set'}")

        if not self.has_chadgpt:
            print("\n⚠️  No ChadGPT API key found.")
            print(
                "   Set CHADGPT_API_KEY environment variable to test with real API calls."
            )
            print("   Demo will show recommendations and configuration only.")
            return False
        return True

    async def _demo_smart_selection(self):
        """Demo smart model selection."""
        print(f"\n🧠 Demo 1: Smart Model Selection")
        print("-" * 35)

        demo_tasks = [
            {
                "description": "Create a simple calculator class",
                "expected": "gpt-5-mini",
                "reason": "Simple task, fast execution",
            },
            {
                "description": "Implement a distributed caching system with Redis and load balancing",
                "expected": "gpt-5",
                "reason": "Complex architecture, high quality needed",
            },
            {
                "description": "Review this authentication code for security vulnerabilities",
                "expected": "claude-4.1-opus",
                "reason": "Code review, security analysis",
            },
            {
                "description": "Write comprehensive unit tests for a sorting algorithm",
                "expected": "gpt-5-mini",
                "reason": "Testing task, good balance",
            },
        ]

        for i, task in enumerate(demo_tasks, 1):
            print(f"\n📝 Task {i}: {task['description']}")

            # Get recommendation
            recommendation = self.selector.recommend_model(task["description"])

            print(f"🎯 Recommended: {recommendation.model}")
            print(f"📊 Confidence: {recommendation.confidence:.2f}")
            print(f"💭 Reasoning: {recommendation.reasoning}")
            print(f"⚙️  Max tokens: {recommendation.max_tokens}")
            print(f"🌡️  Temperature: {recommendation.temperature}")

            # Check if recommendation matches expectation
            if recommendation.model == task["expected"]:
                print(f"✅ Correct! {task['reason']}")
            else:
                print(f"ℹ️  Expected {task['expected']}, got {recommendation.model}")

    async def _demo_smart_generation(self):
        """Demo smart code generation."""
        print(f"\n⚡ Demo 2: Smart Code Generation")
        print("-" * 35)

        if not self.has_chadgpt:
            print("⏭️  Skipping (no API key)")
            return

        tasks = [
            {
                "description": "Create a simple HTTP server with Flask",
                "language": "python",
                "requirements": ["Use Flask", "Include error handling", "Add logging"],
            },
            {
                "description": "Implement a binary search tree with all operations",
                "language": "python",
                "requirements": [
                    "Include insert, delete, search",
                    "Add traversal methods",
                    "Use proper OOP",
                ],
            },
        ]

        for i, task in enumerate(tasks, 1):
            print(f"\n📝 Generation Task {i}: {task['description']}")

            try:
                # Create generator with smart model selection
                generator = CodeGeneratorAgent(external_provider="chadgpt-real")

                # Get smart recommendation
                recommendation = generator.get_smart_model_recommendation(
                    task["description"], task["language"]
                )

                print(f"🎯 Using: {recommendation.model}")
                print(f"💭 Reason: {recommendation.reasoning}")

                # Switch to recommended model
                success = await generator.switch_to_smart_model(
                    task["description"], task["language"]
                )

                if success:
                    print("✅ Successfully switched to recommended model")

                    # Generate code
                    request = CodeGenerationRequest(
                        task_description=task["description"],
                        language=task["language"],
                        requirements=task["requirements"],
                    )

                    print("🔄 Generating code...")
                    result = await generator.process(request)

                    print(f"✅ Generated {len(result.generated_code)} characters")
                    print(f"📊 Tokens used: {result.tokens_used}")
                    print(f"⏱️  Processing time: {result.processing_time:.2f}s")

                    # Show code snippet
                    print("\n📄 Code snippet:")
                    print("```python")
                    print(result.generated_code)
                    print("```")

                else:
                    print("❌ Failed to switch to recommended model")

            except Exception as e:
                print(f"❌ Generation failed: {e}")

    async def _demo_smart_review(self):
        """Demo smart code review."""
        print(f"\n🔍 Demo 3: Smart Code Review")
        print("-" * 30)

        if not self.has_chadgpt:
            print("⏭️  Skipping (no API key)")
            return

        # Sample code to review
        sample_code = """
def calculate_fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def process_user_data(data):
    # Process user data
    result = []
    for item in data:
        if item['age'] > 18:
            result.append(item['name'])
    return result
"""

        print(f"📝 Reviewing sample code:")
        print("```python")
        print(sample_code.strip())
        print("```")

        try:
            # Create reviewer with smart model selection
            reviewer = CodeReviewerAgent(external_provider="chadgpt-real")

            # Get smart recommendation for code review
            recommendation = reviewer.get_smart_model_recommendation(
                "Review this Python code for performance issues and security vulnerabilities",
                "python",
            )

            print(f"\n🎯 Using: {recommendation.model}")
            print(f"💭 Reason: {recommendation.reasoning}")

            # Switch to recommended model
            success = await reviewer.switch_to_smart_model(
                "Review this Python code for performance issues and security vulnerabilities",
                "python",
            )

            if success:
                print("✅ Successfully switched to recommended model")

                # Review code
                request = CodeReviewRequest(
                    code_to_review=sample_code,
                    language="python",
                    review_focus=["performance", "security", "best_practices"],
                )

                print("🔄 Reviewing code...")
                result = await reviewer.process(request)

                print(f"✅ Review completed")
                print(f"📊 Tokens used: {result.tokens_used}")
                print(f"⏱️  Processing time: {result.processing_time:.2f}s")

                # Show review snippet
                print("\n📄 Review snippet:")
                print("```")
                print(result.review_result)
                print("```")

            else:
                print("❌ Failed to switch to recommended model")

        except Exception as e:
            print(f"❌ Review failed: {e}")

    async def _demo_orchestration(self):
        """Demo multi-agent orchestration with smart models."""
        print(f"\n🤖 Demo 4: Multi-Agent Orchestration")
        print("-" * 40)

        if not self.has_chadgpt:
            print("⏭️  Skipping (no API key)")
            return

        try:
            # Create orchestrator with smart models
            orchestrator = MultiAgentOrchestrator(
                generator_model="gpt-5-mini",  # Will be overridden by smart selection
                reviewer_model="claude-4.1-opus",  # Will be overridden by smart selection
                generator_external_provider="chadgpt-real",
                reviewer_external_provider="chadgpt-real",
            )

            print("✅ Created orchestrator with ChadGPT")

            # Complex task that benefits from smart model selection
            task_description = """
            Create a REST API for a library management system with the following features:
            - Book CRUD operations
            - User authentication and authorization
            - Borrowing and returning books
            - Search and filtering
            - Data validation and error handling
            """

            print(f"📝 Task: {task_description.strip()}")

            # Get smart recommendations for both agents
            generator_rec = orchestrator.generator.get_smart_model_recommendation(
                task_description, "python"
            )
            reviewer_rec = orchestrator.reviewer.get_smart_model_recommendation(
                "Review generated API code for security and best practices", "python"
            )

            print(f"\n🎯 Generator recommendation: {generator_rec.model}")
            print(f"🎯 Reviewer recommendation: {reviewer_rec.model}")

            # Switch to smart models
            gen_success = await orchestrator.generator.switch_to_smart_model(
                task_description, "python"
            )
            rev_success = await orchestrator.reviewer.switch_to_smart_model(
                "Review generated API code for security and best practices", "python"
            )

            if gen_success and rev_success:
                print("✅ Both agents switched to smart models")

                # Run orchestration
                print("🔄 Running orchestration...")
                result = await orchestrator.orchestrate_code_generation_and_review(
                    task_description=task_description,
                    language="python",
                    requirements=[
                        "Use FastAPI",
                        "Include authentication",
                        "Add comprehensive tests",
                    ],
                )

                print(f"✅ Orchestration completed")
                print(f"📊 Total tokens used: {result.get('total_tokens', 'N/A')}")
                print(f"⏱️  Total time: {result.get('total_time', 'N/A')}")

                # Show results summary
                if "generation_result" in result:
                    gen_result = result["generation_result"]
                    print(
                        f"📝 Generated code: {len(gen_result.generated_code)} characters"
                    )

                if "review_result" in result:
                    rev_result = result["review_result"]
                    print(
                        f"🔍 Review completed: {len(rev_result.review_result)} characters"
                    )

            else:
                print("❌ Failed to switch agents to smart models")

        except Exception as e:
            print(f"❌ Orchestration failed: {e}")

    async def _demo_performance_comparison(self):
        """Demo performance comparison between models."""
        print(f"\n📊 Demo 5: Performance Comparison")
        print("-" * 35)

        if not self.has_chadgpt:
            print("⏭️  Skipping (no API key)")
            return

        # Simple task for comparison
        task = "Create a function that calculates the factorial of a number"

        print(f"📝 Task: {task}")
        print("\n🔄 Testing different models...")

        models_to_test = ["gpt-5-nano", "gpt-5-mini", "gpt-5"]
        results = []

        for model in models_to_test:
            try:
                print(f"\n🧪 Testing {model}...")

                # Create generator with specific model
                generator = CodeGeneratorAgent(
                    model_name=model, external_provider="chadgpt-real"
                )

                # Check availability
                if await generator.check_provider_availability():
                    print(f"✅ {model} is available")

                    # Generate code
                    request = CodeGenerationRequest(
                        task_description=task, language="python"
                    )

                    start_time = asyncio.get_event_loop().time()
                    result = await generator.process(request)
                    end_time = asyncio.get_event_loop().time()

                    processing_time = end_time - start_time

                    results.append(
                        {
                            "model": model,
                            "tokens": result.tokens_used,
                            "time": processing_time,
                            "code_length": len(result.generated_code),
                            "success": True,
                        }
                    )

                    print(
                        f"✅ {model}: {result.tokens_used} tokens, {processing_time:.2f}s"
                    )

                else:
                    print(f"❌ {model} is not available")
                    results.append({"model": model, "success": False})

            except Exception as e:
                print(f"❌ {model} failed: {e}")
                results.append({"model": model, "success": False, "error": str(e)})

        # Show comparison
        print(f"\n📈 Performance Comparison:")
        print("-" * 30)

        successful_results = [r for r in results if r.get("success", False)]

        if successful_results:
            # Sort by processing time
            successful_results.sort(key=lambda x: x["time"])

            print(f"{'Model':<15} {'Tokens':<8} {'Time':<8} {'Length':<8}")
            print("-" * 45)

            for result in successful_results:
                print(
                    f"{result['model']:<15} {result['tokens']:<8} {result['time']:<8.2f} {result['code_length']:<8}"
                )

            # Find fastest and most efficient
            fastest = min(successful_results, key=lambda x: x["time"])
            most_efficient = min(successful_results, key=lambda x: x["tokens"])

            print(f"\n🏆 Fastest: {fastest['model']} ({fastest['time']:.2f}s)")
            print(
                f"💡 Most efficient: {most_efficient['model']} ({most_efficient['tokens']} tokens)"
            )
        else:
            print("❌ No successful results to compare")


async def main():
    """Main demo function."""
    demo = SmartChadGPTDemo()
    await demo.run_full_demo()


if __name__ == "__main__":
    asyncio.run(main())
