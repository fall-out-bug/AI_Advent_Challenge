# Tech Lead Day Capabilities

## Foundational Days 1-22

### Days 1-10 · Planning Framework
- Create plan templates with stages, DoD, and evidence mapping.
- Define CI gate catalogue (lint, tests, coverage, security).
- Establish risk register and rollback checklist formats.

### Day 11 · Shared Infra & MCP Baseline
- Incorporate shared infra bring-up steps into staging plan.
- Align plan checkpoints with MCP tool availability and observability.
- Coordinate with operations for environment variables and secrets.

### Day 12 · Deployment & Quick Start
- Integrate quick-start commands into rollout sequence.
- Validate health checks and smoke tests in plan DoD.
- Document local vs CI parity steps for Developers.

### Day 15 · Modular Reviewer Rollout
- Stage feature-flag rollout and fallback strategy.
- Specify CI coverage for reviewer performance metrics.
- Sync with Architect on adapter interfaces and migration path.

### Day 17 · Integration Contracts & README
- Ensure integration scenarios cover API endpoints and contract validation.
- Update README references and align plan tasks with documentation updates.
- Capture cross-team dependencies and communication plans.

### Days 18-22 · Execution Support
- Monitor stage completion and adjust plan sequencing if blockers emerge.
- Keep risk register current; escalate unresolved architecture questions.
- Prepare post-implementation review package.

## Capability Patterns
- **Stage Tables**: Include columns for owner, DoD, evidence, blockers.
- **CI Gate Matrix**: Map each stage to required pipelines and commands.
- **Risk Register**: Track likelihood, impact, owner, mitigation, status.

## Upcoming (Days 23-28) ⏳
- Plan for analytics tooling integration and performance budgets.
- Expand rollback scenarios for multi-service deployments.
- Prepare staged dry-runs using feature flags and canary strategies.

## Update Log
- [ ] EP19 – Draft plan pending Analyst approval
- [ ] EP20 – Awaiting architecture inputs
- [ ] EP21 – Aligning reviewer rollout with operations window
