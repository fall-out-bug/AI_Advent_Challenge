# Developer RAG Queries

## Purpose
Surface implementation tasks, test evidence, and review states to guide
day-to-day delivery. Connects to MongoDB resources described in
`docs/operational/shared_infra.md`.

## Collections
- `tasks`: Implementation tasks linked to plan stages.
- `tests`: Test run metadata (type, command, coverage).
- `reviews`: Code review feedback and status.
- `worklogs`: Daily summaries with linked commits and artefacts.

## Baseline Queries

### Active Tasks for Current Stage
```javascript
db.tasks.find({
  epic: "EP21",
  stage: "Stage 2 – Modular Reviewer Integration",
  status: { $in: ["in_progress", "blocked"] }
});
```

### Test Coverage Snapshot
```javascript
db.tests.aggregate([
  { $match: { epic: "EP21", branch: "feature/ep21-reviewer" } },
  {
    $group: {
      _id: "$type",
      latest_run: { $max: "$executed_at" },
      coverage: { $avg: "$coverage" },
      status: { $last: "$status" }
    }
  }
]);
```

### Open Review Comments
```javascript
db.reviews.find({
  epic: "EP21",
  role: "reviewer",
  status: "open"
}).sort({ created_at: 1 });
```

### Worklog Sync
```javascript
db.worklogs.find({
  epic: "EP21",
  author: "developer",
  date: { $gte: ISODate("2025-11-01") }
}).sort({ date: -1 });
```

## Operational Notes
- Index recommendations: `{ epic: 1, stage: 1 }` on `tasks`,
  `{ epic: 1, branch: 1, executed_at: -1 }` on `tests`.
- Mirror critical review items into `docs/roles/developer/examples/` as case studies.
- Align updates with `docs/operational/handoff_contracts.md` outputs.

## Additional Resources
- Capabilities: `docs/roles/developer/day_capabilities.md`
- Tech Lead plan: `docs/roles/tech_lead/role_definition.md`
- Workflow context: `docs/specs/process/agent_workflow.md`

