# Epic 04 · Legacy Archive & Cleanup

## Purpose
Retire legacy assets safely, ensuring the repository reflects the refactored
architecture while preserving historical artefacts under controlled archival
structures.

## Objectives
- Confirm archive candidates (code, docs, scripts, prompts) and align with
  active replacements from EP01–EP03.
- Execute migrations, moving or deleting assets without disrupting ongoing
  development.
- Refresh repository hygiene (README, indices, manifests) to reflect the new
  canonical structure.

## Dependencies
- EP02 completion for MCP/bot replacements.
- EP03 documentation updates for observability references.
- Coordination with stakeholders relying on legacy artefacts before removal.

## Stage Breakdown
| Stage | Scope | Key Deliverables | Exit Criteria |
|-------|-------|------------------|---------------|
| Stage 04_01 | Archive scope confirmation | Final archive list, dependency map, communication plan | Stakeholders approve scope, dependencies documented |
| Stage 04_02 | Migration execution | Assets relocated/removed, redirects or stubs added | Repository builds/tests unaffected, archive organised |
| Stage 04_03 | Repo hygiene & sign-off | Updated README/index, final audit report, closure notes | Docs merged, inventory updated, epic closed |

## Success Criteria
- Legacy assets removed or relocated without breaking builds/tests.
- Documentation and indices accurately reference new locations/scope.
- Archive follows consistent structure with clear retrieval guidance.

## Stakeholders
- Tech Lead Agent: to be assigned (planning, approvals).
- Developer Agents: carry out migrations and refactors.
- Documentation Owners: review updated references.

## Risk & Mitigation Snapshot
- **Risk:** Accidental deletion of still-used assets.  
  **Mitigation:** Maintain dependency map, run impact checks before removal.
- **Risk:** Archive becomes disorganized.  
  **Mitigation:** Apply consistent naming conventions and README entries per
  archive folder.

## References
- `docs/specs/epic_00/stage_00_01.md` inventory notes.
- `docs/specs/progress.md` for epic tracking.
- `docs/specs/operations.md` for infra-related script considerations.

