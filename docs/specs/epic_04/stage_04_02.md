# Stage 04_02 · Migration Execution

## Goal
Carry out the archival plan by relocating, deprecating, or deleting legacy
assets while preserving repository stability.

## Checklist
- [ ] Move targeted assets to `archive/` (or delete) following naming standards.
- [ ] Update imports, references, and documentation to point to replacements.
- [ ] Provide stubs or redirect notes where external references exist.
- [ ] Run full CI/test suite to confirm migrations did not introduce regressions.
- [ ] Record audit trail noting file moves/deletions for future reference.
- [ ] Implement observability follow-ups: commit Grafana dashboard IaC
  provisioning and extend Loki alert rules per Stage 03_03 backlog.

## Deliverables
- Pull requests or change sets executing the migrations.
- Updated documentation indicating new locations or removal notices.
- Migration log appended to stage summary.
- IaC assets for Grafana dashboards and updated Alertmanager/Loki rules merged
  with validation evidence.

## Metrics & Evidence
- CI run showing green status post-migration.
- Repository diff verifying only planned assets affected.
- Search report confirming legacy references resolved.
- Executed `observability-checks` workflow (or equivalent) validating new Grafana
  provisioning and Loki alerts.

## Dependencies
- Stage 04_01 approval and communication plan.
- Coordination with EP02/EP03 where codepaths intersect.
- Access to documentation maintainers for quick updates.

## Exit Criteria
- All scoped assets migrated/removed with sign-offs captured.
- CI/tests green; no unresolved references or import errors.
- Migration log shared with stakeholders and stored alongside archive README.

## Open Questions
- Do we maintain compatibility shims for a deprecation window?
- Are additional metadata (e.g., README in each archive folder) required now or
  in Stage 04_03?

