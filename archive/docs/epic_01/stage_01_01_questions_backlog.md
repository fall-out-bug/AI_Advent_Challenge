# Stage 01_01 · Questions Backlog

All items are routed through the EP01 Tech Lead (главный агент) for triage and delegation.

| ID | Theme | Question / Context | Required Action | Owner | Status |
|----|-------|--------------------|-----------------|-------|--------|
| EP01-Q-001 | Test Strategy | Re-enable skipped reviewer tests during Stage 01_02 or defer? (Stage spec §Open Questions) | Compile inventory of skipped cases, estimate remediation effort, propose timeline. | EP01 Tech Lead | Open |
| EP01-Q-002 | Stakeholder Comms | Do downstream consumers need advance notice before reviewer hardening changes land? | Identify consumer list, draft communication plan, align with coordination channel. | EP01 Tech Lead + Comms | Open |
| EP01-Q-003 | Feature Flags | Should `use_modular_reviewer` remain as a runtime toggle or be promoted to permanent default? | Decide on final flag lifecycle, document migration path, update code if removal planned. | EP01 Tech Lead + Architecture | In progress |
| EP01-Q-004 | Test Infrastructure | How do we satisfy Airflow-dependent tests (install vs mock) in CI? | Assess cost of lightweight Airflow fixtures vs targeted mocks, produce recommendation. | Infra SMEs via EP01 Tech Lead | Open |
| EP01-Q-005 | Lint Strategy | What scope should the staged lint allowlist cover for Stage 01_02 enforcement? | Define minimal reviewer-critical module set, agree on enforcement schedule. | EP01 Tech Lead + QA | Open |
| EP01-Q-006 | Shared SDK Ownership | Who owns raising shared SDK coverage/typing to policy levels without blocking other epics? | Nominate maintainer group, align effort split with EP02 (MCP) dependencies. | EP01 Tech Lead + EP02 Lead | Open |

