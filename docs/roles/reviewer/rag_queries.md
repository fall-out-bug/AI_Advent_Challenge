# Reviewer RAG Queries

Comprehensive MongoDB queries for issue detection, common failure patterns, review history analysis, and quality metrics tracking.

---

## Query Categories

### 1. Past Review Queries (Find Similar Issues)
### 2. Common Failure Pattern Queries
### 3. Architecture Violation Queries
### 4. Test Coverage Analysis Queries
### 5. Production Issue Correlation Queries
### 6. Quality Metrics & Trends

---

## 1. Past Review Queries

### Find Similar Code Reviews (Vector Search)
```javascript
db.reviews.aggregate([
  {
    $vectorSearch: {
      index: "review_vector_index",
      path: "code_embedding",
      queryVector: [0.123, -0.456, ...],  // Current PR's embedding
      numCandidates: 100,
      limit: 10
    }
  },
  {
    $match: {
      "domain": "payment",  // Same domain
      "issues": { $exists: true, $ne: [] }  // Has issues
    }
  },
  {
    $project: {
      epic: 1,
      pr_number: 1,
      files_reviewed: 1,
      issues: 1,
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
    "pr_number": "PR-342",
    "files_reviewed": ["src/infrastructure/adapters/stripe_adapter.py"],
    "issues": [
      {
        "severity": "critical",
        "category": "error_handling",
        "description": "Missing timeout handling for Stripe API calls"
      }
    ],
    "similarity_score": 0.91
  }
]
```
**Token Cost:** ~700 tokens (10 results)
**Use Case:** Find known issues in similar code before manual review

---

### Reviews by File/Component
```javascript
db.reviews.find({
  "files_reviewed": { $regex: "payment.*\\.py" },
  "issues.severity": { $in: ["critical", "high"] },
  "reviewed_at": { $gte: new Date(Date.now() - 90*24*60*60*1000) }  // Last 90 days
}).sort({ reviewed_at: -1 }).limit(5);
```

**Example Result:**
```json
[
  {
    "review_id": "REV-234",
    "epic": "EP21",
    "files_reviewed": ["src/domain/entities/payment.py"],
    "issues": [
      {
        "severity": "high",
        "category": "validation",
        "line": 42,
        "description": "Missing validation for currency code (accepts invalid 'XXX')"
      }
    ]
  }
]
```
**Token Cost:** ~400 tokens
**Use Case:** Check history of issues in specific files

---

## 2. Common Failure Pattern Queries

### Top Issue Categories by Frequency
```javascript
db.reviews.aggregate([
  { $match: { reviewed_at: { $gte: new Date(Date.now() - 180*24*60*60*1000) } } },
  { $unwind: "$issues" },
  {
    $group: {
      _id: "$issues.category",
      count: { $sum: 1 },
      avg_severity_weight: {
        $avg: {
          $switch: {
            branches: [
              { case: { $eq: ["$issues.severity", "critical"] }, then: 4 },
              { case: { $eq: ["$issues.severity", "high"] }, then: 3 },
              { case: { $eq: ["$issues.severity", "medium"] }, then: 2 },
              { case: { $eq: ["$issues.severity", "low"] }, then: 1 }
            ],
            default: 0
          }
        }
      },
      examples: { $push: { issue: "$issues.description", epic: "$epic" } }
    }
  },
  { $sort: { count: -1 } },
  { $limit: 10 }
]);
```

**Example Result:**
```json
[
  {
    "_id": "error_handling",
    "count": 45,
    "avg_severity_weight": 3.2,
    "examples": [
      {"issue": "Missing timeout for API call", "epic": "EP19"},
      {"issue": "No retry logic for DB connection", "epic": "EP20"}
    ]
  },
  {
    "_id": "input_validation",
    "count": 38,
    "avg_severity_weight": 2.8,
    "examples": [...]
  },
  {
    "_id": "test_coverage",
    "count": 32,
    "avg_severity_weight": 2.1,
    "examples": [...]
  }
]
```
**Token Cost:** ~500 tokens
**Use Case:** Identify systemic issues across project

---

### Find Recurring Issues (Same Developer)
```javascript
db.reviews.aggregate([
  {
    $match: {
      "metadata.developer": "developer_1",
      "issues": { $exists: true, $ne: [] }
    }
  },
  { $unwind: "$issues" },
  {
    $group: {
      _id: {
        developer: "$metadata.developer",
        category: "$issues.category"
      },
      occurrences: { $sum: 1 },
      recent_examples: {
        $push: {
          epic: "$epic_id",
          description: "$issues.description",
          reviewed_at: "$reviewed_at"
        }
      }
    }
  },
  { $match: { occurrences: { $gte: 3 } } },  // 3+ occurrences
  { $sort: { occurrences: -1 } }
]);
```

**Example Result:**
```json
[
  {
    "_id": {"developer": "developer_1", "category": "test_coverage"},
    "occurrences": 5,
    "recent_examples": [
      {"epic": "EP23", "description": "Missing edge case tests", "reviewed_at": "2025-11-15T10:00:00Z"},
      {"epic": "EP22", "description": "Integration tests incomplete", "reviewed_at": "2025-11-10T14:00:00Z"}
    ]
  }
]
```
**Token Cost:** ~350 tokens
**Use Case:** Provide personalized coaching feedback

---

## 3. Architecture Violation Queries

### Clean Architecture Boundary Violations
```javascript
db.reviews.find({
  "issues.category": "architecture",
  "issues.description": { $regex: "domain.*import.*infrastructure|application.*import.*infrastructure" },
  "issues.severity": { $in: ["critical", "high"] }
}).sort({ reviewed_at: -1 }).limit(10);
```

**Example Result:**
```json
[
  {
    "review_id": "REV-189",
    "epic": "EP20",
    "files_reviewed": ["src/domain/entities/payment.py"],
    "issues": [
      {
        "severity": "critical",
        "category": "architecture",
        "file": "src/domain/entities/payment.py",
        "line": 5,
        "description": "Domain layer imports from Infrastructure (MongoClient)",
        "suggestion": "Move DB logic to repository in infrastructure layer"
      }
    ]
  }
]
```
**Token Cost:** ~300 tokens
**Use Case:** Enforce Clean Architecture principles

---

### Circular Dependency Detection
```javascript
db.architecture_violations.find({
  type: "circular_dependency",
  detected_at: { $gte: new Date(Date.now() - 30*24*60*60*1000) },
  resolved: false
});
```

**Example Result:**
```json
[
  {
    "violation_id": "VIOL-42",
    "type": "circular_dependency",
    "cycle": [
      "src/application/use_cases/process_payment.py",
      "src/application/use_cases/validate_payment.py",
      "src/application/use_cases/process_payment.py"
    ],
    "detected_at": "2025-11-14T08:00:00Z",
    "resolved": false
  }
]
```
**Token Cost:** ~200 tokens
**Use Case:** Identify structural problems early

---

## 4. Test Coverage Analysis Queries

### Files with Low Test Coverage
```javascript
db.code_artifacts.aggregate([
  {
    $match: {
      epic: "EP23",
      test_coverage: { $lt: 0.80 },
      production_candidate: true
    }
  },
  {
    $lookup: {
      from: "tests",
      localField: "file_path",
      foreignField: "tested_file",
      as: "test_info"
    }
  },
  {
    $project: {
      file_path: 1,
      test_coverage: 1,
      lines_of_code: 1,
      complexity_score: 1,
      missing_tests: {
        $filter: {
          input: "$test_info",
          as: "test",
          cond: { $eq: ["$$test.status", "missing"] }
        }
      }
    }
  },
  { $sort: { test_coverage: 1 } }
]);
```

**Example Result:**
```json
[
  {
    "file_path": "src/application/use_cases/refund_payment.py",
    "test_coverage": 0.45,
    "lines_of_code": 68,
    "complexity_score": 7,
    "missing_tests": [
      "test_refund_with_negative_amount",
      "test_refund_after_deadline",
      "test_partial_refund_edge_case"
    ]
  }
]
```
**Token Cost:** ~400 tokens
**Use Case:** Prioritize test-writing efforts

---

### Critical Path Test Coverage
```javascript
db.code_artifacts.find({
  epic: "EP23",
  critical_path: true,  // Payment processing is critical
  test_coverage: { $lt: 0.90 }  // Higher threshold for critical code
}).sort({ test_coverage: 1 });
```

**Example Result:**
```json
[
  {
    "file_path": "src/application/use_cases/process_payment.py",
    "test_coverage": 0.85,
    "critical_path": true,
    "production_bugs": 0,
    "recommendation": "Increase coverage to 90%+ for critical payment logic"
  }
]
```
**Token Cost:** ~250 tokens
**Use Case:** Ensure critical paths are well-tested

---

## 5. Production Issue Correlation Queries

### Link Past Production Bugs to Code Reviews
```javascript
db.production_issues.aggregate([
  {
    $match: {
      severity: { $in: ["critical", "high"] },
      resolved: true,
      created_at: { $gte: new Date(Date.now() - 180*24*60*60*1000) }
    }
  },
  {
    $lookup: {
      from: "reviews",
      let: { bug_file: "$file_path", bug_epic: "$epic" },
      pipeline: [
        {
          $match: {
            $expr: {
              $and: [
                { $eq: ["$epic_id", "$$bug_epic"] },
                { $in: ["$$bug_file", "$files_reviewed"] }
              ]
            }
          }
        }
      ],
      as: "related_reviews"
    }
  },
  {
    $project: {
      bug_id: 1,
      description: 1,
      file_path: 1,
      root_cause: 1,
      review_missed: { $size: "$related_reviews" },
      review_details: "$related_reviews"
    }
  }
]);
```

**Example Result:**
```json
[
  {
    "bug_id": "BUG-234",
    "description": "Payment timeout not handled, caused failed transactions",
    "file_path": "src/infrastructure/adapters/stripe_adapter.py",
    "root_cause": "Missing timeout parameter in API call",
    "review_missed": 1,
    "review_details": [
      {
        "review_id": "REV-189",
        "status": "approved",
        "issues_found": 2,
        "missed_issue": "Timeout handling was not flagged"
      }
    ]
  }
]
```
**Token Cost:** ~600 tokens
**Use Case:** Improve review process, learn from missed issues

---

### Escape Rate Analysis (Bugs Despite Review)
```javascript
db.production_issues.aggregate([
  {
    $lookup: {
      from: "reviews",
      localField: "epic",
      foreignField: "epic_id",
      as: "review"
    }
  },
  {
    $match: {
      "review": { $ne: [] },  // Bug in reviewed code
      severity: { $in: ["critical", "high"] }
    }
  },
  {
    $group: {
      _id: "$epic",
      escape_count: { $sum: 1 },
      total_reviews: { $first: { $size: "$review" } }
    }
  },
  {
    $project: {
      epic: "$_id",
      escape_count: 1,
      escape_rate: { $divide: ["$escape_count", "$total_reviews"] }
    }
  },
  { $sort: { escape_rate: -1 } }
]);
```

**Example Result:**
```json
[
  {
    "epic": "EP19",
    "escape_count": 3,
    "escape_rate": 0.15  // 15% of reviews missed critical bugs
  },
  {
    "epic": "EP23",
    "escape_count": 0,
    "escape_rate": 0.0   // Perfect record
  }
]
```
**Token Cost:** ~300 tokens
**Use Case:** Measure review effectiveness

---

## 6. Quality Metrics & Trends

### Review Metrics Dashboard
```javascript
db.reviews.aggregate([
  {
    $match: {
      reviewed_at: { $gte: new Date(Date.now() - 30*24*60*60*1000) }
    }
  },
  {
    $group: {
      _id: null,
      total_reviews: { $sum: 1 },
      avg_duration_minutes: { $avg: "$metrics.review_duration_minutes" },
      avg_issues_found: { $avg: { $size: "$issues" } },
      critical_issues: {
        $sum: {
          $size: {
            $filter: {
              input: "$issues",
              as: "issue",
              cond: { $eq: ["$$issue.severity", "critical"] }
            }
          }
        }
      },
      approval_rate: {
        $avg: {
          $cond: [
            { $eq: ["$status", "approved"] },
            1,
            0
          ]
        }
      }
    }
  }
]);
```

**Example Result:**
```json
{
  "total_reviews": 42,
  "avg_duration_minutes": 145,
  "avg_issues_found": 4.2,
  "critical_issues": 8,
  "approval_rate": 0.76  // 76% approved on first review
}
```
**Token Cost:** ~200 tokens
**Use Case:** Monthly review performance report

---

### Quality Trends Over Time
```javascript
db.reviews.aggregate([
  {
    $match: {
      reviewed_at: { $gte: new Date(Date.now() - 180*24*60*60*1000) }
    }
  },
  {
    $group: {
      _id: {
        year: { $year: "$reviewed_at" },
        month: { $month: "$reviewed_at" }
      },
      avg_test_coverage: { $avg: "$metrics.test_coverage_actual" },
      avg_complexity: { $avg: "$metrics.code_complexity" },
      architecture_violations: {
        $sum: {
          $size: {
            $filter: {
              input: "$issues",
              as: "issue",
              cond: { $eq: ["$$issue.category", "architecture"] }
            }
          }
        }
      }
    }
  },
  { $sort: { "_id.year": 1, "_id.month": 1 } }
]);
```

**Example Result:**
```json
[
  {
    "_id": {"year": 2025, "month": 9},
    "avg_test_coverage": 78.5,
    "avg_complexity": 6.2,
    "architecture_violations": 12
  },
  {
    "_id": {"year": 2025, "month": 10},
    "avg_test_coverage": 85.3,
    "avg_complexity": 4.8,
    "architecture_violations": 5
  },
  {
    "_id": {"year": 2025, "month": 11},
    "avg_test_coverage": 91.2,
    "avg_complexity": 3.9,
    "architecture_violations": 2
  }
]
```
**Token Cost:** ~350 tokens
**Use Case:** Track quality improvements over time

---

## Token Cost Summary

| Query Type | Avg Tokens | Use Frequency |
|------------|------------|---------------|
| Similar Code Reviews (vector) | 700 | Before each review |
| Common Failure Patterns | 500 | Weekly |
| Architecture Violations | 300 | After each review |
| Test Coverage Analysis | 400 | Daily |
| Production Issue Correlation | 600 | Monthly |
| Quality Metrics Dashboard | 200 | Weekly |

**Total Monthly Token Budget:** ~45,000 tokens (assuming 30 reviews/month)

---

## Best Practices

### Query Optimization
1. **Filter Early:** Always filter by `epic`, `reviewed_at` range, or `severity`
2. **Limit Results:** Use `.limit(5-10)` to control token cost
3. **Index Usage:** Ensure indexes on `{ epic: 1, reviewed_at: -1 }`, `{ issues.category: 1 }`
4. **Cache Results:** Cache common queries (failure patterns, metrics) for 24 hours

### Review Workflow Integration
```python
class ReviewerAgent:
    def review_pr(self, pr: PullRequest) -> ReviewReport:
        # 1. Pre-review: Query similar past reviews
        similar_reviews = self.query_similar_reviews(pr.code_embedding)

        # 2. Architecture pass: Check for known violations
        arch_violations = self.query_architecture_violations(pr.epic)

        # 3. Component pass: Check test coverage
        coverage_gaps = self.query_coverage_gaps(pr.files)

        # 4. Synthesis: Correlate with production issues
        related_bugs = self.query_production_issues(pr.files, pr.epic)

        # 5. Generate report with citations
        return self.generate_report(
            similar_reviews=similar_reviews,
            violations=arch_violations,
            coverage_gaps=coverage_gaps,
            related_bugs=related_bugs
        )
```

### Performance Monitoring
```python
from prometheus_client import Histogram

review_query_duration = Histogram(
    'review_query_duration_seconds',
    'Review query execution time',
    ['query_type']
)

@review_query_duration.labels(query_type='similar_reviews').time()
def query_similar_reviews(embedding: list[float]) -> list[Review]:
    """Query with performance tracking."""
    return db.reviews.aggregate([...])
```

---

## Linked Resources
- Role Definition: `docs/roles/reviewer/role_definition.md`
- Day Capabilities: `docs/roles/reviewer/day_capabilities.md`
- Examples: `docs/roles/reviewer/examples/`
- Shared Infrastructure: `docs/operational/shared_infra.md`
