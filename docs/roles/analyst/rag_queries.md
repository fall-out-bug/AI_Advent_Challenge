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

## Additional Resources
- Capabilities: `docs/roles/analyst/day_capabilities.md`
- Handoff schema: `docs/operational/handoff_contracts.md`
- Workflow context: `docs/specs/process/agent_workflow.md`

