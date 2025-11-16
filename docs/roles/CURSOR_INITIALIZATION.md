# Cursor Agent Initialization

## How to Use This Guide

When you start a Cursor agent, load this sequence:

1. **Load core role definition**
   - File: `docs/roles/<role>/role_definition.md` (from agent_workflow.md)
   - This is STATIC and doesn't change

2. **Load current capabilities**
   - File: `docs/roles/<role>/day_capabilities.md`
   - This UPDATES with each new Epic
   - Shows which Days/Epics have been completed and what you can now do

3. **Load RAG queries**
   - File: `docs/roles/<role>/rag_queries.md`
   - These are the specific MongoDB queries or document searches you should use
   - Example: Analyst queries "previous requirements similar to X"

4. **Load recent examples**
   - Files: `docs/roles/<role>/examples/epic_*.md`
   - Use the most recent epic as a template for your work

5. **Check operational context**
   - File: `docs/operational/context_limits.md` (max tokens, compression strategy)
   - File: `docs/operational/handoff_contracts.md` (input/output formats)
   - File: `docs/operational/shared_infra.md` (MongoDB, LLM API, Prometheus)

## Example: Starting Analyst Agent on Day 23

1. Load: `docs/roles/analyst/role_definition.md` (core responsibilities)
2. Load: `docs/roles/analyst/day_capabilities.md` (now includes Day 22 RAG + Day 23 Observability!)
3. Load: `docs/roles/analyst/examples/epic_22_rag_example.md` (latest example)
4. Check: `docs/operational/context_limits.md` (token budget for this epic)
5. Ready: Analyst agent can now:
   - Gather requirements (Day 1-3)
   - Compress long dialogs (Day 15)
   - Query RAG for similar requirements (Day 22)
   - Self-observe and log decisions (Day 23) ← NEW!
