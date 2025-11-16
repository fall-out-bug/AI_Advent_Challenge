# Review · Tech Lead Implementation Plan (EP23)

Date: 2025-11-15 (rev.2)
Reviewer: cursor_analyst_v1

## Summary
Plan updated per prior feedback: DR drill scope aligned with restart validation, benchmark gate tied to hardware completion, dataset evidence captured via snapshots, new observability labels + RAG++ addendum locations defined. Remaining clarifications below focus on evidencing and access-control nuances.

## Findings & Questions
1. **Acceptance matrix ownership**
   - TL-00 now mandates `docs/specs/epic_23/acceptance_matrix.md`. Please specify who maintains the file after initial sign-off (Tech Lead vs Analyst) and whether it needs version tagging for subsequent scope tweaks. Without clear ownership, the matrix may diverge from backlog updates.

2. **RU localisation spot-check procedure**
   - TL-01 Definition of Done references a “RU content spot-check log,” but there is no described method (manual sampling? automated script?). Recommend adding a concrete checklist or script reference so the evidence is reproducible.

3. **Observability labels document linkage**
   - TL-04 introduces `docs/operational/observability_labels.md` tied to Architect handoff. Ensure `docs/specs/epic_23/architect_handoff.md` (and the role initialization guide) explicitly reference this new file to avoid discoverability gaps.

4. **Owner-only treatment for RAG++ addendum**
   - TL-07 creates `docs/specs/epic_23/rag_plus_plus_addendum.md` while reiterating that the feature flag is owner-only. Please clarify whether the document should live in a restricted subdirectory (or include guidance on sanitizing configs) so requirements match the access policy.

5. **Restart validation evidence granularity**
   - TL-05 DoD requires a memo in `docs/specs/epic_23/shared_infra_restart.md`. Consider capturing the exact Prometheus/Loki queries or commands used during restart; otherwise developers might only supply narrative text without verifiable telemetry.

## Next Actions
- Provide answers/updates for items above.
- Once resolved, Analyst will update handoff documentation referencing new artifacts as needed.

## Tech Lead Responses (2025-11-15)
1. **Acceptance matrix ownership** – TL-00 now states Tech Lead maintains `docs/specs/epic_23/acceptance_matrix.md` post sign-off with version tags; Analyst co-signs each revision (see plan §4 TL-00 + matrix header).
2. **RU localisation spot-check** – Added checklist `docs/specs/epic_23/checklists/ru_localization_spotcheck.md` and TL-01 task/DoD explicitly require it (5-sample method, dual reviewers).
3. **Observability labels discoverability** – `docs/operational/observability_labels.md` is referenced in TL-04 tasks and added to `architect_handoff.md` + role init guidance note.
4. **Owner-only RAG++ addendum** – TL-07 now stores sanitized content under `docs/specs/epic_23/owner_only/rag_plus_plus_addendum.md` with explicit rules; secrets remain external.
5. **Restart validation evidence** – TL-05 tasks/DoD mandate recording command list plus PromQL/Loki queries within `shared_infra_restart.md`.
