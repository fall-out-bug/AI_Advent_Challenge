"""Detailed LLM intent parsing test with output."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_root))

from src.application.orchestration.intent_orchestrator import IntentOrchestrator


async def test_llm_parsing_detailed():
    """Test LLM parsing with detailed output."""
    print("\n" + "="*80)
    print("LLM Intent Parsing Test")
    print("="*80 + "\n")

    orchestrator = IntentOrchestrator(use_llm=True, model_name="mistral")
    
    test_cases = [
        {
            "text": "напомни завтра в 9 купить хлеба",
            "description": "Russian task with time"
        },
        {
            "text": "Remind me to call mom tomorrow at 3pm",
            "description": "English task with time"
        },
        {
            "text": "Срочно нужно позвонить врачу сегодня в 15:00, это очень важно",
            "description": "Complex Russian task with priority indicators"
        },
        {
            "text": "Напомни позвонить маме",
            "description": "Ambiguous task without time"
        },
        {
            "text": "купить молоко завтра в 9 утра",
            "description": "Russian task with morning time"
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Input: '{test_case['text']}'")
        print("-" * 80)
        
        try:
            result = await orchestrator.parse_task_intent(
                text=test_case['text'],
                context={}
            )
            
            print(f"✅ Title: {result.title}")
            print(f"✅ Deadline: {result.deadline_iso}")
            print(f"✅ Priority: {result.priority}")
            print(f"✅ Needs clarification: {result.needs_clarification}")
            if result.questions:
                print(f"✅ Questions: {result.questions}")
            if result.description:
                print(f"✅ Description: {result.description}")
            if result.tags:
                print(f"✅ Tags: {result.tags}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print()

    print("\n" + "="*80)
    print("Test completed!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_llm_parsing_detailed())

