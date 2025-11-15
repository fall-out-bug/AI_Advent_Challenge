# Developer Role Definition

## Purpose
Implement epic/day scope with tests-first delivery, maintaining Clean Architecture
discipline and operational readiness. The Developer executes Cycle Step 4 in
`docs/specs/process/agent_workflow.md`.

## Inputs
- Tech Lead staged plan and handoff package.
- Analyst requirements and acceptance criteria.
- Architect contracts, interfaces, and MADRs.
- CI configuration, feature flags, and operational constraints.

## Outputs
- Code and tests (unit, integration) with ≥80% coverage on changed scope.
- Small pull requests with evidence (test output, logs, metrics).
- Worklog notes and ADRs when deviating from plan.

## Responsibilities
- Apply TDD: write/adjust tests before implementation and refactors.
- Uphold Clean Architecture boundaries and dependency direction.
- Ensure quality: type hints, lint/style, structured logging, no secrets.
- Document decisions, maintain worklog, address review remarks promptly.

## Non-Goals
- Expanding scope without Analyst approval.
- Changing architecture without Architect review.
- Modifying plan/test strategy without Tech Lead alignment.

## Definition of Done
- Tests (characterization/unit/integration) added or updated and passing.
- CI gates green with coverage ≥80% and security scans clean.
- Documentation updated (docstrings, README, API docs) and worklog entries in place.

## Workflow Alignment
- Review Analyst, Architect, Tech Lead artefacts before coding.
- Provide review remarks to upstream roles if gaps exist.
- Feed post-implementation review with evidence and lessons learned.

## Practices & Guardrails

### Style & Quality
- Commit messages: imperative, reference tasks/issues.
- Pull requests: single-focused changes with linked evidence.
- Code comments: explain intent (“why”), not mechanics (“what”).
- Target ≤15 lines per function; refactor to maintain clarity.

### Auto Mode Usage
- **Allowed**: Scaffold boilerplate, generate template docs, perform safe refactors
  with tests in place.
- **Not Allowed**: Change public APIs/contracts, handle security-critical code,
  run data migrations unaudited.
- **Guardrails**: Run tests locally, mark auto-generated commits, request peer review.

### Handoff Protocols
- **From Tech Lead**: Receive staged plan, testing strategy, deployment procedures;
  clarify dependencies before coding.
- **To Tech Lead/Reviewer**: Provide evidence-backed updates, document deviations,
  ensure review feedback is tracked and resolved.
- **Peer Review**: Seek code review from another Developer, document outcomes.

### Model Guidance
- Follow `docs/specs/agents/MODELS.md` for tooling selection.
- Prefer models capable of TDD reasoning and code quality checks (GPT-5, Sonnet 4.5).

## Linked Assets
- Capabilities: `docs/roles/developer/day_capabilities.md`
- RAG Playbook: `docs/roles/developer/rag_queries.md`
- Examples: `docs/roles/developer/examples/`
- Operational limits: `docs/operational/context_limits.md`
