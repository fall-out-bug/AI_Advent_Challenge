<!-- 86473cf7-3a7d-44c3-8ebe-ddcffc5e019a c4d296dc-8110-4bbb-84c6-2de940d51579 -->
# Phase 2 Plan — NLP Integration and Natural-Language Tasks

## Scope

- Orchestrator for intent parsing and clarifying questions
- LLM-backed parsing of free-form text into structured task intents
- Bot flow: ask clarifications; when resolved, create tasks via MCP
- End-to-end tests for parsing, clarifications, and task creation

## Architecture Decisions (chief-architect)

- Introduce `Intent` schema (`IntentParseResult`, `ClarificationQuestion`) under `src/domain/entities/intent.py`
- Create orchestrator service `src/application/orchestration/intent_orchestrator.py`
- Depends on `LLMClient` interface for model calls
- Stateless, pure functions for parse/clarify; side effects delegated to bot/MCP
- Implement `LLMClient` with provider-agnostic adapter `src/infrastructure/clients/llm_client.py`
- Pluggable backends: (a) local mistral wrapper if present, (b) HTTP provider(s)
- Expose MCP tool `parse_task_intent` in `src/presentation/mcp/tools/nlp_tools.py` that uses orchestrator
- Bot integration: extend `src/presentation/bot/butler_bot.py` to call MCP `parse_task_intent`, run clarification loop, then call reminder tools

## Files to Add/Change

- Add: `src/domain/entities/intent.py`
- Pydantic models: `IntentParseResult` (title, description, deadline, priority, tags, needs_clarification, questions[])
- Add: `src/infrastructure/clients/llm_client.py`
- `LLMClient` protocol; `MistralClient` and `FallbackLLMClient`
- Add: `src/application/orchestration/intent_orchestrator.py`
- `parse_task_intent(text: str, context: dict) -> IntentParseResult`
- `refine_with_answers(original: IntentParseResult, answers: list[str]) -> IntentParseResult`
- Add: `src/presentation/mcp/tools/nlp_tools.py`
- MCP tool `parse_task_intent(text: str, user_context: dict | None)` returning `dict`
- Change: `src/presentation/mcp/server.py`
- Import `src/presentation/mcp/tools/nlp_tools` to register tool
- Change: `src/presentation/bot/butler_bot.py`
- Add `handle_natural_language` flow:
  - call MCP `parse_task_intent`
  - if `needs_clarification` → ask questions, collect answers, re-parse
  - on resolved intent → call `add_task` tool and confirm

## LLM Prompting (ml-engineer)

- Prompt templates under `src/presentation/mcp/prompts/intent_parsing.py`
- System: role, output JSON schema, constraints
- User: task text + optional context (locale/timezone)
- JSON mode with robust schema validation and retries (2 attempts) on parse failure

## Testing Strategy (TDD)

- Add unit tests:
- `src/tests/domain/test_intent_models.py`
- `src/tests/application/test_intent_orchestrator.py` (mock LLM)
- `src/tests/presentation/mcp/test_nlp_tools.py`
- Bot flow tests (integration, async):
- `src/tests/presentation/bot/test_natural_language_flow.py` (simulate messages, mock MCP client calls)
- Ensure coverage ≥80% for new modules

## Config & Env

- Extend `src/infrastructure/config/settings.py` with:
- `llm_model`, `llm_temperature`, `llm_max_tokens`, optional provider keys
- Default to a lightweight model/provider if local mistral not available

## Non-Goals

- Channel digests and workers (Phase 4)
- Advanced date parsing beyond ISO; will add `dateparser` in Phase 3 if needed

## Final Deliverable

- Exactly one summary file at `tasks/day_11/day_11-phase-02-summary.md` containing:
- Completed items and architecture decisions
- How to run (env, docker if any) and how to run tests
- Example prompts and clarification loop transcript example
- Known limitations and Phase 3 pointers

## To-dos

- [ ] Define intent models and validations
- [ ] Implement LLM client(s) and abstraction
- [ ] Build intent orchestrator (parse/refine)
- [ ] Add MCP `parse_task_intent` tool and register
- [ ] Extend bot NL flow (clarify → create task)
- [ ] Add prompts for intent parsing
- [ ] Write unit tests (models, orchestrator, tools)
- [ ] Write bot flow integration test
- [ ] Update settings for LLM config

### To-dos

- [ ] Define intent Pydantic models and validations
- [ ] Implement LLMClient abstraction and provider(s)
- [ ] Implement parse/refine in intent_orchestrator
- [ ] Add MCP parse_task_intent tool and register
- [ ] Extend bot natural-language flow with clarifications → add_task
- [ ] Add intent parsing prompt templates
- [ ] Write unit tests for models, orchestrator, NLP tool
- [ ] Add integration test for bot NL flow
- [ ] Extend settings with LLM config defaults