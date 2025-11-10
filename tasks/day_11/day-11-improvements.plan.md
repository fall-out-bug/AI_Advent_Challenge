<!-- eda897aa-a578-47b5-882f-31ebb0154129 ebb66ee8-0f09-4fe9-be6a-ffb595247a58 -->
# Day 11 Butler Bot Improvements

## Context

Current state: Working bot with basic intent parsing, menu navigation, and worker-based notifications. Needs FSM conversation flow, better clarification handling, code quality improvements, and architectural refinements.

## Architecture Strategy

Keep existing Clean Architecture (domain/application/infrastructure/presentation) and enhance it with best practices from Perplexity spec:

- Add FSM state management in presentation layer
- Improve orchestrator with better prompts and clarification logic
- Refactor large functions (>15 lines) into smaller, testable units
- Remove debug print statements, add proper structured logging
- Ensure 80%+ test coverage for new code

## Implementation Plan

### Phase 1: FSM State Management (High Priority)

**Goal**: Implement conversation state management for natural language task creation with clarifying questions.

**Files to create**:

- `src/presentation/bot/states.py` - FSM state definitions using aiogram's StatesGroup
- `src/presentation/bot/middleware/state_middleware.py` - State persistence middleware

**Files to modify**:

- `src/presentation/bot/butler_bot.py` - Add FSM storage and update handlers to use states
- `src/presentation/bot/handlers/tasks.py` - Add clarification flow handlers

**Key features**:

- `TaskCreation.waiting_for_task` - Initial state for task input
- `TaskCreation.waiting_for_clarification` - State for answering clarifying questions
- Store partial intent in FSM context
- Handle multi-step clarifications with context preservation
- Timeout handling for abandoned conversations

**Testing**: Create `tests/presentation/bot/test_fsm_states.py`

### Phase 2: Enhanced Intent Orchestrator (High Priority)

**Goal**: Improve intent parsing with better prompts, structured output validation, and clarification logic.

**Files to modify**:

- `src/application/orchestration/intent_orchestrator.py`
- Refactor `parse_task_intent` to use improved prompts
- Add `generate_clarification_questions` method
- Add `validate_intent_completeness` method
- Improve JSON parsing with better error handling

**New domain entities**:

- `src/domain/entities/intent.py` - Add fields for clarification tracking

**Key improvements**:

- Better Russian-language prompts with examples
- Structured validation of deadline formats (ISO, relative dates)
- Detect ambiguous requests (e.g., "tomorrow" without time)
- Generate smart clarifying questions based on missing fields
- Priority inference from keywords (urgent, important, etc.)

**Testing**: Expand `tests/application/orchestration/test_intent_orchestrator.py`

### Phase 3: Code Quality Refactoring (Medium Priority)

**Goal**: Break down large functions, remove dead code, improve readability per Python Zen.

**Files to refactor**:

1. `src/workers/summary_worker.py` (705 lines, multiple functions >50 lines)

- Extract `_format_summary` into domain/value objects
- Split `_send_with_retry` into smaller methods
- Remove excessive debug print statements (lines 209-360)
- Move formatting logic to separate formatter class

2. `src/presentation/mcp/tools/reminder_tools.py` (382 lines, `get_summary` is 180 lines)

- Extract query building into repository method
- Split stats calculation into separate function
- Remove debug prints (lines 209-380)
- Simplify timezone handling

3. `src/infrastructure/llm/summarizer.py` (261 lines)

- Already has `MapReduceSummarizer` - good!
- Add missing `import asyncio` (line 246 uses it without import)
- Simplify cleaning logic into separate function
- Add type hints to all helper functions

**Create new modules**:

- `src/domain/value_objects/task_summary.py` - Summary formatting value object
- `src/domain/value_objects/digest_message.py` - Digest formatting value object
- `src/infrastructure/formatters/telegram_formatter.py` - Telegram message formatting

**Testing**: Maintain existing test coverage, add tests for extracted functions

### Phase 4: Menu Integration Improvements (Medium Priority)

**Goal**: Connect menu buttons to actual functionality (summary/digest are placeholders).

**Files to modify**:

- `src/presentation/bot/handlers/menu.py`
- Implement `callback_summary` to show task summary via MCP
- Implement `callback_digest` to show channel digest via MCP
- Add error handling with user-friendly messages

- `src/presentation/bot/butler_bot.py`
- Add helper methods for summary/digest display
- Reuse formatting from worker where applicable

**Testing**: Add integration tests for menu flow

### Phase 5: Enhanced Natural Language Handling (Medium Priority)

**Goal**: Improve bot's natural language processing with better feedback and error messages.

**Files to modify**:

- `src/presentation/bot/butler_bot.py`
- Enhance `handle_natural_language` with FSM integration
- Add typing indicators during LLM processing
- Better error messages when LLM unavailable
- Add conversation context (previous tasks, user preferences)

**Key improvements**:

- Show "thinking..." message while parsing
- Preserve conversation history for context-aware parsing
- Handle common phrases ("add task", "remind me", etc.)
- Graceful degradation when LLM is down

**Testing**: Add e2e tests for natural language flow

### Phase 6: Prompt Engineering (Low Priority)

**Goal**: Optimize LLM prompts for better intent extraction and Russian language support.

**New module**:

- `src/infrastructure/llm/prompts.py` - Already exists for map/reduce, expand it
- Add `get_intent_parse_prompt` with examples
- Add `get_clarification_prompt` for generating questions
- Add Russian/English language switching

**Files to modify**:

- `src/application/orchestration/intent_orchestrator.py` - Use new prompt functions

**Testing**: Create prompt testing suite with golden examples

### Phase 7: Testing & Documentation (Low Priority)

**Goal**: Achieve 80%+ coverage and update documentation.

**Tasks**:

- Add missing tests for FSM states
- Add integration tests for bot handlers
- Test clarification flow end-to-end
- Update README with new features
- Add docstrings to all new functions
- Create architecture diagram showing FSM flow

**Files to create**:

- `docs/reference/en/ARCHITECTURE_FSM.md` - FSM flow documentation
- `tests/integration/test_clarification_flow.py`
- `tests/presentation/bot/test_natural_language_flow.py`

### Phase 8: Configuration & Settings (Low Priority)

**Goal**: Make FSM behavior configurable.

**Files to modify**:

- `src/infrastructure/config/settings.py`
- Add `conversation_timeout_minutes` (default: 5)
- Add `max_clarification_attempts` (default: 3)
- Add `enable_context_aware_parsing` (default: True)

### Phase 9: Comprehensive Testing Strategy (High Priority - TDD)

**Goal**: Achieve 80%+ coverage with unit, integration, E2E, and contract tests following TDD principles.

**Unit Tests** (Test first, then implement):

- `tests/presentation/bot/test_fsm_states.py` - State transitions, timeout handling
- `tests/presentation/bot/test_state_middleware.py` - State persistence
- `tests/application/orchestration/test_intent_orchestrator.py` - Enhanced with clarification tests
- `tests/domain/value_objects/test_task_summary.py` - Formatting value objects
- `tests/infrastructure/formatters/test_telegram_formatter.py` - Message formatting

**Integration Tests** (Multi-component interaction):

- `tests/integration/test_clarification_flow.py`
  - Full flow: user input → intent parsing → clarifying questions → task creation
  - Mock LLM responses with realistic scenarios
  - Test state transitions with real FSM storage
  - Verify MCP tool calls with actual repository
  - Cleanup: Reset DB state after each test
- `tests/integration/test_bot_mcp_integration.py`
  - Bot handlers calling MCP tools
  - Error handling when MCP unavailable
  - Timeout and retry logic

**E2E Tests** (Full user journey):

- `tests/e2e/test_task_creation_journey.py`
  - User sends "Remind me to call mom tomorrow at 3pm"
  - Bot parses intent, asks clarification if needed
  - Task created in MongoDB
  - User sees confirmation
  - Worker sends notification at scheduled time
- `tests/e2e/test_digest_flow.py`
  - User subscribes to channel
  - Worker fetches posts and generates digest
  - User receives formatted digest message

**Contract Tests** (API/Tool schemas):

- `tests/contract/test_mcp_tools_schema.py`
  - Validate add_task/list_tasks/update_task schemas
  - Test backward compatibility of tool responses
  - Ensure intent parsing JSON structure
- `tests/contract/test_llm_prompts.py`
  - Golden examples for intent parsing prompts
  - Verify LLM output structure matches expected schema

**Test Infrastructure**:

- Add pytest fixtures for FSM storage setup/teardown
- Add factory for creating test tasks, intents, users
- Mock LLM responses with realistic Russian-language examples
- Docker compose test environment with isolated MongoDB

**Coverage Targets**:

- Overall: 80%+ (currently 76.10%)
- New code: 90%+ (all FSM and orchestrator code)
- Critical paths: 95%+ (task creation, notification sending)

### Phase 10: Documentation & Token Optimization (Medium Priority)

**Goal**: Create LLM-friendly documentation with optimal token usage.

**AI Reviewer Analysis Before Refactoring**:

1. Function Length Report:

   - Average: ~18 lines (NEEDS REDUCTION to 12)
   - Longest functions:
     - `get_summary` (reminder_tools.py): 180 lines → TARGET: 4 functions of 15 lines each
     - `_send_with_retry` (summary_worker.py): 190 lines → TARGET: 5 functions of 15 lines each
     - `_check_and_send` (summary_worker.py): 45 lines → TARGET: 3 functions of 15 lines each

2. Token Cost Analysis:

   - `summary_worker.py`: 705 lines ≈ 8,500 tokens (CRITICAL - split into 3 files)
   - `reminder_tools.py`: 382 lines ≈ 4,600 tokens (HIGH - split into 2 files)
   - `summarizer.py`: 261 lines ≈ 3,100 tokens (OK, minor improvements)
   - Target: <2,000 tokens per file

3. File Splitting Strategy:

   - `summary_worker.py` →
     - `summary_worker.py` (core loop, ~150 lines)
     - `notification_sender.py` (send logic with retry, ~200 lines)
     - `message_formatters.py` (all formatting, ~150 lines)
   - `reminder_tools.py` →
     - `reminder_tools.py` (CRUD tools, ~200 lines)
     - `summary_query_builder.py` (query logic, ~100 lines)

**Documentation Files to Create**:

1. `docs/reference/en/ARCHITECTURE_FSM.md` (500 lines, ~6K tokens):
````markdown
# FSM-Based Conversation Architecture

## Overview
Butler Bot uses Finite State Machine for multi-turn conversations with users.

## State Diagram
```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> WaitingForTask: User sends message
    WaitingForTask --> WaitingForClarification: Needs clarification
    WaitingForClarification --> TaskCreated: All questions answered
    WaitingForTask --> TaskCreated: Intent clear
    TaskCreated --> [*]
    WaitingForClarification --> Timeout: 5 minutes elapsed
    Timeout --> [*]
````


## States

### TaskCreation.waiting_for_task

Initial state when user sends natural language input...

### TaskCreation.waiting_for_clarification

State for collecting answers to clarifying questions...

## Example Flows

[3-4 realistic examples with Russian and English inputs]

````

2. `docs/reference/en/API_MCP_TOOLS.md` (300 lines, ~3.5K tokens):

```markdown
# MCP Tools API Reference

## add_task
Create a new task with optional scheduling.

**Args**:
- user_id (int): Telegram user ID
- title (str): Task title (max 256 chars)
- description (str): Optional description
- deadline (str|None): ISO datetime
- priority (str): "low"|"medium"|"high"
- tags (list[str]): Optional tags

**Returns**:
```json
{
  "task_id": "507f1f77bcf86cd799439011",
  "created_at": "2025-10-29T12:00:00Z",
  "status": "created"
}
````

**Example**:

```python
result = await mcp.call_tool("add_task", {
    "user_id": 12345,
    "title": "Call mom",
    "deadline": "2025-10-30T15:00:00Z",
    "priority": "high"
})
```
````

3. `docs/archive/2023-day11/QUICK_START_DAY11.md` (400 lines, ~4.5K tokens):

```markdown
# Butler Bot Quick Start

## Installation
```bash
# Clone and setup
cd AI_Challenge
make install

# Configure environment
cp .env.example .env
# Edit .env: add TELEGRAM_BOT_TOKEN
````

## Usage Examples

### Creating Tasks via Natural Language

Example 1: Simple task

```
User: "Buy milk"
Bot: "✅ Task added: Buy milk"
```

Example 2: With deadline

```
User: "Remind me to call mom tomorrow at 3pm"
Bot: "🤔 Which timezone? Please clarify: [UTC, Moscow, etc.]"
User: "Moscow"
Bot: "✅ Task added: Call mom
     📅 2025-10-30 15:00 MSK"
```

[5-6 more examples]

````

4. Update `CHANGELOG.md`:

```markdown
## [1.1.0] - Day 11 Improvements - 2025-10-29

### Added
- FSM-based conversation flow for multi-turn task creation
- Clarifying questions for ambiguous task inputs
- Enhanced intent orchestrator with context-aware parsing (Russian/English)
- Domain value objects for task summary and digest formatting
- Comprehensive test suite: 45 unit, 12 integration, 8 E2E, 6 contract tests
- MCP tools API documentation with examples
- Architecture diagrams for FSM flow

### Changed
- Refactored summary_worker.py: split into 3 modules (8500→6000 tokens, -30%)
- Refactored reminder_tools.py: extracted query builder (4600→3000 tokens, -35%)
- All functions now ≤15 lines (was: 12 functions >30 lines)
- Improved Russian language prompts with golden examples
- Menu summary/digest handlers now fully functional

### Fixed
- Missing asyncio import in summarizer.py (line 246)
- 150+ debug print statements replaced with structured logging
- Timezone handling in get_summary simplified

### Performance
- Token cost reduced by 32% through file splitting (23K→15.5K tokens)
- All files now <2000 tokens for optimal LLM parsing
- Test coverage increased: 76.10% → 82.3%
````

**Docstring Standards** (Google style, all new functions):

```python
async def parse_task_intent(self, text: str, context: dict) -> IntentParseResult:
    """Parse natural language text into structured task intent.

    Uses LLM to extract task components (title, deadline, priority) and
    generates clarifying questions for ambiguous inputs.

    Args:
        text: User's natural language task description
              Example: "Call mom tomorrow"
        context: Conversation context with user history
                 Example: {"timezone": "UTC", "prev_tasks": [...]}

    Returns:
        IntentParseResult with extracted fields and clarification questions.
        If needs_clarification=True, questions list will be non-empty.

    Raises:
        LLMError: When LLM service unavailable after retries
        ValidationError: When intent structure is invalid

    Example:
        >>> intent = await orchestrator.parse_task_intent(
        ...     "Remind me about meeting",
        ...     {"timezone": "UTC"}
        ... )
        >>> print(intent.needs_clarification)
        True
        >>> print(intent.questions[0].text)
        "When is the meeting?"
    """
```

**README Updates**:

- Add "Day 11 FSM Improvements" section (50 lines)
- Update architecture diagram to show FSM layer
- Add "Natural Language Examples" section with 10 examples (100 lines)
- Current README: 850 lines, ~10K tokens - GOOD (no reduction needed)

## Success Criteria

- [ ] FSM states implemented with proper state transitions
- [ ] Clarification flow works end-to-end (ask questions, collect answers, create task)
- [ ] All functions under 15 lines (or documented exceptions)
- [ ] No print statements for debugging (only structured logging)
- [ ] Test coverage maintained at 76%+ (ideally 80%+)
- [ ] Summary and digest menu items work correctly
- [ ] Natural language parsing improved with context awareness
- [ ] All new code follows PEP8, SOLID, DRY, KISS principles
- [ ] Russian language support fully functional
- [ ] Documentation updated with FSM flow diagram

## Technical Considerations

**Clean Architecture Compliance**:

- FSM states in presentation layer (UI concern)
- Intent parsing in application layer (use case)
- Formatting logic in domain layer (business rules)
- LLM calls in infrastructure layer (external service)

**Dependencies**:

- aiogram FSM already installed (good!)
- No new dependencies needed

**Migration Strategy**:

- Implement FSM alongside existing flow (no breaking changes)
- Gradually migrate handlers to use FSM
- Keep backward compatibility for simple task creation

**Performance**:

- FSM state storage uses aiogram's built-in memory storage (sufficient for Day 11)
- Consider Redis storage for production (future enhancement)

## Notes

The Perplexity spec has excellent code examples but proposes a different structure. We're cherry-picking the best ideas (FSM, clarification flow, better prompts) while keeping our superior Clean Architecture. This maintains long-term maintainability while adding the features suggested.

### To-dos

- [ ] Create FSM state definitions and state middleware for conversation flow
- [ ] Enhance intent orchestrator with clarification logic and better prompts
- [ ] Refactor summary_worker.py - split large functions, remove debug prints
- [ ] Refactor reminder_tools.py get_summary method - extract query building and stats
- [ ] Add missing asyncio import in summarizer.py
- [ ] Implement placeholder menu handlers for summary and digest
- [ ] Integrate FSM with natural language handler for clarification flow
- [ ] Create domain value objects for task summary and digest formatting
- [ ] Add comprehensive tests for FSM states and clarification flow
- [ ] Update documentation with FSM architecture diagram and new features
