# Epic 06 · Finishing Touches & Repository Hygiene

## Purpose
Consolidate post-refactor follow-ups, automate shared infrastructure workflows,
and tidy repository structure so the codebase is easy to navigate for new
maintainers and downstream teams.

## Objectives
- Triage and execute outstanding follow-up items from epics 01–04 (observability,
  shared infra automation, test recalibration, documentation parity).
- Reorganise repository assets (docs, scripts, archives) to match the current
  architecture and reduce duplication.
- Provide final polish: green CI without ad-hoc skips, refreshed indices, and a
  maintainers’ guide capturing the new structure.

## Dependencies
- Completion of EP01–EP04 (already signed off).
- Coordination with operations for shared infra automation and DR drill
  scheduling.
- Agreement from documentation owners on the target information architecture.

## Stage Breakdown
| Stage | Scope | Key Deliverables | Exit Criteria |
|-------|-------|------------------|---------------|
| Stage 06_01 | Backlog triage & repository audit | Consolidated follow-up backlog, repo layout assessment, prioritised execution plan | Backlog approved by stakeholders, cleanup RFC circulated |
| Stage 06_02 | Repository reorganisation | Reworked docs/scripts/archives structure, updated indices, migration guide | Repo tree aligns with approved structure, navigation docs merged |
| Stage 06_03 | Automation & quality closure | Shared infra automation, test recalibration, CI gating updates | CI green without provisional skips, automation scripts documented |
| Stage 06_04 | Final verification & hand-off | Maintainer playbook, lessons learned, final sign-offs | All deliverables signed off, maintainers briefed, epic closed |

## Success Criteria
- All outstanding follow-up items from earlier epics are either completed or
  re-filed with owners and deadlines.
- Repository navigation is intuitive; documentation indices and README reflect
  the new layout (English & Russian).
- Shared infrastructure automation and CI validations run consistently without
  manual intervention.

## Stakeholders
- Tech Lead Agent: to be assigned (planning & coordination).
- Developer/Docs Agents: execute backlog items and repo reorganisation.
- Operations/Ops Excellence: coordinate infra automation and DR drills.

## Risk & Mitigation Snapshot
- **Risk:** Repository reorganisation disrupts ongoing work.
  **Mitigation:** Prepare RFC, communicate migration guide, use scripted moves
  with audit logs.
- **Risk:** Follow-up backlog grows beyond capacity.
  **Mitigation:** Prioritise backlog in Stage 06_01, time-box lower priority
  items, coordinate with downstream teams.
- **Risk:** Automation changes break CI.
  **Mitigation:** Introduce changes behind feature toggles, run in shadow mode
  before enforcing.

## References
- `docs/specs/epic_04/epic_04_closure_report.md` – follow-up recommendations.
- `docs/specs/epic_03/observability_gap_report.md` – instrumentation backlog.
- `docs/specs/operations.md` – current infra/runbooks to update.
- `docs/specs/progress.md` – programme tracker (update with EP06).
