# Day 22 Example: RAG & Source Attribution

## Purpose

Demonstrate how the Analyst agent queries MongoDB/RAG index for similar past requirements, cites sources in outputs, and enables pattern reuse across epics.

---

## Scenario

**Epic:** EP26 - Real-Time Analytics Dashboard
**Analyst Task:** Gather requirements for analytics system
**RAG Enhancement:** Query past epics for similar analytics/dashboard requirements
**Expected Benefit:** Reuse proven patterns, reduce design time by 30%

---

## Step 1: Initial Requirement Gathering (Without RAG)

### Stakeholder Input

```
Stakeholder: "We need a real-time analytics dashboard showing user activity metrics, transaction volumes, and system health."

Analyst (Initial gathering):
{
  "requirements": [
    {
      "id": "REQ-001-draft",
      "text": "Build real-time analytics dashboard",
      "clarity_score": 0.45,
      "issues": ["Too vague", "No specific metrics defined"]
    }
  ]
}
```

---

## Step 2: RAG Query for Similar Requirements

### Query Execution

**Analyst Decision:**
> "Before asking clarifying questions, let me check if we have similar requirements from past epics that can guide this conversation."

**RAG Query:**
```javascript
// MongoDB query for similar analytics/dashboard requirements
db.requirements.find({
  $or: [
    { keywords: { $in: ["analytics", "dashboard", "metrics", "real-time"] } },
    { text: { $regex: /dashboard|analytics|metrics/i } }
  ],
  epic: { $gte: "EP15" },  // Recent epics (last ~10 epics)
  clarity_score: { $gte: 0.80 },  // Only high-quality requirements
  status: { $in: ["approved", "implemented"] },  // Validated requirements
  production_validated: true  // Proven in production
}).sort({
  created_at: -1  // Most recent first
}).limit(10)
```

---

### RAG Query Results

**Result Set (Anonymized):**

```json
[
  {
    "_id": "674ad2f1c8e9a1234567890a",
    "epic": "EP18",
    "req_id": "R-34",
    "title": "Admin Dashboard - System Health Metrics",
    "text": "Dashboard must display real-time system health: API latency (p95), error rate, active users, CPU/memory usage",
    "type": "functional",
    "priority": "high",
    "clarity_score": 0.92,
    "acceptance_criteria": [
      "Metrics update every 30 seconds (real-time)",
      "Display p50, p95, p99 latencies",
      "Alert visual indicator when error rate > 1%",
      "Historical comparison: 24h, 7d, 30d views"
    ],
    "status": "implemented",
    "production_validated": true,
    "production_notes": "Dashboard used successfully for 6 months. Users love the 30s refresh rate.",
    "tags": ["dashboard", "metrics", "real-time", "observability"],
    "created_at": "2025-09-12T14:30:00Z"
  },
  {
    "_id": "674ad2f1c8e9a1234567890b",
    "epic": "EP21",
    "req_id": "R-67",
    "title": "Transaction Analytics Dashboard",
    "text": "Dashboard shows transaction volume metrics: total transactions, success rate, revenue, top merchants",
    "type": "functional",
    "priority": "high",
    "clarity_score": 0.88,
    "acceptance_criteria": [
      "Display hourly transaction volume (bar chart)",
      "Success rate percentage (past 24h, 7d, 30d)",
      "Revenue breakdown by payment method",
      "Top 10 merchants by transaction count",
      "Export to CSV functionality"
    ],
    "status": "implemented",
    "production_validated": true,
    "production_notes": "CSV export feature heavily used by finance team. Added caching for performance.",
    "tags": ["dashboard", "analytics", "transactions", "reporting"],
    "created_at": "2025-10-20T09:15:00Z"
  },
  {
    "_id": "674ad2f1c8e9a1234567890c",
    "epic": "EP19",
    "req_id": "R-45",
    "title": "User Activity Heatmap",
    "text": "Display user activity heatmap: active users by hour/day, peak usage times, geographic distribution",
    "type": "functional",
    "priority": "medium",
    "clarity_score": 0.85,
    "acceptance_criteria": [
      "Heatmap shows 24h x 7d grid",
      "Color gradient: low (blue) to high (red) activity",
      "Click on cell shows detailed metrics for that hour",
      "Geographic map shows user distribution by country"
    ],
    "status": "implemented",
    "production_validated": true,
    "production_notes": "Heatmap helped identify peak load times for scaling. Geographic view revealed new markets.",
    "tags": ["dashboard", "user-activity", "visualization", "heatmap"],
    "created_at": "2025-09-28T11:00:00Z"
  },
  {
    "_id": "674ad2f1c8e9a1234567890d",
    "epic": "EP20",
    "req_id": "R-89",
    "title": "Real-Time Data Refresh Architecture",
    "text": "Dashboard data must refresh without full page reload. Use WebSocket or SSE for live updates.",
    "type": "technical",
    "priority": "high",
    "clarity_score": 0.90,
    "acceptance_criteria": [
      "WebSocket connection for live data push",
      "Fallback to polling (30s interval) if WebSocket fails",
      "Client-side reconnection logic (exponential backoff)",
      "Server pushes updates only when data changes (not fixed interval)"
    ],
    "status": "implemented",
    "production_validated": true,
    "production_notes": "WebSocket approach reduced server load by 60% vs polling. Reconnection logic critical for mobile users.",
    "architecture_decision": "MADR-045: WebSocket for real-time dashboards",
    "tags": ["real-time", "websocket", "architecture", "performance"],
    "created_at": "2025-10-05T16:45:00Z"
  },
  {
    "_id": "674ad2f1c8e9a1234567890e",
    "epic": "EP15",
    "req_id": "R-23",
    "title": "Dashboard Performance Budget",
    "text": "Dashboard must load in < 3 seconds, render charts in < 1 second, handle 10K concurrent users",
    "type": "non-functional",
    "priority": "high",
    "clarity_score": 0.87,
    "acceptance_criteria": [
      "Initial load (cold cache): < 3 seconds",
      "Chart rendering: < 1 second",
      "Support 10K concurrent users without degradation",
      "Data query optimization: < 500ms for metrics"
    ],
    "status": "implemented",
    "production_validated": true,
    "production_notes": "Met all targets. Query optimization (indexing + caching) was key. CDN for static assets.",
    "tags": ["performance", "dashboard", "scalability"],
    "created_at": "2025-08-15T10:20:00Z"
  }
]
```

**Query Statistics:**
```
Total matching requirements: 10
Returned: 5 (top relevance)
Average similarity score: 0.87
Token cost: ~450 tokens (for 5 results)
Query time: 120ms
```

---

## Step 3: Analyst Uses RAG Results to Guide Conversation

### Enhanced Requirement Gathering (With RAG Context)

**Analyst (Now with RAG context):**
> "I found 5 similar dashboard requirements from past epics (EP15, EP18, EP19, EP20, EP21). Let me use these as a template for our conversation.
>
> Based on EP18's system health dashboard and EP21's transaction analytics, I'll ask targeted questions:"

**Q1 (Informed by EP18_R-34 & EP21_R-67):**
> "For your analytics dashboard, which specific metrics should we display?
>
> For reference:
> - EP18 showed: API latency, error rate, active users, resource usage
> - EP21 showed: transaction volume, success rate, revenue, top merchants
>
> What metrics are most important for your use case?"

**Stakeholder:**
> "Great examples! For us, we need:
> - Active users (current + 24h trend)
> - API request rate (requests/sec)
> - Error rate (past 1h, 24h, 7d)
> - Database query performance (p95 latency)
> - Recent errors log (last 20 entries)"

**Analyst captures requirement WITH citation:**
```json
{
  "id": "REQ-DASH-001",
  "text": "Dashboard must display real-time system metrics: active users, API request rate, error rate, DB query latency (p95)",
  "rag_citation": {
    "source": "EP18_req#R-34",
    "similarity": 0.92,
    "reason": "Similar system health metrics pattern from EP18 admin dashboard",
    "reused_patterns": [
      "Real-time updates (30s refresh)",
      "Multi-timeframe views (1h, 24h, 7d)",
      "Performance percentiles (p50, p95, p99)"
    ]
  },
  "acceptance_criteria": [
    "Metrics update every 30 seconds (pattern from EP18)",
    "Display p50, p95, p99 latencies (pattern from EP18)",
    "Error rate alert indicator when > 1% (pattern from EP18)",
    "Historical comparison: 1h, 24h, 7d views"
  ],
  "clarity_score": 0.89
}
```

---

**Q2 (Informed by EP20_R-89 - WebSocket architecture):**
> "How should the dashboard refresh? EP20 implemented WebSocket for live updates (reduced server load 60%). Should we follow that pattern?"

**Stakeholder:**
> "Yes! We don't want users manually refreshing. WebSocket sounds perfect."

**Analyst captures requirement WITH citation:**
```json
{
  "id": "REQ-DASH-002",
  "text": "Dashboard must use WebSocket for real-time data updates, fallback to polling if WebSocket unavailable",
  "rag_citation": {
    "source": "EP20_req#R-89",
    "similarity": 0.95,
    "reason": "Proven WebSocket architecture from EP20 real-time dashboard",
    "architecture_reference": "MADR-045: WebSocket for real-time dashboards",
    "production_validated": true,
    "production_notes": "EP20: 60% server load reduction vs polling"
  },
  "acceptance_criteria": [
    "WebSocket connection for live data push (pattern from EP20)",
    "Fallback to 30s polling if WebSocket fails (pattern from EP20)",
    "Client-side reconnection with exponential backoff (pattern from EP20)",
    "Server pushes updates only on data changes (pattern from EP20)"
  ],
  "clarity_score": 0.92,
  "implementation_reference": "src/infrastructure/websocket/ (from EP20)"
}
```

---

**Q3 (Informed by EP15_R-23 - Performance budget):**
> "What are your performance requirements? EP15 set targets: < 3s load, < 1s chart render, 10K concurrent users. Similar for you?"

**Stakeholder:**
> "We have smaller scale - maybe 2K concurrent users max. But yes, fast loading is critical."

**Analyst captures requirement WITH citation:**
```json
{
  "id": "REQ-DASH-003",
  "text": "Dashboard must load in < 3 seconds, render charts in < 1 second, support 2K concurrent users",
  "rag_citation": {
    "source": "EP15_req#R-23",
    "similarity": 0.85,
    "reason": "Performance budget pattern from EP15, adjusted for lower scale",
    "adjustments": [
      "Concurrent users: 10K → 2K (lower scale)",
      "Same load time targets (< 3s, < 1s)",
      "Query optimization approach reused"
    ]
  },
  "acceptance_criteria": [
    "Initial load (cold cache): < 3 seconds",
    "Chart rendering: < 1 second",
    "Support 2K concurrent users without degradation",
    "Data query optimization: < 500ms for metrics"
  ],
  "clarity_score": 0.88,
  "implementation_notes": "Reuse EP15 caching strategy + CDN for static assets"
}
```

---

## Step 4: Final Requirements Output (With Citations)

### Complete Requirements Package

```json
{
  "metadata": {
    "epic_id": "EP26",
    "analyst_agent": "cursor_analyst_v1",
    "timestamp": "2025-11-15T14:30:00Z",
    "version": "1.0",
    "rag_enabled": true
  },

  "requirements": [
    {
      "id": "REQ-DASH-001",
      "text": "Dashboard must display real-time system metrics: active users, API request rate, error rate, DB query latency (p95)",
      "type": "functional",
      "priority": "high",
      "clarity_score": 0.89,
      "acceptance_criteria": [
        "Metrics update every 30 seconds (real-time)",
        "Display p50, p95, p99 latencies",
        "Error rate alert indicator when > 1%",
        "Historical comparison: 1h, 24h, 7d views",
        "Recent errors log (last 20 entries)"
      ],
      "rag_citation": {
        "source_epic": "EP18",
        "source_req": "R-34",
        "similarity_score": 0.92,
        "reason": "Similar system health metrics pattern",
        "production_validated": true,
        "reused_patterns": [
          "Real-time updates (30s refresh)",
          "Multi-timeframe views",
          "Performance percentiles"
        ]
      }
    },

    {
      "id": "REQ-DASH-002",
      "text": "Dashboard must use WebSocket for real-time data updates, fallback to polling if WebSocket unavailable",
      "type": "technical",
      "priority": "high",
      "clarity_score": 0.92,
      "acceptance_criteria": [
        "WebSocket connection for live data push",
        "Fallback to 30s polling if WebSocket fails",
        "Client-side reconnection with exponential backoff",
        "Server pushes updates only on data changes"
      ],
      "rag_citation": {
        "source_epic": "EP20",
        "source_req": "R-89",
        "similarity_score": 0.95,
        "reason": "Proven WebSocket architecture for real-time dashboards",
        "architecture_decision": "MADR-045",
        "production_validated": true,
        "production_impact": "60% server load reduction vs polling",
        "implementation_reference": "src/infrastructure/websocket/"
      }
    },

    {
      "id": "REQ-DASH-003",
      "text": "Dashboard must load in < 3 seconds, render charts in < 1 second, support 2K concurrent users",
      "type": "non-functional",
      "priority": "high",
      "clarity_score": 0.88,
      "acceptance_criteria": [
        "Initial load (cold cache): < 3 seconds",
        "Chart rendering: < 1 second",
        "Support 2K concurrent users without degradation",
        "Data query optimization: < 500ms for metrics"
      ],
      "rag_citation": {
        "source_epic": "EP15",
        "source_req": "R-23",
        "similarity_score": 0.85,
        "reason": "Performance budget pattern, adjusted for lower scale",
        "adjustments": [
          "Concurrent users: 10K → 2K (appropriate for our scale)"
        ],
        "production_validated": true,
        "implementation_reference": "Caching strategy + CDN from EP15"
      }
    },

    {
      "id": "REQ-DASH-004",
      "text": "Dashboard must include data export functionality (CSV, JSON)",
      "type": "functional",
      "priority": "medium",
      "clarity_score": 0.90,
      "acceptance_criteria": [
        "Export current view to CSV",
        "Export current view to JSON",
        "Export includes timestamp and filters applied",
        "Export completes in < 5 seconds"
      ],
      "rag_citation": {
        "source_epic": "EP21",
        "source_req": "R-67",
        "similarity_score": 0.88,
        "reason": "CSV export pattern heavily used by finance team in EP21",
        "production_validated": true,
        "production_notes": "EP21: Export feature used 200+ times/month by finance"
      }
    },

    {
      "id": "REQ-DASH-005",
      "text": "Dashboard must show user activity heatmap (24h x 7d grid)",
      "type": "functional",
      "priority": "medium",
      "clarity_score": 0.86,
      "acceptance_criteria": [
        "Heatmap shows 24 hours x 7 days grid",
        "Color gradient: low (blue) to high (red) activity",
        "Click on cell shows detailed metrics for that time slot",
        "Tooltip shows exact user count on hover"
      ],
      "rag_citation": {
        "source_epic": "EP19",
        "source_req": "R-45",
        "similarity_score": 0.89,
        "reason": "User activity heatmap pattern from EP19",
        "production_validated": true,
        "production_notes": "EP19: Heatmap identified peak load times for auto-scaling"
      }
    }
  ],

  "summary": {
    "total_requirements": 5,
    "clarity_score": 0.89,
    "completeness_score": 0.91,
    "rag_enhanced": true
  },

  "rag_summary": {
    "queries_performed": 1,
    "total_results": 10,
    "results_used": 5,
    "total_citations": 5,
    "token_cost": 450,
    "query_time_ms": 120,
    "patterns_reused": [
      "Real-time WebSocket architecture (EP20)",
      "System health metrics display (EP18)",
      "Performance budgets (EP15)",
      "CSV export functionality (EP21)",
      "User activity heatmap (EP19)"
    ],
    "architecture_references": [
      "MADR-045: WebSocket for real-time dashboards (from EP20)"
    ],
    "implementation_references": [
      "src/infrastructure/websocket/ (from EP20)",
      "Caching strategy from EP15",
      "Chart library from EP18"
    ]
  },

  "open_questions": [
    "Should we include geographic distribution map like EP19? (pending stakeholder input)",
    "Alert thresholds: Use same as EP18 (error rate > 1%) or customize?"
  ],

  "notes": "Leveraged 5 proven patterns from EPs 15, 18, 19, 20, 21. All patterns are production-validated. WebSocket architecture (EP20) is particularly well-documented and can be reused with minimal modifications. Estimated time savings: 30% in design phase, 25% in implementation phase due to code reuse."
}
```

---

## Impact Analysis

### Time Savings

**Without RAG (Traditional Approach):**
```
Requirements Gathering:  4 hours (many clarifying questions)
Architect Design:        8 hours (design from scratch)
Implementation:          40 hours (all new code)
Testing:                 16 hours
Total:                   68 hours
```

**With RAG Citations (Day 22 Pattern):**
```
Requirements Gathering:  2.5 hours (guided by past patterns)
Architect Design:        5 hours (reference EP20 design)
Implementation:          30 hours (reuse EP20 WebSocket code)
Testing:                 12 hours (adapt EP20 tests)
Total:                   49.5 hours

Time Savings: 18.5 hours (27% reduction)
```

### Quality Improvements

**Metrics:**
```
Clarity Score:
- Without RAG: 0.75 average (more ambiguous)
- With RAG: 0.89 average (clearer due to concrete examples)

Architect Clarifications:
- Without RAG: 12 questions back to Analyst
- With RAG: 3 questions (most patterns clear from citations)

Design Rework Rate:
- Without RAG: 25% (unknowingly repeating past mistakes)
- With RAG: 8% (reusing validated patterns)

Implementation Bugs:
- Without RAG: 15 bugs found in testing
- With RAG: 6 bugs (reused proven code patterns)
```

---

## RAG Query Strategies

### Query 1: Keyword-Based Search

```javascript
db.requirements.find({
  keywords: { $in: ["dashboard", "analytics", "real-time"] },
  clarity_score: { $gte: 0.80 },
  status: "approved"
}).sort({ created_at: -1 }).limit(5)
```

**Use When:** Looking for general patterns in a domain
**Token Cost:** ~300-400 tokens for 5 results
**Accuracy:** 70-80% relevant results

---

### Query 2: Semantic Similarity Search (Vector Search)

```python
# Embedding-based search
query_embedding = get_embedding("real-time analytics dashboard")

similar_reqs = vector_index.similarity_search(
    query_embedding,
    k=10,
    filter={"clarity_score": {"$gte": 0.80}}
)
```

**Use When:** Need nuanced semantic matching
**Token Cost:** ~500-600 tokens for 10 results
**Accuracy:** 85-92% relevant results

---

### Query 3: Architecture Pattern Search

```javascript
db.requirements.find({
  architecture_decision: { $exists: true },
  tags: { $in: ["real-time", "websocket", "dashboard"] },
  production_validated: true
}).sort({ created_at: -1 }).limit(3)
```

**Use When:** Looking for specific architectural patterns
**Token Cost:** ~200-300 tokens for 3 results
**Accuracy:** 90%+ (very specific)

---

## Best Practices for RAG Citations

### 1. Always Validate RAG Results

```python
def validate_rag_results(results: list) -> list:
    """Filter RAG results for quality and relevance."""

    validated = []
    for result in results:
        # Check similarity threshold
        if result["similarity_score"] < 0.75:
            continue

        # Check production validation
        if not result.get("production_validated"):
            continue

        # Check clarity score
        if result.get("clarity_score", 0) < 0.80:
            continue

        validated.append(result)

    return validated
```

### 2. Include Source Attribution in All Cited Requirements

```json
{
  "requirement": {
    "id": "REQ-XXX",
    "text": "...",
    "rag_citation": {
      "source_epic": "EP20",
      "source_req": "R-89",
      "similarity_score": 0.92,
      "reason": "Clear explanation of why this is relevant",
      "production_validated": true,
      "adjustments": ["List any modifications from original"]
    }
  }
}
```

### 3. Track RAG Usage Metrics

```json
{
  "rag_summary": {
    "queries_performed": 1,
    "total_results": 10,
    "results_used": 5,
    "token_cost": 450,
    "query_time_ms": 120,
    "patterns_reused": [...]
  }
}
```

### 4. Don't Over-Rely on RAG

**Good Balance:**
- 60% original requirements (new ideas)
- 40% RAG-inspired requirements (proven patterns)

**Warning Signs:**
- 90%+ RAG-inspired: May be too conservative, missing innovation
- 10%- RAG-inspired: Not leveraging organizational knowledge

---

## Integration with MongoDB

### Schema for Requirement Storage

```javascript
{
  _id: ObjectId("..."),
  epic: "EP26",
  req_id: "REQ-DASH-001",
  title: "Real-Time System Metrics Dashboard",
  text: "Dashboard must display...",
  type: "functional",
  priority: "high",
  clarity_score: 0.89,

  // For RAG search
  keywords: ["dashboard", "analytics", "real-time", "metrics"],
  embedding: [0.123, -0.456, ...],  // 1536-dim vector for semantic search

  // Status tracking
  status: "approved",  // draft, approved, implemented, deprecated
  production_validated: false,  // Set to true after successful deployment

  // Citations (if this requirement was inspired by another)
  rag_citation: {
    source_epic: "EP18",
    source_req: "R-34",
    similarity_score: 0.92,
    reused_patterns: [...]
  },

  // Traceability
  acceptance_criteria: [...],
  linked_tests: [...],
  linked_architecture: ["MADR-045"],

  // Metadata
  created_at: ISODate("2025-11-15T14:30:00Z"),
  updated_at: ISODate("2025-11-15T14:30:00Z"),
  created_by: "analyst_agent",

  // Production feedback (added after deployment)
  production_notes: "Dashboard used for 3 months, well-received by users",
  production_metrics: {
    usage_count: 450,
    avg_load_time_ms: 1200,
    user_satisfaction: 4.5
  }
}
```

### Indexes for Fast Retrieval

```javascript
// Text search index
db.requirements.createIndex({
  text: "text",
  title: "text",
  keywords: "text"
})

// Filtering index
db.requirements.createIndex({
  epic: 1,
  status: 1,
  clarity_score: 1,
  created_at: -1
})

// Production-validated index
db.requirements.createIndex({
  production_validated: 1,
  clarity_score: 1
})

// Vector search index (if using MongoDB Atlas Vector Search)
db.requirements.createSearchIndex({
  name: "vector_index",
  type: "vectorSearch",
  definition: {
    fields: [{
      type: "vector",
      path: "embedding",
      numDimensions: 1536,
      similarity: "cosine"
    }]
  }
})
```

---

## Key Takeaways

1. **RAG Dramatically Improves Efficiency**
   - 27% time savings across entire epic lifecycle
   - 30%+ reduction in design phase
   - 25%+ reduction in implementation (code reuse)

2. **Citations Enable Traceability**
   - Every requirement links back to source epic
   - Architect can reference past designs
   - Developer can reuse proven code

3. **Production Validation is Critical**
   - Only cite production-validated patterns
   - Include production notes and metrics
   - Avoids repeating past failures

4. **Quality Improves with RAG**
   - Clarity: 0.75 → 0.89 (concrete examples)
   - Rework rate: 25% → 8% (proven patterns)
   - Bugs: 15 → 6 (reused tested code)

5. **Balance Innovation and Reuse**
   - 60% original + 40% RAG-inspired (healthy mix)
   - Don't over-rely on past patterns
   - Use RAG as guidance, not prescription

6. **Token Cost is Manageable**
   - ~450 tokens for 5 results (< 5% of budget)
   - Query time: ~120ms (negligible)
   - Massive ROI: 450 tokens → 18.5 hours saved

---

## Related Documentation

- See `docs/roles/analyst/day_capabilities.md#day-22` for technique details
- See `docs/roles/analyst/rag_queries.md` for query patterns
- See `docs/specs/epic_20/epic_20.md` for RAG architecture
- See `docs/specs/epic_20/queries.jsonl` for example queries
- See `docs/operational/shared_infra.md#mongodb` for database schema
