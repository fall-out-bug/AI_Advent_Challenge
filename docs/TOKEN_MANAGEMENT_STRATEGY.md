# Token Management Strategy

## Overview

This document describes the token budget management strategy for the multi-pass code review system, including budget allocation, overflow handling, and adaptive distribution.

## Token Budget Architecture

### Total Budget

**Default**: 8000 tokens total for all 3 passes

**Rationale**:
- Mistral-7B-Instruct-v0.2 context window: ~4096 tokens input, 2048 output
- 8000 tokens = ~2× input capacity (safety margin)
- Allows for multiple model calls per pass

### Initial Allocation

```
Total Budget: 8000 tokens
├─ Pass 1 (Architecture): ~2666 tokens (33%)
├─ Pass 2 (Components):   ~2666 tokens (33%) - shared among components
└─ Pass 3 (Synthesis):    ~2666 tokens (33%)
```

**Per-Component Budget** (Pass 2):
- If 2 components detected: ~1333 tokens each
- If 3 components detected: ~889 tokens each
- If 4 components detected: ~667 tokens each

## Adaptive Distribution

### Token Tracking

Each pass tracks:
- `used_tokens`: Cumulative tokens used so far
- `remaining_budget`: Budget - used_tokens
- `token_budget`: Initial budget allocated

### Reallocation Logic

If Pass 1 uses less than allocated:
```python
# Pass 1 budget: 2666 tokens
# Pass 1 actual: 2000 tokens
# Remaining: 666 tokens → available for Pass 2/3
```

**Implementation**:
- Tokens tracked per pass instance
- No automatic reallocation (simple tracking)
- Future: Implement budget pool with reallocation

## Overflow Handling

### Detection

```python
estimated_tokens = adapter.estimate_tokens(prompt)
remaining_budget = token_budget - used_tokens

if estimated_tokens > remaining_budget:
    # Overflow detected - truncate
```

### Truncation Strategy

**When**: Prompt exceeds remaining budget

**How**:
1. Calculate target size: `remaining_budget * 0.9` (90% of remaining)
2. Preserve end of prompt (most recent context)
3. Truncate beginning with `...` prefix
4. Log truncation event

**Code**:
```python
if estimated_tokens > remaining_budget:
    truncated_prompt = adapter.truncate_prompt(
        prompt=prompt,
        max_tokens=int(remaining_budget * 0.9),
        preserve_end=True  # Keep end (most recent context)
    )
```

### Max Tokens Adjustment

**When**: `max_tokens` parameter exceeds budget

**How**:
```python
if max_tokens > remaining_budget:
    max_tokens = max(int(remaining_budget * 0.8), 100)
    # Leave 20% margin, minimum 100 tokens
```

## Token Estimation

### Method

Currently uses `TokenAnalyzer.count_tokens()`:
```python
def count_tokens(text: str) -> int:
    words = text.split()
    return len(words) * 1.3  # ~1.3 tokens per word
```

### Accuracy

- **Approximation**: ~80-90% accurate
- **Limitation**: Doesn't account for code syntax
- **Improvement**: Use tiktoken or similar for better accuracy

## Per-Pass Budget Management

### Pass 1 (Architecture)

**Typical Usage**:
- Input: 2000-2500 tokens (code + prompt template)
- Output: 500-800 tokens (findings summary)
- Total: ~2500-3300 tokens

**Overflow Handling**:
- Truncate code snippet if needed
- Keep prompt template intact
- Preserve end of code (most recent definitions)

### Pass 2 (Components)

**Typical Usage** (per component):
- Input: 1500-2000 tokens (code + context from Pass 1)
- Output: 600-1000 tokens (component-specific findings)
- Total: ~2100-3000 tokens per component

**Overflow Handling**:
- Truncate component code
- Summarize Pass 1 context if too large
- Prioritize component-specific code

### Pass 3 (Synthesis)

**Typical Usage**:
- Input: 2000-3000 tokens (all findings summary + prompt)
- Output: 800-1500 tokens (final report)
- Total: ~2800-4500 tokens

**Overflow Handling**:
- **Context Compression**: If all findings > 32K tokens (150K chars)
  - Prioritize critical findings
  - Summarize major findings
  - Aggregate statistics
- Truncate non-critical information

## Context Compression for Pass 3

### When to Compress

```python
MAX_CONTEXT_CHARS = 150000  # ~32K tokens
if len(full_context) > MAX_CONTEXT_CHARS:
    return compress_context(full_context, all_findings)
```

### Compression Strategy

1. **Priority-based Filtering**:
   - Keep all critical findings (top 3 per pass)
   - Keep top 2 major findings per pass
   - Drop minor findings if needed

2. **Aggregation**:
   - Count totals instead of listing all
   - Summarize per-pass summaries
   - Extract key recommendations only

3. **Format**:
   ```markdown
   # Findings Summary (Compressed)
   
   ## Aggregated Statistics
   - Total Critical: 5
   - Total Major: 12
   
   ## Top Critical Issues
   - [pass_1] Issue 1
   - [pass_2_docker] Issue 2
   ...
   ```

## Monitoring and Metrics

### Tracked Metrics

- Per-pass token usage (input + output)
- Budget utilization percentage
- Truncation events
- Compression events
- Overflow frequency

### Logging

Structured JSON logs:
```json
{
  "event": "token_overflow",
  "pass": "pass_2_docker",
  "estimated_tokens": 3500,
  "remaining_budget": 2500,
  "truncation_ratio": 0.71,
  "preserved_end": true
}
```

## Best Practices

### For Prompt Design

1. **Keep prompts concise**: Remove unnecessary instructions
2. **Prioritize content**: Put important info at end (preserved on truncation)
3. **Use templates**: Reusable, token-efficient prompts

### For Code Processing

1. **Pre-filter code**: Only include relevant files
2. **Chunk large files**: Process in sections if needed
3. **Summarize early**: Create summaries before Pass 3

### For Error Handling

1. **Graceful degradation**: Truncate rather than fail
2. **Log all truncations**: For monitoring and optimization
3. **Preserve critical context**: Always keep most recent/important info

## Future Improvements

1. **Dynamic Budget Allocation**: Reallocate unused tokens
2. **Better Token Counting**: Use tiktoken or model-specific tokenizers
3. **Smart Truncation**: Use semantic understanding to preserve important parts
4. **Budget Prediction**: Estimate needs before allocation
5. **Streaming Responses**: Process large outputs incrementally

## References

- TokenAnalyzer: `src/domain/services/token_analyzer.py`
- MultiPassModelAdapter: `src/infrastructure/adapters/multi_pass_model_adapter.py`
- BaseReviewPass: `src/domain/agents/passes/base_pass.py`
- SynthesisPass compression: `src/domain/agents/passes/synthesis_pass.py::_compress_context`

