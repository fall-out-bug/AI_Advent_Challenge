<!-- 85ab662f-4433-493b-af09-cff970ffeb3c 9a3e6b0d-137b-4014-a186-a8f03505063d -->
# Phase 3: Mistral Agent Orchestrator Implementation

## Architecture Overview

The Mistral Agent will be split across Clean Architecture layers:

**Domain Layer**: Conversation entities and repository interfaces

**Application Layer**: Core orchestrator logic with intent parsing and planning

**Presentation Layer**: MCP-specific integration wrapper and CLI interface

**Infrastructure Layer**: JSON-based conversation repository implementation

The agent will use `UnifiedModelClient` via HTTP to `local_models` for Mistral-7B inference, maintaining consistency with the existing architecture.

## Implementation Components

### 1. Domain Layer - Conversation Entities

Create conversation domain entities and repository interface:

**File**: `src/domain/entities/conversation.py`

- `ConversationMessage` dataclass with role, content, timestamp, metadata
- `Conversation` dataclass with conversation_id, messages list, context, created_at
- `IntentAnalysis` dataclass with primary_goal, tools_needed, parameters, needs_clarification, confidence, unclear_aspects
- `ExecutionPlan` dataclass with steps list, estimated_time, dependencies

**File**: `src/domain/repositories/conversation_repository.py`

- Abstract `ConversationRepository` interface following the existing repository pattern
- Methods: `save()`, `get_by_id()`, `get_all()`, `delete()`, `add_message()`, `get_recent_messages()`

### 2. Infrastructure Layer - Repository Implementation

**File**: `src/infrastructure/repositories/json_conversation_repository.py`

- Implement `JsonConversationRepository` following the pattern from `json_agent_repository.py`
- JSON storage in `data/conversations/` directory
- Serialize/deserialize conversation entities with proper datetime handling
- Thread-safe file operations

### 3. Application Layer - Core Orchestrator

**File**: `src/application/orchestrators/mistral_orchestrator.py`

- `MistralChatOrchestrator` class managing conversation flow
- Constructor: `__init__(unified_client: UnifiedModelClient, conversation_repo: ConversationRepository, model_name: str = "mistral")`
- Core methods (all ≤15 lines per function):
  - `async initialize()` - Setup and validate model availability
  - `async handle_message(message: str, conversation_id: str) -> str` - Main entry point
  - `async _parse_intent(message: str, history: list) -> IntentAnalysis` - Parse user intent using Mistral
  - `async _check_clarification_needed(intent: IntentAnalysis) -> bool` - Check confidence threshold (0.7)
  - `async _generate_clarifying_questions(intent: IntentAnalysis) -> str` - Generate questions
  - `async _generate_execution_plan(intent: IntentAnalysis, tools: dict) -> ExecutionPlan` - Create step-by-step plan
  - `async _format_response(results: list, intent: IntentAnalysis) -> str` - Format final response

**Key Implementation Details**:

- Use system prompts to guide Mistral for JSON-structured intent parsing
- Confidence scoring based on parameter completeness and tool matching
- History context limited to last 5 messages to fit context window
- Timeout handling with fallback responses
- Proper error propagation with domain exceptions

### 4. Presentation Layer - MCP Integration

**File**: `src/presentation/mcp/orchestrators/mcp_mistral_wrapper.py`

- `MCPMistralWrapper` class bridging orchestrator to MCP client
- Constructor: `__init__(server_script: str, orchestrator: MistralChatOrchestrator)`
- Methods:
  - `async initialize()` - Initialize MCP client and discover tools
  - `async execute_plan(plan: ExecutionPlan, conversation_id: str) -> list` - Execute tool chain via MCP
  - `async _call_mcp_tool(tool_name: str, args: dict) -> dict` - Individual tool execution
  - `_substitute_previous_results(args: dict, results: list) -> dict` - Chain results between steps

**Integration Points**:

- Uses existing `MCPClient` from `src/presentation/mcp/client.py`
- Discovers tools dynamically on initialization
- Handles MCP-specific errors and retries
- Logs all tool calls and results

### 5. CLI Interface

**File**: `src/presentation/mcp/cli/interactive_mistral_chat.py`

- Interactive chat CLI for testing and demonstration
- Commands: `/help`, `/tools`, `/history`, `/clear`, `/sessions`, `/load <id>`, `/exit`
- Display conversation context and tool execution steps
- Colorized output for better readability
- Session management (new, save, load, list)

### 6. Use Case Layer

**File**: `src/application/use_cases/mistral_chat_use_case.py`

- `MistralChatUseCase` following existing use case pattern
- Handles validation, orchestration coordination, and response formatting
- Dependencies: `MistralChatOrchestrator`, `ConversationRepository`, `MCPMistralWrapper`

### 7. Configuration

**File**: `config/mistral_orchestrator.yml`

```yaml
mistral_orchestrator:
  model_name: "mistral"
  temperature: 0.2
  max_tokens: 2048
  confidence_threshold: 0.7
  max_clarifying_questions: 3
  conversation_memory_size: 10
  max_plan_steps: 10
  timeout_seconds: 60
```

Update `src/presentation/mcp/config.py` to load orchestrator config.

### 8. Testing

**File**: `tests/integration/test_mistral_orchestrator.py`

- Test complete workflow: message → intent → plan → execution → response
- Test clarification flow with low confidence intent
- Test multi-step tool chaining (formalize → generate → review)
- Test conversation memory persistence and retrieval
- Mock MCP client for controlled tool responses
- Test error handling (model unavailable, tool failure, timeout)

**File**: `tests/unit/application/test_mistral_orchestrator.py`

- Unit tests for individual orchestrator methods
- Mock UnifiedModelClient responses
- Test intent parsing with various inputs
- Test plan generation logic
- Test confidence threshold calculations

## Key Implementation Decisions

**1. Model Access (1a)**: Use `UnifiedModelClient` via HTTP to `local_models`

- Maintains architectural consistency
- No additional VRAM requirements
- Leverages existing model infrastructure
- Slight HTTP latency acceptable for chat use case

**2. Architecture Split (2c)**: Core in application layer, wrapper in presentation

- `MistralChatOrchestrator` in `src/application/orchestrators/` (business logic)
- `MCPMistralWrapper` in `src/presentation/mcp/orchestrators/` (MCP integration)
- Clean separation of concerns, testable in isolation

**3. Persistence (3c)**: Repository pattern with `ConversationRepository`

- Follows existing architecture patterns
- Extensible to database in future
- JSON implementation for development/production
- Thread-safe operations

**4. Clarification (4b)**: Confidence threshold approach

- Ask questions when confidence < 0.7
- Even if defaults exist, interactive for better results
- Configurable threshold via YAML
- Max 3 questions to avoid annoying users

**5. Testing (5a)**: Basic integration tests

- Focus on core workflows and happy paths
- Mock external dependencies (MCP, models)
- Error scenario coverage
- Performance not critical for chat use case

## File Structure

```
src/
├── domain/
│   ├── entities/
│   │   └── conversation.py                          # NEW
│   └── repositories/
│       └── conversation_repository.py                # NEW
├── application/
│   ├── orchestrators/
│   │   └── mistral_orchestrator.py                  # NEW
│   └── use_cases/
│       └── mistral_chat_use_case.py                 # NEW
├── infrastructure/
│   └── repositories/
│       └── json_conversation_repository.py          # NEW
└── presentation/
    └── mcp/
        ├── orchestrators/
        │   ├── __init__.py                          # NEW
        │   └── mcp_mistral_wrapper.py               # NEW
        └── cli/
            ├── __init__.py                          # NEW
            └── interactive_mistral_chat.py          # NEW

config/
└── mistral_orchestrator.yml                         # NEW

tests/
├── unit/
│   └── application/
│       └── test_mistral_orchestrator.py             # NEW
└── integration/
    └── test_mistral_orchestrator.py                 # NEW

examples/
└── mistral_agent_demo.py                            # NEW
```

## Prompts for Mistral

**Intent Parsing Prompt Template**:

```
Available MCP tools: {tools_list}
Conversation history: {history}
User request: "{message}"

Analyze and respond with JSON only:
{
  "primary_goal": "what user wants",
  "tools_needed": ["tool1", "tool2"],
  "parameters": {"param": "value"},
  "confidence": 0.85,
  "needs_clarification": false,
  "unclear_aspects": []
}
```

**Plan Generation Prompt Template**:

```
User wants: {primary_goal}
Available tools: {tools_needed}
Previous context: {history}

Create execution plan as JSON:
[
  {"tool": "formalize_task", "args": {"informal_request": "..."}},
  {"tool": "generate_code", "args": {"description": "{prev_result.formalized_description}"}},
  {"tool": "review_code", "args": {"code": "{prev_result.code}"}}
]
```

## Integration with Existing System

- Uses existing MCP server tools (formalize_task, generate_code, review_code, etc.)
- Leverages `UnifiedModelClient` from `shared/` package
- Follows repository pattern from existing domain/infrastructure layers
- Compatible with existing orchestrators in application layer
- No changes required to existing MCP server implementation

## Success Criteria

- [ ] Orchestrator discovers and lists all MCP tools dynamically
- [ ] Single-step workflow executes correctly (e.g., "formalize this task")
- [ ] Multi-step workflow with 3+ tools works (formalize → generate → review)
- [ ] Clarifying questions generated when confidence < 0.7
- [ ] Conversation persisted and restored across sessions
- [ ] Intent parsing returns structured JSON with confidence scores
- [ ] Integration tests pass with mocked MCP client
- [ ] CLI interface functional for interactive testing

### To-dos

- [ ] Create conversation domain entities (ConversationMessage, Conversation, IntentAnalysis, ExecutionPlan)
- [ ] Create ConversationRepository abstract interface in domain layer
- [ ] Implement JsonConversationRepository with JSON file storage
- [ ] Implement MistralChatOrchestrator in application layer with intent parsing and planning
- [ ] Create MCPMistralWrapper in presentation layer to bridge orchestrator to MCP client
- [ ] Implement MistralChatUseCase following existing use case patterns
- [ ] Create mistral_orchestrator.yml config and update config loader
- [ ] Create interactive CLI for Mistral agent with session management
- [ ] Write integration tests for complete workflows and error scenarios
- [ ] Create example script demonstrating multi-step workflows