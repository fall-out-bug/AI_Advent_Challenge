# Stage 06_01 · Backlog Triage & Repository Audit

## Goal
Consolidate outstanding follow-ups from earlier epics, evaluate the current
repository layout, and define the execution roadmap for cleanup.

## Checklist
- [ ] Collect follow-up items from EP01–EP04 closure reports, known issues, and
  risk registers.
- [ ] Inventory repository structure (docs, scripts, archives, prompts, tests)
  and identify inconsistencies with Clean Architecture boundaries.
- [ ] Produce prioritised backlog grouped into tracks (automation, tests,
  documentation, repository structure).
- [ ] Draft cleanup RFC outlining proposed directory moves, naming conventions,
  and communication plan.
- [ ] Validate backlog and RFC with stakeholders (tech leads, ops, docs owner).

## Deliverables
- Consolidated backlog (`stage_06_01_backlog.md`) with priorities (P0–P2) and
  owners.
- Repository audit notes highlighting redundant/legacy assets and quick wins.
- Cleanup RFC circulated for feedback (target location: `docs/specs/epic_06/repo_cleanup_rfc.md`).

## Metrics & Evidence
- Link to prior epic follow-up tables mapped to the new backlog.
- Comparison of current vs proposed repository tree.
- Stakeholder sign-off (comments/emails) captured in `signoff_log.md`.

## Dependencies
- Access to previous epic documentation and evidence bundles.
- Availability of stakeholders for review (architecture, ops, docs).

## Exit Criteria
- Backlog approved with clear scope for subsequent stages.
- RFC accepted (or feedback incorporated) for repository reorganisation.
- Communication plan ready for Stage 06_02 execution.

## Open Questions
- Which directories must remain untouched due to external tooling?
- Are there compliance requirements for retaining certain archives in-place?

## Repository Audit Notes

- **Docs:** Top-level files (`API_*.md`, `DOCS_OVERVIEW*.md`, legacy guides) live
  alongside specs. Target tree (`docs/specs/`, `docs/guides/en|ru/`, `docs/archive/`)
  should absorb these, with bilingual pairs moved into `guides/`. Evidence bundles
  under `docs/specs/epic_04/evidence/` stay put for sign-off traceability.
- **Scripts:** Mixed bag of standalone utilities (`day12_run.py`,
  `mcp_comprehensive_demo.py`, `clear_db.py`) and partially grouped folders
  (`analysis/`, `maintenance/`, `quality/`). Align with RFC buckets (`ci/`,
  `infra/`, `maintenance/`, `quality/`) and convert legacy demos into archived
  variants before relocation.
- **Archive:** Top-level `archive/` is empty; historical assets currently sit in
  `docs/archive/` despite closure notes referencing `archive/ep04_2025-11/`.
  Confirm retention policy, standardise naming (`archive/<year>-<theme>/`), and
  ensure manifests live beside payloads.
- **Prompts:** Only `prompts/v1/` exists, mixing reviewer passes with the prompt
  registry. Desired structure keeps active reviewer prompts under
  `prompts/reviewer/`, summarisation flows under `prompts/summarisation/`, and
  old variants under `prompts/archive/`.
- **Tests:** Dual hierarchies (`tests/` and `src/tests/`) confuse ownership and
  violate Clean Architecture layering. Stage 06_02 should define canonical
  location (likely `tests/`) and script a staged move while updating imports and
  CI paths.

### Directories tied to external tooling

- `scripts/infra/start_shared_infra.sh`, `scripts/quality/test_review_system.py`, and
  `scripts/quality/qa/` smoke suites feed the operations quick-start in
  `docs/specs/operations.md`; keep entry points stable while reorganising.
- Evidence bundles within `docs/specs/epic_04/evidence/` and
  `docs/specs/epic_01/` underpin prior sign-offs; preserve paths until archives
  are re-indexed.
- `tests/fixtures/` datasets power integration/e2e suites and downstream student
  exercises; require coordination before relocation or renaming.
