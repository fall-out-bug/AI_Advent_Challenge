#!/usr/bin/env python3
"""Example 5: Error Handling

This example demonstrates comprehensive error handling patterns
when working with the multi-agent system.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from exceptions import (
    AgentCommunicationError,
    CodeGenerationError,
    CodeReviewError,
    StarCoderError,
    ValidationError,
)
from orchestrator import process_simple_task


class ErrorHandlingDemo:
    """Demonstrates various error handling scenarios."""

    @staticmethod
    async def test_validation_error():
        """Test validation error handling."""
        print("🧪 Testing validation error...")

        try:
            # This should trigger a validation error
            result = await process_simple_task(
                task_description="", language="python"  # Empty task description
            )
            print("   Unexpected success")
        except ValidationError as e:
            print(f"   ✅ Caught ValidationError: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")

    @staticmethod
    async def test_generation_error():
        """Test code generation error handling."""
        print("🧪 Testing generation error...")

        try:
            # This might trigger a generation error
            result = await process_simple_task(
                task_description="Create a function that does impossible things like solving P=NP",
                language="python",
                requirements=["Must be impossible", "Should fail"],
            )

            if not result.success:
                print(f"   ✅ Generation failed as expected: {result.error_message}")
            else:
                print("   ⚠️  Generation succeeded unexpectedly")

        except CodeGenerationError as e:
            print(f"   ✅ Caught CodeGenerationError: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")

    @staticmethod
    async def test_review_error():
        """Test code review error handling."""
        print("🧪 Testing review error...")

        try:
            # This should work fine
            result = await process_simple_task(
                task_description="Create a simple hello world function",
                language="python",
            )

            if result.success:
                print("   ✅ Review completed successfully")
                print(
                    f"   📊 Quality score: {result.review_result.code_quality_score}/10"
                )
            else:
                print(f"   ❌ Review failed: {result.error_message}")

        except CodeReviewError as e:
            print(f"   ✅ Caught CodeReviewError: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")

    @staticmethod
    async def test_network_error():
        """Test network/communication error handling."""
        print("🧪 Testing network error...")

        try:
            # This will fail if services are not running
            result = await process_simple_task(
                task_description="Create a test function", language="python"
            )

            if result.success:
                print("   ✅ Network communication successful")
            else:
                print(f"   ❌ Network error: {result.error_message}")

        except AgentCommunicationError as e:
            print(f"   ✅ Caught AgentCommunicationError: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")

    @staticmethod
    async def test_timeout_error():
        """Test timeout error handling."""
        print("🧪 Testing timeout error...")

        try:
            # This might timeout with a very complex task
            result = await process_simple_task(
                task_description="Create a complete web framework with authentication, database ORM, API endpoints, frontend, and deployment scripts",
                language="python",
                requirements=[
                    "Must be production ready",
                    "Include all features",
                    "Handle all edge cases",
                ],
            )

            if result.success:
                print("   ✅ Complex task completed successfully")
                print(f"   ⏱️  Time: {result.workflow_time:.2f}s")
            else:
                print(f"   ❌ Task failed: {result.error_message}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    @staticmethod
    async def test_graceful_degradation():
        """Test graceful degradation when services are partially available."""
        print("🧪 Testing graceful degradation...")

        try:
            # Try a simple task
            result = await process_simple_task(
                task_description="Create a function to add two numbers",
                language="python",
            )

            if result.success:
                print("   ✅ Service available - full functionality")
                print(f"   📊 Quality: {result.review_result.code_quality_score}/10")
            else:
                print("   ⚠️  Service degraded - limited functionality")
                print(f"   Error: {result.error_message}")

        except Exception as e:
            print(f"   ❌ Service unavailable: {e}")
            print("   💡 This is expected if services are not running")


async def main():
    """Run error handling examples."""
    print("🚀 Example 5: Error Handling")
    print("=" * 50)

    demo = ErrorHandlingDemo()

    # Run all error handling tests
    await demo.test_validation_error()
    await demo.test_generation_error()
    await demo.test_review_error()
    await demo.test_network_error()
    await demo.test_timeout_error()
    await demo.test_graceful_degradation()

    print("\n📚 Error Handling Best Practices:")
    print("-" * 50)
    print("1. Always check result.success before accessing result data")
    print("2. Use specific exception types for different error scenarios")
    print("3. Implement retry logic for transient errors")
    print("4. Provide meaningful error messages to users")
    print("5. Log errors for debugging and monitoring")
    print("6. Implement graceful degradation when possible")
    print("7. Use timeouts to prevent hanging requests")
    print("8. Validate inputs before processing")

    print("\n🔧 Error Recovery Strategies:")
    print("-" * 50)
    print("• Retry with exponential backoff")
    print("• Fallback to simpler implementations")
    print("• Cache successful results")
    print("• Use circuit breaker pattern")
    print("• Implement health checks")
    print("• Monitor error rates and patterns")


if __name__ == "__main__":
    asyncio.run(main())
