<!-- 7e1c60c3-7b52-4356-b283-56e6f9666b12 f7878824-eda6-4f30-91f6-57cd6400d106 -->
# Implement Agentic Architecture in SDK

## Overview

Create a new agentic architecture from scratch in the shared SDK that supports both direct Python async calls and REST API patterns via adapter interfaces. Add orchestration module for agent coordination patterns. Refactor day_08 to use new SDK agents while keeping day_07 unchanged and maintaining SDK backward compatibility.

## Architecture Design

### 1. SDK Agent Module Structure

```
shared/shared_package/
├── agents/                     # NEW: Core agent abstractions
│   ├── __init__.py
│   ├── base_agent.py          # Abstract base agent with async interface
│   ├── code_generator.py      # Code generation agent
│   ├── code_reviewer.py       # Code review agent
│   └── schemas.py             # Pydantic schemas for agent I/O
├── orchestration/             # NEW: Agent coordination patterns
│   ├── __init__.py
│   ├── base_orchestrator.py  # Abstract orchestrator base
│   ├── sequential.py          # Sequential workflow pattern
│   ├── parallel.py            # Parallel execution pattern
│   └── adapters.py            # Communication adapters (direct/REST)
├── clients/                   # EXISTING: Model clients
│   └── unified_client.py     # Keep unchanged (backward compat)
└── ...
```

### 2. Key Design Principles (SOLID, Clean Architecture)

- **Single Responsibility**: Each agent handles one specific task
- **Open/Closed**: Extensible via inheritance, closed for modification
- **Liskov Substitution**: All agents implement BaseAgent protocol
- **Interface Segregation**: Separate interfaces for different communication patterns
- **Dependency Inversion**: Depend on abstractions (BaseAgent), not concrete implementations

### 3. Communication Adapter Pattern

Support both direct async calls and REST API via adapter pattern:

```python
# Direct async adapter (default for day_08)
agent = CodeGeneratorAgent(client, adapter=DirectAdapter())
result = await agent.generate(request)

# REST API adapter (for day_07 compatibility)
agent = CodeGeneratorAgent(client, adapter=RestAdapter(url="http://..."))
result = await agent.generate(request)
```

## Implementation Steps

### Phase 1: SDK Agent Foundation

**File**: `shared/shared_package/agents/schemas.py`

- Define Pydantic schemas for agent communication
- Models: `AgentRequest`, `AgentResponse`, `TaskMetadata`, `QualityMetrics`
- Follow Python Zen: explicit, simple, readable

**File**: `shared/shared_package/agents/base_agent.py`

- Abstract base class `BaseAgent` with async methods
- Core interface: `async def process(request: AgentRequest) -> AgentResponse`
- Statistics tracking, error handling, logging
- Model client integration via UnifiedModelClient

**File**: `shared/shared_package/agents/code_generator.py`

- Concrete implementation of code generation agent
- Inherits from BaseAgent
- Direct async calls to UnifiedModelClient
- Prompt engineering, response parsing, validation
- No dependency on day_07 (built from scratch)

**File**: `shared/shared_package/agents/code_reviewer.py`

- Concrete implementation of code review agent
- Inherits from BaseAgent
- Quality analysis, PEP8 checking, scoring
- Direct async calls to UnifiedModelClient
- Independent implementation

### Phase 2: Communication Adapters

**File**: `shared/shared_package/orchestration/adapters.py`

- `CommunicationAdapter` abstract base class
- `DirectAdapter`: Direct Python async calls (default)
- `RestAdapter`: HTTP API calls for distributed agents
- Adapter factory for easy switching

### Phase 3: Orchestration Patterns

**File**: `shared/shared_package/orchestration/base_orchestrator.py`

- Abstract `BaseOrchestrator` class
- Agent coordination interface
- Workflow management, result tracking
- Error handling and recovery

**File**: `shared/shared_package/orchestration/sequential.py`

- `SequentialOrchestrator`: Execute agents in sequence
- Pattern: Generator → Reviewer → Result
- Stateful workflow with intermediate results

**File**: `shared/shared_package/orchestration/parallel.py`

- `ParallelOrchestrator`: Execute multiple agents concurrently
- Useful for testing multiple models simultaneously
- Aggregation of results

### Phase 4: Day 08 Refactoring

**File**: `day_08/agents/code_generator_adapter.py`

- Remove day_07 dependency (lines 15-31)
- Import from SDK: `from shared_package.agents import CodeGeneratorAgent`
- Simplify adapter to thin wrapper around SDK agent
- Use DirectAdapter for async calls
- Keep public API unchanged (backward compatibility)

**File**: `day_08/agents/code_reviewer_adapter.py`

- Remove day_07 dependency (lines 16-32)
- Import from SDK: `from shared_package.agents import CodeReviewerAgent`
- Simplify adapter to thin wrapper around SDK agent
- Keep public API unchanged

**File**: `day_08/demo_enhanced.py`

- Update agent initialization to use SDK agents
- Remove fallback logic (SDK agents always available)
- Cleaner error messages
- Enhanced agent output display works directly with SDK responses

**File**: `day_08/core/model_switcher.py`

- Integrate SDK orchestration patterns
- Use `SequentialOrchestrator` for generator→reviewer workflow
- Maintain existing ModelSwitcherOrchestrator API

### Phase 5: SDK Documentation & Tests

**File**: `shared/README.md`

- Add "Agentic Architecture" section
- Usage examples for agents and orchestrators
- Migration guide from day_07/day_08
- Communication adapter patterns

**File**: `shared/shared_package/agents/__init__.py`

- Export public APIs
- Clean module interface

**File**: `shared/tests/test_agents.py`

- Unit tests for BaseAgent, CodeGeneratorAgent, CodeReviewerAgent
- Mock UnifiedModelClient responses
- Test error handling, validation

**File**: `shared/tests/test_orchestration.py`

- Test orchestrators with mock agents
- Test adapter pattern switching
- Integration tests

### Phase 6: Configuration & Integration

**File**: `shared/shared_package/config/agents.py`

- Agent-specific configurations (max_tokens, temperature)
- Model-agent compatibility matrix
- Default prompt templates

**File**: `shared/pyproject.toml`

- Update dependencies if needed
- Version bump to 0.2.0
- Maintain Python 3.10+ compatibility

## Key Files Modified

1. **NEW**: `shared/shared_package/agents/` (entire module)
2. **NEW**: `shared/shared_package/orchestration/` (entire module)
3. **REFACTOR**: `day_08/agents/code_generator_adapter.py` (remove day_07 deps)
4. **REFACTOR**: `day_08/agents/code_reviewer_adapter.py` (remove day_07 deps)
5. **REFACTOR**: `day_08/demo_enhanced.py` (use SDK agents)
6. **ENHANCE**: `shared/README.md` (add agent docs)
7. **UNTOUCHED**: `day_07/` (no changes, preserved as-is)
8. **BACKWARD COMPAT**: `shared/shared_package/clients/` (no breaking changes)

## Benefits

1. **Modular Design**: Clean separation of concerns, reusable agents
2. **SOLID Principles**: Adherence to all 5 principles
3. **Flexibility**: Support both direct calls and REST APIs
4. **Testability**: Easy to mock, comprehensive test coverage
5. **Maintainability**: Single source of truth for agent logic
6. **Extensibility**: Easy to add new agents and orchestration patterns
7. **Python Zen**: Simple, explicit, readable code
8. **No Breaking Changes**: Full backward compatibility with existing code

## Testing Strategy

1. Unit tests for all new SDK modules
2. Integration tests for day_08 refactored code
3. Verify day_07 still works (no changes)
4. Verify SDK backward compatibility (existing clients work)
5. End-to-end demo test with all models

### To-dos

- [ ] Create agent schemas with Pydantic models for requests, responses, metadata
- [ ] Implement BaseAgent abstract class with async interface and UnifiedModelClient integration
- [ ] Implement CodeGeneratorAgent with prompt engineering and response parsing
- [ ] Implement CodeReviewerAgent with quality analysis and scoring
- [ ] Create communication adapters (DirectAdapter, RestAdapter) for flexible agent communication
- [ ] Implement BaseOrchestrator abstract class for agent coordination
- [ ] Implement SequentialOrchestrator for generator->reviewer workflow
- [ ] Implement ParallelOrchestrator for concurrent agent execution
- [ ] Refactor day_08 generator adapter to use SDK agents, remove day_07 dependency
- [ ] Refactor day_08 reviewer adapter to use SDK agents, remove day_07 dependency
- [ ] Update demo_enhanced.py to use SDK agents with cleaner error handling
- [ ] Create agent configuration module with defaults and model compatibility
- [ ] Update SDK README with agentic architecture documentation and examples
- [ ] Write comprehensive unit tests for agents and orchestrators
- [ ] Run end-to-end tests verifying day_08 refactor and SDK backward compatibility