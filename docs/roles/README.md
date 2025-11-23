# Roles & Consensus Documentation

This directory now centers on a single JSON specification for the consensus
architecture, with supporting operator guides kept nearby for quick lookup.

## Canonical Files

- `consensus_architecture.json` &mdash; compact source of truth for every agent,
  artifact, iteration rule, veto authority, automation trigger, and escalation
  package. All other docs reference this schema.
- `cursor_consensus/PROTOCOL.md` &mdash; hands-on workflow describing how to run
  the file-based consensus loop using the JSON artifacts and message schema.
- `cursor_consensus/prompts/*` &mdash; role prompts aligned with the JSON spec.

## Role Guides

Detailed day plans, RAG examples, and legacy prompt material remain under
`docs/specs/agents`. The per-role folders that still live here keep specialized
KO guides or localized artifacts, but the JSON spec dictates the authoritative
interfaces and data contracts the agents must follow.

## Legacy Material

Historical YAML specifications (for example
`docs/reference/legacy/consensus_mechanism_v2.yaml`) are retained only for reference and
should not be used for new work. Always start from the JSON files described
above when wiring new conversations or tools into the workflow.

## How to Read the JSON Spec Quickly

1. **Meta / Paths** &mdash; see where each epic keeps its working files.
2. **Roles / Iteration Flow** &mdash; understand who owns each phase and what
   they must emit.
3. **Artifacts / Message Schema** &mdash; copy these structures into prompts or
   tests to guarantee compatibility.
4. **Veto / Automation / Voting** &mdash; enforce hard boundaries with minimal
   tokens.
5. **Metrics / Escalation / Learning Loop** &mdash; instrument the system and
   keep it improving without spreading logic across multiple markdown files.

Treat this README as the jump point: if a document is not linked here, it is
either archived or still pending migration to the JSON-driven format.
