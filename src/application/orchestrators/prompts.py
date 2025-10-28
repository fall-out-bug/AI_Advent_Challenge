"""Prompt templates for Mistral orchestrator.

Following the Zen of Python:
- Simple is better than complex
- Explicit is better than implicit
- Flat is better than nested
"""

# Intent parsing prompt
INTENT_PARSING_PROMPT = """You are an AI assistant. Analyze user requests and return ONLY valid JSON.

Available tools:
- generate_code: Generate code from description (USE THIS when user asks to build/create/make code)
- review_code: Review and improve code
- generate_tests: Generate tests for code
- format_code: Format code with black
- analyze_complexity: Analyze code complexity
- formalize_task: Convert task description to structured plan

Analyze this request and return ONLY this JSON structure:
{{
  "primary_goal": "brief description of what user wants",
  "tools_needed": [],
  "parameters": {{}},
  "confidence": 0.8,
  "needs_clarification": false,
  "unclear_aspects": []
}}

Rules:
- Return ONLY the JSON object, no other text
- If user asks to build/create/make code, ALWAYS include "generate_code" in tools_needed
- If user asks to review code, include "review_code" in tools_needed
- If user asks to generate/create tests, include "generate_tests" in tools_needed
- Set needs_clarification to true only if the request is truly unclear
- Set confidence between 0.5 and 1.0
- Consider previous messages in context when understanding "this code", "it", etc.

User request: {message}
{context_text}

JSON response:"""

# Plan generation prompt
PLAN_GENERATION_PROMPT = """Generate execution plan. Use MINIMAL tools - only what's absolutely needed.

User goal: {primary_goal}{context_part}

Available MCP tools:
- generate_code: Generate Python code from description
- review_code: Review and improve code
- generate_tests: Generate tests for code
- format_code: Format code with black
- analyze_complexity: Analyze code complexity
- formalize_task: Convert task to structured plan

Important: Only use generate_code unless user explicitly asked for review/testing/analysis.

Return ONLY this JSON array format (use 1-2 tools max):
[
  {{"tool": "generate_code", "args": {{"description": "user's request", "model": "mistral"}}}}
]

JSON array:"""

# Clarification prompt
CLARIFICATION_PROMPT = """Generate 1-3 specific questions to clarify: {unclear_aspects}

Be concise and helpful."""

