# Stage 06_02 · Repository Reorganisation

## Goal
Apply the approved cleanup plan to reorganise documentation, scripts, archives,
and other assets while preserving repository stability.

## Checklist
- [ ] Execute directory/file moves per approved RFC using scripted migrations.
- [ ] Update imports, references, and documentation to reflect new locations.
- [ ] Refresh navigation artefacts (`README`, `INDEX`, `DOCS_OVERVIEW`, archive
  manifests) in English and Russian.
- [ ] Provide migration guide for contributors (summary of changes, how to
  update local clones).
- [ ] Record audit trail of moves in `docs/specs/epic_06/repo_cleanup_log.md`.

## Deliverables
- Updated repository tree matching the target information architecture.
- Migration guide for contributors plus changelog entry.
- Cleanup log with before/after references for each relocation.

## Metrics & Evidence
- CI run demonstrating no missing imports/tests after restructuring.
- Link checker or static analysis confirming docs references updated.
- Screenshots or dumps of the reorganised `docs/` and `archive/` structures.

## Dependencies
- Stage 06_01 backlog and RFC approval.
- Coordination with maintainers whose workflows may be affected.
- Scripted move tools (e.g., custom Python script or make target) ready.

## Exit Criteria
- Repository structure matches the approved plan with zero dangling references.
- Documentation indices and READMEs reflect the new layout in both languages.
- Cleanup log reviewed and stored for future audit.

## Open Questions
- Do we need git history preservation (e.g., `git mv`) for external forks?
- Should we create symlinks or stub files for temporarily relocated assets?
