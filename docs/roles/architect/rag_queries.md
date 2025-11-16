# Architect RAG Queries

## Purpose
Retrieve architecture assets, decisions, and dependency insights supporting
Clean Architecture enforcement. Uses MongoDB collections configured in
`docs/operational/shared_infra.md`.

## Collections
- `architecture`: Vision documents with component/boundary metadata.
- `decisions`: MADRs and decision logs.
- `dependencies`: Static analysis snapshots (imports, services, adapters).

## Baseline Queries

### Current Architecture Vision
```javascript
db.architecture.find({
  epic: "EP21",
  status: { $in: ["draft", "approved"] }
}).sort({ updated_at: -1 });
```

### Pending MADRs
```javascript
db.decisions.find({
  epic: "EP21",
  status: "pending_review"
});
```

### Inward Dependency Violations
```javascript
db.dependencies.aggregate([
  { $match: { epic: "EP21" } },
  { $unwind: "$violations" },
  {
    $match: {
      "violations.type": "inward_dependency",
      "violations.layer_from": { $in: ["infrastructure", "presentation"] },
      "violations.layer_to": "domain"
    }
  },
  {
    $project: {
      module: 1,
      "violations.layer_from": 1,
      "violations.layer_to": 1,
      "violations.symbol": 1
    }
  }
]);
```

### Cross-Cutting Concern Coverage
```javascript
db.architecture.aggregate([
  { $match: { epic: "EP21" } },
  { $unwind: "$cross_cutting" },
  {
    $group: {
      _id: "$cross_cutting.type",
      owners: { $addToSet: "$cross_cutting.owner" },
      components: { $addToSet: "$component" }
    }
  }
]);
```

## Operational Notes
- Ensure indexes on `{ epic: 1, status: 1 }` for `architecture` and `decisions`.
- When exporting diagrams, store references under `docs/roles/architect/examples/`.
- Align query outputs with Tech Lead plans for quick feasibility checks.

---

## Query Examples with Results & Token Costs

### Example 1: Current Architecture Vision

**Query:**
```javascript
db.architecture.find({
  epic: "EP21",
  status: { $in: ["draft", "approved"] }
}).sort({ updated_at: -1 });
```

**Example Results:**
```json
[
  {
    "_id": "674ce1a3b9d2c3456789012a",
    "epic": "EP21",
    "title": "Modular Reviewer Architecture",
    "status": "approved",
    "components": ["ReviewOrchestrator", "ArchitecturePass", "ComponentPass"],
    "patterns": ["clean_architecture", "adapter_pattern"],
    "updated_at": "2025-11-10T16:00:00Z"
  }
]
```

**Token Cost:** ~400 tokens
**When to Use:** Load current architecture for review/extension
**When NOT to Use:** Historical analysis (use version queries instead)

---

### Example 2: Pending MADRs

**Query:**
```javascript
db.decisions.find({
  epic: "EP21",
  status: "pending_review"
});
```

**Example Results:**
```json
[
  {
    "_id": "674ce1a3b9d2c3456789012b",
    "epic": "EP21",
    "madr_id": "MADR-089",
    "title": "Use MongoDB for review session state",
    "status": "pending_review",
    "alternatives": ["PostgreSQL", "Redis"],
    "created_at": "2025-11-09T10:00:00Z"
  }
]
```

**Token Cost:** ~300 tokens
**When to Use:** Check for unresolved decisions before finalizing architecture
**When NOT to Use:** After all MADRs approved (use approved status filter)

---

### Example 3: Inward Dependency Violations (Day 10 Validation)

**Query:**
```javascript
db.dependencies.aggregate([
  { $match: { epic: "EP21" } },
  { $unwind: "$violations" },
  {
    $match: {
      "violations.type": "inward_dependency",
      "violations.layer_to": "domain"
    }
  }
]);
```

**Example Results:**
```json
[
  {
    "module": "src/infrastructure/mongodb_repository.py",
    "violations": {
      "type": "inward_dependency",
      "layer_from": "infrastructure",
      "layer_to": "domain",
      "symbol": "Payment",
      "line": 42
    }
  }
]
```

**Token Cost:** ~500 tokens
**When to Use:** Validate Clean Architecture compliance (Day 10 pattern)
**When NOT to Use:** During initial design (run after implementation)

---

### Example 4: Cross-Cutting Concern Coverage

**Query:**
```javascript
db.architecture.aggregate([
  { $match: { epic: "EP21" } },
  { $unwind: "$cross_cutting" },
  {
    $group: {
      _id: "$cross_cutting.type",
      components: { $addToSet: "$component" }
    }
  }
]);
```

**Example Results:**
```json
[
  {
    "_id": "logging",
    "components": ["ReviewOrchestrator", "ArchitecturePass", "ComponentPass"]
  },
  {
    "_id": "metrics",
    "components": ["ReviewOrchestrator"]
  }
]
```

**Interpretation:** "metrics" only in 1/3 components → needs coverage expansion

**Token Cost:** ~600 tokens
**When to Use:** Validate cross-cutting concerns addressed (Day 11+)
**When NOT to Use:** Initial component listing (premature)

---

### Example 5: Similar Architectures (RAG Day 20)

**Query:**
```javascript
db.architecture.find({
  patterns: { $in: ["adapter_pattern", "strategy_pattern"] },
  domain: "payments",
  status: "approved"
}).limit(3)
```

**Example Results:**
```json
[
  {
    "epic": "EP19",
    "title": "Payment Gateway Multi-Provider Architecture",
    "patterns": ["adapter_pattern", "strategy_pattern"],
    "components": ["ProviderAdapter", "StripeAdapter", "PayPalAdapter"],
    "madrs": ["MADR-045"],
    "production_validated": true
  },
  {
    "epic": "EP15",
    "title": "Payment API Architecture",
    "patterns": ["clean_architecture"],
    "madrs": ["MADR-023"],
    "production_validated": true
  }
]
```

**Token Cost:** ~700 tokens (includes patterns + MADRs)
**When to Use:** Find proven patterns for reuse (Day 20 RAG)
**When NOT to Use:** Exact match needed (use epic-specific query)

---

## Token Cost Summary

| Query Type | Avg Results | Token Cost | Query Time | Use Case |
|------------|-------------|------------|------------|----------|
| Architecture Lookup | 3 | 400 | 60ms | Load current vision |
| Pending MADRs | 5 | 300 | 50ms | Check unresolved decisions |
| Dependency Violations | 10 | 500 | 150ms | Validate Clean Arch |
| Cross-Cutting Coverage | 4 | 600 | 120ms | Coverage analysis |
| Similar Architectures | 3 | 700 | 180ms | Pattern reuse (RAG) |

**Total Budget Impact:**
- Single query: 300-700 tokens (2-6% of 12K window)
- Full architecture session: ~2,000 tokens (17% of window)
- ROI: 2,000 tokens investment → 30% design time savings

---

## Best Practices

### 1. Filter by Status
```javascript
// ✅ Good: Filter approved architectures only
db.architecture.find({ status: "approved", production_validated: true })

// ❌ Bad: Include draft/deprecated
db.architecture.find({})  // Returns noise
```

### 2. Limit Results
```javascript
// ✅ Always limit
db.architecture.find({}).limit(5)

// ❌ Never unlimited
db.architecture.find({})  // Could return 100+ docs
```

### 3. Use Indexes
```javascript
// Create covering indexes
db.architecture.createIndex({ epic: 1, status: 1, updated_at: -1 })
db.decisions.createIndex({ epic: 1, status: 1 })
db.dependencies.createIndex({ epic: 1, "violations.type": 1 })
```

---

## Additional Resources
- Capabilities: `docs/roles/architect/day_capabilities.md`
- Day 20 RAG Pattern: `docs/roles/architect/examples/day_20_rag_reuse.md` (future)
- Handoff schema: `docs/operational/handoff_contracts.md`
- Workflow context: `docs/specs/process/agent_workflow.md`
