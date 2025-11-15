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

## Additional Resources
- Capabilities: `docs/roles/architect/day_capabilities.md`
- Handoff schema: `docs/operational/handoff_contracts.md`
- Workflow context: `docs/specs/process/agent_workflow.md`

