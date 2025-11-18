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
<<<<<<< HEAD
=======

---

## Query Examples with Results & Token Costs

### Example 1: Test Coverage by Stage
```javascript
db.plans.aggregate([
  { $match: { epic: "EP23" } },
  { $unwind: "$stages" },
  { $project: {
      stage: "$stages.name",
      test_coverage: "$stages.ci_gates.coverage",
      tests_passing: "$stages.ci_gates.tests_status"
  }}
]);
```
**Results:** `[{stage: "Domain Layer", test_coverage: 100%, tests_passing: "green"}]`
**Token Cost:** ~350 tokens | **Use:** Track test progress per stage

---

### Example 2: Deployment History
```javascript
db.deployments.find({
  epic: "EP23",
  environment: "production"
}).sort({ deployed_at: -1 }).limit(5);
```
**Results:** Last 5 production deployments with: version, strategy (canary/blue-green), success_rate
**Token Cost:** ~400 tokens | **Use:** Reference successful deployment patterns

---

### Example 3: Blocked Stages
```javascript
db.plans.aggregate([
  { $match: { epic: "EP23" } },
  { $unwind: "$stages" },
  { $match: { "stages.status": "blocked" } },
  { $project: {
      stage: "$stages.name",
      blocker: "$stages.blocker",
      owner: "$stages.owner"
  }}
]);
```
**Results:** Stages with blockers and assigned owners
**Token Cost:** ~300 tokens | **Use:** Daily standup, unblock stages

---

## Token Cost Summary
| Query Type | Tokens | Use Case |
|------------|--------|----------|
| Test Coverage | 350 | Progress tracking |
| Deployment History | 400 | Pattern reuse |
| Blocked Stages | 300 | Unblock work |
| Risk Register | 450 | Risk monitoring |

**ROI:** 300-450 tokens → Save hours in manual status collection
>>>>>>> origin/master
