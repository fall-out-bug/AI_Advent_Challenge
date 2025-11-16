# Analyst Role Examples

This directory contains detailed, real-world examples demonstrating how the Analyst role applies day-by-day capabilities to gather, validate, and hand off requirements.

---

## Overview

Each example demonstrates a specific capability learned during the AI Challenge (Days 1-22). Examples are based on anonymized real-world scenarios and show:

- **Full workflows** with conversation transcripts
- **Before/after** comparisons (e.g., with/without compression)
- **Metrics and measurements** (token costs, time savings, quality scores)
- **Integration impact** on downstream roles (Architect, Tech Lead, Developer)

---

## Day-by-Day Examples

### Day 3 · Conversation Stopping Conditions

**File:** [`day_3_conversation_stopping.md`](day_3_conversation_stopping.md)

**Purpose:** Demonstrates how the Analyst recognizes when sufficient clarity is achieved (clarity_score ≥ 0.80) and stops gathering requirements.

**Key Takeaways:**
- Clarity score calculation methodology
- Stopping triggers: threshold met, max exchanges, external blockers
- Impact on downstream roles: fewer Architect clarifications

**Metrics:**
```
Session: EP23 Payment Methods
Exchanges: 3 (vs 8-10 without stopping condition)
Clarity Score: 0.88 (exceeds 0.80 threshold)
Token Savings: 42% (6.4K vs 11K average)
Architect Clarifications: 1 (vs 5 average)
```

**Related:** See [`../day_capabilities.md#day-3`](../day_capabilities.md#day-3) for technique details

---

### Day 8 · Token Management & Context Budgeting

**File:** [`day_8_token_budgeting.md`](day_8_token_budgeting.md)

**Purpose:** Demonstrates proactive token budget management during long requirement sessions (25+ exchanges) within 12K context window.

**Key Takeaways:**
- Real-time token tracking (12K context window budget)
- Compression trigger at 70% usage (7K tokens)
- Token allocation: system prompts (800), working (9,200), safety (2,000)
- Enables long sessions without overflow

**Metrics:**
```
Session: EP24 Multi-Tenant SaaS Platform
Total Exchanges: 25
Peak Token Usage: 8,699 (72% of window)
Compression Event: Exchange 15 (8,645 → 1,729 tokens)
Token Savings: 30% via compression
Result: ✅ Completed all 5 modules in single session
```

**Related:** See [`../day_capabilities.md#day-8`](../day_capabilities.md#day-8) for budget configuration

---

### Day 15 · Dialog Compression & Summarization

**File:** [`day_15_compression.md`](day_15_compression.md)

**Purpose:** Demonstrates map-reduce compression technique reducing 8K+ token conversations to ~1.6K tokens (80% reduction) while preserving 90%+ critical information.

**Key Takeaways:**
- Map-Reduce pattern: Group by topic → Summarize → Merge
- Lossy compression: Discard timestamps, filler, redundant confirmations
- Lossless preservation: Requirements, decisions, open questions, clarity scores
- Quality validation: Ensure ≥90% information retention

**Metrics:**
```
Session: EP25 E-Commerce Platform Redesign
Original Conversation: 8,142 tokens (20 exchanges)
Compressed Context: 1,640 tokens
Compression Ratio: 80%
Information Retention: 92%
Requirements Preserved: 15/15 (100%)
Decisions Preserved: 18/18 (100%)
```

**Comparison:**
```
Without Compression: Session incomplete (overflow at Ex 21)
With Compression: ✅ All 9 topics covered in one session
Architect Token Budget: 3,058 → 9,560 tokens (3x increase)
```

**Related:** See [`../day_capabilities.md#day-15`](../day_capabilities.md#day-15) for algorithm details

---

### Day 22 · RAG & Source Attribution

**File:** [`day_22_rag_citations.md`](day_22_rag_citations.md)

**Purpose:** Demonstrates querying MongoDB/RAG index for similar past requirements and citing sources to enable pattern reuse across epics.

**Key Takeaways:**
- RAG queries for similar requirements (semantic search)
- Citation format: source_epic, similarity_score, reason, production_validated
- Pattern reuse: 40% of requirements adapted from past epics
- Traceability: Full audit trail from current → past requirements

**Metrics:**
```
Session: EP26 Real-Time Analytics Dashboard
RAG Queries: 1 (MongoDB vector search)
Results: 10 found, 5 used
Citations: 5 (EP15, EP18, EP19, EP20, EP21)
Token Cost: 450 tokens (~4% of budget)

Time Savings:
- Requirements Gathering: 4h → 2.5h (38% faster)
- Architect Design: 8h → 5h (38% faster, reused designs)
- Implementation: 40h → 30h (25% faster, code reuse)
Total: 68h → 49.5h (27% reduction)

Quality Improvements:
- Clarity Score: 0.75 → 0.89 (concrete examples)
- Architect Clarifications: 12 → 3 (75% reduction)
- Design Rework Rate: 25% → 8% (proven patterns)
```

**Example MongoDB Query:**
```javascript
db.requirements.find({
  keywords: { $in: ["dashboard", "analytics", "real-time"] },
  clarity_score: { $gte: 0.80 },
  production_validated: true
}).limit(5)
```

**Related:** 
- See [`../day_capabilities.md#day-22`](../day_capabilities.md#day-22) for RAG technique
- See [`../rag_queries.md`](../rag_queries.md) for query patterns with examples

---

### Day 23 · Observability Self-Observation

**File:** [`day_23_observability.md`](day_23_observability.md)

**Purpose:** Demonstrates how Analyst agents use Day 23 observability metrics (Prometheus, structured logs, tracing) to self-verify handoff quality and trace requirement gathering sessions.

**Key Takeaways:**
- Include observability metadata (`trace_id`, `epic_id`, `stage_id`, `latency_ms`) in handoff JSON
- Query `/metrics` endpoints (MCP/Butler/CLI) to verify handoff completion metrics
- Use structured logs to track requirement gathering quality scores
- Reference benchmark export duration metrics to validate dataset completeness

**Metrics:**
```
Session: EP23 Observability & Benchmark Enablement
Trace ID: 550e8400-e29b-41d4-a716-446655440000
Latency: 2450ms
Structured Logs: 127 entries
Observability Verification: ✅ Passed

Handoff Quality:
- Metrics Endpoint: http://localhost:8004/metrics accessible
- Structured Logs Rate: 2.5 logs/second (normal)
- Benchmark Export Duration: 12.5s (within threshold)
- Shared Infra Bootstrap: mongo=1, mock_services=1 (healthy)
```

**Example Handoff JSON with Observability Metadata:**
```json
{
  "metadata": {
    "epic_id": "EP23",
    "trace_id": "550e8400-e29b-41d4-a716-446655440000",
    "observability": {
      "structured_logs_total": 127,
      "benchmark_export_duration_seconds": 12.5,
      "shared_infra_bootstrap_status": {"mongo": 1, "mock_services": 1}
    }
  }
}
```

**Related:** 
- See [`../day_capabilities.md#day-23`](../day_capabilities.md#day-23) for observability capability
- See [`../../operational/observability_labels.md`](../../operational/observability_labels.md) for metric taxonomy

---

## Cross-Cutting Examples

### Handoff Quality Examples

**File:** [`../../operational/handoff_contracts.md#real-handoff-examples`](../../operational/handoff_contracts.md#real-handoff-examples)

**Contains:**
1. **Analyst → Architect** (EP23 Payment Module)
   - Complete requirements JSON with RAG citations
   - Architect response with architecture decisions
   - Quality metrics and impact analysis

2. **Architect → Tech Lead** (EP23 Payment Module)
   - Implementation plan with 8 stages
   - CI gates, risk register, team allocation
   - Traceability from requirements → stages

**Key Patterns:**
- Complete metadata (epic_id, timestamps, versions)
- RAG citations for pattern reuse
- Open questions with blocking status
- Traceability chain: REQ → Component → MADR → Stage → Test

**Metrics:**
```
Handoff Quality: Analyst → Architect
✅ Clarity Score: 0.87 (high)
✅ Completeness: 8/8 requirements with AC
✅ RAG Citations: 2 (EP15, EP19 patterns)
✅ Compression: 7,800 → 2,100 tokens
Architect Response Time: 4.5h (expected: 6-8h)
Clarification Requests: 1 (minimal back-and-forth)
```

---

## Example Matrix: Day Capabilities → Use Cases

| Day | Capability | Example File | Key Metric | Impact on Downstream |
|-----|------------|--------------|------------|---------------------|
| 3 | Conversation Stopping | `day_3_conversation_stopping.md` | 42% token savings | 75% fewer Architect clarifications |
| 8 | Token Budgeting | `day_8_token_budgeting.md` | 25+ exchanges in 12K window | Enables complex epics in single session |
| 15 | Compression | `day_15_compression.md` | 80% reduction, 92% retention | 3x more tokens for Architect design |
| 22 | RAG Citations | `day_22_rag_citations.md` | 27% time savings, 40% pattern reuse | 30% faster design + implementation |
| 23 | Observability Self-Observation | `day_23_observability.md` | Trace coverage 100%, telemetry verification | Enables evidence-based handoff validation |

---

## How to Use These Examples

### For Analyst Agents

1. **Read examples** to understand expected output quality
2. **Replicate patterns** in your requirement gathering sessions
3. **Measure results** using same metrics (clarity score, token cost, etc.)
4. **Reference in handoffs**: "Following Day 15 compression pattern..."

### For Architect/Tech Lead Agents

1. **Understand Analyst outputs** to provide better feedback
2. **Leverage RAG citations** to reference past designs
3. **Validate handoff quality** using metrics from examples
4. **Request missing patterns**: "Please apply Day 22 RAG to find similar requirements"

### For Reviewers

1. **Quality benchmarks**: Compare handoffs to examples
2. **Checklist validation**: All examples include metadata, citations, clarity scores
3. **Pattern compliance**: Ensure Day 3/8/15/22 techniques applied when appropriate

---

## Creating New Examples

When documenting new epics or capabilities:

1. **Use consistent structure**:
   - Purpose
   - Key Takeaways
   - Full walkthrough (with transcripts if applicable)
   - Metrics and measurements
   - Integration impact on downstream roles
   - Related documentation links

2. **Anonymize data**:
   - Use generic epic IDs (EP23, EP24, etc.)
   - Remove company names, personal info
   - Use realistic but fake metrics

3. **Keep examples concise**:
   - Target: 1-2 pages per example
   - Use tables, code blocks, and metrics for readability
   - Cross-link to detailed docs (e.g., `day_capabilities.md`)

4. **Show before/after**:
   - Without pattern: What goes wrong?
   - With pattern: How does it improve?
   - Quantify improvements (%, hours saved, etc.)

---

## Example Folder Structure (Future Expansion)

```
examples/
├── README.md (this file)
├── day_3_conversation_stopping.md ✅
├── day_8_token_budgeting.md ✅
├── day_15_compression.md ✅
├── day_22_rag_citations.md ✅
├── EP21/                           (Future: Epic-specific examples)
│   ├── day_19_indexing.md
│   ├── requirements_matrix.md
│   └── review_remarks.md
├── EP23/                           (Future: Complex epic examples)
│   ├── full_session_transcript.md
│   ├── rag_query_results.json
│   └── handoff_chain.md
└── templates/                      (Future: Reusable templates)
    ├── requirement_template.json
    ├── handoff_template.json
    └── rag_query_template.js
```

---

## Related Documentation

- **Capabilities:** [`../day_capabilities.md`](../day_capabilities.md) - Full Day 1-22 techniques
- **RAG Queries:** [`../rag_queries.md`](../rag_queries.md) - MongoDB query patterns with costs
- **Role Definition:** [`../role_definition.md`](../role_definition.md) - Analyst purpose and responsibilities
- **Handoff Contracts:** [`../../operational/handoff_contracts.md`](../../operational/handoff_contracts.md) - Cross-role handoff patterns
- **Context Limits:** [`../../operational/context_limits.md`](../../operational/context_limits.md) - Token budget configuration
- **Workflow:** [`../../specs/process/agent_workflow.md`](../../specs/process/agent_workflow.md) - Agent cycle sequence

---

## Changelog

- **2025-11-15**: Created comprehensive examples for Days 3, 8, 15, 22
- **2025-11-15**: Added real handoff examples (Analyst → Architect → Tech Lead)
- **2025-11-15**: Enhanced rag_queries.md with example results and token costs
- **2025-11-16**: Added Day 23 observability self-observation example (Epic 23)

---

## Questions or Feedback

If you need additional examples or have questions about applying these patterns:

1. Check [`../day_capabilities.md`](../day_capabilities.md) for detailed technique documentation
2. Review [`../rag_queries.md`](../rag_queries.md) for query patterns
3. Refer to [`../../operational/handoff_contracts.md`](../../operational/handoff_contracts.md) for handoff quality standards

All examples maintain 80%+ test coverage and follow repository Clean Code practices.
