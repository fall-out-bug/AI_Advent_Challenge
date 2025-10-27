#!/usr/bin/env python3
"""Quick demo of ChadGPT Multi-Agent System."""

import asyncio
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from agents.core.code_generator import CodeGeneratorAgent
from agents.core.code_reviewer import CodeReviewerAgent
from agents.core.smart_model_selector import get_smart_selector
from agents.core.unified_model_adapter import UnifiedModelAdapter
from communication.message_schema import CodeGenerationRequest, CodeReviewRequest


async def quick_chadgpt_demo():
    """Quick demo of ChadGPT multi-agent system."""
    print("⚡ Quick ChadGPT Multi-Agent Demo")
    print("=" * 40)

    # Check API key
    has_chadgpt = bool(os.getenv("CHADGPT_API_KEY"))
    print(f"🔑 ChadGPT API: {'✅ Available' if has_chadgpt else '❌ Not set'}")

    if not has_chadgpt:
        print("⚠️  This demo requires CHADGPT_API_KEY environment variable.")
        print("   Set it with: export CHADGPT_API_KEY='your-key'")
        print("\n📋 Demo will show smart model selection only...")

        # Show smart model selection without API calls
        await demo_smart_selection_only()
        return

    # Demo with actual API calls
    await demo_with_api_calls()


async def demo_smart_selection_only():
    """Demo smart model selection without API calls."""
    print(f"\n🧠 Smart Model Selection Demo")
    print("-" * 35)

    selector = get_smart_selector()

    # Demo tasks
    tasks = [
        "Create a function to calculate the factorial of a number",
        "Create a REST API endpoint for user authentication",
        "Review this code for security vulnerabilities",
        "Write comprehensive unit tests for a sorting algorithm",
    ]

    for i, task in enumerate(tasks, 1):
        print(f"\n📝 Task {i}: {task}")

        # Get recommendations for both generator and reviewer
        gen_rec = selector.recommend_model(task, "python")
        rev_rec = selector.recommend_model(
            "Review generated code for quality and best practices", "python"
        )

        print(f"   🎯 Generator: {gen_rec.model} (confidence: {gen_rec.confidence:.2f})")
        print(f"   🎯 Reviewer: {rev_rec.model} (confidence: {rev_rec.confidence:.2f})")
        print(f"   💭 Gen reason: {gen_rec.reasoning}")
        print(f"   💭 Rev reason: {rev_rec.reasoning}")


async def demo_with_api_calls():
    """Demo with actual API calls."""
    print(f"\n🤖 Live API Demo")
    print("-" * 20)

    # Simple task
    task = "Create a function to calculate the factorial of a number"
    print(f"📝 Task: {task}")

    try:
        # Create agents
        generator = CodeGeneratorAgent(external_provider="chadgpt-real")
        reviewer = CodeReviewerAgent(external_provider="chadgpt-real")

        # Get smart recommendations
        gen_rec = generator.get_smart_model_recommendation(task, "python")
        rev_rec = reviewer.get_smart_model_recommendation(
            "Review generated code for quality and best practices", "python"
        )

        print(f"🎯 Generator: {gen_rec.model} (confidence: {gen_rec.confidence:.2f})")
        print(f"🎯 Reviewer: {rev_rec.model} (confidence: {rev_rec.confidence:.2f})")

        # Switch to smart models
        print("🔄 Switching to smart models...")
        gen_success = await generator.switch_to_smart_model(task, "python")
        rev_success = await reviewer.switch_to_smart_model(
            "Review generated code for quality and best practices", "python"
        )

        if not (gen_success and rev_success):
            print("❌ Failed to switch to smart models")
            return

        print("✅ Both agents switched to smart models")

        # Generate code
        print(f"\n⚡ Generating code with {gen_rec.model}...")
        gen_request = CodeGenerationRequest(
            task_description=task,
            language="python",
            requirements=["Handle edge cases", "Include type hints", "Add tests"],
        )

        gen_result = await generator.process(gen_request)

        print(f"✅ Code generated!")
        print(
            f"📊 Tokens: {gen_result.tokens_used}, Time: {gen_result.processing_time:.2f}s"
        )

        # Review code
        print(f"\n🔍 Reviewing code with {rev_rec.model}...")
        rev_request = CodeReviewRequest(
            code_to_review=gen_result.generated_code,
            language="python",
            review_focus=["quality", "best_practices", "security"],
        )

        rev_result = await reviewer.process(rev_request)

        print(f"✅ Code review completed!")
        print(
            f"📊 Tokens: {rev_result.tokens_used}, Time: {rev_result.processing_time:.2f}s"
        )

        # Show results
        print(f"\n📝 Generated Code:")
        print("-" * 30)
        print(gen_result.generated_code)

        print(f"\n🧪 Generated Tests:")
        print("-" * 30)
        print(gen_result.tests)

        print(f"\n🔍 Review Results:")
        print("-" * 30)
        print(f"Quality Score: {rev_result.code_quality_score}/10")
        print(f"Issues: {len(rev_result.issues)}")
        print(f"Recommendations: {len(rev_result.recommendations)}")

        if rev_result.issues:
            print(f"\n⚠️  Issues:")
            for issue in rev_result.issues[:3]:  # Show first 3
                print(f"  • {issue}")

        if rev_result.recommendations:
            print(f"\n💡 Recommendations:")
            for rec in rev_result.recommendations[:3]:  # Show first 3
                print(f"  • {rec}")

        # Summary
        total_time = gen_result.processing_time + rev_result.processing_time
        total_tokens = gen_result.tokens_used + rev_result.tokens_used

        print(f"\n📊 Summary:")
        print(f"  • Total time: {total_time:.2f}s")
        print(f"  • Total tokens: {total_tokens}")
        print(f"  • Quality score: {rev_result.code_quality_score}/10")
        print(f"  • Generator: {gen_rec.model}")
        print(f"  • Reviewer: {rev_rec.model}")

    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")


async def demo_model_comparison():
    """Quick model comparison demo."""
    print(f"\n📊 Model Comparison Demo")
    print("-" * 30)

    # Check API key
    has_chadgpt = bool(os.getenv("CHADGPT_API_KEY"))
    if not has_chadgpt:
        print("⏭️  Skipping (no API key)")
        return

    task = "Create a simple HTTP server with Flask"
    print(f"📝 Task: {task}")

    # Test different models
    models = ["gpt-5-nano", "gpt-5-mini", "gpt-5"]
    results = []

    for model in models:
        print(f"\n🧪 Testing {model}...")

        try:
            generator = CodeGeneratorAgent(
                model_name=model, external_provider="chadgpt-real"
            )

            if await generator.check_provider_availability():
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
                    }
                )

                print(
                    f"   ✅ {model}: {result.tokens_used} tokens, {processing_time:.2f}s"
                )

            else:
                print(f"   ❌ {model} not available")

        except Exception as e:
            print(f"   ❌ {model} failed: {e}")

    # Show comparison
    if results:
        print(f"\n📈 Comparison Results:")
        print(f"{'Model':<15} {'Tokens':<8} {'Time':<8} {'Length':<8}")
        print("-" * 45)

        for result in results:
            print(
                f"{result['model']:<15} {result['tokens']:<8} {result['time']:<8.2f} {result['code_length']:<8}"
            )

        # Find best performers
        fastest = min(results, key=lambda x: x["time"])
        most_efficient = min(results, key=lambda x: x["tokens"])

        print(f"\n🏆 Best Performance:")
        print(f"  Fastest: {fastest['model']} ({fastest['time']:.2f}s)")
        print(
            f"  Most efficient: {most_efficient['model']} ({most_efficient['tokens']} tokens)"
        )


async def main():
    """Main demo function."""
    print("🌟 ChadGPT Multi-Agent System - Quick Demo")
    print("=" * 50)

    try:
        # Main demo
        await quick_chadgpt_demo()

        # Model comparison
        await demo_model_comparison()

        print(f"\n🎉 Quick demo completed!")
        print(f"\n📚 Key Features:")
        print(f"  • Smart model selection for generator and reviewer")
        print(f"  • Automatic switching to optimal models")
        print(f"  • Code generation with ChadGPT models")
        print(f"  • Code review with specialized models")
        print(f"  • Performance comparison between models")

        print(f"\n🚀 Next Steps:")
        print(f"  • Run full demo: python chadgpt_demo.py")
        print(f"  • Try interactive demo: python interactive_demo.py")
        print(f"  • Use CLI tools: python manage_providers.py --help")

    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
