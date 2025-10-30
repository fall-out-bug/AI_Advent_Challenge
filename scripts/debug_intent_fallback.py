#!/usr/bin/env python3
"""Test script to debug IntentOrchestrator fallback behavior.

This script helps identify why LLM parsing might be falling back to deterministic parser.
Run with DEBUG logging to see detailed logs.

Usage:
    python scripts/debug_intent_fallback.py "напомни завтра в 9 купить хлеба"
"""

import asyncio
import logging
import sys

# Enable DEBUG logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from src.application.orchestration.intent_orchestrator import IntentOrchestrator


async def main() -> None:
    """Test intent parsing with detailed logging."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/debug_intent_fallback.py 'текст задачи'")
        sys.exit(1)
    
    text = " ".join(sys.argv[1:])
    print(f"\n🔍 Testing intent parsing for: '{text}'\n")
    
    orchestrator = IntentOrchestrator(use_llm=True, model_name="mistral")
    
    print(f"LLM enabled: {orchestrator.use_llm}")
    print(f"LLM client available: {orchestrator.llm_client is not None}")
    print()
    
    result = await orchestrator.parse_task_intent(text=text, context={})
    
    print("\n📊 Result:")
    print(f"  Title: {result.title}")
    print(f"  Description: {result.description}")
    print(f"  Deadline: {result.deadline_iso}")
    print(f"  Priority: {result.priority}")
    print(f"  Needs clarification: {result.needs_clarification}")
    if result.questions:
        print(f"  Questions: {result.questions}")


if __name__ == "__main__":
    asyncio.run(main())

