"""Prompt templates for Mistral orchestrator."""

INTENT_PARSING_PROMPT = """Analyze request and return ONLY JSON.

Tools: generate_code, review_code, generate_tests, format_code, analyze_complexity, formalize_task
Use generate_code when user asks to build/create/make code.

Return: {{"primary_goal": "...", "tools_needed": [...], "parameters": {{}}, "confidence": 0.8, "needs_clarification": false, "unclear_aspects": []}}

Request: {message}
{context_text}
JSON:"""

PLAN_GENERATION_PROMPT = """Generate execution plan. Minimize tool usage.

Goal: {primary_goal}{context_part}
Tools: generate_code, review_code, generate_tests, format_code, analyze_complexity, formalize_task
Use generate_code unless user explicitly needs review/testing/analysis.

Return JSON array (1-2 tools max): [{{"tool": "...", "args": {{...}}}}]
JSON:"""

CLARIFICATION_PROMPT = """Ask 1-3 concise questions about: {unclear_aspects}"""
