# Reviewer RAG Queries

## Purpose
Aggregate review findings, evidence, and regression history to inform approval
decisions. Utilizes MongoDB endpoints defined in
`docs/operational/shared_infra.md`.

## Collections
- `reviews`: Review records with findings, status, evidence links.
- `evidence`: Test runs, logs, metrics attached to review items.
- `incidents`: Post-release incidents correlated with epics/days.

## Baseline Queries

### Open Findings
```javascript
db.reviews.find({
  epic: "EP21",
  status: { $in: ["open", "blocked"] }
}).sort({ created_at: 1 });
```

### Evidence Lookup
```javascript
db.evidence.aggregate([
  { $match: { epic: "EP21", type: { $in: ["test", "log", "metric"] } } },
  {
    $group: {
      _id: "$run_id",
      artefacts: { $push: { type: "$type", path: "$path", status: "$status" } },
      last_seen: { $max: "$created_at" }
    }
  }
]);
```

### Regression History
```javascript
db.incidents.find({
  epic: { $in: ["EP19", "EP20", "EP21"] },
  component: "reviewer"
}).sort({ detected_at: -1 });
```

### Approval Ledger
```javascript
db.reviews.aggregate([
  { $match: { epic: "EP21", status: "approved" } },
  {
    $project: {
      reviewer: 1,
      approved_at: 1,
      evidence_ids: 1,
      summary: 1
    }
  }
]);
```

## Operational Notes
- Index `reviews` on `{ epic: 1, status: 1 }` for quick dashboards.
- Sync approved findings into `docs/roles/reviewer/examples/`.
- Coordinate with Tech Lead if approval ledger shows gating blockers.

## Additional Resources
- Capabilities: `docs/roles/reviewer/day_capabilities.md`
- Handoff schema: `docs/operational/handoff_contracts.md`
- Workflow context: `docs/specs/process/agent_workflow.md`
