#!/usr/bin/env python3
"""Demo comparing original StarCoder system with ChadGPT smart system."""

import asyncio
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from agents.core.code_generator import CodeGeneratorAgent
from agents.core.code_reviewer import CodeReviewerAgent
from agents.core.smart_model_selector import get_smart_selector
from communication.message_schema import CodeGenerationRequest, CodeReviewRequest


async def demo_comparison():
    """Demo comparing original system with ChadGPT smart system."""
    print("🔄 StarCoder vs ChadGPT Smart System Comparison")
    print("=" * 60)

    # Check API key
    has_chadgpt = bool(os.getenv("CHADGPT_API_KEY"))
    print(f"🔑 ChadGPT API: {'✅ Available' if has_chadgpt else '❌ Not set'}")

    if not has_chadgpt:
        print("⚠️  This demo requires CHADGPT_API_KEY environment variable.")
        print("   Set it with: export CHADGPT_API_KEY='your-key'")
        print("\n📋 Demo will show smart model selection only...")
        await demo_smart_selection_comparison()
        return

    # Demo tasks
    tasks = [
        {
            "description": "Create a function to calculate the factorial of a number",
            "complexity": "Simple",
            "expected_gen": "gpt-5-mini",
            "expected_rev": "claude-4.5-sonnet",
        },
        {
            "description": "Create a REST API endpoint for user authentication",
            "complexity": "Complex",
            "expected_gen": "gpt-5",
            "expected_rev": "claude-4.1-opus",
        },
        {
            "description": "Implement a machine learning pipeline with data preprocessing",
            "complexity": "Expert",
            "expected_gen": "gpt-5",
            "expected_rev": "claude-4.1-opus",
        },
    ]

    print(f"\n📋 Demo Tasks:")
    for i, task in enumerate(tasks, 1):
        print(f"   {i}. {task['description']} ({task['complexity']})")

    # Test each task
    for i, task in enumerate(tasks, 1):
        print(f"\n{'='*60}")
        print(f"📝 Task {i}: {task['description']}")
        print(f"🏷️  Complexity: {task['complexity']}")
        print(f"{'='*60}")

        await demo_task_comparison(task, i)


async def demo_smart_selection_comparison():
    """Demo smart model selection comparison."""
    print(f"\n🧠 Smart Model Selection Comparison")
    print("-" * 40)

    selector = get_smart_selector()

    # Demo tasks
    tasks = [
        "Create a simple calculator class",
        "Implement a distributed caching system",
        "Review code for security vulnerabilities",
        "Write comprehensive unit tests",
    ]

    print(f"\n📊 Model Selection Analysis:")
    print(f"{'Task':<40} {'Generator':<15} {'Reviewer':<15} {'Confidence':<10}")
    print("-" * 85)

    for task in tasks:
        gen_rec = selector.recommend_model(task, "python")
        rev_rec = selector.recommend_model(
            "Review generated code for quality and best practices", "python"
        )

        print(
            f"{task[:39]:<40} {gen_rec.model:<15} {rev_rec.model:<15} {gen_rec.confidence:.2f}"
        )


async def demo_task_comparison(task_info, task_num):
    """Demo comparison for a specific task."""
    task = task_info["description"]
    complexity = task_info["complexity"]
    expected_gen = task_info["expected_gen"]
    expected_rev = task_info["expected_rev"]

    try:
        # Create agents
        generator = CodeGeneratorAgent(external_provider="chadgpt-real")
        reviewer = CodeReviewerAgent(external_provider="chadgpt-real")

        # Get smart recommendations
        gen_rec = generator.get_smart_model_recommendation(task, "python")
        rev_rec = reviewer.get_smart_model_recommendation(
            "Review generated code for quality and best practices", "python"
        )

        print(f"\n🧠 Smart Model Selection:")
        print(f"   Generator: {gen_rec.model} (confidence: {gen_rec.confidence:.2f})")
        print(f"   Reviewer: {rev_rec.model} (confidence: {rev_rec.confidence:.2f})")

        # Check if recommendations match expectations
        gen_match = gen_rec.model == expected_gen
        rev_match = rev_rec.model == expected_rev

        print(f"\n✅ Expected vs Actual:")
        print(
            f"   Generator: {expected_gen} {'✅' if gen_match else '❌'} → {gen_rec.model}"
        )
        print(
            f"   Reviewer: {expected_rev} {'✅' if rev_match else '❌'} → {rev_rec.model}"
        )

        # Switch to smart models
        print(f"\n🔄 Switching to smart models...")
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
            requirements=["Include error handling", "Add docstrings", "Add type hints"],
        )

        gen_result = await generator.process(gen_request)

        print(f"✅ Code generated!")
        print(f"📊 Tokens: {gen_result.tokens_used}")
        print(f"⏱️  Time: {gen_result.processing_time:.2f}s")
        print(f"📏 Length: {len(gen_result.generated_code)} characters")

        # Review code
        print(f"\n🔍 Reviewing code with {rev_rec.model}...")
        rev_request = CodeReviewRequest(
            code_to_review=gen_result.generated_code,
            language="python",
            review_focus=["quality", "best_practices", "security", "performance"],
        )

        rev_result = await reviewer.process(rev_request)

        print(f"✅ Code review completed!")
        print(f"📊 Tokens: {rev_result.tokens_used}")
        print(f"⏱️  Time: {rev_result.processing_time:.2f}s")

        # Show results
        print(f"\n📊 Results Summary:")
        print(f"   Quality Score: {rev_result.code_quality_score}/10")
        print(f"   Issues found: {len(rev_result.issues)}")
        print(f"   Recommendations: {len(rev_result.recommendations)}")

        # Show code snippet
        print(f"\n📝 Generated Code:")
        print("-" * 50)
        print(gen_result.generated_code)

        # Show review snippet
        if rev_result.issues:
            print(f"\n⚠️  Issues (first 3):")
            for issue in rev_result.issues[:3]:
                print(f"   • {issue}")

        if rev_result.recommendations:
            print(f"\n💡 Recommendations (first 3):")
            for rec in rev_result.recommendations[:3]:
                print(f"   • {rec}")

        # Performance summary
        total_time = gen_result.processing_time + rev_result.processing_time
        total_tokens = gen_result.tokens_used + rev_result.tokens_used

        print(f"\n📈 Performance Summary:")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Total tokens: {total_tokens}")
        print(f"   Quality score: {rev_result.code_quality_score}/10")
        print(f"   Model efficiency: {total_tokens/total_time:.1f} tokens/sec")

        # Comparison with original system
        print(f"\n🔄 Comparison with Original StarCoder System:")
        print(f"   Original: Single model (starcoder) for both generation and review")
        print(f"   ChadGPT: Smart model selection ({gen_rec.model} + {rev_rec.model})")
        print(f"   Advantage: Specialized models for different tasks")
        print(f"   Quality: {rev_result.code_quality_score}/10 (ChadGPT smart system)")

    except Exception as e:
        print(f"❌ Task {task_num} failed: {str(e)}")


async def demo_workflow_comparison():
    """Demo comparing complete workflows."""
    print(f"\n🔄 Complete Workflow Comparison")
    print("-" * 35)

    # Check API key
    has_chadgpt = bool(os.getenv("CHADGPT_API_KEY"))
    if not has_chadgpt:
        print("⏭️  Skipping (no API key)")
        return

    # Complex task
    task = "Create a complete web application with authentication, CRUD operations, and API documentation"
    print(f"📝 Complex Task: {task}")

    try:
        # Create agents
        generator = CodeGeneratorAgent(external_provider="chadgpt-real")
        reviewer = CodeReviewerAgent(external_provider="chadgpt-real")

        # Get smart recommendations
        gen_rec = generator.get_smart_model_recommendation(task, "python")
        rev_rec = reviewer.get_smart_model_recommendation(
            "Review generated web application code for security and best practices",
            "python",
        )

        print(f"🎯 Generator: {gen_rec.model} (confidence: {gen_rec.confidence:.2f})")
        print(f"🎯 Reviewer: {rev_rec.model} (confidence: {rev_rec.confidence:.2f})")

        # Switch to smart models
        await generator.switch_to_smart_model(task, "python")
        await reviewer.switch_to_smart_model(
            "Review generated web application code for security and best practices",
            "python",
        )

        # Generate code
        print(f"\n⚡ Generating web application...")
        gen_request = CodeGenerationRequest(
            task_description=task,
            language="python",
            requirements=[
                "Use FastAPI",
                "Include JWT authentication",
                "Add comprehensive error handling",
                "Include API documentation",
                "Add database integration",
            ],
        )

        gen_result = await generator.process(gen_request)

        # Review code
        print(f"\n🔍 Reviewing web application...")
        rev_request = CodeReviewRequest(
            code_to_review=gen_result.generated_code,
            language="python",
            review_focus=["security", "best_practices", "performance", "scalability"],
        )

        rev_result = await reviewer.process(rev_request)

        # Show comprehensive results
        print(f"\n📊 Comprehensive Results:")
        print(f"   Code length: {len(gen_result.generated_code)} characters")
        print(f"   Quality score: {rev_result.code_quality_score}/10")
        print(
            f"   Security issues: {len([i for i in rev_result.issues if 'security' in i.lower()])}"
        )
        print(
            f"   Performance issues: {len([i for i in rev_result.issues if 'performance' in i.lower()])}"
        )
        print(f"   Total recommendations: {len(rev_result.recommendations)}")

        # Show code structure
        print(f"\n📝 Generated Code Structure:")
        lines = gen_result.generated_code.split("\n")
        for i, line in enumerate(lines):
            if line.strip():
                print(f"   {i+1:2d}: {line}")

        # Show security review
        security_issues = [i for i in rev_result.issues if "security" in i.lower()]
        if security_issues:
            print(f"\n🔒 Security Review:")
            for issue in security_issues[:3]:
                print(f"   • {issue}")

        # Performance summary
        total_time = gen_result.processing_time + rev_result.processing_time
        total_tokens = gen_result.tokens_used + rev_result.tokens_used

        print(f"\n📈 Performance Metrics:")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Total tokens: {total_tokens}")
        print(
            f"   Generation rate: {len(gen_result.generated_code)/gen_result.processing_time:.1f} chars/sec"
        )
        print(
            f"   Review rate: {len(rev_result.review_result)/rev_result.processing_time:.1f} chars/sec"
        )

    except Exception as e:
        print(f"❌ Workflow comparison failed: {str(e)}")


async def main():
    """Main demo function."""
    print("🌟 StarCoder vs ChadGPT Smart System Comparison")
    print("=" * 60)
    print("🔄 Comparing Original Multi-Agent System with Smart Model Selection")
    print("=" * 60)

    try:
        # Main comparison demo
        await demo_comparison()

        # Workflow comparison
        await demo_workflow_comparison()

        print(f"\n🎉 Comparison demo completed!")
        print(f"\n📊 Key Differences:")
        print(f"  Original StarCoder System:")
        print(f"    • Single model (starcoder) for all tasks")
        print(f"    • Fixed model selection")
        print(f"    • No task-specific optimization")

        print(f"\n  ChadGPT Smart System:")
        print(f"    • Multiple specialized models")
        print(f"    • Smart model selection based on task analysis")
        print(f"    • Optimized for different task types")
        print(f"    • Better quality and performance")

        print(f"\n🚀 Advantages of ChadGPT Smart System:")
        print(f"  • Automatic model selection based on task complexity")
        print(f"  • Specialized models for generation vs review")
        print(f"  • Better code quality through expert models")
        print(f"  • Faster execution for simple tasks")
        print(f"  • More comprehensive analysis for complex tasks")

    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
