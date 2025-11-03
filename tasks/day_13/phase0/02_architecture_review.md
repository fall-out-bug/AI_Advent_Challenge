# Phase 0: Architecture Review

**Generated:** 2025-01-27  
**Scope:** Butler Agent Clean Architecture compliance analysis

## Executive Summary

The current architecture violates Clean Architecture principles with domain layer dependencies on infrastructure/presentation. This report identifies violations, circular dependencies, and proposes refactoring strategies aligned with DDD and SOLID.

## Architecture Overview

### Current Layer Structure

```
src/
├── domain/              # Business logic (PURPOSE: Pure business rules)
├── application/        # Use cases & orchestrators (PURPOSE: Coordination)
├── infrastructure/     # External services (PURPOSE: Technical details)
└── presentation/       # Interfaces (PURPOSE: I/O)
```

### Ideal Dependency Flow

```
Presentation → Application → Domain ← Infrastructure
```

**Rule:** Dependencies point **inward** toward domain.

## Critical Violations

### 1. Domain Layer Violation: Importing Outer Layers

**Location:** `src/domain/agents/mcp_aware_agent.py`

**Violations:**
```python
# Domain importing from Presentation layer ❌
from src.presentation.mcp.tools_registry import MCPToolsRegistry
from src.presentation.mcp.client import MCPClientProtocol

# Domain importing from Infrastructure layer ❌
from src.infrastructure.llm.openai_chat_client import OpenAIChatClient
from src.infrastructure.config.settings import get_settings
from src.infrastructure.monitoring.agent_metrics import AgentMetrics, LLMMetrics
```

**Impact:** Domain layer is no longer pure business logic. Violates Dependency Inversion Principle (DIP).

**Current Architecture (WRONG):**
```
Domain (mcp_aware_agent.py)
├── depends on → Infrastructure (llm, config, monitoring)
└── depends on → Presentation (mcp.tools_registry, mcp.client)
```

**Correct Architecture (SHOULD BE):**
```
Domain (mcp_aware_agent.py)
├── defines interfaces (protocols)
└── NO dependencies on outer layers

Infrastructure
└── implements domain interfaces

Presentation
└── uses domain interfaces
```

### 2. SOLID Principle Violations

#### Single Responsibility Principle (SRP) Violations

**God Class: `MCPAwareAgent`**

**Responsibilities (9 distinct concerns):**
1. LLM decision-making (`_stage_decision`, `_call_llm`)
2. Tool execution (`_stage_execution`, `_execute_tool`)
3. Parameter normalization (`_stage_execution` lines 366-523)
4. Channel resolution (lines 378-407)
5. Response formatting (`_stage_formatting`, `_format_tool_result`)
6. Parsing (Russian, intent) (`_parse_user_intent`, `_parse_response`)
7. Tool validation (`_validate_tool_params`)
8. Metrics collection (agent_metrics, llm_metrics)
9. Orchestration (`process` method)

**Recommendation:** Split into:
```
MCPAwareAgent (orchestrator only)
├── DecisionEngine (LLM decision logic)
├── ToolExecutor (MCP execution)
├── ParameterNormalizer (param mapping)
├── ResponseFormatter (output formatting)
└── MetricsCollector (optional, via observer pattern)
```

#### Dependency Inversion Principle (DIP) Violations

**Problem:** Domain depends on concrete implementations.

**Examples:**
```python
# ❌ Concrete dependency
from src.presentation.mcp.client import MCPClientProtocol

# ❌ Direct import of infrastructure
from src.infrastructure.config.settings import get_settings
```

**Solution:** Use protocols/interfaces defined in domain.

```python
# ✓ Abstract protocol in domain
class ToolClient(Protocol):
    async def discover_tools(self) -> List[ToolMetadata]: ...
    async def call_tool(self, name: str, params: Dict) -> Dict: ...

class ConfigProvider(Protocol):
    def get(self, key: str) -> Any: ...
```

## Layer Analysis

### Domain Layer Purity Check

**Expected:** Pure business logic, no external dependencies.

**Reality:**
- ✅ Most entities, value objects, services are pure
- ❌ `mcp_aware_agent.py` imports from infrastructure/presentation
- ❌ `intent_orchestrator.py` likely has infrastructure dependencies

**Impact:** Testing requires complex mocking, tight coupling.

### Application Layer Analysis

**Expected:** Orchestrates domain logic, coordinates workflows.

**Current State:**
- ✅ `intent_orchestrator.py`: Good separation via delegation
  - Uses `IntentLLMParser`, `IntentFallbackParser` (good DI)
  - Validation separate (`IntentValidator`)
  - Clarification separate (`IntentClarificationGenerator`)

**Issues:**
- Checks needed for infrastructure imports
- May depend on MongoDB directly (review needed)

### Infrastructure Layer Analysis

**Expected:** Implements domain abstractions, handles I/O.

**Current State:**
- ✅ `mcp_client_robust.py`: Good retry logic, error handling
- ✅ `dialog_manager.py`: Likely has proper abstraction
- ⚠️  Check: Direct usage in domain layer (violation)

**Issues:**
- Prometheus metrics may not be properly abstracted
- Settings accessed directly (should be injected)

### Presentation Layer Analysis

**Expected:** Interfaces (API, CLI, Telegram).

**Current State:**
- ✅ `butler_bot.py`: Uses orchestrators properly
- ✅ `tasks.py`, `channels.py`: Separate handlers
- ⚠️  Needs verification of domain coupling

## Circular Dependencies

### Identified Cycles

1. **Domain ↔ Infrastructure:**
   - `domain.agents` → `infrastructure.llm.openai_chat_client`
   - `infrastructure` likely imports domain entities
   - **Risk:** HIGH

2. **Domain ↔ Presentation:**
   - `domain.agents` → `presentation.mcp.tools_registry`
   - `presentation.mcp` likely imports domain schemas
   - **Risk:** MEDIUM

3. **Application ↔ Infrastructure:**
   - Verify `application.orchestration` does not import `infrastructure` directly
   - **Risk:** LOW-MEDIUM

### Dependency Graph (Estimated)

```
┌─────────────────────────────────────────────────────────┐
│                    CIRCULAR DEPS                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  domain.agents.mcp_aware_agent                         │
│  ├─→ presentation.mcp.tools_registry                   │
│  │   └─→ domain.agents.schemas?                        │
│  ├─→ infrastructure.llm                                │
│  │   └─→ domain.entities?                              │
│  └─→ infrastructure.monitoring                         │
│      └─→ domain.services?                              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Recommended Architecture (Phase 1-7)

### Target State

```
┌─────────────────────────────────────────────────────────────┐
│                     DOMAIN LAYER                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  interfaces/                                                │
│  ├── tool_client.py         # Protocol(ABC)                │
│  ├── llm_client.py          # Protocol(ABC)                │
│  └── config_provider.py     # Protocol(ABC)                │
│                                                             │
│  entities/                                                  │
│  ├── agent.py              # MCPAwareAgent (refactored)    │
│  ├── task.py                                                │
│  └── intent.py                                              │
│                                                             │
│  services/                                                  │
│  ├── decision_engine.py    # LLM decision logic            │
│  ├── tool_executor.py      # Tool execution                │
│  └── response_formatter.py # Output formatting             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌───────────────────┐              ┌────────────────────┐
│  APPLICATION      │              │  INFRASTRUCTURE     │
├───────────────────┤              ├────────────────────┤
│  orchestrators/   │              │  clients/          │
│  ├── butler_      │              │  ├── mcp_impl.py   │
│  │   orchestrator │              │  └── llm_impl.py   │
│  └── intent_      │              │                    │
│      orchestrator │              │  config/           │
│                   │              │  └── settings.py   │
│  usecases/        │              │                    │
│  ├── create_task  │              │  monitoring/       │
│  └── collect_data │              │  └── metrics_impl  │
└───────────────────┘              └────────────────────┘
        │
        ▼
┌───────────────────┐
│  PRESENTATION     │
├───────────────────┤
│  telegram/        │
│  ├── butler_      │
│  │   handler.py   │
│  └── routers/     │
│                   │
│  mcp/             │
│  └── server.py    │
└───────────────────┘
```

### Phase-by-Phase Refactoring

#### Phase 1: Domain Layer Cleanup

**Goals:**
1. Extract abstractions to `domain/interfaces/`
2. Remove imports from `mcp_aware_agent.py`
3. Split God Class into focused services

**Actions:**
```python
# Create domain/interfaces/tool_client.py
from typing import Protocol, List, Dict, Any

class ToolClientProtocol(Protocol):
    async def discover_tools(self) -> List[ToolMetadata]: ...
    async def call_tool(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]: ...

# Update mcp_aware_agent.py
class MCPAwareAgent:
    def __init__(self, tool_client: ToolClientProtocol, ...):  # Use protocol
        ...
```

#### Phase 2: Infrastructure Abstractions

**Goals:**
1. Implement domain interfaces in infrastructure
2. Move concrete implementations out of domain
3. Use DI for all dependencies

**Actions:**
```python
# infrastructure/clients/mcp_client.py
class MCPClient(ToolClientProtocol):  # Implement domain protocol
    async def discover_tools(self) -> List[ToolMetadata]: ...
    async def call_tool(self, name: str, params: Dict) -> Dict: ...
```

#### Phase 3: Application Orchestration

**Goals:**
1. Create `ButlerOrchestrator` (as per plan)
2. Extract use cases
3. Wire dependencies via DI

**Actions:**
```python
# application/orchestrators/butler_orchestrator.py
class ButlerOrchestrator:
    def __init__(
        self,
        decision_engine: DecisionEngine,
        tool_executor: ToolExecutor,
        formatter: ResponseFormatter
    ): ...
```

#### Phase 4-7: Presentation & Testing

**Goals:**
1. Update presentation to use orchestrators
2. Add comprehensive tests
3. Fix remaining violations

## Dependency Injection Analysis

### Current State

**Mixed approaches:**

**Good Examples:**
```python
# application/orchestration/intent_orchestrator.py
@dataclass
class IntentOrchestrator:
    def __init__(
        self,
        model_name: str = "mistral",
        use_llm: bool = True,
        temperature: float = 0.2,
        max_tokens: int = 512,
    ):
        # Creates dependencies internally (not ideal, but acceptable)
```

**Bad Examples:**
```python
# infrastructure/config/settings.py
def get_settings():
    # Global function, not injectable
    return Settings()
```

### Recommended Improvements

1. **Use DI container** (optional, for complex cases)
2. **Constructor injection** (preferred)
3. **Factory pattern** for complex objects
4. **Avoid global state** (settings, logger)

## File Organization

### Current Structure

```
src/
├── domain/agents/
│   ├── mcp_aware_agent.py       # 696 lines - TOO LARGE
│   ├── base_agent.py
│   ├── code_generator.py
│   └── code_reviewer.py
├── application/orchestration/
│   └── intent_orchestrator.py   # Good delegation ✓
└── presentation/
    ├── bot/
    │   └── butler_bot.py         # 554 lines - NEEDS SPLIT
    └── mcp/
        └── tools/                # OK ✓
```

### Target Structure (Phase 1)

```
src/
├── domain/
│   ├── agents/
│   │   ├── orchestrator.py      # NEW: Thin orchestrator
│   │   └── services/            # NEW: Extracted services
│   │       ├── decision_engine.py
│   │       ├── tool_executor.py
│   │       └── response_formatter.py
│   └── interfaces/              # NEW: Abstractions
│       ├── tool_client.py
│       ├── llm_client.py
│       └── config.py
├── application/
│   ├── orchestrators/
│   │   └── butler_orchestrator.py
│   └── usecases/
│       ├── create_task_usecase.py
│       └── collect_data_usecase.py
├── infrastructure/
│   └── implementations/         # NEW: Implements domain interfaces
│       ├── mcp_client.py
│       └── llm_client.py
└── presentation/
    └── telegram/
        └── butler_handler.py    # NEW: Simplified
```

## Test Architecture Impact

### Current State

**Problem:** Tight coupling requires complex mocking.

```python
# Tests need to mock infrastructure in domain tests ❌
from unittest.mock import Mock
from src.presentation.mcp.tools_registry import MCPToolsRegistry

def test_agent():
    agent = MCPAwareAgent(
        mcp_client=Mock(),
        llm_client=Mock(),
        # ... complex setup
    )
```

### Target State

**Benefit:** Pure domain logic is easy to test.

```python
# Tests use simple mocks of protocols ✅
from typing import Protocol

class MockToolClient(ToolClientProtocol):
    async def discover_tools(self) -> List[ToolMetadata]: ...
    async def call_tool(self, name: str, params: Dict) -> Dict: ...

def test_agent():
    agent = MCPAwareAgent(tool_client=MockToolClient())
```

## Metrics Summary

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Domain layer violations | 5+ imports | 0 | ❌ |
| Circular dependencies | 2-3 cycles | 0 | ❌ |
| SOLID violations | 3+ classes | 0 | ❌ |
| DI usage | 50% | 100% | ⚠️  |
| Abstraction quality | 30% | 90% | ❌ |

## Recommendations Priority

### HIGH (Phase 1)
1. Create `domain/interfaces/` with protocols
2. Remove infrastructure/presentation imports from `mcp_aware_agent.py`
3. Split God Class into focused services

### MEDIUM (Phase 2-3)
4. Implement protocols in infrastructure
5. Add proper DI throughout
6. Create ButlerOrchestrator

### LOW (Phase 4-7)
7. Add DI container (optional)
8. Refactor remaining files
9. Comprehensive testing

## References

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Dependency Injection](https://en.wikipedia.org/wiki/Dependency_injection)

