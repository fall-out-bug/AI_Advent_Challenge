# Stage 02_03 · Telegram Manual Testing Checklist

## Scope
- Bot limited to channel management, digest delivery, and conversational help.
- Reminder/task flows removed; ensure no residual entry points.
- English and Russian localisation must reflect new scope.

## Preconditions
- Deploy bot in staging with updated code.
- MCP servers reachable; CLI backoffice available for cross-checks.
- Test user subscribed to at least one channel with recent posts.

## Checklist
1. **Startup & Health**
   - Launch bot, confirm no errors in logs.
   - Hit `/start`, `/help`, `/menu` — verify responses mention channels/digests only.
   - Check Prometheus metrics endpoint reports healthy status.
2. **Menu Navigation**
   - Ensure menu buttons exclude tasks/reminders.
   - Navigate to each submenu; links or prompts respond without errors.
3. **Channel Operations**
   - Trigger channel subscription via natural language.
   - Verify orchestrator routes to channel handler and confirms action.
   - Cross-validate subscription exists via CLI `channels list`.
4. **Digest Retrieval**
   - Request latest digest in chat; confirm summary references CLI scope.
   - Ensure markdown renders correctly; no task terminology present.
5. **Error Handling**
   - Submit unsupported command; bot should reply with fallback guidance.
   - Induce MCP failure (disable temporarily) and confirm graceful error message.
6. **Localisation**
   - Switch to Russian locale; repeat `/menu` and digest flow.
   - Ensure translations reflect new scope, no task references.
7. **Cleanup**
   - Remove test subscriptions using CLI and confirm bot acknowledges.
   - Restore MCP connectivity if altered; stop bot gracefully.

## Sign-off
- Record tester, date, and environment.
- Capture chat transcript snippets for archival.


