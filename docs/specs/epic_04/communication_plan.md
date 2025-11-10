# Stage 04_01 · Communication Plan

## Objectives

- Align stakeholders on the archive scope, dependency remediation, and rollout
  timeline.
- Provide clear messaging and channels for questions or escalations.
- Ensure approvals are captured before Stage 04_02 begins.

## Stakeholder Matrix

| Role | Primary Contact | Impacted Assets | Communication Channel | Required Action | Target Date |
|------|-----------------|-----------------|-----------------------|-----------------|-------------|
| EP01 Tech Lead (Modular Reviewer) | TBD (Reviewer owner) | Legacy reviewer agents, homework MCP tool | Review meeting + async notes | Approve replacement readiness, confirm MCP rollout plan | T-5 days |
| EP02 Tech Lead (MCP & Bot) | TBD (MCP owner) | MCP tool registry, CLI migration, Telegram handlers | Async review + sync checkpoint | Validate CLI coverage, approve MCP registry changes | T-5 days |
| EP03 Tech Lead (Observability) | TBD (Ops owner) | Logging/metrics in archived modules, health scripts | Documentation review (async) | Confirm monitoring coverage remains intact | T-4 days |
| Application Lead | TBD | Legacy usecases imports | Async review | Sign off on use case migration plan | T-4 days |
| Workers Lead | TBD | Reminder schedulers, message sender | Stand-up update + async checklist | Deliver worker refactor plan | T-3 days |
| Documentation Owner | TBD | Legacy guides, MCP docs, model setup | PR review | Approve doc replacements and navigation changes | T-2 days |
| Operations Owner | TBD | Local model scripts, Makefile targets | Ops sync + checklist | Validate shared infra workflow coverage | T-2 days |
| QA Lead | TBD | Legacy tests (MCP, reminder, workers) | Async review + test baseline note | Approve retirement of legacy suites and replacement coverage | T-2 days |
| Developer Agents | Team | Implementation tasks | Slack / project channel broadcast | Prepare execution backlog for Stage 04_02 | T-1 day |

## Timeline

| Milestone | When | Description | Owner |
|-----------|------|-------------|-------|
| Draft distribution | T-7 days | Share archive scope + dependency map for initial feedback | EP04 Tech Lead |
| Coordination checkpoint | T-5 days | Meeting with EP01–EP03 leads to confirm remediation owners | EP04 Tech Lead |
| Remediation updates | T-4 to T-2 days | Collect status updates on hard blockers; track in progress tracker | Respective leads |
| Final approvals | T-1 day | Circulate final scope, dependency status, and evidence; capture approvals | EP04 Tech Lead |
| Archive execution kickoff | T-0 | Begin Stage 04_02 migrations per approved scope | EP04 Tech Lead |
| Post-archive review | T+2 days | Confirm no regressions, update documentation indexes | Documentation + QA |

## Communication Channels

- **Weekly coordination call** (EP leads, QA, Ops) — review blocker status.
- **Async updates** via project Slack/issue tracker — daily check-in on
  remediation tasks.
- **Approval tracking** in `docs/specs/progress.md` and Stage 04_01 PR comments.
- **Emergency escalation** — Ops on-call + Tech Lead for critical dependencies.

## Key Messages

1. **Archive scope is conservative:** Assets move only after replacements and
   approvals are confirmed.
2. **Replacements documented:** Modular reviewer services, CLI backoffice, and
   updated docs cover legacy functionality.
3. **No production downtime expected:** Archives target unused or deprecated
   paths; active flows remain intact.
4. **Roll-back plan:** Assets remain in git history and will be stored under
   `archive/ep04_2025-11` for reference.
5. **Testing baseline maintained:** QA lead ensures coverage shifts to new suites
   before legacy tests are removed.

## Approval Checklist

- [ ] EP01 Tech Lead sign-off recorded in Stage 04_01 PR
- [ ] EP02 Tech Lead sign-off recorded
- [ ] EP03 Tech Lead sign-off recorded
- [ ] Application/Workers leads approve migration timeline
- [ ] Documentation and Ops owners approve doc/script updates
- [ ] QA lead confirms replacement test coverage

## Supporting Artifacts

- `archive_scope.md` — authoritative asset list.
- `dependency_map.md` — blocker tracking.
- `docs/specs/progress.md` — status updates and approvals.
- Evidence bundle under `docs/specs/epic_04/evidence/`.


