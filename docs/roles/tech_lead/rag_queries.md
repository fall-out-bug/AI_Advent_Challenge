# Tech Lead RAG Queries

## Purpose
Retrieve planning artefacts, risk registers, and CI gate metadata to maintain
staged delivery plans. Uses MongoDB endpoints referenced in
`docs/operational/shared_infra.md`.

## Collections
- `plans`: Staged implementation plans with tasks and evidence.
- `risks`: Risk registers covering likelihood/impact/mitigation.
- `pipelines`: CI job catalog with command references and coverage targets.

## Baseline Queries

### Current Plan Stages
```javascript
db.plans.aggregate([
  { $match: { epic: "EP21" } },
  { $unwind: "$stages" },
  { $sort: { "stages.order": 1 } },
  {
    $project: {
      _id: 0,
      stage: "$stages.name",
      owner: "$stages.owner",
      dod: "$stages.definition_of_done",
      evidence: "$stages.evidence"
    }
  }
]);
```

### Open Risks
```javascript
db.risks.find({
  epic: "EP21",
  status: { $in: ["open", "mitigating"] }
}).sort({ severity: -1 });
```

### Pipeline Coverage Gaps
```javascript
db.pipelines.aggregate([
  { $match: { epic: "EP21" } },
  {
    $project: {
      name: 1,
      coverage_target: 1,
      current_coverage: "$metrics.coverage",
      gap: { $subtract: ["$coverage_target", "$metrics.coverage"] }
    }
  },
  { $match: { gap: { $gt: 0 } } }
]);
```

### Handoff Checklist Validation
```javascript
db.plans.aggregate([
  { $match: { epic: "EP21" } },
  { $unwind: "$handoff.checklist" },
  {
    $match: {
      "handoff.checklist.status": { $ne: "complete" }
    }
  },
  {
    $project: {
      item: "$handoff.checklist.item",
      owner: "$handoff.checklist.owner",
      due: "$handoff.checklist.due"
    }
  }
]);
```

## Operational Notes
- Create compound indexes `{ epic: 1, "stages.order": 1 }` for responsive lookups.
- Export sanitized plan stages to `docs/roles/tech_lead/examples/`.
- Align findings with `docs/operational/handoff_contracts.md` before handoff.

## Additional Resources
- Capabilities: `docs/roles/tech_lead/day_capabilities.md`
- Developer handoff expectations: `docs/roles/developer/role_definition.md`
- Workflow context: `docs/specs/process/agent_workflow.md`
