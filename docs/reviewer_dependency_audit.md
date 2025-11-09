# Multi-Pass Reviewer Dependency Audit

> Date: 2025-11-07

This document captures the current dependency landscape for the multi-pass
reviewer so that subsequent refactors can follow Clean Architecture rules.

## Domain Layer Dependencies

| Domain Module | Current Dependency | Notes |
|---------------|--------------------|-------|
| `src/domain/agents/multi_pass_reviewer.py` | `ReviewLoggerProtocol` (new), `SessionManager`, `DiffAnalyzer`, `CodeDiff` | Imports now reference the protocol rather than the infrastructure logger. Still relies on infrastructure adapters for prompts/model access (see below). |
| `src/domain/agents/passes/base_pass.py` | `ReviewLoggerProtocol` (new), `MultiPassModelAdapter`, `PromptLoader` | Review logger dependency inverted via protocol. `MultiPassModelAdapter`/`PromptLoader` remain infrastructure dependencies that need adapter interfaces in a later phase. |
| `src/domain/agents/passes/*` | `ReviewLoggerProtocol` | Pass implementations now call the protocol methods only. |

## Infrastructure Dependencies Requiring Interfaces

| Component | Location | Action |
|-----------|----------|--------|
| `MultiPassModelAdapter` | `src/infrastructure/adapters/multi_pass_model_adapter.py` | Will need an application-layer interface once the adapter is moved into the new package. |
| `PromptLoader` | `src/infrastructure/prompt_loader.py` | Prompts should be embedded resources in the new package. |

## Interfaces Added

- `src/domain/interfaces/review_logger.py` — Defines `ReviewLoggerProtocol` used across the domain and application layers.

## Next Steps

1. Introduce adapter interfaces for model access and prompt loading during package extraction (Phase 2).
2. Replace direct imports of infrastructure adapters in domain modules with protocol-based abstractions once interfaces exist.
3. Update tests to rely on protocol-compliant fakes instead of concrete infrastructure classes.


