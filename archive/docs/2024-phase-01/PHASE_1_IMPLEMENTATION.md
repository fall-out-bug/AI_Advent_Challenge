# Phase 1: Multi-Pass Code Review Implementation

## Overview

Phase 1 implements a 3-pass code review system that provides deep analysis for projects with multiple components (Docker, Airflow, Spark, MLflow).

## Architecture

The system consists of:

1. **SessionManager** - Manages state between passes
2. **BaseReviewPass** - Abstract base class for all passes
3. **ArchitectureReviewPass** (Pass 1) - High-level architecture analysis
4. **ComponentDeepDivePass** (Pass 2) - Component-specific deep analysis
5. **SynthesisPass** (Pass 3) - Synthesis and integration validation
6. **MultiPassReviewerAgent** - Orchestrator for all passes

## Usage

```python
from shared_package.clients.unified_client import UnifiedModelClient
from src.domain.agents.multi_pass_reviewer import MultiPassReviewerAgent

# Initialize
client = UnifiedModelClient()
agent = MultiPassReviewerAgent(client, token_budget=8000)

# Run review
report = await agent.process_multi_pass(
    code=project_code,
    repo_name="my_project"
)

# Export report
markdown = report.to_markdown()
print(markdown)
```

## Components

### Models

- `PassFindings` - Findings from a single pass
- `MultiPassReport` - Final aggregated report
- `Finding` - Single finding with severity

### Passes

- **Pass 1**: Detects components and analyzes architecture
- **Pass 2**: Performs detailed analysis per component type
- **Pass 3**: Synthesizes findings and validates integration

## File Structure

```
src/domain/
├── models/
│   └── code_review_models.py
├── agents/
│   ├── session_manager.py
│   ├── multi_pass_reviewer.py
│   └── passes/
│       ├── base_pass.py
│       ├── architecture_pass.py
│       ├── component_pass.py
│       └── synthesis_pass.py

src/infrastructure/
├── adapters/
│   └── multi_pass_model_adapter.py
└── prompt_loader.py

prompts/v1/
├── prompt_registry.yaml
├── pass_1_architecture_overview.md
├── pass_2_docker_review.md
├── pass_2_airflow_review.md
├── pass_2_spark_review.md
├── pass_2_mlflow_review.md
└── pass_3_synthesis.md
```

## Session Management

Sessions are stored in `/tmp/sessions/{session_id}/`:
- `findings_pass_1.json`
- `findings_pass_2_{component}.json`
- `findings_pass_3.json`
- `session_metadata.json`

## Model Client Integration

### MultiPassModelAdapter

The system uses `MultiPassModelAdapter` to wrap `UnifiedModelClient` and provide retry logic, token management, and structured logging:

```python
from src.infrastructure.adapters.multi_pass_model_adapter import MultiPassModelAdapter

adapter = MultiPassModelAdapter(
    unified_client=client,
    model_name="mistral-7b-instruct-v0.2",
    max_retries=3,
    initial_retry_delay=1.0,
    backoff_factor=2.0,
    max_retry_delay=10.0
)

# Usage in passes
response = await adapter.send_prompt(
    prompt="Review this code...",
    temperature=0.5,
    max_tokens=1000,
    pass_name="pass_1"
)
```

### Retry Logic

The adapter implements exponential backoff retry:
- Default: 3 retry attempts
- Initial delay: 1.0 second
- Backoff factor: 2.0 (doubles each retry)
- Max delay: 10.0 seconds

On retry, prompts are automatically truncated to 70% of original length if they exceed limits.

### Token Estimation

```python
# Estimate tokens
estimated = adapter.estimate_tokens(prompt)

# Truncate if needed
if estimated > max_tokens:
    truncated = adapter.truncate_prompt(
        prompt=prompt,
        max_tokens=max_tokens,
        preserve_end=True  # Keep end (most recent context)
    )
```

### Error Handling in Adapter

If model call fails:
1. Log structured error event
2. Retry with exponential backoff
3. Truncate prompt on subsequent retries
4. Raise exception if all retries exhausted

## Session State Management

### JSON Structure

Each session stores findings as JSON files in `/tmp/sessions/{session_id}/`:

**session_metadata.json:**
```json
{
  "created_at": "2025-11-03T15:30:00Z",
  "repo_name": "my_project"
}
```

**findings_pass_1.json:**
```json
{
  "pass_name": "pass_1",
  "timestamp": "2025-11-03T15:30:05Z",
  "findings": [
    {
      "severity": "critical",
      "title": "Missing health checks",
      "description": "Docker services lack health checks",
      "location": "docker-compose.yml:12",
      "recommendation": "Add healthcheck to all services",
      "effort_estimate": "low"
    }
  ],
  "recommendations": [
    "Add health checks",
    "Use named volumes"
  ],
  "summary": "Architecture overview: 2 critical, 3 major issues",
  "metadata": {
    "detected_components": ["docker", "airflow"],
    "token_estimate": 2500
  }
}
```

**findings_pass_2_docker.json:**
```json
{
  "pass_name": "pass_2_docker",
  "timestamp": "2025-11-03T15:30:30Z",
  "findings": [...],
  "metadata": {
    "component_type": "docker",
    "token_estimate": 1800
  }
}
```

### Context Passing Flow

1. **Pass 1** → saves findings → `SessionManager.persist()`
2. **Pass 2** → loads Pass 1 findings → creates summary → includes in prompt
3. **Pass 3** → loads all findings → builds comprehensive context → compresses if > 32K tokens

### Failure Scenarios

| Scenario | Handling | Result |
|----------|----------|--------|
| Pass 2 for component X fails | Log error, continue with other components | Partial report with Pass 1+other components |
| Pass 1 fails | Use fallback detection | Report with generic component analysis |
| Pass 3 fails | Return Pass 1+2 findings only | Partial report without synthesis |
| SessionManager disk full | Store in memory only | Report in memory, not persisted |

## Token Budget Management

### Budget Allocation

Default: 8000 tokens total, split evenly:
- Pass 1: ~2666 tokens (architecture overview)
- Pass 2 per component: ~2666 tokens (shared among components)
- Pass 3: ~2666 tokens (synthesis)

### Adaptive Distribution

Token usage is tracked per pass:

```python
# In BaseReviewPass
remaining = self.get_remaining_budget()  # Tracks used_tokens
if not self.can_afford(estimated_tokens):
    # Automatically truncates prompt
```

If Pass 1 uses only 2000 tokens:
- Remaining 666 tokens can be reallocated
- Pass 2/3 budgets effectively increase

### Overflow Handling

If prompt exceeds budget:

1. **Automatic Truncation**: Prompt truncated to 70% if exceeds remaining budget
2. **Max Tokens Adjustment**: `max_tokens` reduced to fit within budget
3. **Preserve End**: By default, end of prompt is preserved (most recent context)
4. **Warning Logged**: All truncations logged with before/after metrics

```python
# Example in BaseReviewPass._call_mistral()
if estimated_tokens > remaining_budget:
    truncated_prompt = self.adapter.truncate_prompt(
        prompt=prompt,
        max_tokens=int(remaining_budget * 0.9),
        preserve_end=True
    )
```

### Token Tracking

Each pass tracks:
- Input tokens (estimated)
- Output tokens (estimated)
- Total used tokens
- Remaining budget

Available via:
```python
pass_instance.used_tokens  # Tokens used so far
pass_instance.get_remaining_budget()  # Remaining budget
pass_instance.can_afford(estimated)  # Check if affordable
```

## Error Handling

### Error Scenarios Table

| Scenario | Cause | Handling | Result |
|----------|-------|----------|--------|
| Pass 1 fails | Model error/ timeout | Retry 3x, then fallback detection | Partial report with generic component |
| Pass 2 component fails | Model timeout / error | Skip component, continue | Partial report (other components included) |
| Pass 3 context too large | All findings > 32K tokens | Automatically compress context | Final report with compressed findings |
| SessionManager disk full | Storage error | Use memory only | Report in memory, not persisted |
| Prompt file missing | File error | Use fallback prompt | Generic review with fallback |
| Token budget exceeded | Prompt too large | Auto-truncate to 70% | Review with truncated context |

### Recovery Strategies

1. **Partial Reports**: System always tries to return usable data even if some passes fail
2. **Error Tracking**: All errors stored in report metadata for debugging
3. **Graceful Degradation**: Missing Pass 2 components don't block Pass 3
4. **Critical vs Non-Critical**: Pass 1 failure is critical; Pass 2/3 failures are recoverable

### Error Metadata

Errors are stored in:
- `PassFindings.metadata["errors"]` - Per-pass errors
- `session_metadata.json` - Session-level errors
- Structured logs - All errors logged as JSON events

## Observability & Logging

### Structured Logging

All model calls log structured JSON events:

```json
{
  "timestamp": "2025-11-03T15:30:00Z",
  "pass": "ArchitectureReviewPass",
  "event": "model_request_start",
  "model": "mistral-7b-instruct-v0.2",
  "prompt_length": 3500,
  "estimated_tokens": 4200,
  "max_tokens": 1000,
  "temperature": 0.5
}
```

```json
{
  "timestamp": "2025-11-03T15:30:03Z",
  "pass": "ArchitectureReviewPass",
  "event": "model_request_success",
  "model": "mistral-7b-instruct-v0.2",
  "response_length": 1200,
  "tokens": 5500,
  "input_tokens": 4200,
  "output_tokens": 1300,
  "execution_time_ms": 3200,
  "attempt": 1
}
```

```json
{
  "timestamp": "2025-11-03T15:30:05Z",
  "pass": "ComponentDeepDivePass",
  "event": "model_request_error",
  "model": "mistral-7b-instruct-v0.2",
  "error": "Connection timeout",
  "error_type": "TimeoutError",
  "execution_time_ms": 30000,
  "attempt": 1,
  "will_retry": true
}
```

### Metrics to Track

- Per-pass execution time
- Token usage per pass (input/output)
- Component detection accuracy
- Error rate by pass
- Retry counts
- Context compression events

### Dashboard Queries

Example queries for monitoring:

```python
# Average execution time by component type
# Token budget utilization
# Error rate trends
# Pass 1→3 success rate
# Context compression frequency
```

## Testing Strategy

### Unit Tests

**Example: Component Detection**
```python
@pytest.mark.asyncio
async def test_component_detection():
    code = """
    version: '3.8'
    services:
      postgres:
        image: postgres:14
    """
    pass_obj = ArchitectureReviewPass(mock_client, mock_session)
    components = pass_obj._detect_components(code)
    assert set(components) == {"docker"}
```

**Example: Token Budget**
```python
@pytest.mark.asyncio
async def test_token_overflow_handling():
    pass_obj = BaseReviewPass(mock_client, mock_session, token_budget=1000)
    large_prompt = "x" * 10000  # Exceeds budget

    # Should auto-truncate
    response = await pass_obj._call_mistral(large_prompt)
    assert pass_obj.used_tokens <= 1000
```

**Example: Context Compression**
```python
def test_context_compression():
    synthesis_pass = SynthesisPass(mock_client, mock_session)
    large_context = "x" * 200000  # > 32K tokens

    compressed = synthesis_pass._compress_context(large_context, {})
    assert len(compressed) < len(large_context)
    assert "Compressed" in compressed
```

### Integration Tests

**Example: Full Review Flow**
```python
@pytest.mark.asyncio
async def test_full_review_docker_only():
    code = load_fixture("docker_compose.yml")
    agent = MultiPassReviewerAgent(mock_client)

    report = await agent.process_multi_pass(code, "docker_project")

    assert report.pass_1 is not None
    assert "docker" in report.detected_components
    assert report.pass_3 is not None
```

**Example: Error Recovery**
```python
@pytest.mark.asyncio
async def test_error_recovery():
    # Simulate Pass 2 failure
    failing_client = MockClient(raise_on_pass_2=True)
    agent = MultiPassReviewerAgent(failing_client)

    report = await agent.process_multi_pass(code)

    assert report.pass_1 is not None
    assert len(report.pass_2_results) == 0  # Empty due to failure
    assert report.pass_3 is not None  # Still generated
```

### E2E Tests

**Example: Complete Stack**
```python
@pytest.mark.asyncio
async def test_e2e_all_components():
    # Real Mistral client, real prompts
    code = load_fixture("complete_ml_project")  # All 4 types
    agent = MultiPassReviewerAgent(real_mistral_client)

    report = await agent.process_multi_pass(code)

    assert len(report.detected_components) == 4
    assert report.execution_time_seconds < 180  # < 3 minutes
    assert report.critical_count >= 0

    # Verify report exportable
    markdown = report.to_markdown()
    assert len(markdown) > 100
```

## Prompt Management

### PromptLoader

Prompts are loaded from `prompts/v1/` directory using `PromptLoader`:

```python
from src.infrastructure.prompt_loader import PromptLoader

# Load prompt by name
template = PromptLoader.load_prompt("pass_1_architecture")

# List all available prompts
all_prompts = PromptLoader.list_prompts()
```

### Prompt Registry

`prompt_registry.yaml` maps prompt names to files:

```yaml
prompts:
  pass_1_architecture:
    filename: "pass_1_architecture_overview.md"
    description: "High-level architecture analysis"

  pass_2_docker_review:
    filename: "pass_2_docker_review.md"
    description: "Detailed Docker/Compose configuration review"
```

### Usage in Passes

```python
class ArchitectureReviewPass(BaseReviewPass):
    async def run(self, code: str):
        # Load prompt template
        template = self._load_prompt_template("pass_1_architecture")

        # Format with variables
        prompt = template.format(
            code_snippet=code,
            component_summary=summary
        )

        # Use in model call
        response = await self._call_mistral(prompt)
```

### Fallback Strategy

If prompt file missing:
1. Log warning
2. Use built-in fallback prompt (generic but functional)
3. Continue review with fallback
4. Log event for monitoring

Fallback prompts are defined in each Pass class `_build_fallback_prompt()` method.

## Troubleshooting

### Prompt Not Found
If prompts are not found, the system uses fallback prompts. Ensure `prompts/v1/prompt_registry.yaml` exists and contains all prompt entries.

### Component Detection
If components are not detected correctly, check the detection logic in `ArchitectureReviewPass._detect_components()`.

### Token Budget
Default token budget is 8000, split evenly between passes. Adjust in `MultiPassReviewerAgent` initialization.

### Session Storage
If sessions not persisting, check:
- `/tmp/sessions/` directory permissions
- Disk space availability
- SessionManager logs for errors
