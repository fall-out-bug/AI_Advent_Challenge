# Multi-Pass Code Review Architecture

## Overview

The multi-pass review system now delivers comprehensive analysis through **five sequential stages**: three classical review passes, automated static analysis, and Pass 4 log diagnostics with LLM insights.

## Architecture Diagram

```
┌─────────────────────────────────────────────┐
│   MultiPassReviewerAgent                    │
│   (Orchestrator)                            │
└──────────────┬──────────────────────────────┘
               │
       ┌───────▼───────┐
       │ Pass 1        │
       │ Architecture  │
       └───────┬───────┘
               │
       ┌───────▼───────┐
       │ Pass 2        │
       │ Components    │
       └───────┬───────┘
               │
       ┌───────▼───────┐
       │ Pass 3        │
       │ Synthesis     │
       └───────┬───────┘
               │
       ┌───────▼────────────┐
       │ Static Analysis    │
       │ (Lint & Type checks)│
       └───────┬────────────┘
               │
       ┌───────▼───────┐
       │ Pass 4        │
       │ Log Analysis  │
       └───────┬───────┘
               │
       ┌───────▼────────────┐
       │ Report, Haiku &    │
       │ MCP Publishing     │
       └────────────────────┘
```

## Flow

1. **Pass 1 (Architecture)**: Detects components, analyzes structure
2. **Pass 2 (Components)**: Deep analysis per detected component
3. **Pass 3 (Synthesis)**: Merges findings, validates integration
4. **Static Analysis Stage**: Runs Flake8, Pylint, MyPy, Black, isort with summarized findings
5. **Pass 4 (Log Analysis)**: Groups runtime logs, applies LLM diagnostics, and surfaces remediation hints
6. **Report & Publish**: Generates Markdown + haiku, publishes via MCP tool call with HTTP fallback

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

### Static Analysis Tooling
- Executed via `CodeQualityChecker` with adapters for Flake8, Pylint, MyPy, Black, and isort.
- Results are normalized into `MultiPassReport.static_analysis_results` for inclusion in Markdown output.
- Findings are grouped by severity and mapped to actionable remediation tips.

### Log Analysis Components
- **`LogParserImpl`**: Parses heterogeneous sources (`checker.log`, Docker stdout/stderr, compose logs) into structured `LogEntry` objects.
- **`LogNormalizer`**: Filters by severity (`Settings.log_analysis_min_severity`), groups by component, and enforces `log_analysis_max_groups` cap.
- **`LLMLogAnalyzer`**: Uses `UnifiedModelClient` to classify groups, surface root causes, and recommend fixes.
- Results flow into `MultiPassReport.pass_4_logs` with metadata for publishing.

### Publishing Flow
- **`MCPHTTPClient`**: Discovers and invokes the `submit_review_result` tool on the external HW Checker MCP (`Settings.hw_checker_mcp_url`).
- **Fallback Publisher**: Reuses `ExternalAPIClient` when MCP publishing fails or is disabled.
- **Session Metadata**: Reports include `new_commit`, `session_id`, overall score, and haiku for rich downstream presentation.

## Error Handling

- Component pass failures don't block synthesis
- Partial reports returned on errors
- Fallback prompts used if templates missing
- Static analysis issues are captured as warnings; review continues with existing findings
- MCP publishing failures trigger HTTP fallback via `ExternalAPIClient`

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
    ↓
Static Analysis (lint & format checks)
    ↓
Pass 4 (Log Analysis)
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
[STATIC_ANALYSIS]
    │
    ├─ run_linters()
    ├─ collect_violations()
    └─ attach_to_report()
    │
    ↓
[PASS_4_RUNNING]
    │
    ├─ extract_logs()
    ├─ normalize_groups()
    ├─ analyze_with_llm()
    └─ persist_pass_4()
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

