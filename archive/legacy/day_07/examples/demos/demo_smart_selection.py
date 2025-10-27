#!/usr/bin/env python3
"""Demo script showing smart model selection with ChadGPT."""

import asyncio
import logging
import os

# Add project root to path
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from agents.core.code_generator import CodeGeneratorAgent
from agents.core.smart_model_selector import get_smart_selector
from communication.message_schema import CodeGenerationRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def demo_smart_model_selection():
    """Demonstrate smart model selection capabilities."""
    print("🧠 Smart Model Selection Demo")
    print("=" * 50)

    # Check API keys
    has_chadgpt = bool(os.getenv("CHADGPT_API_KEY"))

    print(f"🔑 API Keys Status:")
    print(f"   ChadGPT: {'✅' if has_chadgpt else '❌'}")

    if not has_chadgpt:
        print(
            "\n⚠️  No ChadGPT API key found. This demo will show recommendations but skip actual API calls."
        )
        print("   Set CHADGPT_API_KEY to test smart model selection.")

    # Initialize smart selector
    selector = get_smart_selector()

    # Demo tasks with different complexities
    demo_tasks = [
        {
            "description": "Create a simple hello world function",
            "language": "python",
            "expected_model": "gpt-5-nano",
        },
        {
            "description": "Create a class for managing a binary search tree with insert, delete, and search methods",
            "language": "python",
            "expected_model": "gpt-5-mini",
        },
        {
            "description": "Implement a machine learning pipeline with data preprocessing, model training, and evaluation",
            "language": "python",
            "expected_model": "gpt-5",
        },
        {
            "description": "Review this code for security vulnerabilities and suggest improvements",
            "language": "python",
            "expected_model": "claude-4.1-opus",
        },
        {
            "description": "Create comprehensive unit tests for a complex algorithm",
            "language": "python",
            "expected_model": "claude-4.5-sonnet",
        },
    ]

    print(f"\n📋 Demo Tasks:")
    for i, task in enumerate(demo_tasks, 1):
        print(f"   {i}. {task['description']}")

    # Test smart recommendations
    print(f"\n🎯 Smart Model Recommendations:")
    print("-" * 40)

    for i, task in enumerate(demo_tasks, 1):
        print(f"\n📝 Task {i}: {task['description']}")
        print("-" * 30)

        # Get recommendation
        recommendation = selector.recommend_model(task["description"], task["language"])

        print(f"🎯 Recommended: {recommendation.model}")
        print(f"📊 Confidence: {recommendation.confidence:.2f}")
        print(f"💭 Reasoning: {recommendation.reasoning}")
        print(f"⚙️  Max tokens: {recommendation.max_tokens}")
        print(f"🌡️  Temperature: {recommendation.temperature}")

        # Show all recommendations
        all_recommendations = selector.get_all_recommendations(
            task["description"], task["language"]
        )

        print(f"\n📈 All model scores:")
        for rec in all_recommendations:
            status = "✅" if rec.model == recommendation.model else "  "
            print(f"   {status} {rec.model}: {rec.confidence:.2f} - {rec.reasoning}")

    # Demo speed vs quality preferences
    print(f"\n⚡ Speed vs Quality Preferences:")
    print("-" * 35)

    complex_task = "Implement a distributed microservices architecture with authentication and load balancing"

    print(f"📝 Task: {complex_task}")
    print()

    # Speed preference
    speed_rec = selector.recommend_model(complex_task, "python", prefer_speed=True)
    print(
        f"⚡ Speed preference: {speed_rec.model} (confidence: {speed_rec.confidence:.2f})"
    )
    print(f"   Reasoning: {speed_rec.reasoning}")

    # Quality preference
    quality_rec = selector.recommend_model(complex_task, "python", prefer_quality=True)
    print(
        f"🎯 Quality preference: {quality_rec.model} (confidence: {quality_rec.confidence:.2f})"
    )
    print(f"   Reasoning: {quality_rec.reasoning}")

    # Balanced (default)
    balanced_rec = selector.recommend_model(complex_task, "python")
    print(
        f"⚖️  Balanced: {balanced_rec.model} (confidence: {balanced_rec.confidence:.2f})"
    )
    print(f"   Reasoning: {balanced_rec.reasoning}")

    # Demo model capabilities
    print(f"\n🔧 Model Capabilities:")
    print("-" * 25)

    capabilities = selector.get_model_capabilities()
    for model, info in capabilities.items():
        print(f"\n🤖 {model}:")
        print(f"   Display: {info['display_name']}")
        print(f"   Description: {info['description']}")
        print(f"   Max tokens: {info['max_tokens']}")
        print(f"   Temperature: {info['temperature']}")
        print(f"   Speed: {info['speed']}")
        print(f"   Cost: {info['cost']}")
        print(f"   Best for: {', '.join([t.value for t in info['best_for']])}")
        print(f"   Complexity: {', '.join([c.value for c in info['complexity']])}")

    # Demo with actual agent (if API key available)
    if has_chadgpt:
        print(f"\n🤖 Smart Agent Demo:")
        print("-" * 20)

        try:
            # Create agent
            generator = CodeGeneratorAgent(
                model_name="gpt-5-mini", external_provider="chadgpt-real"
            )

            # Test smart model switching
            task = "Create a simple calculator class with basic operations"
            print(f"📝 Task: {task}")

            # Get recommendation
            recommendation = generator.get_smart_model_recommendation(task)
            print(f"🎯 Smart recommendation: {recommendation.reasoning}")

            # Try to switch to recommended model
            print("🔄 Switching to recommended model...")
            success = await generator.switch_to_smart_model(task)

            if success:
                print("✅ Successfully switched to recommended model")
                print(f"📊 Current provider: {generator.get_provider_info()}")

                # Generate code with smart model
                request = CodeGenerationRequest(
                    task_description=task, language="python"
                )

                print("🔄 Generating code with smart model...")
                result = await generator.process(request)

                print(f"✅ Generated code ({result.tokens_used} tokens):")
                print("```python")
                print(result.generated_code)
                print("```")

            else:
                print("❌ Failed to switch to recommended model")

        except Exception as e:
            print(f"❌ Smart agent demo failed: {e}")

    print(f"\n🎉 Smart Model Selection Demo completed!")
    print(f"\n📚 Key Features:")
    print(f"   • Automatic model selection based on task complexity")
    print(f"   • Support for speed vs quality preferences")
    print(f"   • Detailed model capabilities and recommendations")
    print(f"   • Integration with ChadGPT's multiple models")
    print(f"   • Smart switching between models")


if __name__ == "__main__":
    asyncio.run(demo_smart_model_selection())
