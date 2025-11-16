# Developer RAG Queries

Comprehensive MongoDB queries for code artifacts, test results, implementation tasks, and review feedback.

---

## Query Categories

### 1. Code Artifact Queries
### 2. Test & Coverage Queries
### 3. Implementation Task Queries
### 4. Review Feedback Queries
### 5. RAG Code Reuse Queries

---

## 1. Code Artifact Queries

### Find Similar Implementation Patterns
```javascript
db.code_artifacts.aggregate([
  {
    $vectorSearch: {
      index: "code_vector_index",
      path: "embedding",
      queryVector: [0.123, -0.456, ...],  // 1536-dim embedding from "payment adapter"
      numCandidates: 50,
      limit: 5
    }
  },
  {
    $match: {
      language: "python",
      test_coverage: { $gte: 0.80 },
      production_status: "stable",
      bugs_reported: { $eq: 0 }
    }
  },
  {
    $project: {
      epic: 1,
      file_path: 1,
      function_name: 1,
      description: 1,
      test_coverage: 1,
      lines_of_code: 1,
      complexity_score: 1,
      similarity_score: { $meta: "vectorSearchScore" }
    }
  }
]);
```

**Example Result:**
```json
[
  {
    "epic": "EP19",
    "file_path": "src/infrastructure/adapters/stripe_adapter.py",
    "function_name": "StripeAdapter.process_payment",
    "description": "Stripe payment processing with retry logic",
    "test_coverage": 0.95,
    "lines_of_code": 42,
    "complexity_score": 4,
    "similarity_score": 0.89
  },
  {
    "epic": "EP15",
    "file_path": "src/infrastructure/adapters/paypal_adapter.py",
    "function_name": "PayPalAdapter.process_payment",
    "description": "PayPal payment adapter with fallback",
    "test_coverage": 0.88,
    "lines_of_code": 38,
    "complexity_score": 3,
    "similarity_score": 0.82
  }
]
```
**Token Cost:** ~600 tokens (5 results with metadata)
**Use Case:** Find proven implementation patterns before writing new code

---

### Query Code by Quality Metrics
```javascript
db.code_artifacts.find({
  epic: { $gte: "EP15" },  // Recent epics
  language: "python",
  test_coverage: { $gte: 0.90 },
  complexity_score: { $lte: 5 },  // Low complexity
  production_bugs: { $eq: 0 },
  production_deployed: true
}).sort({ test_coverage: -1, complexity_score: 1 }).limit(10);
```

**Example Result:**
```json
[
  {
    "epic": "EP19",
    "file_path": "src/domain/entities/payment.py",
    "class_name": "Payment",
    "test_coverage": 1.0,
    "complexity_score": 2,
    "production_bugs": 0,
    "reuse_count": 8  // Used in 8 other epics
  }
]
```
**Token Cost:** ~400 tokens (10 results)
**Use Case:** Identify high-quality code to reuse

---

## 2. Test & Coverage Queries

### Current Test Coverage by Type
```javascript
db.tests.aggregate([
  { $match: { epic: "EP23", branch: "feature/ep23-payment" } },
  {
    $group: {
      _id: "$test_type",
      latest_run: { $max: "$executed_at" },
      avg_coverage: { $avg: "$coverage_percent" },
      total_tests: { $sum: "$test_count" },
      failed_tests: { $sum: "$failed_count" },
      status: { $last: "$status" }
    }
  },
  { $sort: { _id: 1 } }
]);
```

**Example Result:**
```json
[
  {
    "_id": "unit",
    "latest_run": "2025-11-15T10:30:00Z",
    "avg_coverage": 92.5,
    "total_tests": 145,
    "failed_tests": 0,
    "status": "passed"
  },
  {
    "_id": "integration",
    "latest_run": "2025-11-15T10:35:00Z",
    "avg_coverage": 78.3,
    "total_tests": 42,
    "failed_tests": 1,
    "status": "failed"
  },
  {
    "_id": "e2e",
    "latest_run": "2025-11-15T10:40:00Z",
    "avg_coverage": 65.0,
    "total_tests": 12,
    "failed_tests": 0,
    "status": "passed"
  }
]
```
**Token Cost:** ~300 tokens
**Use Case:** Daily test health check

---

### Find Untested Code
```javascript
db.code_artifacts.find({
  epic: "EP23",
  test_coverage: { $lt: 0.80 },
  production_candidate: true
}).sort({ test_coverage: 1 });
```

**Example Result:**
```json
[
  {
    "file_path": "src/application/use_cases/refund_payment.py",
    "function_name": "RefundPaymentUseCase.execute",
    "test_coverage": 0.45,
    "lines_of_code": 28,
    "reason": "Edge cases not tested"
  }
]
```
**Token Cost:** ~200 tokens
**Action:** Write tests before deploying

---

### Test Failures & Regressions
```javascript
db.tests.find({
  epic: "EP23",
  status: "failed",
  executed_at: { $gte: new Date(Date.now() - 24*60*60*1000) }  // Last 24h
}).sort({ executed_at: -1 });
```

**Example Result:**
```json
[
  {
    "test_type": "integration",
    "test_name": "test_payment_with_invalid_provider",
    "status": "failed",
    "error_message": "AssertionError: Expected ProviderError, got None",
    "file": "tests/integration/test_payment_flow.py:45",
    "executed_at": "2025-11-15T09:15:00Z",
    "duration_ms": 1200
  }
]
```
**Token Cost:** ~250 tokens per failure
**Action:** Fix immediately

---

## 3. Implementation Task Queries

### Active Tasks for Current Developer
```javascript
db.tasks.find({
  epic: "EP23",
  assignee: "developer_1",
  status: { $in: ["in_progress", "blocked"] }
}).sort({ priority: -1, created_at: 1 });
```

**Example Result:**
```json
[
  {
    "task_id": "TASK-42",
    "title": "Implement payment refund logic",
    "status": "in_progress",
    "priority": "high",
    "stage": "Stage 3 – Refund Module",
    "dod": [
      "RefundPaymentUseCase implemented",
      "Unit tests: 100% coverage",
      "Integration test with Stripe sandbox"
    ],
    "blockers": []
  },
  {
    "task_id": "TASK-47",
    "title": "Add monitoring metrics for payment errors",
    "status": "blocked",
    "priority": "medium",
    "blockers": ["Prometheus not configured in staging"]
  }
]
```
**Token Cost:** ~400 tokens (5 tasks)
**Use Case:** Morning standup, task planning

---

### Tasks by Stage (Dependency Check)
```javascript
db.tasks.aggregate([
  { $match: { epic: "EP23" } },
  {
    $group: {
      _id: "$stage",
      total_tasks: { $sum: 1 },
      completed: { $sum: { $cond: [{ $eq: ["$status", "completed"] }, 1, 0] } },
      in_progress: { $sum: { $cond: [{ $eq: ["$status", "in_progress"] }, 1, 0] } },
      blocked: { $sum: { $cond: [{ $eq: ["$status", "blocked"] }, 1, 0] } }
    }
  },
  { $sort: { _id: 1 } }
]);
```

**Token Cost:** ~300 tokens
**Use Case:** Track stage progress

---

## 4. Review Feedback Queries

### Open Review Comments
```javascript
db.reviews.find({
  epic: "EP23",
  reviewer_role: "reviewer",
  status: "open",
  severity: { $in: ["critical", "high"] }
}).sort({ severity: -1, created_at: 1 });
```

**Example Result:**
```json
[
  {
    "review_id": "REV-89",
    "file_path": "src/infrastructure/adapters/stripe_adapter.py",
    "line_number": 45,
    "severity": "critical",
    "comment": "Missing error handling for network timeout",
    "status": "open",
    "created_at": "2025-11-14T16:20:00Z"
  }
]
```
**Token Cost:** ~300 tokens (5 comments)
**Action:** Address before merging

---

### Review Statistics
```javascript
db.reviews.aggregate([
  { $match: { epic: "EP23", reviewer_role: "reviewer" } },
  {
    $group: {
      _id: "$status",
      count: { $sum: 1 },
      avg_resolution_hours: {
        $avg: {
          $divide: [
            { $subtract: ["$resolved_at", "$created_at"] },
            1000 * 60 * 60
          ]
        }
      }
    }
  }
]);
```

**Example Result:**
```json
[
  { "_id": "open", "count": 3, "avg_resolution_hours": null },
  { "_id": "resolved", "count": 12, "avg_resolution_hours": 4.5 },
  { "_id": "wont_fix", "count": 1, "avg_resolution_hours": 0.5 }
]
```
**Token Cost:** ~200 tokens
**Use Case:** Review health metrics

---

## 5. RAG Code Reuse Queries

### Find Implementation by Domain Pattern
```javascript
db.code_artifacts.find({
  domain_pattern: "adapter",  // Strategy, Factory, Repository, etc.
  test_coverage: { $gte: 0.85 },
  production_bugs: { $eq: 0 }
}).sort({ reuse_count: -1 }).limit(5);
```

**Example Result:**
```json
[
  {
    "epic": "EP19",
    "file_path": "src/infrastructure/adapters/payment_adapter.py",
    "class_name": "PaymentAdapter",
    "domain_pattern": "adapter",
    "test_coverage": 0.98,
    "reuse_count": 12,
    "description": "Base adapter for payment providers"
  }
]
```
**Token Cost:** ~350 tokens
**Use Case:** Find proven design patterns

---

### Code Citation for Reuse
```javascript
db.code_artifacts.findOne({
  epic: "EP19",
  file_path: "src/infrastructure/adapters/stripe_adapter.py",
  function_name: "StripeAdapter.process_payment"
});
```

**Example Result:**
```json
{
  "epic": "EP19",
  "file_path": "src/infrastructure/adapters/stripe_adapter.py",
  "function_name": "StripeAdapter.process_payment",
  "source_code": "async def process_payment(self, payment: Payment) -> TransactionResult:\n    ...",
  "test_coverage": 0.95,
  "production_status": "stable",
  "deployment_count": 24,
  "last_bug": null,
  "citation": "Adapted from EP19 Stripe integration (0 bugs in 24 deployments)"
}
```
**Token Cost:** ~500 tokens (includes source code)
**Use Case:** Cite when adapting code

---

## Query Performance & Best Practices

### Token Cost Summary
| Query Type | Avg Tokens | Use Frequency |
|------------|------------|---------------|
| Code Artifacts (5 results) | 600 | Daily |
| Test Coverage | 300 | After each CI run |
| Active Tasks | 400 | Morning standup |
| Review Comments | 300 | Before merge |
| Code Reuse (with source) | 500 | When starting new feature |

### Best Practices
1. **Filter First:** Always filter by `epic` and relevant status
2. **Limit Results:** Use `.limit(5-10)` to control token cost
3. **Index Usage:** Ensure indexes on `{ epic: 1, status: 1 }`
4. **Cache Results:** Cache test results for 1 hour (reduce DB load)
5. **Batch Queries:** Combine related queries in aggregation pipelines

### Performance Monitoring
```python
from pymongo import MongoClient
from datetime import datetime

class RAGQueryMonitor:
    """Monitor RAG query performance."""

    def __init__(self, mongo_uri: str):
        self.client = MongoClient(mongo_uri)
        self.db = self.client.developer_rag

    def log_query(self, query_type: str, tokens: int, duration_ms: int):
        """Log query execution metrics."""
        self.db.query_logs.insert_one({
            "query_type": query_type,
            "tokens": tokens,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow()
        })
```

---

## Linked Resources
- Day Capabilities: `docs/roles/developer/day_capabilities.md`
- Examples: `docs/roles/developer/examples/`
- Shared Infrastructure: `docs/operational/shared_infra.md`
