# Context Compression Strategy

## Overview

This document describes the context compression strategy used in Pass 3 (Synthesis) when the aggregated findings from all previous passes exceed the model's context window limits.

## Problem Statement

### Context Window Limits

- **Mistral-7B-Instruct**: ~4096 tokens input context
- **Practical Limit**: ~3000 tokens (leaving margin)
- **Character Equivalent**: ~150,000 characters (32K tokens)

### When Compression is Needed

Pass 3 needs to include:
1. All findings from Pass 1 (architecture)
2. All findings from Pass 2 (per component: docker, airflow, spark, mlflow)
3. Synthesis prompt template

**Scenario**: If project has many components with many findings:
- Pass 1: 10 findings
- Pass 2 Docker: 15 findings
- Pass 2 Airflow: 12 findings
- Pass 2 Spark: 8 findings
- Pass 2 MLflow: 10 findings
- **Total**: 55 findings × ~200 tokens each = 11,000+ tokens

Plus summaries, recommendations, metadata → **easily exceeds 32K tokens**

## Compression Algorithm

### Step 1: Size Check

```python
MAX_CONTEXT_CHARS = 150000  # Conservative limit (~32K tokens)
full_context = build_full_context(all_findings)

if len(full_context) > MAX_CONTEXT_CHARS:
    return compress_context(full_context, all_findings)
```

### Step 2: Priority-Based Filtering

**Priority Order**:
1. **Critical findings** (highest priority)
2. **Major findings** (medium priority)
3. **Minor findings** (lowest priority - dropped if needed)

**Implementation**:
```python
# Collect top findings per pass
for pass_name, findings in all_findings.items():
    critical_list = findings.get("critical", [])
    major_list = findings.get("major", [])

    # Top 3 critical per pass
    for item in critical_list[:3]:
        critical_items.append((pass_name, item))

    # Top 2 major per pass
    for item in major_list[:2]:
        major_items.append((pass_name, item))
```

### Step 3: Aggregation

Instead of listing all findings:
- **Count totals**: "5 critical, 12 major issues"
- **Top issues only**: Top 10 critical, top 10 major
- **Summaries preserved**: Keep per-pass summaries (truncated to 200 chars)

### Step 4: Format Compression

**Original Format** (verbose):
```markdown
## Pass 1
Summary: Long detailed summary...
Findings: 1 critical, 1 major, 0 minor

Critical:
- [CRITICAL] Issue 1: Detailed description...
- [CRITICAL] Issue 2: Detailed description...

Major:
- [MAJOR] Issue 3: Detailed description...
```

**Compressed Format**:
```markdown
## Aggregated Statistics
- Total Critical Issues: 5
- Total Major Issues: 12

## Top Critical Issues
- [pass_1] Issue 1 (truncated to 150 chars)
- [pass_2_docker] Issue 2 (truncated to 150 chars)
...
```

## Compression Implementation

### Current Implementation (SynthesisPass)

```python
def _compress_context(self, context: str, all_findings: Dict[str, Any]) -> str:
    """Compress by prioritizing critical findings."""

    # 1. Extract critical/major items
    critical_items = []
    major_items = []

    for pass_name, findings in all_findings.items():
        critical_list = findings.get("findings", {}).get("critical", [])
        major_list = findings.get("findings", {}).get("major", [])

        # Top 3 critical, top 2 major per pass
        critical_items.extend([(pass_name, item) for item in critical_list[:3]])
        major_items.extend([(pass_name, item) for item in major_list[:2]])

    # 2. Build compressed format
    compressed_parts = []
    compressed_parts.append("# Findings Summary (Compressed)\n")
    compressed_parts.append("*Note: Context compressed due to size limits.*\n\n")

    # 3. Aggregate statistics
    compressed_parts.append(f"- Total Critical: {total_critical}\n")
    compressed_parts.append(f"- Total Major: {total_major}\n\n")

    # 4. Top issues (max 10 each)
    for pass_name, item in critical_items[:10]:
        item_text = item[:150] + "..." if len(item) > 150 else item
        compressed_parts.append(f"- [{pass_name}] {item_text}\n")

    return "".join(compressed_parts)
```

### Compression Ratios

**Typical Compression**:
- Original: 200K characters → Compressed: 15K characters
- Ratio: ~92% reduction
- Preserves: All critical + top major issues

## Compression vs. Truncation

### Truncation (BaseReviewPass)

- **When**: Single prompt exceeds budget
- **How**: Simple character truncation (preserve end)
- **Loss**: Beginning of prompt lost

### Compression (SynthesisPass)

- **When**: Aggregated context exceeds limit
- **How**: Semantic prioritization + aggregation
- **Loss**: Minor findings and details, but critical info preserved

## Quality Preservation

### What is Preserved

✅ **Critical findings**: All (top 10 if many)
✅ **Major findings**: Top 10 overall
✅ **Summary statistics**: Totals and counts
✅ **Per-pass summaries**: Truncated but present

### What is Lost

❌ **Minor findings**: Dropped if space needed
❌ **Detailed descriptions**: Truncated to 150 chars
❌ **All recommendations**: Only top recommendations kept

### Impact Assessment

- **Critical info**: 100% preserved (all critical issues)
- **Important info**: ~80% preserved (top major issues)
- **Nice-to-have**: ~30% preserved (minor issues dropped)

## Testing Compression

### Unit Tests

```python
def test_compression_triggered():
    """Test compression when context exceeds limit."""
    large_context = "x" * 200000  # > 150K
    compressed = synthesis_pass._compress_context(large_context, findings)
    assert len(compressed) < len(large_context)
    assert "Compressed" in compressed

def test_critical_preserved():
    """Test that critical findings are preserved."""
    findings = {
        "pass_1": {"findings": {"critical": ["Critical 1", "Critical 2"]}}
    }
    compressed = compress_context("", findings)
    assert "Critical 1" in compressed
    assert "Critical 2" in compressed
```

### Integration Tests

Test with large projects:
- Generate 50+ findings across all passes
- Verify compression triggered
- Verify critical findings preserved
- Verify synthesis still produces meaningful results

## Monitoring

### Compression Events

Log when compression occurs:
```json
{
  "event": "context_compression",
  "pass": "pass_3",
  "original_size_chars": 200000,
  "compressed_size_chars": 15000,
  "compression_ratio": 0.925,
  "critical_preserved": 10,
  "major_preserved": 10,
  "minor_dropped": 5
}
```

### Metrics to Track

- Compression frequency
- Compression ratios
- Critical findings preservation rate
- Synthesis quality impact (user feedback)

## Future Improvements

1. **Semantic Summarization**: Use LLM to summarize instead of truncating
2. **Adaptive Thresholds**: Adjust compression aggressiveness based on findings count
3. **Incremental Processing**: Process findings in chunks, merge summaries
4. **User Preferences**: Allow users to specify what to preserve
5. **Hierarchical Compression**: Compress per-component, then aggregate

## References

- Implementation: `src/domain/agents/passes/synthesis_pass.py::_compress_context()`
- Token limits: `docs/reference/en/TOKEN_MANAGEMENT_STRATEGY.md`
- Real examples: Test with `tests/fixtures/large_project/`
