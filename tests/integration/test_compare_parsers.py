"""Comparison test: LLM vs Fallback parser."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_root))

from src.application.orchestration.intent_orchestrator import IntentOrchestrator


async def compare_parsers():
    """Compare LLM and fallback parser results."""
    print("\n" + "=" * 80)
    print("LLM vs Fallback Parser Comparison")
    print("=" * 80 + "\n")

    llm_orchestrator = IntentOrchestrator(use_llm=True, model_name="mistral")
    fallback_orchestrator = IntentOrchestrator(use_llm=False)

    test_cases = [
        "напомни завтра в 9 купить хлеба",
        "Remind me to call mom tomorrow at 3pm",
        "Напомни позвонить маме",
    ]

    for text in test_cases:
        print(f"\nInput: '{text}'")
        print("-" * 80)

        # LLM parsing
        print("\n🤖 LLM Parser:")
        try:
            llm_result = await llm_orchestrator.parse_task_intent(text=text, context={})
            print(f"   Title: {llm_result.title}")
            print(f"   Deadline: {llm_result.deadline_iso}")
            print(f"   Priority: {llm_result.priority}")
            print(f"   Needs clarification: {llm_result.needs_clarification}")
            if llm_result.description:
                print(f"   Description: {llm_result.description}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Fallback parsing
        print("\n📝 Fallback Parser:")
        try:
            fallback_result = await fallback_orchestrator.parse_task_intent(
                text=text, context={}
            )
            print(f"   Title: {fallback_result.title}")
            print(f"   Deadline: {fallback_result.deadline_iso}")
            print(f"   Priority: {fallback_result.priority}")
            print(f"   Needs clarification: {fallback_result.needs_clarification}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        print()

    print("\n" + "=" * 80)
    print("Comparison completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(compare_parsers())
