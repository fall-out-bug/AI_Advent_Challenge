# Multi-Pass Code Review Architecture

## Overview

The multi-pass review system provides comprehensive code analysis through three sequential passes, each building on the previous one's findings.

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│   MultiPassReviewerAgent               │
│   (Orchestrator)                       │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴───────┐
       │               │
   ┌───▼───┐      ┌────▼────┐
   │Pass 1 │      │ Pass 2  │
   │(Arch) │      │(Comp)   │
   └───┬───┘      └────┬────┘
       │               │
       └───────┬───────┘
               │
           ┌───▼───┐
           │Pass 3 │
           │(Synth)│
           └───────┘
               │
       ┌───────▼───────┐
       │ SessionManager│
       │  (State)     │
       └───────────────┘
```

## Flow

1. **Pass 1 (Architecture)**: Detects components, analyzes structure
2. **Pass 2 (Components)**: Deep analysis per detected component
3. **Pass 3 (Synthesis)**: Merges findings, validates integration

## Integration Points

### UnifiedModelClient
- Used through `MultiPassModelAdapter`
- Provides consistent model interface

### SessionManager
- Persists state between passes
- Enables context passing

### PromptLoader
- Loads versioned prompts from `prompts/v1/`
- Uses `prompt_registry.yaml` for discovery

## Error Handling

- Component pass failures don't block synthesis
- Partial reports returned on errors
- Fallback prompts used if templates missing

## Concurrency Model

### Pass 2 Execution Strategy

Pass 2 components are executed **sequentially** (one after another):

```
Pass 1 (Architecture)
    ↓
    ├─ Pass 2: Docker    (sequential)
    ├─ Pass 2: Airflow   (sequential)
    ├─ Pass 2: Spark     (sequential)
    └─ Pass 2: MLflow    (sequential)
    ↓
Pass 3 (Synthesis)
```

**Rationale:**
- Prevents token budget conflicts
- Easier error isolation per component
- Simpler debugging and logging
- Allows progressive partial reports

**Future Enhancement:** Could be parallelized with proper token budget allocation per component.

## State Transitions

### Session Lifecycle

```
[CREATED]
    │
    ├─ SessionManager.create()
    │
    ↓
[PASS_1_RUNNING]
    │
    ├─ save_findings("pass_1", ...)
    │
    ↓
[PASS_2_RUNNING]
    │
    ├─ for each component:
    │   ├─ save_findings("pass_2_{component}", ...)
    │   └─ continue on error (non-blocking)
    │
    ↓
[PASS_3_RUNNING]
    │
    ├─ load_all_findings()
    ├─ build_synthesis_context()
    ├─ compress if > 32K tokens
    └─ save_findings("pass_3", ...)
    │
    ↓
[COMPLETE]
    │
    └─ persist() → /tmp/sessions/{session_id}/
```

### Error State Transitions

```
[NORMAL_FLOW]
    │
    ├─ Pass 1 error → [PASS_1_FAILED]
    │                   │
    │                   ├─ Fallback detection → [PARTIAL]
    │                   └─ Continue with generic
    │
    ├─ Pass 2 error → [PASS_2_PARTIAL]
    │                   │
    │                   └─ Skip component, continue others
    │
    └─ Pass 3 error → [PASS_3_FAILED]
                        │
                        └─ Return Pass 1+2 findings only
```

## Error Handling Flow

```
┌─────────────────────────────────────────┐
│   MultiPassReviewerAgent               │
│   (Orchestrator)                       │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴───────┐
       │               │
   ┌───▼───┐      ┌────▼────┐
   │Pass 1 │      │ Pass 2  │
   │(Arch) │      │(Comp)   │
   └───┬───┘      └────┬────┘
       │               │
       │               ├─── Error? ──→ Log, continue next component
       │               │
       └─── Error? ──→ Fallback detection
                        │
           ┌───────┬────┴────┬────────┐
           │       │         │        │
       ┌───▼───┐  │  ┌──────▼──────┐ │
       │Pass 2 │  │  │ Pass 2     │ │
       │Docker │  │  │ Airflow    │ │
       └───────┘  │  └────────────┘ │
                  │                 │
           ┌───────▼─────────────────┘
           │
       ┌───▼───┐
       │Pass 3 │
       │(Synth)│
       └───┬───┘
           │
           ├─── Error? ──→ Return Pass 1+2 only
           │
       ┌───▼────────────┐
       │ SessionManager │
       │  (Persist)     │
       └────────────────┘
```

## Extensibility

- New components: Add detection logic in Pass 1
- New prompts: Add to `prompts/v1/` and registry
- Custom passes: Extend `BaseReviewPass`

