# Stage 02_03 · Telegram & Documentation Alignment

## Goal
Align Telegram bot behaviour, localisation, and documentation with the
consolidated MCP and CLI scope.

## Checklist
- [x] Remove or archive reminder/task flows from bot handlers, state machine, and
  menus.
- [x] Ensure digest/channel flows reference the hardened modular reviewer APIs
  and CLI equivalents.
- [x] Review and update localisation files/content for Russian copy; align tests
  with new strings.
- [x] Refresh bot-related documentation and FAQs to match new scope.
- [x] Coordinate acceptance testing with operations or representative users.

## Deliverables
- Updated bot source code reflecting reduced scope.
- Localisation diff (RU copy) validated by reviewer.
- Documentation updates merged (README snippets, bot guides).
- Acceptance test report or sign-off notes.

## Metrics & Evidence
- Bot test suite results (unit + integration where feasible).
- Manual Telegram run log (screen captures or transcripts) demonstrating key
  flows.
- Documentation change summary.

## Dependencies
- Stage 02_02 CLI commands (for cross-linking and feature parity).
- EP01 outputs (reviewer endpoints and flags).
- EP04 schedule for archiving removed bot assets.

## Exit Criteria
- Telegram bot deployed or ready for deployment with updated scope.
- Documentation and localisation approved by tech lead and localisation reviewer.
- Follow-up tasks (e.g., translation automation) recorded with owners/dates.

## Open Questions
- Do we maintain a feature flag to temporarily re-enable any archived flows?
  - Decision: No feature flag; removed flows stay archived (Stage 02_03).
- Are additional support materials (videos, quick guides) required for end
  users?
  - Decision: No new assets for this stage; README updates suffice.

