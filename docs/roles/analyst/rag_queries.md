# Analyst RAG Queries

## Purpose
Support requirement discovery and validation using MongoDB-backed knowledge
bases and document stores. All queries assume credentials from
`docs/operational/context_limits.md`.

## Collections
- `requirements`: Canonical epic/day requirement documents.
- `decisions`: MADR entries with trade-offs and consequences.
- `reviews`: Review feedback from Architect, Tech Lead, Developer, Reviewer.

## Baseline Queries

### Latest Requirements by Epic
```javascript
db.requirements
  .find({ epic: "EP21" })
  .sort({ updated_at: -1 })
  .limit(5);
```

### Acceptance Criteria Coverage
```javascript
db.requirements.aggregate([
  { $match: { epic: "EP21" } },
  { $unwind: "$acceptance_criteria" },
  {
    $lookup: {
      from: "tests",
      localField: "acceptance_criteria.test_id",
      foreignField: "test_id",
      as: "linked_tests"
    }
  },
  { $project: { number: 1, title: 1, "acceptance_criteria": 1, linked_tests: 1 } }
]);
```

### Open Review Remarks
```javascript
db.reviews.find({
  epic: "EP21",
  status: { $in: ["open", "in_progress"] },
  role: { $in: ["architect", "tech_lead"] }
});
```

### Traceability Gaps
```javascript
db.requirements.aggregate([
  { $match: { epic: "EP21" } },
  {
    $project: {
      number: 1,
      title: 1,
      missing_traceability: {
        $setDifference: ["$acceptance_criteria.targets", "$linked_tests"]
      }
    }
  },
  { $match: { missing_traceability: { $ne: [] } } }
]);
```

## Operational Notes
- Index recommendations: `{ epic: 1, updated_at: -1 }` on `requirements`,
  `{ status: 1, role: 1 }` on `reviews`.
- Always sanitize epic/day inputs; prefer parameterized helpers in application
  layer.
- For cross-epoch analyses, mirror queries into dedicated analytics views and
  export summaries to `docs/epics/<epic>/analytics.md`.

---

## Query Examples with Results & Costs

### Example 1: Latest Requirements by Epic

**Query:**
```javascript
db.requirements
  .find({ epic: "EP21" })
  .sort({ updated_at: -1 })
  .limit(5);
```

**Example Results (Anonymized):**
```json
[
  {
    "_id": "674ad2f1c8e9a1234567890a",
    "epic": "EP21",
    "req_id": "REQ-MOD-001",
    "title": "Modular Reviewer Architecture",
    "text": "System must support pluggable review modules for different code aspects",
    "type": "functional",
    "priority": "high",
    "clarity_score": 0.91,
    "status": "approved",
    "updated_at": "2025-11-10T14:30:00Z"
  },
  {
    "_id": "674ad2f1c8e9a1234567890b",
    "epic": "EP21",
    "req_id": "REQ-MOD-002",
    "title": "Session State Persistence",
    "text": "Review sessions must persist state across multiple passes",
    "type": "functional",
    "priority": "high",
    "clarity_score": 0.88,
    "status": "approved",
    "updated_at": "2025-11-09T16:45:00Z"
  },
  {
    "_id": "674ad2f1c8e9a1234567890c",
    "epic": "EP21",
    "req_id": "REQ-PERF-001",
    "title": "Review Performance Budget",
    "text": "Full review must complete in < 30 seconds for files < 500 LOC",
    "type": "non-functional",
    "priority": "high",
    "clarity_score": 0.89,
    "status": "approved",
    "updated_at": "2025-11-08T10:20:00Z"
  }
]
```

**Token Cost:** ~300 tokens (for 5 results with metadata)  
**Query Time:** ~50ms  
**When to Use:** Initial requirement discovery for specific epic  
**When NOT to Use:** Cross-epic pattern search (use semantic search instead)

---

### Example 2: Acceptance Criteria Coverage

**Query:**
```javascript
db.requirements.aggregate([
  { $match: { epic: "EP21" } },
  { $unwind: "$acceptance_criteria" },
  {
    $lookup: {
      from: "tests",
      localField: "acceptance_criteria.test_id",
      foreignField: "test_id",
      as: "linked_tests"
    }
  },
  { $project: { 
      req_id: 1, 
      title: 1, 
      "acceptance_criteria": 1, 
      test_coverage: { $size: "$linked_tests" }
    } 
  }
]);
```

**Example Results:**
```json
[
  {
    "_id": "674ad2f1c8e9a1234567890a",
    "req_id": "REQ-MOD-001",
    "title": "Modular Reviewer Architecture",
    "acceptance_criteria": {
      "id": "AC-001",
      "text": "System must load modules dynamically at runtime",
      "test_id": "TEST-MOD-001"
    },
    "test_coverage": 1
  },
  {
    "_id": "674ad2f1c8e9a1234567890a",
    "req_id": "REQ-MOD-001",
    "title": "Modular Reviewer Architecture",
    "acceptance_criteria": {
      "id": "AC-002",
      "text": "Modules must register via decorator pattern",
      "test_id": null
    },
    "test_coverage": 0
  }
]
```

**Token Cost:** ~500 tokens (includes aggregation results with test links)  
**Query Time:** ~120ms (includes JOIN operation)  
**When to Use:** Validating test coverage before epic sign-off  
**When NOT to Use:** Real-time validation (too slow for interactive use)

---

### Example 3: Open Review Remarks

**Query:**
```javascript
db.reviews.find({
  epic: "EP21",
  status: { $in: ["open", "in_progress"] },
  role: { $in: ["architect", "tech_lead"] }
});
```

**Example Results:**
```json
[
  {
    "_id": "674bd3a2d9f0b2345678901a",
    "epic": "EP21",
    "requirement_id": "REQ-MOD-001",
    "role": "architect",
    "reviewer": "architect_agent",
    "status": "open",
    "remarks": [
      {
        "id": "REM-001",
        "text": "Module interface needs versioning strategy",
        "severity": "medium",
        "blocking": false
      }
    ],
    "created_at": "2025-11-11T09:30:00Z"
  },
  {
    "_id": "674bd3a2d9f0b2345678901b",
    "epic": "EP21",
    "requirement_id": "REQ-PERF-001",
    "role": "tech_lead",
    "reviewer": "tech_lead_agent",
    "status": "in_progress",
    "remarks": [
      {
        "id": "REM-002",
        "text": "Performance target may be too aggressive for complex files",
        "severity": "high",
        "blocking": true
      }
    ],
    "created_at": "2025-11-10T15:20:00Z"
  }
]
```

**Token Cost:** ~400 tokens (for 2 results with remarks)  
**Query Time:** ~60ms  
**When to Use:** Before finalizing requirements (check for blockers)  
**When NOT to Use:** Historical analysis (use archived reviews)

---

### Example 4: Traceability Gaps

**Query:**
```javascript
db.requirements.aggregate([
  { $match: { epic: "EP21" } },
  {
    $project: {
      req_id: 1,
      title: 1,
      acceptance_criteria_count: { $size: "$acceptance_criteria" },
      linked_tests_count: { 
        $size: { $ifNull: ["$linked_tests", []] } 
      }
    }
  },
  { 
    $match: { 
      $expr: { 
        $lt: ["$linked_tests_count", "$acceptance_criteria_count"] 
      } 
    } 
  }
]);
```

**Example Results:**
```json
[
  {
    "_id": "674ad2f1c8e9a1234567890a",
    "req_id": "REQ-MOD-001",
    "title": "Modular Reviewer Architecture",
    "acceptance_criteria_count": 5,
    "linked_tests_count": 3
  },
  {
    "_id": "674ad2f1c8e9a1234567890c",
    "req_id": "REQ-PERF-001",
    "title": "Review Performance Budget",
    "acceptance_criteria_count": 4,
    "linked_tests_count": 2
  }
]
```

**Interpretation:** 
- REQ-MOD-001: 2 acceptance criteria lack tests (5 - 3 = 2)
- REQ-PERF-001: 2 acceptance criteria lack tests (4 - 2 = 2)

**Token Cost:** ~250 tokens (for 2 results)  
**Query Time:** ~100ms (aggregation pipeline)  
**When to Use:** Pre-implementation validation, CI gate checks  
**When NOT to Use:** During active requirement gathering (premature)

---

### Example 5: Semantic Search for Similar Requirements (Day 22)

**Query (Vector Search):**
```javascript
// Using MongoDB Atlas Vector Search
db.requirements.aggregate([
  {
    $vectorSearch: {
      index: "requirements_vector_index",
      path: "embedding",
      queryVector: [0.123, -0.456, ...],  // 1536-dim embedding
      numCandidates: 100,
      limit: 5
    }
  },
  {
    $match: {
      clarity_score: { $gte: 0.80 },
      status: { $in: ["approved", "implemented"] },
      production_validated: true
    }
  },
  {
    $project: {
      epic: 1,
      req_id: 1,
      title: 1,
      text: 1,
      clarity_score: 1,
      similarity_score: { $meta: "vectorSearchScore" }
    }
  }
]);
```

**Example Results:**
```json
[
  {
    "epic": "EP18",
    "req_id": "R-34",
    "title": "Admin Dashboard - System Health Metrics",
    "text": "Dashboard must display real-time system health: API latency, error rate, active users",
    "clarity_score": 0.92,
    "similarity_score": 0.91
  },
  {
    "epic": "EP20",
    "req_id": "R-89",
    "title": "Real-Time Data Refresh Architecture",
    "text": "Dashboard data must refresh without full page reload using WebSocket",
    "clarity_score": 0.90,
    "similarity_score": 0.87
  },
  {
    "epic": "EP15",
    "req_id": "R-23",
    "title": "Dashboard Performance Budget",
    "text": "Dashboard must load in < 3 seconds, handle 10K concurrent users",
    "clarity_score": 0.87,
    "similarity_score": 0.85
  }
]
```

**Token Cost:** ~450 tokens (for 5 results with embeddings metadata)  
**Query Time:** ~150ms (vector index lookup + filters)  
**When to Use:** Finding similar patterns across epics (Day 22 RAG)  
**When NOT to Use:** Exact text matching (use keyword search instead)

---

## Token Cost Summary

| Query Type | Avg Results | Token Cost | Query Time | Use Case |
|------------|-------------|------------|------------|----------|
| Simple Find | 5 | 300 | 50ms | Epic-specific lookup |
| Aggregation (JOIN) | 10 | 500 | 120ms | Coverage analysis |
| Review Lookup | 3 | 400 | 60ms | Blocking issue check |
| Traceability Gap | 5 | 250 | 100ms | Quality gates |
| Vector Search | 5 | 450 | 150ms | Semantic similarity (RAG) |

**Total Budget Impact:**
- Single query: 250-500 tokens (2-4% of 12K window)
- Full requirement session with RAG: ~1,500 tokens (12% of window)
- ROI: 1,500 tokens investment → 30%+ time savings

---

## Query Selection Guide

### Use Simple Find When:
- ✅ Looking for requirements in specific epic
- ✅ Need latest updates (sorted by timestamp)
- ✅ Fast response critical (< 100ms)
- ❌ Don't need: Cross-epic patterns, semantic matching

### Use Aggregation When:
- ✅ Need to JOIN collections (requirements + tests)
- ✅ Complex filtering (gaps, coverage analysis)
- ✅ Acceptable latency (100-200ms)
- ❌ Don't need: Real-time interactive queries

### Use Vector Search When:
- ✅ Finding similar requirements across epics (Day 22 RAG)
- ✅ Semantic matching (not exact keywords)
- ✅ Pattern reuse and citations
- ❌ Don't need: Exact text matching (use keyword search)

---

## Best Practices

### 1. Filter Aggressively

```javascript
// ✅ Good: Pre-filter before expensive operations
db.requirements.find({
  clarity_score: { $gte: 0.80 },  // Filter first
  status: "approved",
  production_validated: true
}).limit(5)

// ❌ Bad: Fetch everything then filter in application
db.requirements.find({}).toArray()
  .filter(r => r.clarity_score >= 0.80)
```

### 2. Use Indexes

```javascript
// Create covering indexes for common queries
db.requirements.createIndex({
  epic: 1,
  status: 1,
  clarity_score: 1,
  updated_at: -1
})

// Check index usage
db.requirements.find({ epic: "EP21" }).explain("executionStats")
```

### 3. Limit Results

```javascript
// ✅ Always limit (save tokens)
db.requirements.find({ epic: "EP21" }).limit(5)

// ❌ Never fetch unlimited
db.requirements.find({ epic: "EP21" })  // Could return 100+ results
```

### 4. Project Only Needed Fields

```javascript
// ✅ Good: Project only what you need
db.requirements.find(
  { epic: "EP21" },
  { req_id: 1, title: 1, clarity_score: 1 }
)

// ❌ Bad: Fetch entire documents (wasteful)
db.requirements.find({ epic: "EP21" })
```

---

## Query Performance Monitoring

### Track Query Metrics

```python
class QueryMetrics:
    def __init__(self):
        self.query_count = 0
        self.total_tokens = 0
        self.total_time_ms = 0
    
    def record_query(self, tokens: int, time_ms: int):
        self.query_count += 1
        self.total_tokens += tokens
        self.total_time_ms += time_ms
    
    def report(self):
        return {
            "queries": self.query_count,
            "total_tokens": self.total_tokens,
            "avg_tokens_per_query": self.total_tokens / self.query_count,
            "total_time_ms": self.total_time_ms,
            "avg_time_per_query_ms": self.total_time_ms / self.query_count
        }

# Example usage:
# Session metrics: 3 queries, 1150 tokens, 310ms total
# → Avg: 383 tokens/query, 103ms/query
```

---

## Additional Resources
- Capabilities: `docs/roles/analyst/day_capabilities.md`
- Day 22 RAG Pattern: `docs/roles/analyst/examples/day_22_rag_citations.md`
- Handoff schema: `docs/operational/handoff_contracts.md`
- Workflow context: `docs/specs/process/agent_workflow.md`
- MongoDB Schema: `docs/operational/shared_infra.md#mongodb`
