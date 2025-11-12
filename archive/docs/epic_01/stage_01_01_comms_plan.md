# EP01 Stage 01_01 · Stakeholder Communication Plan

## 1. Contact Sheet

| Stakeholder Group | Primary Contact(s) | Channel(s) | Cadence | Notes |
|-------------------|--------------------|------------|---------|-------|
| Application Services (Butler / Review worker) | `app-services@company.com` · Slack `#app-platform` | Email, Slack | T–7 days notice, follow-up on deploy day | Flag API changes, review worker downtime. |
| MCP Tools Owners | `mcp-leads@company.com` · Slack `#mcp-coordination` | Email, Slack, Coordination board | T–7 days announcement, T–2 reminder | Align on interface updates and cutover sequencing. |
| Shared SDK Consumers (internal teams) | `sdk-users@company.com` · Slack `#sdk-users` | Email digest, Slack pinned message | Weekly digest until hardening completes | Highlight SDK lint/coverage commitments. |
| QA / Release Management | `qa-team@company.com` · Slack `#release-desk` | Email, Slack | Include in T–7/T–2 notices + Day 0 go/no-go | Track sign-offs and rollback plan. |
| Documentation / Enablement | `docs@company.com` | Email | Post-change summary within 48h | Ensure docs updates land with release notes. |
| External Consumers (if any) | <TBD> | Email | Coordinate per contract | Determine whether notification is required. |

## 2. Notification Cadence

- **T–7 days:** Initial announcement (scope, expected impact, testing plan).
- **T–2 days:** Reminder with final schedule, links to readiness checklist.
- **Day 0 (deployment):** Real-time Slack update in coordination channel, post in release board.
- **T+1 day:** Post-mortem summary & feedback request.

## 3. Message Template (Email / Slack)

```
Subject: [Heads-up] Modular Reviewer Hardening – Upcoming Changes on <Date>

Hello <Team>,

We are rolling out Stage 01_02 items for the modular reviewer on <Date>.

Scope:
- <Bullet 1>
- <Bullet 2>

Impact:
- Services affected: <list>
- Expected downtime/latency: <details or "none">
- Action required: <who needs to do what>

Readiness Checklist:
- [ ] Tests reviewed / sign-off owner: <name>
- [ ] Feature flag state confirmed (use_modular_reviewer = <value>)
- [ ] Rollback instructions linked here: <URL>

Next Steps & Support:
- Questions in Slack `#ep01-reviewer`
- Escalation contact: <Tech Lead name & handle>

Thank you,
<Your Name>
EP01 Stage 01_02 Coordination
```

Adapt the same structure for Slack (shorter intro + link to full email/board entry).

## 4. Coordination Board Checklist

1. Attach initial announcement to the Stage 01_02 card.
2. Log acknowledgements from each stakeholder group.
3. Confirm QA sign-off and readiness checklist completion before deployment.
4. Capture post-deployment feedback and link to retrospective notes.

