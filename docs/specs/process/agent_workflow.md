# Agent Workflow · Review Cycles and Hand-offs

## Roles
- Analyst → base requirements
- Architect → architecture vision
- Tech Lead → implementation plan
- Developer → implementation + review feedback

## Cycle
1) Analyst: write base epic/day requirements (scope, constraints, acceptance).
2) Architect: produce architecture vision; Analyst reviews, prepares remarks; Architect applies.
3) Tech Lead: prepare staged implementation plan; Analyst + Architect review; Tech Lead applies.
4) Developer: reviews all docs, prepares remarks; return to 1)–3) to address gaps.
5) After sign-offs: Tech Lead produces final staged plan; Developer implements and logs decisions.
6) Post-implementation review: Analyst, Architect, Tech Lead review; Developer applies fixes.
7) Analyst: prepare epic summary; archive docs into a non-indexed folder.

## Documents (locations)
- Requirements: `docs/specs/epics/<epic>/requirements.md`
- Architecture: `docs/specs/epics/<epic>/architecture.md`
- Plan: `docs/specs/epics/<epic>/plan.md`
- Reviews: `docs/specs/epics/<epic>/reviews/*.md`
- Decisions (MADR): `docs/specs/epics/<epic>/decisions/*.md`
- Worklogs: `docs/specs/epics/<epic>/worklogs/*.md`
- Summary: `docs/specs/epics/<epic>/summary.md`
- Archive: move finalized docs to top-level `archive/` (per repo rules)

## Rules
- Single language: EN only (token-efficient, concise).
- Keep docs concise, machine-friendly; use provided templates.
- Each stage has Definition of Done and acceptance checks.
- Use checklists and references (paths/commands); no prose dumps.
- Epics numbered by AI Advent days (EP<day>, e.g., EP19, EP20).
