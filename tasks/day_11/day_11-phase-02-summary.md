# Day 11 — Phase 2 Summary (NLP Integration)

## Scope delivered
- Intent models: `src/domain/entities/intent.py`
- LLM abstraction: `src/infrastructure/clients/llm_client.py`
- Orchestrator: `src/application/orchestration/intent_orchestrator.py`
- MCP NLP tool: `src/presentation/mcp/tools/nlp_tools.py` (registered in server)
- Bot NL flow: `src/presentation/bot/butler_bot.py` (parse → clarify → add_task)
- Prompt templates: `src/presentation/mcp/prompts/intent_parsing.py`
- Settings extended for LLM: `src/infrastructure/config/settings.py`
- Tests:
  - Domain: `src/tests/domain/test_intent_models.py`
  - Orchestrator: `src/tests/application/test_intent_orchestrator.py`
  - MCP NLP tool: `src/tests/ppresentation/mcp/test_nlp_tools.py`
  - Bot flow: `src/tests/presentation/bot/test_natural_language_flow.py`

## Architecture decisions
- Stateless orchestrator using pluggable `LLMClient`
- JSON-only prompting with schema hinting and defensive parsing fallback
- Bot remains thin; MCP handles parsing and task creation

## How to run tests
```bash
pytest --maxfail=1 --disable-warnings -q --cov=src --cov-report=term-missing
```

## Example prompt
- Input: "Напомни оплатить аренду 5 числа"
- Tool: `parse_task_intent` → returns intent with `title`, `deadline`, `priority`

## Known limitations
- Clarification refinement uses simple key-based merge
- No timezone normalization beyond provided context

## Next steps (Phase 3)
- Enhance date parsing (e.g., `dateparser` with locale)
- Expand bot menus and task/channel UIs
- Prepare workers for summaries/digests
