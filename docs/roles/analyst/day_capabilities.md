# Analyst Day Capabilities

<<<<<<< HEAD
## Foundational Days 1-22

### Days 1-10 · Discovery Primer
- Stand up requirement templates and traceability matrices.
- Establish acceptance criteria catalog shared with Architect and Tech Lead.
- Document archive rules and review cadence checkpoints.

### Day 11 · Shared Infra & MCP Baseline
- Capture infra assumptions (Mongo, Prometheus, Grafana, LLM API).
- Align requirement acceptance with monitoring and MCP tool availability.
- Ensure docs reference `docs/specs/day11-17_summary.md` for context.

### Day 12 · Deployment & Quick Start
- Embed deployment health checks into acceptance criteria.
- Reference quick-start guides in requirement packs.
- Coordinate with Tech Lead for environment readiness signals.

### Day 15 · Modular Reviewer Rollout
- Update requirements for modular reviewer feature flag and rollout plan.
- Track performance baselines and acceptance metrics for reviewer flows.
- Archive deprecated reminder/task tooling requirements.

### Day 17 · Integration Contracts & README
- Define integration coverage expectations and contract checkpoints.
- Sync README and integration notes with updated requirements.
- Align with `docs/specs/epic_03/alerting_runbook.md` for escalation data.

### Days 18-22 · Continuous Alignment
- Maintain decision logs as new MADRs emerge.
- Validate cross-team dependencies and escalate gaps.
- Prepare summaries for epic archiving and knowledge transfer.

## Capability Patterns
- **Requirement Matrices**: Use tables mapping Must/Should/Out-of-Scope to tests.
- **Traceability**: Link acceptance criteria to `tests/` paths and CI evidence.
- **Review Feedback**: Log remarks in `docs/epics/<epic>/reviews/` with timestamps.

## Upcoming (Days 23-28) ⏳
- Placeholder for new epics: capture planned scope and anticipated constraints.
- Prepare to expand RAG queries for emerging domains (e.g., analytics, billing).
- Coordinate with Architect to pre-register decision templates.

## Update Log
- [ ] EP19 – Requirements refresh pending
- [ ] EP20 – Awaiting initial scoping session
- [ ] EP21 – Sync with architecture decision queue
=======
This document details how each Challenge Day enhances the Analyst role's capabilities, with specific techniques, use cases, and integration points for requirements gathering, validation, and handoff to downstream roles.

---

## Day 1 · First Agent & Basic Interaction

**Capability:** Initiate structured conversations with stakeholders to gather initial requirements.

**Use Case:**
- Product Owner describes a new feature idea
- Analyst agent captures basic requirements in structured format
- Output: Initial requirement skeleton with Must/Should/Out-of-Scope categories

**Key Technique:**
- Use prompt engineering to extract structured data from free-form input
- Template-based requirement capture: `{"id": "R-XXX", "text": "...", "type": "functional"}`
- Simple question-answer loop without advanced memory

**Example:**
```
User: We need a payment processing feature
Agent: I'll help gather requirements. Let me ask:
1. What payment methods must be supported?
2. What's the expected transaction volume?
3. Are there regulatory constraints?

[After 3-5 exchanges]
Agent outputs:
{
  "requirements": [
    {"id": "R-001", "text": "Support credit card payments", "type": "functional"},
    {"id": "R-002", "text": "PCI compliance mandatory", "type": "constraint"}
  ]
}
```

**Status:** ✅ MASTERED (Day 1)

**Integration Points:**
- Foundation for all requirement gathering workflows
- Output format becomes input for Architect role
- Establishes basic traceability from stakeholder input to requirement ID

---

## Day 2 · Structured Output Format

**Capability:** Return requirements in predictable, parseable JSON format that downstream roles can consume.

**Use Case:**
- Analyst gathers requirements from 10-exchange conversation
- Outputs structured JSON with clear schema
- Architect role can parse without manual intervention

**Key Technique:**
- Define JSON schema in system prompt: "Always return requirements in this format: {...}"
- Use JSON validation before handoff (pydantic models)
- Include metadata: epic_id, timestamp, version, clarity_score

**Example Output:**
```json
{
  "metadata": {
    "epic_id": "EP20",
    "analyst_version": "v1.0",
    "timestamp": "2025-11-15T10:30:00Z",
    "total_exchanges": 8
  },
  "requirements": [
    {
      "id": "REQ-001",
      "text": "System must process payments within 2 seconds",
      "type": "functional",
      "priority": "high",
      "acceptance_criteria": [
        "Transaction completes in < 2s (p95)",
        "Successful transactions logged with timestamp"
      ]
    }
  ],
  "summary": {
    "total_requirements": 5,
    "clarity_score": 0.82,
    "completeness_score": 0.88
  }
}
```

**Status:** ✅ MASTERED (Day 2)

**Integration Points:**
- Enables automated handoff to Architect (no manual parsing)
- JSON schema versioning allows backward compatibility
- Clarity/completeness scores help prioritize clarification efforts

---

## Day 3 · Conversation Mechanics & Stopping Conditions

**Capability:** Recognize when sufficient clarity is achieved and stop gathering; avoid over-questioning.

**Use Case:**
- Analyst asks 5-7 clarifying questions
- Tracks clarity_score per requirement: 0.0 (unclear) → 1.0 (crystal clear)
- When avg clarity ≥ 0.80, stops asking and moves to validation

**Key Technique:**
- Define stopping condition in prompt: "Stop when clarity_score ≥ 0.80 OR after 15 exchanges"
- Calculate clarity_score based on:
  - Specificity of stakeholder answers (vague vs precise)
  - Presence of acceptance criteria
  - Absence of contradictions
- Signal to stakeholder: "I have enough information. Moving to validation phase."

**Example Session:**
```
Exchange 1:
Analyst: What payment methods should we support?
User: Credit cards and PayPal
→ clarity_score: 0.6 (medium - lacks detail)

Exchange 2:
Analyst: Which credit card types? International support?
User: Visa, Mastercard, AmEx. Global support required.
→ clarity_score: 0.85 (high - specific)

Exchange 3:
Analyst: What about refunds? Timeline?
User: Yes, 14-day refund window
→ clarity_score: 0.90 (high)

→ Average clarity: 0.88 → STOP gathering
Analyst: "I have sufficient clarity (score: 0.88). Proceeding to requirement synthesis."
```

**Status:** ✅ MASTERED (Day 3)

**Integration Points:**
- Changes role_definition: Requirements gathering now has exit condition
- Improves handoff quality to Architect (clearer requirements = better designs)
- Tech Lead benefits: fewer clarification loops during implementation planning
- See example: `docs/roles/analyst/examples/day_3_conversation_stopping.md`

---

## Day 4 · Temperature Tuning for Requirement Clarity

**Capability:** Adjust LLM temperature based on task: T=0 for structured parsing, T=0.7 for exploratory questions.

**Use Case:**
- T=0.0: Parsing stakeholder input into structured JSON (deterministic)
- T=0.7: Generating clarifying questions (creative, diverse)
- T=0.0: Final validation and acceptance criteria generation (precise)

**Key Technique:**
- Use multi-pass approach:
  1. Gather (T=0.7): Ask diverse, exploratory questions
  2. Parse (T=0.0): Convert answers to structured requirements
  3. Validate (T=0.0): Check for contradictions, gaps
- Track which temperature was used for audit trail

**Example:**
```python
# Gathering phase (creative questions)
response = llm.generate(
    prompt="Generate 5 clarifying questions about payment system",
    temperature=0.7
)
# Output: ["What about cryptocurrency?", "Subscription billing?", ...]

# Parsing phase (deterministic)
requirements = llm.generate(
    prompt="Extract requirements from: [transcript]",
    temperature=0.0,
    format="json"
)
# Output: {"requirements": [{"id": "R-001", ...}]}
```

**Status:** ✅ MASTERED (Day 4)

**Integration Points:**
- Improves requirement quality: creative questions, deterministic parsing
- Reduces hallucinations in structured output (T=0 for JSON)
- Temperature metadata included in handoff for traceability

---

## Day 5 · Model Selection for Requirements Work

**Capability:** Choose appropriate LLM model based on task complexity and token budget.

**Use Case:**
- Simple requirement parsing: Use fast, cheap model (e.g., GPT-4o-mini)
- Complex domain analysis: Use powerful model (e.g., GPT-5, Claude Sonnet 4.5)
- Budget constraint: Track cost per requirement gathering session

**Key Technique:**
- Model routing based on task:
  - Initial questions: GPT-4o-mini (fast, cheap)
  - Domain analysis: GPT-5 (deep reasoning)
  - Final validation: Claude Sonnet 4.5 (thorough)
- Track tokens and cost per epic for budget planning

**Example Routing:**
```python
if task == "initial_questions":
    model = "gpt-4o-mini"  # ~$0.15 per 1M tokens
elif task == "domain_analysis":
    model = "gpt-5"  # ~$2.50 per 1M tokens
elif task == "final_validation":
    model = "claude-sonnet-4.5"  # ~$3.00 per 1M tokens
```

**Metrics:**
```
EP20 Requirements Session:
- Initial gathering: 3K tokens × $0.15 = $0.0005
- Domain analysis: 8K tokens × $2.50 = $0.02
- Validation: 2K tokens × $3.00 = $0.006
Total cost: $0.0265 per epic
```

**Status:** ✅ MASTERED (Day 5)

**Integration Points:**
- Cost tracking for epic budgets
- Model selection documented in handoff metadata
- See `docs/specs/agents/MODELS.md` for cross-role model mapping

---

## Day 6 · Chain of Thought for Requirements Validation

**Capability:** Use CoT prompting to validate requirements for logical consistency and completeness.

**Use Case:**
- Analyst gathered 10 requirements
- Before handoff, runs CoT validation: "Think step-by-step: Are these requirements consistent?"
- Catches contradictions (e.g., "Must support offline mode" + "Requires real-time API")

**Key Technique:**
- Append to validation prompt: "Let's think step by step:"
  1. List all requirements
  2. Identify dependencies between them
  3. Check for contradictions
  4. Highlight missing pieces
- Compare CoT output vs direct output

**Example:**
```
Without CoT:
Analyst: "Requirements look good, no issues found."

With CoT:
Analyst: "Let me validate step by step:
1. REQ-001: Offline mode required
2. REQ-005: Real-time fraud detection via API
3. → CONTRADICTION: Offline mode incompatible with real-time API
4. → ACTION: Clarify with stakeholder: partial offline support?"

Result: Caught critical issue before handoff to Architect
```

**Status:** ✅ MASTERED (Day 6)

**Integration Points:**
- Reduces rework for Architect (fewer contradictions)
- Improves requirement quality score from 0.75 → 0.90
- CoT reasoning included in handoff notes for transparency

---

## Day 7 · Multi-Agent Validation (Analyst ↔ Peer Review)

**Capability:** Use second agent to peer-review gathered requirements before handoff.

**Use Case:**
- Analyst A gathers requirements (15 items)
- Analyst B reviews for completeness, clarity, contradictions
- Only requirements passing peer review go to Architect

**Key Technique:**
- Agent 1 (Gatherer): Focuses on breadth and stakeholder alignment
- Agent 2 (Reviewer): Focuses on internal consistency and technical feasibility
- Handoff format includes peer_review_status: "approved" | "needs_clarification"

**Example Workflow:**
```
Agent A (Gatherer):
{
  "requirements": [
    {"id": "R-001", "text": "Support 10K concurrent users"},
    {"id": "R-002", "text": "Response time < 100ms"}
  ]
}

Agent B (Reviewer):
{
  "review_result": "needs_clarification",
  "issues": [
    {
      "requirement_id": "R-001",
      "issue": "10K concurrent users: Peak or sustained? What's the ramp-up curve?",
      "severity": "medium"
    },
    {
      "requirement_id": "R-002",
      "issue": "Response time < 100ms may conflict with complex payment processing",
      "severity": "high"
    }
  ]
}

→ Agent A goes back to stakeholder for clarification
→ After resolution, Agent B approves
→ Only then handoff to Architect
```

**Status:** ✅ MASTERED (Day 7)

**Integration Points:**
- Dramatically improves handoff quality to Architect
- Reduces Architect clarification requests by ~50%
- Peer review logs stored in `docs/epics/<epic>/reviews/analyst_peer_review.md`

---

## Day 8 · Token Management & Context Budgeting

**Capability:** Aware of token limits (12K context window); budget 10K for work, 2K safety margin.

**Use Case:**
- Long requirement gathering session: 20+ exchanges
- After 15 exchanges, used ~7.5K tokens (15 × 500 tokens/exchange)
- Analyst knows to compress conversation before hitting limit
- Compress 7.5K → 1.5K using Day 15 technique, freeing 6K tokens

**Key Technique:**
- Track tokens per exchange: ~400-500 tokens average
- Formula: Remaining budget = 10K - (num_exchanges × 500)
- When remaining < 3K, trigger compression or wrap up
- Reserve 2K tokens for final JSON output + system prompts

**Example Session:**
```
Exchange 1: 450 tokens
Exchange 2: 520 tokens
...
Exchange 15: 480 tokens
→ Total: 7,350 tokens used (73% of budget)

Analyst: "Approaching token limit (7.3K/10K). I'll compress our conversation now."
[Applies Day 15 compression: 7.3K → 1.5K]
→ New budget: 1.5K used, 8.5K available
→ Can continue gathering or proceed to synthesis
```

**Token Budget Breakdown:**
```
12K total context window:
- System prompts: 800 tokens (fixed)
- Conversation history: 1,500 tokens (compressed)
- Active gathering: 6,000 tokens (buffer)
- Final JSON output: 2,000 tokens (reserved)
- Safety margin: 1,700 tokens
```

**Status:** ✅ MASTERED (Day 8)

**Integration Points:**
- Directly implements `docs/operational/context_limits.md` budgets
- Enables longer requirement sessions without overflow
- Compression technique (Day 15) becomes critical dependency
- See example: `docs/roles/analyst/examples/day_8_token_budgeting.md`

---

## Day 9 · MCP Integration for Requirements Discovery

**Capability:** Query MCP tools to discover existing requirements, past decisions, and reusable patterns.

**Use Case:**
- Gathering requirements for "new payment system"
- Query MCP tool: "Find past epics related to payments"
- Discover EP15 (previous payment API) and EP19 (payment gateway integration)
- Reference past requirements as templates

**Key Technique:**
- Connect to MCP server: `mcp.tools.list()` → discover available tools
- Use tool: `search_requirements(keywords=["payment", "transaction"])`
- Results feed into current requirement gathering as context
- Cite sources in output: `"Based on EP15_req#42..."`

**Example:**
```python
# MCP tool discovery
tools = mcp_client.list_tools()
# → ["search_requirements", "get_epic_summary", "find_decisions"]

# Query for related requirements
results = mcp_client.call_tool(
    "search_requirements",
    keywords=["payment", "processing"],
    epic_range=["EP10", "EP20"]
)

# Results:
[
  {
    "epic": "EP15",
    "req_id": "R-42",
    "text": "Payment processing < 2 seconds",
    "clarity_score": 0.9
  }
]

# Use in current requirements
new_req = {
  "id": "REQ-001",
  "text": "Payment processing < 2 seconds",
  "rag_citation": "Adapted from EP15_req#42",
  "notes": "Proven pattern from successful EP15"
}
```

**Status:** ✅ MASTERED (Day 9)

**Integration Points:**
- MCP tools become requirement discovery mechanism
- Reduces "reinventing the wheel" for common patterns
- Citations improve traceability across epics
- See `docs/guides/en/MCP_TOOL_USAGE.md` for tool catalog

---

## Day 10 · Custom MCP Tool for Requirement Validation

**Capability:** Create custom MCP tool to validate requirements against organizational standards.

**Use Case:**
- Organization has "requirement quality checklist" (10 criteria)
- Analyst creates MCP tool: `validate_requirement(req_id)`
- Tool checks: Has acceptance criteria? Testable? Non-ambiguous?
- Auto-validation before handoff

**Key Technique:**
- Implement MCP tool with FastMCP:
  ```python
  @mcp.tool()
  def validate_requirement(req: RequirementInput) -> ValidationResult:
      """Validate requirement against org standards."""
      checks = [
          has_acceptance_criteria(req),
          is_testable(req),
          has_priority(req),
          within_scope_guidelines(req)
      ]
      return {"passed": all(checks), "issues": [...]}
  ```
- Register tool in MCP server config
- Analyst agent calls tool for each requirement before handoff

**Example Validation:**
```
Input:
{
  "id": "REQ-001",
  "text": "System should be fast",
  "type": "functional"
}

Tool output:
{
  "passed": false,
  "issues": [
    "Missing acceptance criteria (required)",
    "Ambiguous: 'fast' not measurable",
    "No priority specified"
  ],
  "recommendation": "Add: 'Response time < 2s (p95)' + priority: high"
}

→ Analyst revises requirement before handoff
```

**Status:** ✅ MASTERED (Day 10)

**Integration Points:**
- Enforces organizational quality standards automatically
- Reduces Architect/Tech Lead rework
- Tool reusable across all epics
- Validation results logged in `docs/epics/<epic>/validation_report.md`

---

## Day 11 · Shared Infrastructure Awareness

**Capability:** Understand shared infrastructure constraints and embed them in requirements.

**Use Case:**
- Gathering requirements for new feature
- Must align with shared infra: MongoDB, Prometheus, Grafana, MCP server
- Requirements include constraints: "Must use MongoDB for persistence", "Must emit Prometheus metrics"

**Key Technique:**
- Load shared infra constraints from `docs/operational/shared_infra.md`
- Auto-inject infrastructure requirements into every epic:
  - "Must integrate with existing MongoDB cluster"
  - "Must expose /health and /metrics endpoints"
  - "Must emit structured logs compatible with Loki"
- Tag as non-negotiable: `priority: "critical", type: "constraint"`

**Example Auto-Injected Requirements:**
```json
{
  "requirements": [
    {
      "id": "REQ-INFRA-001",
      "text": "Service must connect to shared MongoDB cluster (mongodb://shared-mongo:27017)",
      "type": "constraint",
      "priority": "critical",
      "source": "shared_infra.md#mongodb",
      "non_negotiable": true
    },
    {
      "id": "REQ-INFRA-002",
      "text": "Service must expose Prometheus metrics at /metrics endpoint",
      "type": "constraint",
      "priority": "critical",
      "source": "shared_infra.md#observability"
    }
  ]
}
```

**Status:** ✅ MASTERED (Day 11)

**Integration Points:**
- Aligns with `docs/specs/day11-17_summary.md` infrastructure baseline
- Architect gets infrastructure constraints upfront (no surprises)
- Tech Lead can plan deployment knowing infrastructure is standardized
- See `docs/operational/shared_infra.md` for full constraint list

---

## Day 12 · Deployment & Health Check Requirements

**Capability:** Embed deployment readiness and health check acceptance criteria in requirements.

**Use Case:**
- Every epic now includes deployment requirements:
  - "Must have /health endpoint returning 200 when ready"
  - "Must support docker-compose.yml for local development"
  - "Must pass smoke tests in staging before production"

**Key Technique:**
- Template-based deployment requirements (auto-injected):
  ```json
  {
    "id": "REQ-DEPLOY-001",
    "text": "Service must expose /health endpoint",
    "acceptance_criteria": [
      "GET /health returns 200 when service ready",
      "Returns 503 if dependencies unavailable",
      "Response includes version and uptime"
    ]
  }
  ```
- Reference quick-start guides in requirement notes
- Coordinate with Tech Lead for environment-specific requirements

**Example Deployment Requirements:**
```json
{
  "deployment_requirements": [
    {
      "id": "REQ-DEPLOY-001",
      "text": "Service must expose /health endpoint",
      "acceptance_criteria": [
        "GET /health returns 200 when ready",
        "Returns 503 if dependencies unavailable"
      ]
    },
    {
      "id": "REQ-DEPLOY-002",
      "text": "Service must start via docker-compose up",
      "acceptance_criteria": [
        "Single command startup",
        "All dependencies auto-configured",
        "Logs visible via docker-compose logs"
      ],
      "reference": "docs/guides/en/DOCKER_SETUP.md"
    },
    {
      "id": "REQ-DEPLOY-003",
      "text": "Smoke tests must pass before production deployment",
      "acceptance_criteria": [
        "All critical paths tested",
        "Tests complete in < 5 minutes",
        "CI gates on smoke test results"
      ]
    }
  ]
}
```

**Status:** ✅ MASTERED (Day 12)

**Integration Points:**
- Tech Lead uses for rollout planning
- Developer knows deployment expectations upfront
- Smoke tests become acceptance criteria
- See `docs/guides/en/DEPLOYMENT.md` for deployment standards

---

## Day 13 · Environment & Integration Requirements

**Capability:** Define requirements for real environment integration (Docker, emulators, test harnesses).

**Use Case:**
- Feature requires testing in Docker container
- Requirements specify: "Must run in isolated Docker environment", "Must not depend on host filesystem"
- Enables automated testing and CI/CD

**Key Technique:**
- Environment requirements category:
  ```json
  {
    "environment_requirements": [
      {
        "id": "REQ-ENV-001",
        "text": "Feature must run in Docker container",
        "acceptance_criteria": [
          "No host filesystem dependencies",
          "All config via environment variables",
          "Container image < 500MB"
        ]
      }
    ]
  }
  ```
- Reference Docker setup guides
- Specify test environment constraints

**Status:** ✅ MASTERED (Day 13)

**Integration Points:**
- Tech Lead uses for CI/CD pipeline design
- Developer knows containerization requirements
- Enables Day 14 (code analysis in containers)

---

## Day 14 · Code Analysis Requirements & Quality Gates

**Capability:** Define requirements for code quality, analysis, and automated review gates.

**Use Case:**
- Epic requires code analysis before merge
- Requirements specify: "Code must pass linting", "Test coverage ≥ 80%", "No security vulnerabilities"
- These become CI gate acceptance criteria

**Key Technique:**
- Quality gate requirements:
  ```json
  {
    "quality_requirements": [
      {
        "id": "REQ-QUALITY-001",
        "text": "Code must pass all linters",
        "acceptance_criteria": [
          "flake8: 0 errors",
          "mypy: 100% type coverage",
          "black: code formatted"
        ],
        "ci_gate": "lint"
      },
      {
        "id": "REQ-QUALITY-002",
        "text": "Test coverage must be ≥ 80%",
        "acceptance_criteria": [
          "Line coverage ≥ 80%",
          "Branch coverage ≥ 75%",
          "No untested critical paths"
        ],
        "ci_gate": "coverage"
      }
    ]
  }
  ```
- Map requirements to CI gates
- Tech Lead uses for pipeline configuration

**Status:** ✅ MASTERED (Day 14)

**Integration Points:**
- Defines CI/CD gates in requirements phase
- Tech Lead configures pipelines based on these requirements
- Reviewer uses quality gates for automated checks
- See `docs/reference/en/TESTING.md` for quality standards

---

## Day 15 · Dialog Compression & Summarization

**Capability:** Compress long requirement gathering sessions (8K tokens → 1.6K) while preserving critical information.

**Use Case:**
- 20-exchange requirement session: 8,000 tokens
- Compress to 1,600 tokens (80% reduction)
- Preserve: clarity scores, key decisions, open questions, acceptance criteria
- Lose: timestamps, conversational filler, redundant details

**Key Technique:**
- Map-Reduce pattern:
  1. **Map**: Group exchanges by topic (payment methods, security, performance)
  2. **Reduce**: Summarize each group to core decisions
  3. **Merge**: Combine summaries with decision tree structure
- Lossy compression (remove): timestamps, greetings, redundant confirmations
- Lossless preservation: decisions, constraints, unclear points, acceptance criteria

**Example Compression:**

**BEFORE (8K tokens):**
```
Exchange 1: What's the scope?
User: We need payment processing, reporting, dashboards
Agent: Got it. Let me dive deeper into payment processing...

Exchange 2: Any regulatory needs?
User: Yes, PCI compliance, GDPR
Agent: Noted. What about...

[... 18 more exchanges with timestamps, filler, conversational back-and-forth ...]

Exchange 20: Timeline?
User: 3 months MVP, then scale
Agent: Perfect, I have everything I need.
```

**AFTER (1.6K tokens):**
```markdown
# COMPRESSION SUMMARY (Day 15 Pattern)

## Core Requirements (High Clarity: 0.85)
- Payment processing: Credit card (Visa/MC/AmEx), PayPal, bank transfer
- Reporting: Daily/monthly reports, CSV export, drill-down by merchant
- Dashboard: Real-time transaction view, 24h data lag acceptable
- Authentication: OAuth2 for API access, JWT tokens

## Constraints (Certainty: 100%)
- PCI compliance mandatory (Level 1 merchant)
- GDPR data handling required (EU customers)
- 3-month MVP timeline → December 15, 2025 launch
- Budget: $50K infrastructure, $200K development

## Open Questions (Needs Clarification)
1. Refund timeline not specified (ask Product Owner: same-day? 7-day?)
2. International markets unclear (Which regions: US+EU only? APAC?)
3. Scaling metrics TBD (CTO input needed: 10K tps? 100K tps?)
4. Offline mode: Required or nice-to-have?

## Decision Points (Finalized)
- ✅ Use Stripe as primary payment provider (if available)
- ✅ Store sensitive data encrypted (AES-256)
- ✅ Daily reports job scheduled at 00:00 UTC
- ✅ Fallback to PayPal if Stripe unavailable

## Action Items
- [ ] Clarify refund policy with Product Owner (by Nov 20)
- [ ] Confirm CTO on scaling architecture (by Nov 18)
- [ ] Get legal approval for GDPR handling (by Nov 22)

## Metadata
- Original tokens: 8,000
- Compressed tokens: 1,600
- Compression ratio: 80%
- Information retention: 92% (measured by clarity alignment)
- Exchanges: 20 → Summarized by topic
```

**Compression Quality Metrics:**
```
Before compression:
- Tokens: 8,000
- Clarity score: 0.85
- Completeness: 0.88

After compression:
- Tokens: 1,600 (80% reduction)
- Clarity score: 0.83 (2% loss - acceptable)
- Completeness: 0.87 (1% loss - acceptable)

→ 80% token savings, 92% information retained
```

**Status:** ✅ MASTERED (Day 15)

**Integration Points:**
- **Critical for Day 8 token management**: Enables long sessions without overflow
- **Architect benefit**: Gets full context in compressed form (saves tokens)
- **Tech Lead benefit**: Clear decision summary, no conversational noise
- **Traceability**: Compression metadata logged for audit
- See detailed example: `docs/roles/analyst/examples/day_15_compression.md`

---

## Day 16 · External Memory for Requirements

**Capability:** Persist requirements and conversation state to SQLite/MongoDB for cross-session continuity.

**Use Case:**
- Requirement gathering spans multiple days/sessions
- Session 1: Gather functional requirements → Save to DB
- Session 2: Load previous session, continue with non-functional requirements
- Session 3: Load full history, perform final validation

**Key Technique:**
- Store in MongoDB `requirements` collection:
  ```javascript
  {
    "session_id": "sess_20251115_001",
    "epic_id": "EP20",
    "timestamp": "2025-11-15T10:30:00Z",
    "exchanges": [
      {"role": "user", "content": "...", "timestamp": "..."},
      {"role": "analyst", "content": "...", "timestamp": "..."}
    ],
    "current_requirements": [...],
    "clarity_score": 0.75,
    "status": "in_progress"
  }
  ```
- Load previous session: `db.requirements.findOne({session_id: "sess_20251115_001"})`
- Resume conversation with full context

**Example Multi-Session Flow:**
```
Session 1 (Nov 15, 10:00):
- Gather functional requirements
- Save to DB: {"requirements": [R-001, R-002, R-003], "status": "in_progress"}

Session 2 (Nov 16, 14:00):
- Load Session 1 from DB
- Continue with security requirements
- Save: {"requirements": [R-001...R-006], "status": "in_progress"}

Session 3 (Nov 17, 09:00):
- Load full history from DB
- Final validation and synthesis
- Save: {"requirements": [R-001...R-010], "status": "complete", "clarity_score": 0.88}
```

**Status:** ✅ MASTERED (Day 16)

**Integration Points:**
- Enables multi-day requirement gathering for complex epics
- Persistent storage means no lost context between sessions
- MongoDB queries (Day 22 RAG) can reference past sessions
- See `docs/operational/shared_infra.md#mongodb` for schema

---

## Day 17 · Integration Contracts & Acceptance Mapping

**Capability:** Define integration contracts between components and map to acceptance criteria.

**Use Case:**
- Epic has multiple components: PaymentService, ReportingService, Dashboard
- Define integration contracts: "PaymentService → ReportingService: POST /events"
- Map contracts to acceptance criteria: "Integration test must verify event delivery"

**Key Technique:**
- Integration requirement type:
  ```json
  {
    "integration_requirements": [
      {
        "id": "REQ-INT-001",
        "text": "PaymentService must send transaction events to ReportingService",
        "contract": {
          "source": "PaymentService",
          "target": "ReportingService",
          "endpoint": "POST /api/v1/events",
          "payload_schema": "schemas/transaction_event.json"
        },
        "acceptance_criteria": [
          "Integration test verifies event delivery",
          "Events arrive within 5 seconds",
          "Failed events trigger retry (3 attempts)"
        ]
      }
    ]
  }
  ```
- Reference contract schemas in `contracts/` directory
- Architect uses for component design
- Tech Lead uses for integration test planning

**Status:** ✅ MASTERED (Day 17)

**Integration Points:**
- Defines inter-component contracts at requirements phase
- Architect designs component interfaces based on contracts
- Tech Lead creates integration tests from acceptance criteria
- See `contracts/INTEGRATION_GUIDE.md` for contract patterns
- Aligns with `docs/specs/day11-17_summary.md#integration`

---

## Day 18 · Real-World Task Requirements

**Capability:** Translate real-world business tasks into detailed technical requirements.

**Use Case:**
- Business task: "Deploy app to production app store"
- Analyst breaks down into technical requirements:
  - App store account setup
  - Build signing certificates
  - Submission guidelines compliance
  - Post-deployment monitoring

**Key Technique:**
- Decompose business goal into technical steps
- For each step, create requirement with acceptance criteria
- Include external dependencies (app store approval, DNS, certificates)
- Map to operational runbooks

**Example Decomposition:**
```
Business Task: Deploy payment app to production

Technical Requirements:
REQ-PROD-001: "App must be signed with production certificate"
  AC: Certificate valid for ≥1 year, stored in secrets manager

REQ-PROD-002: "App store submission must include privacy policy"
  AC: Policy reviewed by legal, accessible at /privacy URL

REQ-PROD-003: "DNS must point to production load balancer"
  AC: Health checks pass, SSL certificate valid, CDN configured

REQ-PROD-004: "Monitoring alerts configured for production"
  AC: Prometheus rules deployed, PagerDuty integration tested

REQ-PROD-005: "Rollback plan documented and tested"
  AC: Rollback completes in < 10 minutes, tested in staging
```

**Status:** ✅ MASTERED (Day 18)

**Integration Points:**
- Bridges business goals and technical execution
- Tech Lead uses for production readiness checklist
- Operations uses for runbook generation
- See `docs/guides/en/DEPLOYMENT.md` for production standards

---

## Day 19 · Document Indexing Requirements

**Capability:** Define requirements for document indexing, chunking, and embedding generation.

**Use Case:**
- Epic requires RAG system for documentation search
- Requirements specify: chunk size, overlap, embedding model, index storage
- These become acceptance criteria for indexer implementation

**Key Technique:**
- RAG system requirements:
  ```json
  {
    "rag_requirements": [
      {
        "id": "REQ-RAG-001",
        "text": "Documents must be chunked for embedding",
        "acceptance_criteria": [
          "Chunk size: 512 tokens (with 50 token overlap)",
          "Preserve markdown structure in chunks",
          "Metadata: source file, chunk index, timestamp"
        ]
      },
      {
        "id": "REQ-RAG-002",
        "text": "Embeddings generated using text-embedding-ada-002",
        "acceptance_criteria": [
          "1536-dimensional vectors",
          "Batch processing: 100 chunks per API call",
          "Retry logic for API failures"
        ]
      },
      {
        "id": "REQ-RAG-003",
        "text": "Index stored in FAISS with metadata",
        "acceptance_criteria": [
          "Index serialized to disk (persistent)",
          "Metadata stored in SQLite for filtering",
          "Index rebuild completes in < 10 minutes"
        ]
      }
    ]
  }
  ```
- Reference embedding models, index formats
- Specify performance requirements

**Status:** ✅ MASTERED (Day 19)

**Integration Points:**
- Enables Day 20 (RAG queries) with clear requirements
- Architect designs indexer based on these specs
- Developer knows exact implementation requirements
- See `docs/specs/epic_20/epic_20.md` for RAG architecture

---

## Day 20 · RAG Query Requirements

**Capability:** Define requirements for RAG-based requirement discovery and validation.

**Use Case:**
- Analyst gathering requirements for "payment system"
- Should query RAG index: "Find similar past requirements"
- Requirements specify: similarity threshold, result limit, ranking method

**Key Technique:**
- RAG query requirements:
  ```json
  {
    "rag_query_requirements": [
      {
        "id": "REQ-RAG-Q-001",
        "text": "Analyst must query RAG index for similar requirements",
        "acceptance_criteria": [
          "Similarity threshold: cosine similarity ≥ 0.75",
          "Result limit: Top 5 matches",
          "Results ranked by similarity + recency"
        ]
      },
      {
        "id": "REQ-RAG-Q-002",
        "text": "Query results must include source citations",
        "acceptance_criteria": [
          "Each result includes: epic_id, req_id, similarity_score",
          "Results link to original requirement doc",
          "Metadata: creation date, clarity_score, status"
        ]
      }
    ]
  }
  ```
- Compare requirements with/without RAG:
  - Without RAG: 100% original requirements (risk of duplication)
  - With RAG: 60% original + 40% adapted from past epics (consistency)

**Status:** ✅ MASTERED (Day 20)

**Integration Points:**
- Analyst role queries RAG during requirement gathering
- Improves consistency across epics (reuse proven patterns)
- See `docs/roles/analyst/rag_queries.md` for query patterns
- See `docs/specs/epic_20/queries.jsonl` for example queries

---

## Day 21 · Reranking & Filtering Requirements

**Capability:** Define requirements for reranking RAG results to improve relevance.

**Use Case:**
- RAG query returns 10 results, but only top 3 are truly relevant
- Reranker applies second-stage model to refine ranking
- Requirements specify: reranker model, threshold, performance budget

**Key Technique:**
- Reranking requirements:
  ```json
  {
    "reranking_requirements": [
      {
        "id": "REQ-RERANK-001",
        "text": "RAG results must be reranked for relevance",
        "acceptance_criteria": [
          "Use cross-encoder model (e.g., ms-marco-MiniLM)",
          "Rerank top 10 → select top 3",
          "Relevance threshold: score ≥ 0.70"
        ]
      },
      {
        "id": "REQ-RERANK-002",
        "text": "Filter out low-relevance results",
        "acceptance_criteria": [
          "Minimum similarity: 0.75 (first stage)",
          "Minimum rerank score: 0.70 (second stage)",
          "If no results pass filters, return empty (no hallucination)"
        ]
      }
    ]
  }
  ```
- Performance requirements: reranking adds ≤500ms latency
- Compare quality: RAG without reranking vs with reranking
  - Without: 60% relevant results
  - With: 85% relevant results

**Status:** ✅ MASTERED (Day 21)

**Integration Points:**
- Improves Day 20 RAG query quality
- Reduces irrelevant results shown to Analyst
- See `config/retrieval_rerank_config.yaml` for configuration

---

## Day 22 · Citations & Source Attribution in Requirements

**Capability:** Include RAG citations in requirement outputs; link to source epics/requirements.

**Use Case:**
- Gathering requirements for "payment system"
- Query RAG: "Find similar payment requirements from past epics"
- Results: EP15_req#42 (payment API), EP19_req#78 (payment gateway)
- Output includes: `rag_citations: ["EP15_req#42", "EP19_req#78"]`
- Architect sees precedents, can reuse design patterns

**Key Technique:**
- Include RAG citations in every requirement that references past work:
  ```json
  {
    "requirements": [
      {
        "id": "REQ-001",
        "text": "Payment processing must complete in < 2 seconds",
        "rag_citation": {
          "source": "EP15_req#42",
          "similarity": 0.92,
          "reason": "Proven performance target from successful payment API"
        },
        "acceptance_criteria": [
          "Transaction completes in < 2s (p95)",
          "Same performance target as EP15 (validated in production)"
        ]
      }
    ],
    "summary": {
      "rag_citations": [
        {
          "epic": "EP15",
          "req_id": "R-42",
          "reused_patterns": ["Performance targets", "Error handling"]
        },
        {
          "epic": "EP19",
          "req_id": "R-78",
          "reused_patterns": ["Multi-provider support", "Fallback logic"]
        }
      ]
    }
  }
  ```

**MongoDB Query Example:**
```javascript
db.requirements.find({
  keywords: { $in: ["payment", "transaction", "processing"] },
  epic: { $gte: "EP10" },  // Recent epics only
  clarity_score: { $gte: 0.8 },
  status: "approved"
}).sort({ created_at: -1 }).limit(5)
```

**Example Query Results:**
```json
[
  {
    "epic": "EP15",
    "req_id": "R-42",
    "text": "System must process credit card payments within 2 seconds",
    "clarity_score": 0.9,
    "acceptance_criteria": [
      "Transaction completes in < 2s (p95)",
      "PCI compliance maintained",
      "Successful transactions logged"
    ],
    "status": "approved",
    "production_validated": true
  },
  {
    "epic": "EP19",
    "req_id": "R-78",
    "text": "Support multiple payment providers with automatic failover",
    "clarity_score": 0.85,
    "acceptance_criteria": [
      "Primary: Stripe, Fallback: PayPal",
      "Failover within 5 seconds",
      "Provider health checks every 30s"
    ],
    "status": "approved"
  }
]
```

**Analyst Output with Citations:**
```json
{
  "epic_id": "EP23",
  "requirements": [
    {
      "id": "REQ-001",
      "text": "System must process payments within 2 seconds",
      "rag_citation": "Based on EP15_req#42 (production-validated)",
      "clarity_score": 0.88,
      "acceptance_criteria": [
        "Transaction < 2s (p95) - same as EP15",
        "PCI compliance maintained",
        "Logging matches EP15 format"
      ]
    },
    {
      "id": "REQ-002",
      "text": "Support Stripe and PayPal with automatic failover",
      "rag_citation": "Pattern from EP19_req#78",
      "clarity_score": 0.86,
      "acceptance_criteria": [
        "Failover < 5s (EP19 standard)",
        "Health checks every 30s (EP19 pattern)"
      ]
    }
  ],
  "rag_summary": {
    "queries_performed": 2,
    "total_citations": 2,
    "token_cost": 450,
    "patterns_reused": [
      "Performance targets (EP15)",
      "Multi-provider architecture (EP19)",
      "Error handling (EP15, EP19)"
    ]
  },
  "notes": "Leveraged proven patterns from EP15 (payment API) and EP19 (payment gateway). Reduces design risk and implementation time by ~30%."
}
```

**Impact Metrics:**
```
Without RAG Citations:
- Design time: 3 days
- Rework rate: 25% (unknowingly duplicating past mistakes)
- Architect questions: 15

With RAG Citations (Day 22):
- Design time: 2 days (33% faster)
- Rework rate: 8% (reusing validated patterns)
- Architect questions: 5 (clearer requirements)

→ 30% time savings, 17% quality improvement
```

**Status:** ✅ MASTERED (Day 22)

**Integration Points:**
- **Architect benefit**: Sees precedents, can reference EP15/EP19 designs
- **Tech Lead benefit**: Implementation plans can reuse EP15/EP19 code
- **Developer benefit**: Can copy code patterns from cited epics
- **Traceability**: Full audit trail from current requirement → past epic
- **Quality**: Reduces reinventing wheel, improves consistency
- See detailed example: `docs/roles/analyst/examples/day_22_rag_citations.md`
- See query patterns: `docs/roles/analyst/rag_queries.md`

---

## Capability Summary Matrix

| Day | Capability | Primary Benefit | Integration Impact |
|-----|------------|-----------------|-------------------|
| 1 | Basic conversation | Structured requirement capture | Foundation for all roles |
| 2 | Structured output | Parseable JSON handoffs | Architect/Tech Lead automation |
| 3 | Stopping conditions | Know when to stop asking | Higher quality, less noise |
| 4 | Temperature tuning | Creative questions + precise parsing | Better requirement clarity |
| 5 | Model selection | Cost optimization | Budget management |
| 6 | Chain of Thought | Catch contradictions early | Fewer Architect clarifications |
| 7 | Peer review | Multi-agent validation | 50% fewer handoff issues |
| 8 | Token management | Long sessions without overflow | Enables complex epics |
| 9 | MCP integration | Discover past requirements | Pattern reuse |
| 10 | Custom validation | Automated quality checks | Enforces standards |
| 11 | Infra awareness | Embed infra constraints | Architect gets complete picture |
| 12 | Deployment reqs | Health checks, smoke tests | Tech Lead rollout planning |
| 13 | Environment reqs | Docker, isolation | CI/CD automation |
| 14 | Quality gates | Linting, coverage | Automated CI gates |
| 15 | Compression | 80% token reduction | Critical for Day 8 |
| 16 | External memory | Multi-session continuity | Complex epic support |
| 17 | Integration contracts | Component interfaces | Architect component design |
| 18 | Real-world tasks | Business → technical | Operations runbooks |
| 19 | Document indexing | RAG foundation | Enables Day 20-22 |
| 20 | RAG queries | Find similar requirements | 40% pattern reuse |
| 21 | Reranking | Improve RAG relevance | 85% vs 60% relevance |
| 22 | Citations | Source attribution | 30% time savings, audit trail |

---

## Upcoming Days 23-28 ⏳

### Planned Capabilities (Future Enhancement)

**Day 23 · Observability Requirements**
- Define logging, metrics, and tracing requirements
- Map observability to acceptance criteria
- Integration with Prometheus/Grafana

**Day 24 · Security Requirements & Threat Modeling**
- Threat modeling for each epic
- Security acceptance criteria
- OWASP Top 10 compliance checks

**Day 25 · Performance Budgets**
- Define performance budgets per component
- SLA/SLO requirements
- Load testing acceptance criteria

**Day 26 · Cost Optimization Requirements**
- Cloud cost budgets
- Token usage optimization
- Infrastructure cost acceptance criteria

**Day 27 · Compliance & Audit Requirements**
- Regulatory compliance (GDPR, PCI, SOC2)
- Audit trail requirements
- Compliance acceptance criteria

**Day 28 · Knowledge Transfer & Documentation Requirements**
- Documentation completeness criteria
- Runbook requirements
- Knowledge transfer acceptance

**Day 23 · Observability & Benchmark Enablement (Epic 23)**
- **Capability:** Self-observe Analyst workflow using Prometheus metrics, structured logs, and tracing metadata stored in MongoDB.
- **Use Case:** Analyst agent reviews handoff quality by querying telemetry metadata (trace_id, epic_id, stage_id, latency_ms) from observability endpoints.
- **Key Technique:**
  - Query `/metrics` endpoints on MCP/Butler/CLI to verify handoff completion metrics
  - Include observability metadata (`trace_id`, `epic_id`, `stage_id`, `latency_ms`) in handoff JSON
  - Use structured logs to track requirement gathering quality scores
  - Reference benchmark export duration metrics to validate dataset completeness
- **Example Output with Observability Metadata:**
```json
{
  "metadata": {
    "epic_id": "EP23",
    "analyst_version": "v1.0",
    "timestamp": "2025-11-16T13:00:00Z",
    "trace_id": "550e8400-e29b-41d4-a716-446655440000",
    "stage_id": "TL-04",
    "latency_ms": 2450,
    "observability": {
      "metrics_endpoint": "http://localhost:8004/metrics",
      "structured_logs_total": 127,
      "benchmark_export_duration_seconds": 12.5,
      "shared_infra_bootstrap_status": {"mongo": 1, "mock_services": 1}
    }
  },
  "requirements": [
    {
      "id": "REQ-001",
      "text": "System must expose Prometheus metrics on /metrics endpoints",
      "type": "observability",
      "priority": "high",
      "acceptance_criteria": [
        "MCP HTTP server /metrics returns non-zero values for new Epic 23 metrics",
        "Butler bot metrics_server exposes structured_logs_total counter",
        "CLI backoffice commands emit benchmark_export_duration_seconds histogram"
      ],
      "telemetry_evidence": {
        "promql_query": "rate(structured_logs_total[5m])",
        "expected_min_value": 0.1
      }
    }
  ]
}
```
- **Status:** ✅ MASTERED (Day 23, Epic 23)
- **Integration Points:**
  - Observability metadata flows from Analyst handoff JSON to Architect/Tech Lead acceptance matrix
  - Trace IDs link requirements to implementation commits via MongoDB audit trail
  - Benchmark metrics validate dataset completeness before exporter verification (TL-01/TL-02)
- **Self-Observation Pattern:**
  - Analyst queries own telemetry: `curl http://localhost:8004/metrics | grep structured_logs_total`
  - Verifies handoff quality by checking latency_ms in handoff JSON metadata
  - Uses trace_id to correlate requirement gathering sessions with downstream stage outcomes

---

## Linked Assets

- **Role Definition**: `docs/roles/analyst/role_definition.md`
- **RAG Queries**: `docs/roles/analyst/rag_queries.md`
- **Examples**: `docs/roles/analyst/examples/`
- **Handoff Contracts**: `docs/operational/handoff_contracts.md`
- **Context Limits**: `docs/operational/context_limits.md`
- **Workflow**: `docs/specs/process/agent_workflow.md`

---

## Update Log

- ✅ 2025-11-15: Comprehensive Day 1-22 capabilities documented
- ✅ Integration points mapped to Architect/Tech Lead/Developer roles
- ✅ Examples created for Days 3, 8, 15, 22
- ✅ RAG queries enhanced with citations pattern (Day 22)
- ✅ 2025-11-16: Day 23 observability capability added with self-observation pattern
- ✅ Example created: `docs/roles/analyst/examples/day_23_observability.md`
- [ ] Days 24-28: Pending epic scope definition
>>>>>>> origin/master
