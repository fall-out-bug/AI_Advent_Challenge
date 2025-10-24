#!/usr/bin/env python3
"""Interactive demo of smart ChadGPT integration."""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from agents.core.code_generator import CodeGeneratorAgent
from agents.core.smart_model_selector import get_smart_selector
from communication.message_schema import CodeGenerationRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class InteractiveDemo:
    """Interactive demo of smart ChadGPT features."""

    def __init__(self):
        """Initialize the demo."""
        self.has_chadgpt = bool(os.getenv("CHADGPT_API_KEY"))
        self.selector = get_smart_selector()

    async def run(self):
        """Run the interactive demo."""
        print("🎮 Interactive Smart ChadGPT Demo")
        print("=" * 35)

        # Check API key
        await self._check_api_key()

        # Show menu
        while True:
            print(f"\n📋 Available Options:")
            print(f"   1. 🧠 Smart Model Recommendation")
            print(f"   2. 🤖 Live Code Generation (requires API key)")
            print(f"   3. 📊 Model Capabilities")
            print(f"   4. 🎯 Task Analysis Demo")
            print(f"   5. ❌ Exit")

            choice = input(f"\n👉 Choose an option (1-5): ").strip()

            if choice == "1":
                await self._demo_recommendation()
            elif choice == "2":
                await self._demo_live_generation()
            elif choice == "3":
                await self._demo_capabilities()
            elif choice == "4":
                await self._demo_task_analysis()
            elif choice == "5":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please try again.")

    async def _check_api_key(self):
        """Check API key availability."""
        print(f"\n🔑 API Key Status:")
        print(f"   ChadGPT: {'✅ Available' if self.has_chadgpt else '❌ Not set'}")

        if not self.has_chadgpt:
            print("\n⚠️  Some features require CHADGPT_API_KEY environment variable.")
            print("   Set it to test live API calls: export CHADGPT_API_KEY='your-key'")

    async def _demo_recommendation(self):
        """Demo smart model recommendation."""
        print(f"\n🧠 Smart Model Recommendation")
        print("-" * 30)

        # Get task from user
        task = input("📝 Enter your task description: ").strip()

        if not task:
            print("❌ Please enter a task description.")
            return

        # Get language preference
        language = (
            input("🔤 Programming language (default: python): ").strip() or "python"
        )

        # Get preference
        print(f"\n⚙️  Choose preference:")
        print(f"   1. ⚖️  Balanced (default)")
        print(f"   2. ⚡ Speed")
        print(f"   3. 🎯 Quality")

        pref_choice = input("👉 Choose preference (1-3): ").strip()

        prefer_speed = pref_choice == "2"
        prefer_quality = pref_choice == "3"

        # Get recommendation
        recommendation = self.selector.recommend_model(
            task, language, prefer_speed, prefer_quality
        )

        print(f"\n🎯 Recommendation:")
        print(f"   Model: {recommendation.model}")
        print(f"   Confidence: {recommendation.confidence:.2f}")
        print(f"   Max tokens: {recommendation.max_tokens}")
        print(f"   Temperature: {recommendation.temperature}")
        print(f"   Reasoning: {recommendation.reasoning}")

        # Show all recommendations
        show_all = input(f"\n❓ Show all model recommendations? (y/n): ").strip().lower()

        if show_all == "y":
            print(f"\n📈 All Model Recommendations:")
            all_recommendations = self.selector.get_all_recommendations(task, language)

            for i, rec in enumerate(all_recommendations, 1):
                status = "✅" if rec.model == recommendation.model else "  "
                print(f"   {status} {i}. {rec.model}: {rec.confidence:.2f}")
                print(f"      {rec.reasoning}")

    async def _demo_live_generation(self):
        """Demo live code generation."""
        print(f"\n🤖 Live Code Generation")
        print("-" * 25)

        if not self.has_chadgpt:
            print("❌ This feature requires CHADGPT_API_KEY.")
            print("   Set it with: export CHADGPT_API_KEY='your-key'")
            return

        # Get task from user
        task = input("📝 Enter your coding task: ").strip()

        if not task:
            print("❌ Please enter a coding task.")
            return

        # Get language
        language = (
            input("🔤 Programming language (default: python): ").strip() or "python"
        )

        # Get requirements
        requirements_input = input("📋 Additional requirements (optional): ").strip()
        requirements = requirements_input.split(",") if requirements_input else []

        try:
            # Create generator
            generator = CodeGeneratorAgent(external_provider="chadgpt-real")

            # Get smart recommendation
            recommendation = generator.get_smart_model_recommendation(task, language)

            print(f"\n🎯 Smart recommendation: {recommendation.model}")
            print(f"💭 Reasoning: {recommendation.reasoning}")

            # Switch to smart model
            print("🔄 Switching to recommended model...")
            success = await generator.switch_to_smart_model(task, language)

            if success:
                print("✅ Successfully switched to smart model")

                # Generate code
                request = CodeGenerationRequest(
                    task_description=task, language=language, requirements=requirements
                )

                print("🔄 Generating code...")
                result = await generator.process(request)

                print(f"✅ Code generated successfully!")
                print(f"📊 Tokens used: {result.tokens_used}")
                print(f"⏱️  Processing time: {result.processing_time:.2f}s")

                # Show code
                print(f"\n📄 Generated code:")
                print("```" + language)
                print(result.generated_code)
                print("```")

                # Ask if user wants to save
                save = input(f"\n💾 Save code to file? (y/n): ").strip().lower()
                if save == "y":
                    filename = (
                        input("📁 Enter filename (default: generated_code.py): ").strip()
                        or "generated_code.py"
                    )
                    with open(filename, "w") as f:
                        f.write(result.generated_code)
                    print(f"✅ Code saved to {filename}")

            else:
                print("❌ Failed to switch to smart model")

        except Exception as e:
            print(f"❌ Generation failed: {e}")

    async def _demo_capabilities(self):
        """Demo model capabilities."""
        print(f"\n📊 Model Capabilities")
        print("-" * 25)

        capabilities = self.selector.get_model_capabilities()

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

    async def _demo_task_analysis(self):
        """Demo task analysis."""
        print(f"\n🎯 Task Analysis Demo")
        print("-" * 25)

        # Get task from user
        task = input("📝 Enter your task description: ").strip()

        if not task:
            print("❌ Please enter a task description.")
            return

        # Analyze task
        analysis = self.selector.analyze_task(task)

        print(f"\n🔍 Task Analysis:")
        print(f"   Type: {analysis['task_type'].value}")
        print(f"   Complexity: {analysis['complexity'].value}")
        print(f"   Estimated length: {analysis['estimated_length']} characters")
        print(f"   Language: {analysis['language']}")

        if analysis["special_requirements"]:
            print(
                f"   Special requirements: {', '.join(analysis['special_requirements'])}"
            )

        # Show how this affects model selection
        print(f"\n🎯 How this affects model selection:")

        for model, capabilities in self.selector.model_capabilities.items():
            score = 0.0

            # Task type match
            if analysis["task_type"] in capabilities["best_for"]:
                score += 0.3

            # Complexity match
            if analysis["complexity"] in capabilities["complexity"]:
                score += 0.3

            # Code length consideration
            if analysis["estimated_length"] <= capabilities["max_tokens"]:
                score += 0.2
            else:
                score -= 0.1

            print(f"   {model}: {score:.2f} (max tokens: {capabilities['max_tokens']})")


async def main():
    """Main demo function."""
    demo = InteractiveDemo()
    await demo.run()


if __name__ == "__main__":
    asyncio.run(main())
