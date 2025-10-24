#!/usr/bin/env python3
"""Example usage of external API providers with agents."""

import asyncio
import logging
import os

# Add project root to path
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from agents.core.code_generator import CodeGeneratorAgent
from agents.core.code_reviewer import CodeReviewerAgent
from agents.core.external_api_config import ProviderConfig, ProviderType, get_config
from communication.message_schema import CodeGenerationRequest, CodeReviewRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_basic_usage():
    """Example of basic usage with external API providers."""
    print("🚀 Basic External API Usage Example")
    print("=" * 40)

    # Create generator agent with ChatGPT
    generator = CodeGeneratorAgent(
        model_name="gpt-3.5-turbo", external_provider="chatgpt"
    )

    # Create reviewer agent with Claude
    reviewer = CodeReviewerAgent(
        model_name="claude-3-sonnet-20240229", external_provider="claude"
    )

    # Generate code
    request = CodeGenerationRequest(
        task_description="Create a function that calculates fibonacci numbers",
        language="python",
        requirements=["Use memoization for efficiency", "Include type hints"],
    )

    print("📝 Generating code with ChatGPT...")
    generation_result = await generator.process(request)

    print(f"✅ Generated code ({generation_result.tokens_used} tokens):")
    print("-" * 30)
    print(generation_result.generated_code)
    print("-" * 30)

    # Review code
    review_request = CodeReviewRequest(
        task_description=request.task_description,
        generated_code=generation_result.generated_code,
        tests=generation_result.tests,
        metadata=generation_result.metadata,
    )

    print("\n🔍 Reviewing code with Claude...")
    review_result = await reviewer.process(review_request)

    print(f"✅ Review completed (Score: {review_result.code_quality_score}/10):")
    print("-" * 30)
    print(review_result.review_summary)
    print("-" * 30)


async def example_provider_switching():
    """Example of switching between providers dynamically."""
    print("\n🔄 Provider Switching Example")
    print("=" * 35)

    # Start with local model
    generator = CodeGeneratorAgent(model_name="starcoder")

    print(f"Current provider: {generator.get_provider_info()}")

    # Switch to ChatGPT
    print("Switching to ChatGPT...")
    success = await generator.switch_to_external_provider("chatgpt")

    if success:
        print(f"✅ Switched to: {generator.get_provider_info()}")

        # Generate code with ChatGPT
        request = CodeGenerationRequest(
            task_description="Create a simple calculator class", language="python"
        )

        result = await generator.process(request)
        print(f"Generated code with ChatGPT ({result.tokens_used} tokens)")

    else:
        print("❌ Failed to switch to ChatGPT")

    # Switch to Claude
    print("\nSwitching to Claude...")
    success = await generator.switch_to_external_provider("claude")

    if success:
        print(f"✅ Switched to: {generator.get_provider_info()}")

        # Generate code with Claude
        request = CodeGenerationRequest(
            task_description="Create a data validation function", language="python"
        )

        result = await generator.process(request)
        print(f"Generated code with Claude ({result.tokens_used} tokens)")

    else:
        print("❌ Failed to switch to Claude")

    # Switch back to local
    print("\nSwitching back to local model...")
    success = await generator.switch_to_local_model("mistral")

    if success:
        print(f"✅ Switched to: {generator.get_provider_info()}")
    else:
        print("❌ Failed to switch to local model")


async def example_configuration_management():
    """Example of managing provider configurations."""
    print("\n⚙️  Configuration Management Example")
    print("=" * 40)

    # Get configuration manager
    config = get_config()

    print("Current configuration:")
    stats = config.get_stats()
    print(f"  Total providers: {stats['total_providers']}")
    print(f"  Enabled providers: {stats['enabled_providers']}")
    print(f"  Default provider: {stats['default_provider']}")

    # Add a new provider
    print("\nAdding new provider...")
    new_provider = ProviderConfig(
        provider_type=ProviderType.CHATGPT,
        api_key="your-api-key-here",
        model="gpt-4",
        timeout=120.0,
        max_tokens=8000,
        temperature=0.5,
        enabled=True,
    )

    config.add_provider("chatgpt-4", new_provider)
    print("✅ Added ChatGPT-4 provider")

    # Validate configuration
    print("\nValidating configuration...")
    validation_results = config.validate_config()

    if validation_results["valid"]:
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration has errors:")
        for error in validation_results["errors"]:
            print(f"  • {error}")

    # Show provider details
    print("\nProvider details:")
    for name, provider_config in config.providers.items():
        status = "✅" if provider_config.enabled else "❌"
        print(
            f"  {status} {name}: {provider_config.provider_type.value} ({provider_config.model})"
        )


async def example_error_handling():
    """Example of error handling with external APIs."""
    print("\n🛡️  Error Handling Example")
    print("=" * 30)

    # Create agent with invalid provider
    try:
        generator = CodeGeneratorAgent(external_provider="nonexistent")
        print("❌ Should have failed with invalid provider")
    except Exception as e:
        print(f"✅ Caught expected error: {e}")

    # Create agent with valid provider but test availability
    generator = CodeGeneratorAgent(external_provider="chatgpt")

    print("Checking provider availability...")
    is_available = await generator.check_provider_availability()

    if is_available:
        print("✅ Provider is available")

        # Try to generate code
        try:
            request = CodeGenerationRequest(
                task_description="Create a simple function", language="python"
            )

            result = await generator.process(request)
            print(f"✅ Generated code successfully ({result.tokens_used} tokens)")

        except Exception as e:
            print(f"❌ Code generation failed: {e}")
    else:
        print("❌ Provider is not available")


async def example_performance_comparison():
    """Example of comparing performance between providers."""
    print("\n📊 Performance Comparison Example")
    print("=" * 35)

    task_description = "Create a function to sort a list of dictionaries by a key"

    providers_to_test = [
        ("local", "starcoder", None),
        ("chatgpt", "gpt-3.5-turbo", "chatgpt"),
        ("claude", "claude-3-sonnet-20240229", "claude"),
    ]

    results = {}

    for provider_name, model_name, external_provider in providers_to_test:
        print(f"\nTesting {provider_name}...")

        try:
            generator = CodeGeneratorAgent(
                model_name=model_name, external_provider=external_provider
            )

            # Check availability
            if not await generator.check_provider_availability():
                print(f"❌ {provider_name} is not available")
                continue

            # Generate code and measure time
            request = CodeGenerationRequest(
                task_description=task_description, language="python"
            )

            import time

            start_time = time.time()
            result = await generator.process(request)
            end_time = time.time()

            results[provider_name] = {
                "time": end_time - start_time,
                "tokens": result.tokens_used,
                "success": True,
            }

            print(
                f"✅ {provider_name}: {end_time - start_time:.2f}s, {result.tokens_used} tokens"
            )

        except Exception as e:
            print(f"❌ {provider_name} failed: {e}")
            results[provider_name] = {
                "time": None,
                "tokens": None,
                "success": False,
                "error": str(e),
            }

    # Show comparison
    print("\n📈 Performance Summary:")
    print("-" * 25)
    for provider_name, result in results.items():
        if result["success"]:
            print(
                f"{provider_name:10}: {result['time']:6.2f}s, {result['tokens']:4d} tokens"
            )
        else:
            print(
                f"{provider_name:10}: Failed - {result.get('error', 'Unknown error')}"
            )


async def main():
    """Run all examples."""
    print("🤖 External API Provider Examples")
    print("=" * 50)

    # Check if API keys are configured
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  Warning: No API keys found in environment variables.")
        print(
            "   Set OPENAI_API_KEY and/or ANTHROPIC_API_KEY to test external providers."
        )
        print("   Examples will show configuration but may fail on actual API calls.")
        print()

    try:
        await example_basic_usage()
        await example_provider_switching()
        await example_configuration_management()
        await example_error_handling()
        await example_performance_comparison()

        print("\n🎉 All examples completed!")

    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        logger.exception("Example execution failed")


if __name__ == "__main__":
    asyncio.run(main())
